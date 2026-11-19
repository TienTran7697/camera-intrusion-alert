"""Từ track YOLO11x, rút ra các lượt VÀO/RA Z3 gợi ý và vẽ ảnh ghép để người gán nhãn kiểm tra.
- Lượt: điểm chân trong vùng liên tục >= 3 khung (bỏ qua khung mất dấu) -> VÀO tại khung đầu tiên trong vùng;
  ngoài vùng liên tục >= 3 khung -> RA tại khung đầu tiên ngoài vùng.
- Ảnh ghép: mỗi ô cách 12 khung (~0,5 s); người có điểm chân trong vùng được ghi số lượt gợi ý (C1, C2...),
  người khác chỉ chấm vàng nhỏ ở điểm chân.
python z3_candidates.py  -> _label_work/z3_candidates.json và _label_work/Z3R_<video>_<k>.jpg
"""
import cv2, json, os, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "../../Videos/cua_hang_giay")
W = f"{B}/_label_work"
T = json.load(open(f"{W}/z3_tracks_x.json"))
Z = json.load(open(f"{B}/zones.json", encoding="utf-8"))
RUN = 3
CROP = (575, 330, 855, 580); TW = 180; COLS, ROWS = 8, 6; STEP = 12
cands = {}
for v, dets in T.items():
    poly = [np.array(z["polygon"], np.float32) / 2 for z in Z["videos"][v] if z["zone_id"] == "Z3"][0]
    ins = lambda p: cv2.pointPolygonTest(poly, p, False) >= 0
    by_id = collections.defaultdict(list)
    for f, tid, x1, y1, x2, y2, cf in dets:
        by_id[tid].append((f, ((x1 + x2) / 2, y2)))
    C = []
    for tid, seq in by_id.items():
        state, run, start, cur = "out", 0, None, None
        for f, p in sorted(seq):
            i = ins(p)
            if state == "out":
                if i:
                    if run == 0: start = f
                    run += 1
                    if run >= RUN: state, run, cur = "in", 0, {"id": tid, "enter": start, "exit": None}
                else: run = 0
            else:
                if not i:
                    if run == 0: start = f
                    run += 1
                    if run >= RUN: cur["exit"] = start; C.append(cur); state, run, cur = "out", 0, None
                else: run = 0
        if cur: C.append(cur)
    C.sort(key=lambda c: c["enter"])
    for k, c in enumerate(C): c["c"] = f"C{k + 1}"
    cands[v] = C
    # ảnh ghép
    det_at = collections.defaultdict(list)
    for f, tid, x1, y1, x2, y2, cf in dets: det_at[f].append((tid, (x1 + x2) / 2, y2))
    cap = cv2.VideoCapture(f"{B}/720p/{v}_720p.avi"); n = int(cap.get(7))
    x1c, y1c, x2c, y2c = CROP; s = TW / (x2c - x1c); th = int((y2c - y1c) * s)
    frames = list(range(0, n, STEP)); per = COLS * ROWS
    for k in range(0, len(frames), per):
        tiles = []
        for f in frames[k:k + per]:
            cap.set(1, f); ok, im = cap.read()
            cv2.polylines(im, [poly.astype(np.int32)], True, (0, 0, 255), 1)
            t = cv2.resize(im[y1c:y2c, x1c:x2c], (TW, th))
            for tid, fx, fy in det_at.get(f, []):
                p = (int((fx - x1c) * s), int((fy - y1c) * s))
                lab = [c["c"] for c in C if c["id"] == tid and c["enter"] <= f and (c["exit"] is None or f < c["exit"])]
                if lab:
                    cv2.circle(t, p, 4, (0, 255, 0), -1)
                    cv2.putText(t, lab[0], (p[0] - 10, p[1] + 14), 0, 0.45, (0, 0, 0), 3)
                    cv2.putText(t, lab[0], (p[0] - 10, p[1] + 14), 0, 0.45, (0, 255, 0), 1)
                else:
                    cv2.circle(t, p, 3, (0, 255, 255), -1)
            cv2.putText(t, str(f), (2, 14), 0, 0.45, (0, 0, 0), 3); cv2.putText(t, str(f), (2, 14), 0, 0.45, (255, 255, 255), 1)
            tiles.append(t)
        while len(tiles) < per: tiles.append(np.zeros((th, TW, 3), np.uint8))
        cv2.imwrite(f"{W}/Z3R_{v}_{k // per:02d}.jpg",
                    np.vstack([np.hstack(tiles[r * COLS:(r + 1) * COLS]) for r in range(ROWS)]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(v, len(C), "luot goi y")
json.dump(cands, open(f"{W}/z3_candidates.json", "w"), indent=1)
