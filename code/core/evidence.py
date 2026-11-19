"""Lưu bằng chứng vi phạm: SQLite (thư viện sqlite3 có sẵn của Python) + ảnh/clip trên ổ đĩa.

Thiết kế (đã chốt 11/11/2026):
- Một tệp events.db, bảng `events`: mỗi lượt xâm nhập là một dòng. Trong DB chỉ lưu ĐƯỜNG DẪN tới tệp bằng chứng.
- Bằng chứng mỗi lượt: ảnh toàn cảnh có vẽ vùng cấm + khung người + ID + thời điểm; ảnh cắt riêng người vi phạm;
  clip ngắn ~3 s trước và ~3 s sau lúc cảnh báo (tùy chọn, dùng bộ đệm vòng).
- Mọi thao tác ghi đĩa/DB chạy ở MỘT LUỒNG RIÊNG thông qua hàng đợi -> luồng xử lý video chỉ tốn thời gian
  sao chép khung hình, không chờ ghi đĩa, nên không làm giảm FPS và không ảnh hưởng phép đo FP32/INT8.
- Thời gian lưu theo mốc thời gian của video (giây, tính từ số thứ tự khung / FPS).

Cách dùng:
    ev = EvidenceStore("events.db", "evidence", model_version="int8", fps=25, clip_seconds=3)
    for f, frame in ...:
        ev.push_frame(frame)                                    # cho bộ đệm vòng (chỉ khi bật clip)
        for e in alarm.update(f, dets):
            if e["type"] == "alert": ev.on_alert(video_id, zone_id, e, frame, polygons)
            else:                    ev.on_exit(video_id, zone_id, e["track_id"], e["frame"])
    ev.close()                                                  # chờ ghi xong mọi thứ
"""
import collections, csv, json, os, queue, sqlite3, threading
from datetime import datetime
import cv2
import numpy as np

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id      TEXT    NOT NULL,
    zone_id       TEXT    NOT NULL,
    track_id      INTEGER NOT NULL,
    frame_enter   INTEGER,
    frame_alert   INTEGER NOT NULL,
    frame_exit    INTEGER,
    t_enter       REAL,              -- giây, theo thời gian của video
    t_alert       REAL    NOT NULL,
    t_exit        REAL,
    confidence    REAL,
    bbox          TEXT,              -- JSON [x1, y1, x2, y2] theo khung hình xử lý
    model_version TEXT,              -- vd: pytorch_fp32 / openvino_fp32 / openvino_int8
    snapshot_path TEXT,
    crop_path     TEXT,
    clip_path     TEXT,
    created_at    TEXT    NOT NULL   -- thời điểm ghi (đồng hồ hệ thống), chỉ để tra cứu
);
CREATE INDEX IF NOT EXISTS idx_events_video ON events(video_id, zone_id);
CREATE INDEX IF NOT EXISTS idx_events_model ON events(model_version);
"""
ZONE_COLORS = [(0, 0, 255), (255, 0, 255), (0, 200, 255), (255, 200, 0)]


def draw_snapshot(frame, polygons, bbox, track_id, zone_id, t_alert, conf):
    """Ảnh toàn cảnh làm bằng chứng: vùng cấm, khung người vi phạm, ID, vùng, thời điểm."""
    im = frame.copy(); ov = im.copy()
    for i, (zid, poly) in enumerate(polygons):
        p = np.asarray(poly, np.int32); col = ZONE_COLORS[i % 4]
        cv2.fillPoly(ov, [p], col)
    im = cv2.addWeighted(ov, 0.2, im, 0.8, 0)
    for i, (zid, poly) in enumerate(polygons):
        cv2.polylines(im, [np.asarray(poly, np.int32)], True, ZONE_COLORS[i % 4], 2)
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(im, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.circle(im, ((x1 + x2) // 2, y2), 4, (0, 255, 255), -1)
    lab = f"ID {track_id} | {zone_id} | t={t_alert:.2f}s | conf {conf:.2f}"
    s = max(0.4, im.shape[1] / 1600)
    (tw, th), _ = cv2.getTextSize(lab, 0, s, 1)
    cv2.rectangle(im, (0, 0), (tw + 10, th + 12), (0, 0, 0), -1)
    cv2.putText(im, lab, (5, th + 5), 0, s, (255, 255, 255), 1, cv2.LINE_AA)
    return im


def crop_person(frame, bbox, pad=0.15):
    H, W = frame.shape[:2]; x1, y1, x2, y2 = bbox; w, h = x2 - x1, y2 - y1
    a, b = int(max(0, x1 - pad * w)), int(max(0, y1 - pad * h))
    c, d = int(min(W, x2 + pad * w)), int(min(H, y2 + pad * h))
    return frame[b:d, a:c].copy() if d > b and c > a else frame[0:1, 0:1].copy()


class EvidenceStore:
    def __init__(self, db_path, evidence_dir, model_version, fps=25.0, clip_seconds=0.0,
                 save_images=True, jpeg_quality=90):
        self.db_path, self.dir, self.model_version, self.fps = db_path, evidence_dir, model_version, float(fps)
        self.save_images, self.jq = save_images, jpeg_quality
        self.clip_n = int(round(clip_seconds * self.fps))
        self.ring = collections.deque(maxlen=self.clip_n) if self.clip_n else None
        self.pending_clips = []                 # [{"frames": [...], "left": n, "path": ...}]
        os.makedirs(self.dir, exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self.q = queue.Queue()
        self._open = {}                         # (video, zone, track) -> event_id (để cập nhật t_exit)
        self._id_ready = {}                     # khóa tạm -> threading.Event + id
        self.worker = threading.Thread(target=self._run, daemon=True); self.worker.start()

    # ---------- gọi từ luồng xử lý video (phải nhanh)
    def push_frame(self, frame):
        if self.ring is None: return
        self.ring.append(frame.copy())
        done = []
        for c in self.pending_clips:
            c["frames"].append(self.ring[-1]); c["left"] -= 1
            if c["left"] <= 0: done.append(c)
        for c in done:
            self.pending_clips.remove(c); self.q.put(("clip", c))

    def on_alert(self, video_id, zone_id, e, frame, polygons):
        """e: sự kiện 'alert' từ ZoneAlarm.update; polygons: [(zone_id, polygon), ...] theo khung hình xử lý."""
        fa = int(e["frame"]); fe = int(e.get("enter_frame", fa))
        key = (video_id, zone_id, int(e["track_id"]), fa)
        base = f"{video_id}_{zone_id}_id{int(e['track_id'])}_f{fa:06d}_{self.model_version}"
        clip_path = None
        if self.ring is not None:
            clip_path = os.path.join(self.dir, base + ".mp4")
            self.pending_clips.append({"frames": list(self.ring), "left": self.clip_n, "path": clip_path})
        self.q.put(("alert", {"key": key, "video_id": video_id, "zone_id": zone_id, "track_id": int(e["track_id"]),
                              "frame_enter": fe, "frame_alert": fa, "conf": float(e.get("conf", 0) or 0),
                              "bbox": [round(float(v), 1) for v in e["bbox"]], "frame": frame.copy(),
                              "polygons": polygons, "base": base, "clip_path": clip_path}))
        self._open[(video_id, zone_id, int(e["track_id"]))] = key

    def on_exit(self, video_id, zone_id, track_id, frame_idx):
        key = self._open.pop((video_id, zone_id, int(track_id)), None)
        if key is not None:
            self.q.put(("exit", {"key": key, "frame_exit": int(frame_idx)}))

    def close(self):
        for c in self.pending_clips:            # video hết trước khi đủ 3 s sau cảnh báo: ghi phần đã có
            self.q.put(("clip", c))
        self.pending_clips = []
        self.q.put(None); self.worker.join()

    def _rel(self, p):
        """Đường dẫn lưu trong DB: tương đối theo thư mục chứa events.db (di chuyển cả thư mục vẫn dùng được)."""
        return None if p is None else os.path.relpath(p, os.path.dirname(os.path.abspath(self.db_path))).replace(os.sep, "/")

    # ---------- luồng ghi
    def _run(self):
        con = sqlite3.connect(self.db_path); con.executescript(SCHEMA); ids = {}
        while True:
            item = self.q.get()
            if item is None: break
            kind, d = item
            try:
                if kind == "alert":
                    snap = crop = None
                    if self.save_images:
                        snap = os.path.join(self.dir, d["base"] + "_full.jpg")
                        crop = os.path.join(self.dir, d["base"] + "_crop.jpg")
                        t_alert = d["frame_alert"] / self.fps
                        cv2.imwrite(snap, draw_snapshot(d["frame"], d["polygons"], d["bbox"], d["track_id"], d["zone_id"],
                                                        t_alert, d["conf"]), [cv2.IMWRITE_JPEG_QUALITY, self.jq])
                        cv2.imwrite(crop, crop_person(d["frame"], d["bbox"]), [cv2.IMWRITE_JPEG_QUALITY, self.jq])
                    cur = con.execute(
                        "INSERT INTO events (video_id, zone_id, track_id, frame_enter, frame_alert, t_enter, t_alert,"
                        " confidence, bbox, model_version, snapshot_path, crop_path, clip_path, created_at)"
                        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (d["video_id"], d["zone_id"], d["track_id"], d["frame_enter"], d["frame_alert"],
                         round(d["frame_enter"] / self.fps, 3), round(d["frame_alert"] / self.fps, 3), round(d["conf"], 3),
                         json.dumps(d["bbox"]), self.model_version, self._rel(snap), self._rel(crop), self._rel(d["clip_path"]),
                         datetime.now().isoformat(timespec="seconds")))
                    con.commit(); ids[d["key"]] = cur.lastrowid
                elif kind == "exit":
                    eid = ids.get(d["key"])
                    if eid is not None:
                        con.execute("UPDATE events SET frame_exit=?, t_exit=? WHERE id=?",
                                    (d["frame_exit"], round(d["frame_exit"] / self.fps, 3), eid)); con.commit()
                elif kind == "clip":
                    fr = d["frames"]
                    if fr:
                        h, w = fr[0].shape[:2]
                        wr = cv2.VideoWriter(d["path"], cv2.VideoWriter_fourcc(*"mp4v"), self.fps, (w, h))
                        for f in fr: wr.write(f)
                        wr.release()
            except Exception as ex:             # không để lỗi ghi bằng chứng làm dừng hệ thống
                print("[evidence] loi:", kind, ex, flush=True)
        con.close()


def export_csv(db_path, out_csv, model_version=None):
    """Xuất bảng events ra CSV (để chấm điểm hoặc nộp kèm báo cáo)."""
    con = sqlite3.connect(db_path); con.row_factory = sqlite3.Row
    q, a = "SELECT * FROM events", ()
    if model_version: q, a = q + " WHERE model_version=?", (model_version,)
    rows = [dict(r) for r in con.execute(q + " ORDER BY video_id, zone_id, frame_alert", a)]
    con.close()
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        if rows:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    return len(rows)
