"""Chạy mô hình phát hiện + ByteTrack + logic vùng cấm trên các video CAVIAR, ghi sự kiện và thời gian xử lý.

Ví dụ:  python run_videos.py --model yolo11n.pt --device cpu --tag pretrained_fp32
Kết quả: results/<tag>/pred_events.csv, results/<tag>/timing.csv
"""
import argparse, csv, json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from ultralytics import YOLO
from core.alarm import ZoneAlarm

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, "../../Videos/CAVIAR")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="yolo11n.pt")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--conf", type=float, default=0.25)
    ap.add_argument("--confirm", type=int, default=8)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--videos", nargs="*")
    a = ap.parse_args()

    out = os.path.join(HERE, "results", a.tag); os.makedirs(out, exist_ok=True)
    zones = json.load(open(os.path.join(VID, "zones.json")))["zones"]
    videos = a.videos or sorted(zones)
    model = YOLO(a.model)
    ev_rows, t_rows = [], []
    for v in videos:
        alarm = ZoneAlarm(zones[v]["polygon"], confirm_frames=a.confirm)
        src = os.path.join(VID, v, f"{v}.mpg")
        pre = inf = post = 0.0; n = 0; t0 = time.perf_counter()
        for f, r in enumerate(model.track(src, stream=True, persist=False, tracker="bytetrack.yaml", classes=[0],
                                          device=a.device, imgsz=a.imgsz, conf=a.conf, verbose=False)):
            dets = []
            if r.boxes is not None and r.boxes.id is not None:
                for (x1, y1, x2, y2), tid, c in zip(r.boxes.xyxy.tolist(), r.boxes.id.int().tolist(), r.boxes.conf.tolist()):
                    dets.append((tid, x1, y1, x2, y2, c))
            for e in alarm.update(f, dets):
                if e["type"] == "alert":
                    ev_rows.append({"video": v, "track_id": e["track_id"], "alert_frame": e["frame"],
                                    "enter_frame": e["enter_frame"], "foot_x": round(e["foot"][0], 1),
                                    "foot_y": round(e["foot"][1], 1), "conf": round(e["conf"], 3)})
            s = r.speed; pre += s["preprocess"]; inf += s["inference"]; post += s["postprocess"]; n += 1
        wall = time.perf_counter() - t0
        t_rows.append({"video": v, "frames": n, "preprocess_ms": round(pre / n, 2), "inference_ms": round(inf / n, 2),
                       "postprocess_ms": round(post / n, 2), "wall_s": round(wall, 2), "fps_end_to_end": round(n / wall, 2)})
        print(t_rows[-1], "alerts:", sum(1 for e in ev_rows if e["video"] == v), flush=True)
        model.predictor = None  # reset tracker giữa các video
    for name, rows in (("pred_events.csv", ev_rows), ("timing.csv", t_rows)):
        with open(os.path.join(out, name), "w", newline="", encoding="utf-8") as fh:
            keys = rows[0].keys() if rows else ["video"]
            w = csv.DictWriter(fh, fieldnames=list(keys)); w.writeheader(); w.writerows(rows)
    json.dump(vars(a), open(os.path.join(out, "config.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
