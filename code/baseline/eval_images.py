"""Đánh giá mô hình phát hiện người trên tập ảnh Human Dataset (mAP, Precision, Recall).

Ví dụ: python eval_images.py --model yolo11n.pt --split test --tag pretrained_fp32 --device 0
Mô hình COCO có sẵn có 80 lớp; lớp 0 của COCO là person, trùng với lớp 0 của bộ dữ liệu nên chỉ giữ classes=[0].
"""
import argparse, json, os
from ultralytics import YOLO

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "../../Dataset/data.yaml")

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="yolo11n.pt"); ap.add_argument("--split", default="test")
ap.add_argument("--tag", required=True); ap.add_argument("--device", default="0")
ap.add_argument("--imgsz", type=int, default=640); ap.add_argument("--batch", type=int, default=16)
a = ap.parse_args()

m = YOLO(a.model).val(data=DATA, split=a.split, classes=[0], imgsz=a.imgsz, batch=a.batch, device=a.device, workers=0,
                      project=os.path.join(HERE, "results", a.tag), name=f"val_{a.split}", exist_ok=True, plots=True, verbose=False)
res = {"split": a.split, "model": a.model, "imgsz": a.imgsz,
       "precision": round(float(m.box.mp), 4), "recall": round(float(m.box.mr), 4),
       "mAP50": round(float(m.box.map50), 4), "mAP50_95": round(float(m.box.map), 4),
       "speed_ms_per_img": {k: round(v, 2) for k, v in m.speed.items()}}
os.makedirs(os.path.join(HERE, "results", a.tag), exist_ok=True)
json.dump(res, open(os.path.join(HERE, "results", a.tag, f"image_metrics_{a.split}.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
