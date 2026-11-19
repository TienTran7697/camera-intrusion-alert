"""Luồng xử lý hoàn chỉnh của hệ thống (dùng chung cho dòng lệnh và giao diện):
video -> YOLO11n (PyTorch hoặc OpenVINO FP32/INT8) -> ByteTrack -> điểm chân trong vùng cấm -> logic cảnh báo
(+ bộ lọc) -> vẽ kết quả -> lưu bằng chứng (SQLite + ảnh + clip, luồng riêng).

Vùng cấm đọc theo tên video:
- Video CAVIAR:      Videos/CAVIAR/zones.json      {"zones": {video: {"polygon": [...]}}}  (384x288, xử lý nguyên cỡ)
- Video cửa hàng:    Videos/cua_hang_giay/zones.json {"frame_size": [2560,1440], "videos": {video: [{"zone_id","polygon"}]}}
  (khung hình được thu về 1280x720 trước khi xử lý, tọa độ vùng được quy đổi tương ứng)
- Video khác: tệp <video>.zones.json cạnh video, dạng {"frame_size": [W, H], "zones": [{"zone_id", "polygon"}]}.
"""
import json, os, time
import cv2
import numpy as np
from ultralytics import YOLO
from .alarm import ZoneAlarm, foot_point
from .evidence import EvidenceStore, ZONE_COLORS

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
MAX_W = 1280


def model_version_of(path):
    p = path.lower()
    if p.endswith(".pt"): return "pytorch_fp32"
    return "openvino_int8" if "int8" in p else "openvino_fp32"


def load_zones(video_path):
    """Trả về (danh sách [(zone_id, polygon)], cỡ khung xử lý (W, H) hoặc None = giữ nguyên)."""
    name = os.path.splitext(os.path.basename(video_path))[0]
    own = os.path.splitext(video_path)[0] + ".zones.json"
    cav = os.path.join(ROOT, "Videos/CAVIAR/zones.json"); shop = os.path.join(ROOT, "Videos/cua_hang_giay/zones.json")
    if os.path.exists(own):
        Z = json.load(open(own, encoding="utf-8")); fw, fh = Z["frame_size"]; zl = Z["zones"]
    elif name in json.load(open(cav)).get("zones", {}):
        return [("A", json.load(open(cav))["zones"][name]["polygon"])], None
    elif os.path.exists(shop) and name in json.load(open(shop, encoding="utf-8"))["videos"]:
        Z = json.load(open(shop, encoding="utf-8")); fw, fh = Z["frame_size"]; zl = Z["videos"][name]
    else:
        return [], None
    pw, ph = (MAX_W, round(fh * MAX_W / fw)) if fw > MAX_W else (fw, fh)
    s = fw / pw
    return [(z["zone_id"], [[x / s, y / s] for x, y in z["polygon"]]) for z in zl], ((pw, ph) if s != 1 else None)


class Pipeline:
    def __init__(self, model_path, zones, proc_size=None, conf=0.25, confirm=8, filters=None, imgsz=640,
                 evidence=None, video_id="video"):
        self.model = YOLO(model_path, task="detect"); self.model_version = model_version_of(model_path)
        self.zones, self.proc_size, self.conf, self.imgsz = zones, proc_size, conf, imgsz
        self.alarms = {zid: ZoneAlarm(poly, confirm, **(filters or {})) for zid, poly in zones}
        self.evidence, self.video_id = evidence, video_id
        self.f = -1; self.events = []

    def step(self, frame):
        """Xử lý một khung. Trả về (khung đã thu nhỏ, danh sách detection, sự kiện mới, thời gian ms)."""
        t0 = time.perf_counter(); self.f += 1
        if self.proc_size: frame = cv2.resize(frame, self.proc_size, interpolation=cv2.INTER_AREA)
        r = self.model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0], conf=self.conf,
                             imgsz=self.imgsz, device="cpu", verbose=False)[0]
        dets = []
        if r.boxes is not None and r.boxes.id is not None:
            for (x1, y1, x2, y2), tid, c in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist(), r.boxes.conf.tolist()):
                dets.append((tid, x1, y1, x2, y2, c))
        if self.evidence: self.evidence.push_frame(frame)
        new = []
        for zid, al in self.alarms.items():
            for e in al.update(self.f, dets):
                e = dict(e, zone_id=zid); new.append(e); self.events.append(e)
                if self.evidence:
                    if e["type"] == "alert": self.evidence.on_alert(self.video_id, zid, e, frame, self.zones)
                    else: self.evidence.on_exit(self.video_id, zid, e["track_id"], e["frame"])
        return frame, dets, new, (time.perf_counter() - t0) * 1000

    def alerting_ids(self):
        return {tid for al in self.alarms.values() for tid, st in al.tracks.items() if st.state == "in"}

    def draw(self, frame, dets, fps=None):
        im = frame.copy(); ov = im.copy(); hot = self.alerting_ids()
        for i, (zid, poly) in enumerate(self.zones):
            col = (0, 0, 255) if any(al.tracks.get(t) and al.tracks[t].state == "in" for t in hot for al in [self.alarms[zid]]) else ZONE_COLORS[i % 4]
            cv2.fillPoly(ov, [np.asarray(poly, np.int32)], col)
        im = cv2.addWeighted(ov, 0.18, im, 0.82, 0)
        for i, (zid, poly) in enumerate(self.zones):
            p = np.asarray(poly, np.int32); cv2.polylines(im, [p], True, ZONE_COLORS[i % 4], 2)
            cx, cy = p.mean(0).astype(int); cv2.putText(im, zid, (cx - 10, cy), 0, 0.6, (255, 255, 255), 2)
        for tid, x1, y1, x2, y2, c in dets:
            col = (0, 0, 255) if tid in hot else (0, 200, 0)
            cv2.rectangle(im, (int(x1), int(y1)), (int(x2), int(y2)), col, 2)
            fx, fy = foot_point(x1, y1, x2, y2); cv2.circle(im, (int(fx), int(fy)), 3, (0, 255, 255), -1)
            cv2.putText(im, f"{tid}", (int(x1), int(y1) - 3), 0, 0.45, col, 1, cv2.LINE_AA)
        state = "CANH BAO" if hot else "AN TOAN"
        cv2.rectangle(im, (0, 0), (230, 26), (0, 0, 180) if hot else (0, 120, 0), -1)
        txt = f"{state} | {self.model_version}" + (f" | {fps:.0f} FPS" if fps else "")
        cv2.putText(im, txt, (5, 18), 0, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        return im


def run_video(video_path, model_path, out_dir, filters=None, clip_seconds=3.0, evidence=True, save_video=False,
              max_frames=None, conf=0.25):
    zones, size = load_zones(video_path)
    cap = cv2.VideoCapture(video_path); fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    vid = os.path.splitext(os.path.basename(video_path))[0]
    store = EvidenceStore(os.path.join(out_dir, "events.db"), os.path.join(out_dir, "evidence"),
                          model_version_of(model_path), fps=fps, clip_seconds=clip_seconds) if evidence else None
    P = Pipeline(model_path, zones, size, conf=conf, filters=filters, evidence=store, video_id=vid)
    wr = None; times = []; t_start = time.perf_counter(); n = 0
    while True:
        ok, frame = cap.read()
        if not ok or (max_frames and n >= max_frames): break
        fr, dets, new, ms = P.step(frame); times.append(ms); n += 1
        if save_video:
            im = P.draw(fr, dets, 1000 / np.median(times[-25:]))
            if wr is None:
                os.makedirs(out_dir, exist_ok=True)
                wr = cv2.VideoWriter(os.path.join(out_dir, f"{vid}_{P.model_version}.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                     fps, (im.shape[1], im.shape[0]))
            wr.write(im)
    wall = time.perf_counter() - t_start
    if store: store.close()
    if wr: wr.release()
    return {"video": vid, "frames": n, "alerts": sum(e["type"] == "alert" for e in P.events),
            "step_ms_median": round(float(np.median(times)), 2), "fps_end_to_end": round(n / wall, 2)}
