"""Tạo nhãn chuẩn (ground truth) cho sự kiện xâm nhập vùng cấm từ nhãn gốc CAVIAR.

Quy tắc (giống quy tắc cảnh báo của hệ thống, nhưng dùng khung bao do người gán):
- Điểm đại diện: trung điểm cạnh dưới khung bao p = (xc, yc + h/2).
- Mỗi ID bắt đầu ở trạng thái "ngoài vùng".
- VÀO: điểm chân nằm trong vùng liên tục >= CONF khung hình. Thời điểm vào = khung đầu tiên của đoạn đó.
- RA: điểm chân nằm ngoài vùng liên tục >= CONF khung hình. Thời điểm ra = khung đầu tiên của đoạn đó.
- Chỉ tạo lượt VÀO mới sau khi đã RA ổn định (tránh đếm lặp khi đứng trên mép vùng).
- Người đã ở sẵn trong vùng khi xuất hiện vẫn tính là một lượt vào (mọi người ở trong vùng đều là vi phạm),
  được đánh dấu start_inside = 1 để phân tích riêng.
- Bỏ các ID xuất hiện ít hơn CONF khung hình.
Kết quả: Videos/CAVIAR/zones.json và Videos/CAVIAR/events_gt.csv
"""
import os, json, csv, cv2, numpy as np
from caviar_gt import load_tracks

R = os.path.join(os.path.dirname(__file__), "../../Videos/CAVIAR")
FPS = 25.0
CONF = 8            # 8 khung = 0,32 giây
NEAR_PX = 15        # "sát mép": cách vùng < 15 px nhưng không vào
ZONE_A = [(25, 95), (100, 88), (112, 150), (88, 200), (28, 200)]

def events_for_track(t, poly):
    frames = [b[0] for b in t]
    dist = [cv2.pointPolygonTest(poly, (b[1], b[2] + b[4] / 2), True) for b in t]
    inside = [d >= 0 for d in dist]
    evs, state, run_in, run_out, cur = [], "out", 0, 0, None
    for k, v in enumerate(inside):
        if v:
            run_in += 1; run_out = 0
            if state == "out" and run_in == CONF:
                start = k - CONF + 1
                cur = {"enter_frame": frames[start], "start_inside": int(start == 0)}
                state = "in"
        else:
            run_out += 1; run_in = 0
            if state == "in" and run_out == CONF:
                cur["exit_frame"] = frames[k - CONF + 1]
                evs.append(cur); cur = None; state = "out"
    if cur is not None:
        cur["exit_frame"] = None   # vẫn ở trong vùng khi kết thúc / mất dấu
        evs.append(cur)
    near = (not any(inside)) and max(dist) > -NEAR_PX
    return evs, near, round(max(dist), 1)

def main():
    poly = np.array(ZONE_A, np.int32)
    json.dump({"frame_size": [384, 288], "fps": FPS,
               "zones": {v: {"zone_id": "A", "polygon": ZONE_A} for v in sorted(os.listdir(R)) if os.path.isdir(os.path.join(R, v))}},
              open(os.path.join(R, "zones.json"), "w"), indent=1)
    rows, summary = [], []
    for v in sorted(d for d in os.listdir(R) if os.path.isdir(os.path.join(R, d))):
        n_ev = n_near = 0
        for tid, t in sorted(load_tracks(os.path.join(R, v)).items()):
            if len(t) < CONF:
                continue
            evs, near, _ = events_for_track(t, poly)
            n_near += near
            for e in evs:
                n_ev += 1
                rows.append({"video": v, "zone_id": "A", "track_id": tid,
                             "enter_frame": e["enter_frame"], "enter_time_s": round(e["enter_frame"] / FPS, 2),
                             "exit_frame": e["exit_frame"] if e["exit_frame"] is not None else "",
                             "exit_time_s": round(e["exit_frame"] / FPS, 2) if e["exit_frame"] is not None else "",
                             "start_inside": e["start_inside"], "verified": 0, "note": ""})
            if near:
                rows.append({"video": v, "zone_id": "A", "track_id": tid, "enter_frame": "", "enter_time_s": "",
                             "exit_frame": "", "exit_time_s": "", "start_inside": "", "verified": 0,
                             "note": "near_miss (sat mep, khong vao)"})
        summary.append((v, n_ev, n_near))
    with open(os.path.join(R, "events_gt.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    for s in summary:
        print(f"{s[0]:20s} luot_vao={s[1]}  sat_mep={s[2]}")
    print("TONG luot_vao=%d sat_mep=%d" % (sum(s[1] for s in summary), sum(s[2] for s in summary)))

if __name__ == "__main__":
    main()
