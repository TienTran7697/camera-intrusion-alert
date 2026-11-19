"""Fine-tune YOLO11n (khởi tạo từ trọng số COCO) trên Human Dataset + khung hình CAVIAR dev.

Ví dụ:
  python train_ft.py --name ft_v1 --epochs 50                 # chạy thật
  python train_ft.py --name thu --epochs 1 --fraction 0.1     # chạy thử đo thời gian
  python train_ft.py --name ft_v1 --resume                    # chạy tiếp nếu bị dừng giữa chừng
Kết quả: code/train/runs/<name>/weights/best.pt
"""
import argparse, os
from ultralytics import YOLO

HERE = os.path.dirname(os.path.abspath(__file__))

# Bắt buộc có khối main trên Windows: tiến trình nạp dữ liệu (workers) sẽ nạp lại file này.
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--name", required=True); ap.add_argument("--epochs", type=int, default=50)
    ap.add_argument("--batch", type=int, default=16); ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--workers", type=int, default=2); ap.add_argument("--fraction", type=float, default=1.0)
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()

    if a.resume:
        YOLO(os.path.join(HERE, "runs", a.name, "weights", "last.pt")).train(resume=True, workers=a.workers)
    else:
        YOLO(os.path.join(HERE, "../models/yolo11n.pt")).train(
            data=os.path.join(HERE, "../../Dataset/data_ft.yaml"), epochs=a.epochs, imgsz=a.imgsz, batch=a.batch,
            device=0, workers=a.workers, amp=True, cache=False, fraction=a.fraction, single_cls=False,
            patience=15, close_mosaic=10, seed=42, deterministic=False,
            project=os.path.join(HERE, "runs"), name=a.name, exist_ok=True, plots=False, verbose=False)
