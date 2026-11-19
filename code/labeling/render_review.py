"""Tạo video kiểm tra nhãn: vùng cấm, khung chuẩn CAVIAR, ID, điểm chân và sự kiện VAO/RA.
Kết quả: Videos/_review/<video>_review.mp4 và review_events.png (ảnh khung hình tại mỗi lượt vào)."""
import os, csv, cv2, numpy as np
from caviar_gt import load_tracks

BASE = os.path.join(os.path.dirname(__file__), "../../Videos")
R, OUT = os.path.join(BASE, "CAVIAR"), os.path.join(BASE, "_review")
os.makedirs(OUT, exist_ok=True)
import json
zones = json.load(open(os.path.join(R, "zones.json")))["zones"]
events = list(csv.DictReader(open(os.path.join(R, "events_gt.csv"), encoding="utf-8")))

thumbs = []
for v in sorted(d for d in os.listdir(R) if os.path.isdir(os.path.join(R, d))):
    poly = np.array(zones[v]["polygon"], np.int32)
    tracks = load_tracks(os.path.join(R, v))
    by_frame = {}
    for tid, t in tracks.items():
        for b in t: by_frame.setdefault(b[0], []).append((tid, *b[1:]))
    evs = [e for e in events if e["video"] == v and e["enter_frame"] != ""]
    marks = {}
    for e in evs:
        ef = int(e["enter_frame"])
        for k in range(ef, ef + 25): marks.setdefault(k, []).append(f"VAO id{e['track_id']}")
        if e["exit_frame"]:
            xf = int(e["exit_frame"])
            for k in range(xf, xf + 25): marks.setdefault(k, []).append(f"RA id{e['track_id']}")
    in_zone = lambda tid, f: any(int(e["track_id"]) == tid and int(e["enter_frame"]) <= f and (e["exit_frame"] == "" or f < int(e["exit_frame"])) for e in evs)
    cap = cv2.VideoCapture(os.path.join(R, v, f"{v}.mpg"))
    W, H = 384 * 2, 288 * 2
    wr = cv2.VideoWriter(os.path.join(OUT, f"{v}_review.mp4"), cv2.VideoWriter_fourcc(*"mp4v"), 25, (W, H))
    want = {int(e["enter_frame"]) + 4: e for e in evs}
    f = 0
    while True:
        ok, img = cap.read()
        if not ok: break
        img = cv2.resize(img, (W, H)); s = 2
        ov = img.copy(); cv2.fillPoly(ov, [poly * s], (0, 0, 255)); img = cv2.addWeighted(ov, 0.2, img, 0.8, 0)
        cv2.polylines(img, [poly * s], True, (0, 0, 255), 2)
        for tid, xc, yc, w, h in by_frame.get(f, []):
            c = (0, 0, 255) if in_zone(tid, f) else (0, 200, 0)
            cv2.rectangle(img, (int((xc - w / 2) * s), int((yc - h / 2) * s)), (int((xc + w / 2) * s), int((yc + h / 2) * s)), c, 2)
            cv2.circle(img, (int(xc * s), int((yc + h / 2) * s)), 4, (0, 255, 255), -1)
            cv2.putText(img, f"id{tid}", (int((xc - w / 2) * s), int((yc - h / 2) * s) - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, c, 2)
        cv2.rectangle(img, (0, 0), (W, 28), (255, 255, 255), -1)
        cv2.putText(img, f"{v}  frame {f}  t={f / 25:.2f}s", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        for j, m in enumerate(marks.get(f, [])):
            cv2.putText(img, m, (W - 170, 60 + 30 * j), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if m.startswith("VAO") else (255, 0, 0), 2)
        wr.write(img)
        if f in want:
            e = want[f]; t = cv2.resize(img, (384, 288))
            cv2.putText(t, f"{v} id{e['track_id']} vao@{e['enter_frame']}", (4, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
            thumbs.append(t)
        f += 1
    wr.release()
    print("ok", v, f)

cols = 6
rows = [np.hstack(thumbs[i:i + cols] + [np.full_like(thumbs[0], 255)] * (cols - len(thumbs[i:i + cols]))) for i in range(0, len(thumbs), cols)]
cv2.imwrite(os.path.join(OUT, "review_events.png"), np.vstack(rows))
