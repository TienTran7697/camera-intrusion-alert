"""Ghép ảnh cắt quanh vùng cấm theo thời gian (không dùng mô hình) để người gán nhãn xem nhanh.
python make_montage.py Z1 1.0  -> mỗi ô cách nhau 1 giây, 30 ô/ảnh."""
import cv2, json, numpy as np, os, sys
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Videos/cua_hang_giay")
CROP = {"Z1": (60, 150, 400, 500), "Z3": (575, 330, 855, 580)}   # x1,y1,x2,y2 trên khung 1280x720
zid, step = sys.argv[1], float(sys.argv[2]); cols, rows = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (6, 5)
Z = json.load(open(f"{B}/zones.json", encoding="utf-8"))
for v in ["Video1", "Video2"]:
    poly = [np.array(z["polygon"], np.int32) // 2 for z in Z["videos"][v] if z["zone_id"] == zid][0]
    cap = cv2.VideoCapture(f"{B}/720p/{v}_720p.avi"); n = int(cap.get(7)); fps = cap.get(5)
    x1, y1, x2, y2 = CROP[zid]; tw = int(os.environ.get("TW", 250)); th = int(tw * (y2 - y1) / (x2 - x1))
    frames = list(range(0, n, int(step * fps))); per = cols * rows
    for k in range(0, len(frames), per):
        tiles = []
        for f in frames[k:k + per]:
            cap.set(1, f); ok, im = cap.read()
            cv2.polylines(im, [poly], True, (0, 0, 255), 2)
            t = cv2.resize(im[y1:y2, x1:x2], (tw, th))
            cv2.putText(t, f"{f}", (3, 18), 0, 0.55, (0, 0, 0), 4); cv2.putText(t, f"{f}", (3, 18), 0, 0.55, (0, 255, 255), 1)
            tiles.append(t)
        while len(tiles) < per: tiles.append(np.zeros((th, tw, 3), np.uint8))
        g = np.vstack([np.hstack(tiles[r * cols:(r + 1) * cols]) for r in range(rows)])
        cv2.imwrite(f"{B}/_label_work/{zid}_{v}_{k // per:02d}.jpg", g, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(v, len(frames), "o", (len(frames) + per - 1) // per, "anh")
