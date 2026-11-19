"""Công cụ gán nhãn thời điểm VÀO / RA vùng cấm cho video cửa hàng giày.

Chạy:  python label_tool.py --video Video1      (rồi làm tiếp với --video Video2)
Cần chạy prepare_720p.py một lần trước để có bản 720p tua được.

Quy ước gán nhãn (giống logic hệ thống):
- Điểm xét là ĐIỂM CHÂN của người (giữa hai bàn chân).
- VÀO = khung đầu tiên điểm chân nằm trong vùng. RA = khung đầu tiên điểm chân đã ra khỏi vùng.
- Mỗi người, mỗi lần vào là một dòng. Ra rồi vào lại thì tạo dòng mới.
- Người đã ở trong vùng từ khung 0: bấm VÀO ở khung 0 (tự ghi start_inside=1).
- Hết video mà người vẫn còn trong vùng: để trống thời điểm RA.

Phím tắt (gõ khi cửa sổ video đang được chọn, bộ gõ tiếng Việt nên TẮT):
  Space        phát / tạm dừng           <- / ->     lùi / tới 1 khung
  Up / Down    tới / lùi 1 giây           J / L      lùi / tới 5 giây
  [ / ]        giảm / tăng tốc độ phát    Click vào thanh thời gian bên dưới để nhảy tới đó
  1 / 2        chọn vùng (Z1 / Z3)        Click vào ảnh: đánh dấu điểm chân người đang gán (không bắt buộc)
  E            VÀO: tạo lượt mới trong vùng đang chọn tại khung hiện tại
  X            RA: đóng lượt đang chọn (mũi tên > trong danh sách) tại khung hiện tại
  Tab          chọn lượt đang mở khác     G          nhảy tới thời điểm VÀO của lượt đang chọn
  M            bật/tắt ghi chú "sat_mep" (ca sát mép vùng) cho lượt đang chọn
  N            bật/tắt ghi chú "khuat" (bị che khuất) cho lượt đang chọn
  Backspace    xóa lượt đang chọn         U          hoàn tác thao tác gần nhất
  H            bật/tắt khung gợi ý của mô hình (mặc định TẮT để không bị ảnh hưởng)
  Q / Esc      lưu và thoát  (mọi thay đổi cũng được lưu ngay vào CSV)
"""
import argparse, copy, csv, json, os
import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "../../Videos/cua_hang_giay")
COLS = ["video", "zone_id", "track_id", "enter_frame", "enter_time_s", "exit_frame", "exit_time_s",
        "start_inside", "verified", "note", "foot_x", "foot_y"]
ZCOL = [(0, 0, 255), (255, 0, 255), (0, 200, 255), (255, 200, 0)]
SPEEDS = [0.25, 0.5, 1, 2, 4, 8]
W, H, PANEL, BAR = 1280, 720, 330, 70
K_LEFT, K_UP, K_RIGHT, K_DOWN = 2424832, 2490368, 2555904, 2621440


class Labeler:
    """Phần dữ liệu và thao tác (không phụ thuộc giao diện, để kiểm thử được)."""

    def __init__(self, video, zones, out_csv, fps, scale):
        self.video, self.zones, self.out, self.fps, self.scale = video, zones, out_csv, fps, scale
        self.zone_idx, self.sel, self.undo_stack = 0, None, []
        self.others, self.events = [], []          # others: dòng của video khác, giữ nguyên khi lưu
        if os.path.exists(out_csv):
            for r in csv.DictReader(open(out_csv, encoding="utf-8")):
                if r["video"] != video:
                    self.others.append(r); continue
                self.events.append({"zone_id": r["zone_id"], "track_id": r["track_id"],
                                    "enter": int(r["enter_frame"]),
                                    "exit": int(r["exit_frame"]) if r["exit_frame"] not in ("", None) else None,
                                    "note": r.get("note", ""),
                                    "foot": (float(r["foot_x"]), float(r["foot_y"])) if r.get("foot_x") else None})
        self._fix_sel()

    # ---- tiện ích
    def zone_id(self):
        return self.zones[self.zone_idx]["zone_id"]

    def open_events(self):
        return [e for e in self.events if e["exit"] is None]

    def _fix_sel(self):
        op = self.open_events()
        if self.sel not in self.events:
            self.sel = op[0] if op else (self.events[-1] if self.events else None)

    def _push(self):
        self.undo_stack.append(copy.deepcopy(self.events)); self.undo_stack = self.undo_stack[-200:]

    def _new_id(self):
        used = {int(e["track_id"][1:]) for e in self.events if e["track_id"][1:].isdigit()}
        return f"P{max(used, default=0) + 1}"

    # ---- thao tác
    def enter(self, frame, foot=None):
        self._push()
        e = {"zone_id": self.zone_id(), "track_id": self._new_id(), "enter": frame, "exit": None,
             "note": "", "foot": foot}
        self.events.append(e); self.sel = e; self.save()
        return e

    def exit(self, frame):
        e = self.sel
        if e is None or e["exit"] is not None:
            return "Chua chon luot dang mo (bam Tab)"
        if frame <= e["enter"]:
            return "Khung RA phai sau khung VAO"
        self._push(); e["exit"] = frame
        op = self.open_events(); self.sel = op[0] if op else e; self.save()
        return f"Da dong {e['zone_id']} {e['track_id']}"

    def cycle(self):
        lst = self.open_events() or self.events
        if not lst:
            return
        i = lst.index(self.sel) if self.sel in lst else -1
        self.sel = lst[(i + 1) % len(lst)]

    def toggle_note(self, tag):
        if self.sel is None:
            return
        self._push()
        tags = [t for t in self.sel["note"].split(";") if t]
        tags = [t for t in tags if t != tag] if tag in tags else tags + [tag]
        self.sel["note"] = ";".join(tags); self.save()

    def delete(self):
        if self.sel is None:
            return
        self._push(); self.events.remove(self.sel); self.sel = None; self._fix_sel(); self.save()

    def undo(self):
        if not self.undo_stack:
            return "Khong con gi de hoan tac"
        self.events = self.undo_stack.pop(); self.sel = None; self._fix_sel(); self.save()
        return "Da hoan tac"

    # ---- lưu
    def rows(self):
        out = []
        for e in sorted(self.events, key=lambda e: (e["zone_id"], e["enter"])):
            fx, fy = (round(e["foot"][0] * self.scale, 1), round(e["foot"][1] * self.scale, 1)) if e["foot"] else ("", "")
            out.append({"video": self.video, "zone_id": e["zone_id"], "track_id": e["track_id"],
                        "enter_frame": e["enter"], "enter_time_s": round(e["enter"] / self.fps, 2),
                        "exit_frame": "" if e["exit"] is None else e["exit"],
                        "exit_time_s": "" if e["exit"] is None else round(e["exit"] / self.fps, 2),
                        "start_inside": int(e["enter"] == 0), "verified": 1, "note": e["note"],
                        "foot_x": fx, "foot_y": fy})
        return out

    def save(self):
        tmp = self.out + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=COLS); w.writeheader()
            for r in self.others:
                w.writerow({c: r.get(c, "") for c in COLS})
            w.writerows(self.rows())
        os.replace(tmp, self.out)


class App:
    def __init__(self, a):
        path = os.path.join(BASE, "720p", f"{a.video}_720p.avi")
        if not os.path.exists(path):
            raise SystemExit(f"Chua co {path}. Hay chay prepare_720p.py truoc.")
        self.cap = cv2.VideoCapture(path)
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)); self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 25
        Z = json.load(open(os.path.join(BASE, "zones.json"), encoding="utf-8"))
        s = Z["frame_size"][0] / W                       # tọa độ vùng theo video gốc -> chia về 1280x720
        self.zones = [{"zone_id": z["zone_id"], "poly": (np.array(z["polygon"], np.float32) / s).astype(np.int32)}
                      for z in Z["videos"][a.video]]
        self.L = Labeler(a.video, self.zones, os.path.join(BASE, a.out), self.fps, s)
        self.hints = {}
        hp = os.path.join(BASE, "_zone_work", "tracks_pretrained.json")
        if os.path.exists(hp):
            for f, tid, x1, y1, x2, y2, cf in json.load(open(hp)).get(a.video, []):
                self.hints.setdefault(f, []).append((tid, x1, y1, x2, y2))
        self.cur, self.frame, self.playing, self.speed_i = -1, None, False, 2
        self.show_hints, self.click, self.msg = False, None, "Bam E de gan VAO, X de gan RA. Xem huong dan o dau file."
        self.win = f"Gan nhan - {a.video}"
        cv2.namedWindow(self.win, cv2.WINDOW_NORMAL); cv2.resizeWindow(self.win, W + PANEL, H + BAR)
        cv2.setMouseCallback(self.win, self.on_mouse)
        self.seek(0)

    def seek(self, f):
        f = int(max(0, min(self.n - 1, f)))
        if f != self.cur + 1:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, f)
        ok, im = self.cap.read()
        if ok:
            self.cur, self.frame = f, im
        else:
            self.playing = False

    def on_mouse(self, ev, x, y, flags, _):
        if ev != cv2.EVENT_LBUTTONDOWN:
            return
        if y >= H and x < W:                               # thanh thời gian
            self.seek(x / W * self.n); self.playing = False
        elif x < W and y < H:
            self.click = (x, y)

    def t(self, f):
        s = f / self.fps
        return f"{int(s // 60):02d}:{s % 60:05.2f}"

    def draw(self):
        im = self.frame.copy(); L = self.L
        ov = im.copy()
        for i, z in enumerate(self.zones):
            cv2.fillPoly(ov, [z["poly"]], ZCOL[i % 4])
        im = cv2.addWeighted(ov, 0.18, im, 0.82, 0)
        for i, z in enumerate(self.zones):
            cv2.polylines(im, [z["poly"]], True, ZCOL[i % 4], 4 if i == L.zone_idx else 2)
            cx, cy = z["poly"].mean(0).astype(int)
            cv2.putText(im, z["zone_id"], (cx - 15, cy), 0, 0.9, (255, 255, 255), 2)
        if self.show_hints:
            for tid, x1, y1, x2, y2 in self.hints.get(self.cur, []):
                cv2.rectangle(im, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 1)
                cv2.circle(im, (int((x1 + x2) / 2), int(y2)), 4, (0, 255, 255), -1)
        for e in L.events:                                 # điểm chân đã đánh dấu của các lượt đang ở trong vùng
            if e["foot"] and e["enter"] <= self.cur and (e["exit"] is None or self.cur < e["exit"]):
                p = (int(e["foot"][0]), int(e["foot"][1]))
                cv2.circle(im, p, 7, (0, 255, 255), 2); cv2.putText(im, e["track_id"], (p[0] + 8, p[1]), 0, 0.6, (0, 255, 255), 2)
        if self.click:
            cv2.drawMarker(im, self.click, (0, 255, 0), cv2.MARKER_CROSS, 22, 2)
        # thanh thời gian
        bar = np.full((BAR, W, 3), 40, np.uint8)
        for e in L.events:
            i = [z["zone_id"] for z in self.zones].index(e["zone_id"]) if e["zone_id"] in [z["zone_id"] for z in self.zones] else 0
            x1 = int(e["enter"] / self.n * W); x2 = int((e["exit"] if e["exit"] is not None else self.cur) / self.n * W)
            y = 8 + i * 22
            cv2.rectangle(bar, (x1, y), (max(x2, x1 + 2), y + 16), ZCOL[i % 4], -1)
        cx = int(self.cur / self.n * W); cv2.line(bar, (cx, 0), (cx, BAR), (255, 255, 255), 2)
        cv2.putText(bar, self.msg[:150], (5, BAR - 6), 0, 0.5, (200, 255, 200), 1)
        # bảng bên phải
        pn = np.full((H + BAR, PANEL, 3), 25, np.uint8)
        lines = [(f"Khung {self.cur}/{self.n - 1}", (255, 255, 255)), (f"Thoi gian {self.t(self.cur)}", (255, 255, 255)),
                 (f"Toc do x{SPEEDS[self.speed_i]}  {'PHAT' if self.playing else 'DUNG'}", (255, 255, 255)),
                 (f"Vung dang chon: {L.zone_id()}", ZCOL[L.zone_idx % 4]),
                 (f"Goi y mo hinh: {'BAT' if self.show_hints else 'TAT'}", (180, 180, 180)), ("", 0),
                 (f"Tong so luot: {len(L.events)}  (dang mo {len(L.open_events())})", (255, 255, 255)), ("", 0)]
        ev = sorted(L.events, key=lambda e: e["enter"])
        ev = [e for e in ev if e["exit"] is None] + [e for e in ev if e["exit"] is not None][::-1]
        for e in ev[:22]:
            mark = ">" if e is L.sel else " "
            ex = "..." if e["exit"] is None else self.t(e["exit"])
            col = (0, 255, 255) if e["exit"] is None else (200, 200, 200)
            lines.append((f"{mark}{e['zone_id']} {e['track_id']:<4} {self.t(e['enter'])} -> {ex} {e['note'][:8]}", col))
        for i, (s, c) in enumerate(lines):
            if s:
                cv2.putText(pn, s, (8, 24 + i * 26), 0, 0.5, c, 1)
        return np.hstack([np.vstack([im, bar]), pn])

    def run(self):
        L = self.L
        while True:
            cv2.imshow(self.win, self.draw())
            if self.playing:
                delay = max(1, int(1000 / (self.fps * SPEEDS[self.speed_i])))
                step = max(1, int(SPEEDS[self.speed_i] // 2))  # tốc độ cao thì bỏ bớt khung cho kịp
            else:
                delay = 30
            k = cv2.waitKeyEx(delay)
            if cv2.getWindowProperty(self.win, cv2.WND_PROP_VISIBLE) < 1:
                break
            if k == -1:
                if self.playing:
                    self.seek(self.cur + step)
                continue
            c = chr(k & 0xFF).lower() if k < 256 else ""
            if c in ("q",) or k == 27: break
            elif c == " ": self.playing = not self.playing
            elif k == K_LEFT: self.playing = False; self.seek(self.cur - 1)
            elif k == K_RIGHT: self.playing = False; self.seek(self.cur + 1)
            elif k == K_UP: self.seek(self.cur + self.fps)
            elif k == K_DOWN: self.seek(self.cur - self.fps)
            elif c == "j": self.seek(self.cur - 5 * self.fps)
            elif c == "l": self.seek(self.cur + 5 * self.fps)
            elif c == "[": self.speed_i = max(0, self.speed_i - 1)
            elif c == "]": self.speed_i = min(len(SPEEDS) - 1, self.speed_i + 1)
            elif c.isdigit() and 1 <= int(c) <= len(self.zones): L.zone_idx = int(c) - 1; self.msg = f"Chon vung {L.zone_id()}"
            elif c == "e":
                self.playing = False; e = L.enter(self.cur, self.click); self.click = None
                self.msg = f"VAO: {e['zone_id']} {e['track_id']} tai {self.t(self.cur)}"
            elif c == "x": self.playing = False; self.msg = L.exit(self.cur)
            elif k == 9: L.cycle()
            elif c == "g" and L.sel: self.playing = False; self.seek(L.sel["enter"])
            elif c == "m": L.toggle_note("sat_mep"); self.msg = "Doi ghi chu sat_mep"
            elif c == "n": L.toggle_note("khuat"); self.msg = "Doi ghi chu khuat"
            elif k == 8: L.delete(); self.msg = "Da xoa luot"
            elif c == "u": self.msg = L.undo()
            elif c == "h": self.show_hints = not self.show_hints
        L.save(); cv2.destroyAllWindows()
        print(f"Da luu {len(L.events)} luot cua {L.video} vao {L.out}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, choices=["Video1", "Video2"])
    ap.add_argument("--out", default="events_gt.csv", help="ten file CSV trong Videos/cua_hang_giay")
    App(ap.parse_args()).run()
