"""Lưu toàn bộ kết quả theo dõi (khung, ID, bbox, conf) của 10 video CAVIAR và 2 video cửa hàng giày,
để thử các bộ lọc cảnh báo offline mà không phải chạy lại mô hình.
python dump_tracks.py --model ../train/runs/ft_v1/weights/best.pt --tag ft_v1 --device 0
-> results/<tag>/tracks.json  {video: [[f, id, x1, y1, x2, y2, conf], ...]}  (CAVIAR: 384x288; cửa hàng: 1280x720)
"""
import argparse, json, os, cv2
from ultralytics import YOLO

HERE = os.path.dirname(os.path.abspath(__file__))
CAV = os.path.join(HERE, "../../Videos/CAVIAR"); SHOP = os.path.join(HERE, "../../Videos/cua_hang_giay")


def frames(v):
    if v.startswith("Video"):
        cap = cv2.VideoCapture(os.path.join(SHOP, f"{v}.mp4"))
        while True:
            ok, im = cap.read()
            if not ok: return
            yield cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA)
    else:
        cap = cv2.VideoCapture(os.path.join(CAV, v, f"{v}.mpg"))
        while True:
            ok, im = cap.read()
            if not ok: return
            yield im


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True); ap.add_argument("--tag", required=True)
    ap.add_argument("--device", default="0"); ap.add_argument("--conf", type=float, default=0.25); ap.add_argument("--imgsz", type=int, default=640)
    a = ap.parse_args()
    vids = sorted(json.load(open(os.path.join(CAV, "zones.json")))["zones"]) + ["Video1", "Video2"]
    out = {}
    for v in vids:
        m = YOLO(a.model); T = []
        for f, im in enumerate(frames(v)):
            r = m.track(im, persist=True, tracker="bytetrack.yaml", classes=[0], conf=a.conf, imgsz=a.imgsz,
                        device=a.device, verbose=False)[0]
            if r.boxes.id is not None:
                for tid, b, c in zip(r.boxes.id.int().tolist(), r.boxes.xyxy.cpu().numpy().round(1).tolist(),
                                     r.boxes.conf.cpu().numpy().round(3).tolist()):
                    T.append([f, tid, *b, c])
        out[v] = T; print(v, len(T), flush=True)
    os.makedirs(os.path.join(HERE, "results", a.tag), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "results", a.tag, "tracks.json"), "w"))
