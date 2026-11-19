"""Trích khung hình từ các video CAVIAR thuộc tập DEV kèm nhãn YOLO (lớp 0 = person), dùng để fine-tune.
Video tập TEST (Browse3, Browse4, Meet_WalkTogether1, Walk2, Walk3) KHÔNG được dùng ở đây.

- train: Browse1, Browse2, Meet_Crowd, Meet_WalkSplit, lấy 1 khung mỗi 2 khung.
- val:   Walk1, lấy 1 khung mỗi 5 khung (đo khả năng của mô hình trên góc nhìn từ trên xuống).
- Chỉ lấy khung có nhãn gốc (khung không có nhãn ở đầu/cuối video có thể có người chưa được gán).
- Bỏ khung bao quá nhỏ (w hoặc h < 6 px), đó là nhãn lỗi của CAVIAR. Khung bao được cắt về trong ảnh.
Kết quả: Dataset/caviar_dev/{images,labels}/{train,val}/<video>_<frame>.jpg|.txt
"""
import os, sys, cv2, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../labeling"))
from caviar_gt import load_tracks

V = os.path.join(HERE, "../../Videos/CAVIAR")
OUT = os.path.join(HERE, "../../Dataset/caviar_dev")
PLAN = {"train": (["Browse1", "Browse2", "Meet_Crowd", "Meet_WalkSplit"], 2), "val": (["Walk1"], 5)}
MIN_PX = 6

shutil.rmtree(OUT, ignore_errors=True)
for split, (vids, step) in PLAN.items():
    os.makedirs(f"{OUT}/images/{split}"); os.makedirs(f"{OUT}/labels/{split}")
    n_img = n_box = n_drop = 0
    for v in vids:
        by_f = {}
        for tid, seq in load_tracks(f"{V}/{v}").items():
            for f, xc, yc, w, h in seq:
                by_f.setdefault(f, []).append((xc, yc, w, h))
        cap = cv2.VideoCapture(f"{V}/{v}/{v}.mpg"); f = -1
        while True:
            ok, im = cap.read()
            if not ok:
                break
            f += 1
            if f % step or f not in by_f:
                continue
            H, W = im.shape[:2]; lines = []
            for xc, yc, w, h in by_f[f]:
                x1, y1, x2, y2 = max(0, xc - w / 2), max(0, yc - h / 2), min(W, xc + w / 2), min(H, yc + h / 2)
                if x2 - x1 < MIN_PX or y2 - y1 < MIN_PX:
                    n_drop += 1; continue
                lines.append(f"0 {(x1+x2)/2/W:.6f} {(y1+y2)/2/H:.6f} {(x2-x1)/W:.6f} {(y2-y1)/H:.6f}")
            name = f"{v}_{f:05d}"
            cv2.imwrite(f"{OUT}/images/{split}/{name}.jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 95])
            open(f"{OUT}/labels/{split}/{name}.txt", "w").write("\n".join(lines) + ("\n" if lines else ""))
            n_img += 1; n_box += len(lines)
    print(f"{split}: {n_img} anh, {n_box} khung nguoi, bo {n_drop} khung qua nho")
