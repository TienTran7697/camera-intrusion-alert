"""Chấm sự kiện trên video cửa hàng giày bằng events_gt.csv (Z1, Z3).

Video này không có khung bao chuẩn cho từng người, nên ghép cặp theo VÙNG + THỜI GIAN:
một cảnh báo (vùng z, khung fa) khớp một lượt chuẩn cùng vùng nếu fa nằm trong [enter - 25, exit + 12].
Mỗi lượt chuẩn / cảnh báo chỉ ghép một lần, ưu tiên |fa - enter| nhỏ nhất. Khi nhiều người cùng ở trong vùng,
cách ghép này dễ dãi hơn CAVIAR (không kiểm tra đúng người) -> cần nói rõ trong báo cáo.
Ví dụ: python eval_shop.py --tag ft_v1
"""
import argparse, csv, json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
VID = os.path.join(HERE, "../../Videos/cua_hang_giay")
FPS = 25.0


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tag", required=True); a = ap.parse_args()
    out = os.path.join(HERE, "results", a.tag)
    gt = list(csv.DictReader(open(os.path.join(VID, "events_gt.csv"), encoding="utf-8")))
    pred = list(csv.DictReader(open(os.path.join(out, "shop_pred_events.csv"), encoding="utf-8")))
    tm = {r["video"]: r for r in csv.DictReader(open(os.path.join(out, "shop_timing.csv"), encoding="utf-8"))}
    rows = []
    for v in sorted(tm):
        nframes = int(tm[v]["frames"])
        for z in ("Z1", "Z3"):
            G = [g for g in gt if g["video"] == v and g["zone_id"] == z]
            P = [p for p in pred if p["video"] == v and p["zone_id"] == z]
            cand = []
            for gi, g in enumerate(G):
                ef = int(g["enter_frame"]); xf = int(g["exit_frame"]) if g["exit_frame"] else nframes
                for pi, p in enumerate(P):
                    fa = int(p["alert_frame"])
                    if ef - 25 <= fa <= xf + 12: cand.append((abs(fa - ef), gi, pi, (fa - ef) / FPS))
            ug, up, lat = set(), set(), []
            for _, gi, pi, l in sorted(cand):
                if gi in ug or pi in up: continue
                ug.add(gi); up.add(pi); lat.append(l)
            tp = len(ug)
            rows.append({"video": v, "zone": z, "gt": len(G), "tp": tp, "fn": len(G) - tp, "fp": len(P) - tp,
                         "lat_med_s": round(st.median(lat), 2) if lat else "", "minutes": round(nframes / FPS / 60, 2)})
    tot = {k: sum(r[k] for r in rows) for k in ("gt", "tp", "fn", "fp")}
    mins = sum(float(tm[v]["frames"]) for v in tm) / FPS / 60
    tot.update(recall=round(tot["tp"] / tot["gt"], 3) if tot["gt"] else None,
               precision=round(tot["tp"] / (tot["tp"] + tot["fp"]), 3) if tot["tp"] + tot["fp"] else None,
               fp_per_hour=round(tot["fp"] / mins * 60, 1),
               fps=round(sum(float(tm[v]["frames"]) for v in tm) / sum(float(tm[v]["wall_s"]) for v in tm), 2))
    with open(os.path.join(out, "shop_event_eval.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    json.dump({"rows": rows, "total": tot}, open(os.path.join(out, "shop_summary.json"), "w"), indent=1)
    for r in rows: print(r)
    print("TONG", tot)


if __name__ == "__main__":
    main()
