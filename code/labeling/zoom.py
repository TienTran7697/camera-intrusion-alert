"""python zoom.py Video1 Z1 x1 y1 x2 y2 f_start f_end step [cols] -> ảnh phóng to vùng nhỏ (tọa độ 1280x720)"""
import cv2, json, numpy as np, sys, os
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../Videos/cua_hang_giay")
v, zid = sys.argv[1], sys.argv[2]; x1, y1, x2, y2, fs, fe, st = map(int, sys.argv[3:10]); cols = int(sys.argv[10]) if len(sys.argv) > 10 else 6
Z = json.load(open(f"{B}/zones.json", encoding="utf-8"))
polys = [np.array(z["polygon"], np.int32) // 2 for z in Z["videos"][v]]
cap = cv2.VideoCapture(f"{B}/720p/{v}_720p.avi"); tiles = []
tw = int(os.environ.get("TW", 300)); th = int(tw * (y2 - y1) / (x2 - x1))
for f in range(fs, fe + 1, st):
    cap.set(1, f); ok, im = cap.read()
    if not ok: break
    for p in polys: cv2.polylines(im, [p], True, (0, 0, 255), 1)
    t = cv2.resize(im[y1:y2, x1:x2], (tw, th), interpolation=cv2.INTER_CUBIC)
    cv2.putText(t, str(f), (3, 18), 0, 0.6, (0, 0, 0), 4); cv2.putText(t, str(f), (3, 18), 0, 0.6, (0, 255, 255), 1); tiles.append(t)
while len(tiles) % cols: tiles.append(np.zeros_like(tiles[0]))
cv2.imwrite(f"{B}/_label_work/zoom.jpg", np.vstack([np.hstack(tiles[r:r + cols]) for r in range(0, len(tiles), cols)]))
print(len(tiles))
