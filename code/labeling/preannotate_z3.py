"""Gợi ý nhãn cho vùng Z3 bằng YOLO11x + ByteTrack (mô hình lớn, KHÁC mô hình được đánh giá).
Kết quả chỉ là gợi ý; người gán nhãn phải xem lại từng lượt trước khi đưa vào events_gt.csv.

Chạy trên bản 720p, cắt một vùng quanh Z3 (đủ cao để thấy cả người) rồi phóng lên imgsz 960.
Lưu: Videos/cua_hang_giay/_label_work/z3_tracks_x.json  {video: [[frame, id, x1, y1, x2, y2, conf], ...]} (tọa độ 1280x720)
"""
import cv2, json, os
from ultralytics import YOLO

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "../../Videos/cua_hang_giay")
CX1, CY1, CX2, CY2 = 470, 120, 960, 720          # vùng cắt trên khung 1280x720 (Z3 nằm ở x 605-825, y 430-560)
out = {}
for v in ["Video1", "Video2"]:
    m = YOLO(os.path.join(HERE, "../models/yolo11x.pt"))
    cap = cv2.VideoCapture(f"{B}/720p/{v}_720p.avi"); f = -1; T = []
    while True:
        ok, im = cap.read()
        if not ok:
            break
        f += 1
        r = m.track(im[CY1:CY2, CX1:CX2], persist=True, tracker="bytetrack.yaml", classes=[0], conf=0.3,
                    imgsz=960, device=0, half=True, verbose=False)[0]
        if r.boxes.id is not None:
            for tid, (x1, y1, x2, y2), cf in zip(r.boxes.id.int().tolist(), r.boxes.xyxy.cpu().numpy().tolist(),
                                                 r.boxes.conf.cpu().numpy().tolist()):
                T.append([f, tid, round(x1 + CX1, 1), round(y1 + CY1, 1), round(x2 + CX1, 1), round(y2 + CY1, 1), round(cf, 2)])
        if f % 1000 == 0:
            print(v, f, flush=True)
    out[v] = T
    print(v, "xong", f + 1, "khung", len({t[1] for t in T}), "ID", flush=True)
json.dump(out, open(f"{B}/_label_work/z3_tracks_x.json", "w"))
