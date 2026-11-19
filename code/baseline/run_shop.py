"""Chạy pipeline (phát hiện + ByteTrack + logic vùng cấm) trên video cửa hàng giày, nhiều vùng (Z1, Z3).

Video gốc 2560x1440 HEVC được đọc tuần tự và thu về 1280x720 trước khi đưa vào mô hình
(thời gian đọc + thu nhỏ được tính vào FPS toàn hệ thống). Tọa độ vùng trong zones.json theo video gốc -> chia 2.
Ví dụ: python run_shop.py --model ../train/runs/ft_v1/weights/best.pt --tag ft_v1
Kết quả: results/<tag>/shop_pred_events.csv, results/<tag>/shop_timing.csv
"""
import argparse, csv, json, os, sys, time
import cv2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ultralytics import YOLO
from core.alarm import ZoneAlarm

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, "../../Videos/cua_hang_giay")
W, H = 1280, 720


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--tag", required=True)
    ap.add_argument("--device", default="cpu"); ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--conf", type=float, default=0.25); ap.add_argument("--confirm", type=int, default=8)
    ap.add_argument("--videos", nargs="*", default=["Video1", "Video2"])
    a = ap.parse_args()
    out = os.path.join(HERE, "results", a.tag); os.makedirs(out, exist_ok=True)
    Z = json.load(open(os.path.join(VID, "zones.json"), encoding="utf-8")); s = Z["frame_size"][0] / W
    model = YOLO(a.model); ev, tm = [], []
    for v in a.videos:
        alarms = {z["zone_id"]: ZoneAlarm([[x / s, y / s] for x, y in z["polygon"]], a.confirm) for z in Z["videos"][v]}
        cap = cv2.VideoCapture(os.path.join(VID, f"{v}.mp4")); f = -1; t0 = time.perf_counter(); inf = 0.0
        while True:
            ok, im = cap.read()
            if not ok: break
            f += 1
            im = cv2.resize(im, (W, H), interpolation=cv2.INTER_AREA)
            r = model.track(im, persist=True, tracker="bytetrack.yaml", classes=[0], device=a.device,
                            imgsz=a.imgsz, conf=a.conf, verbose=False)[0]
            inf += r.speed["inference"]
            dets = []
            if r.boxes is not None and r.boxes.id is not None:
                for (x1, y1, x2, y2), tid, c in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist(), r.boxes.conf.tolist()):
                    dets.append((tid, x1, y1, x2, y2, c))
            for zid, al in alarms.items():
                for e in al.update(f, dets):
                    if e["type"] == "alert":
                        ev.append({"video": v, "zone_id": zid, "track_id": e["track_id"], "alert_frame": e["frame"],
                                   "enter_frame": e["enter_frame"], "foot_x": round(e["foot"][0] * s, 1),
                                   "foot_y": round(e["foot"][1] * s, 1), "conf": round(e["conf"], 3)})
            if f % 2000 == 0: print(v, f, flush=True)
        wall = time.perf_counter() - t0; n = f + 1
        tm.append({"video": v, "frames": n, "inference_ms": round(inf / n, 2), "wall_s": round(wall, 1),
                   "fps_end_to_end": round(n / wall, 2)})
        print(tm[-1], "alerts:", sum(e["video"] == v for e in ev), flush=True)
        model.predictor = None
    for name, rows in (("shop_pred_events.csv", ev), ("shop_timing.csv", tm)):
        with open(os.path.join(out, name), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()) if rows else ["video"]); w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    main()
