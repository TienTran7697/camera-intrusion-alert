"""So sánh sự kiện dự đoán với nhãn chuẩn (events_gt.csv).

Ghép cặp: một cảnh báo dự đoán (khung fa, điểm chân p) khớp với một lượt vào chuẩn nếu
  - fa nằm trong [enter_frame - 25, exit_frame + 12] (exit trống = khung cuối của người đó), và
  - p nằm trong khung bao chuẩn của người đó tại khung fa (nới rộng 15 px).
Mỗi lượt chuẩn và mỗi cảnh báo chỉ được ghép một lần; ưu tiên cặp có |fa - enter_frame| nhỏ nhất.
Độ trễ cảnh báo = (fa - enter_frame) / 25 giây (đã gồm thời gian xác nhận 8 khung).

Ví dụ: python eval_events.py --tag pretrained_fp32
"""
import argparse, csv, json, os, sys, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "../labeling"))
from caviar_gt import load_tracks

VID = os.path.join(HERE, "../../Videos/CAVIAR")
FPS, MARGIN = 25.0, 15


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--tag", required=True); a = ap.parse_args()
    out = os.path.join(HERE, "results", a.tag)
    gt = [r for r in csv.DictReader(open(os.path.join(VID, "events_gt.csv"), encoding="utf-8")) if r["enter_frame"] != ""]
    pred = list(csv.DictReader(open(os.path.join(out, "pred_events.csv"), encoding="utf-8")))
    split = json.load(open(os.path.join(VID, "split.json")))
    timing = {r["video"]: r for r in csv.DictReader(open(os.path.join(out, "timing.csv"), encoding="utf-8"))}
    rows, matches = [], []
    for v in sorted({r["video"] for r in gt} | set(timing)):
        tracks = load_tracks(os.path.join(VID, v))
        boxes = {tid: {b[0]: b for b in t} for tid, t in tracks.items()}
        G = [g for g in gt if g["video"] == v]; P = [p for p in pred if p["video"] == v]
        cand = []
        for gi, g in enumerate(G):
            tid = int(g["track_id"]); ef = int(g["enter_frame"])
            last = max(boxes[tid]); xf = int(g["exit_frame"]) if g["exit_frame"] else last
            for pi, p in enumerate(P):
                fa = int(p["alert_frame"])
                if not (ef - 25 <= fa <= xf + 12): continue
                b = boxes[tid].get(fa) or boxes[tid][min(boxes[tid], key=lambda k: abs(k - fa))]
                _, xc, yc, w, h = b
                if abs(float(p["foot_x"]) - xc) <= w / 2 + MARGIN and abs(float(p["foot_y"]) - yc) <= h / 2 + MARGIN:
                    cand.append((abs(fa - ef), gi, pi, (fa - ef) / FPS))
        used_g, used_p = set(), set()
        for _, gi, pi, lat in sorted(cand):
            if gi in used_g or pi in used_p: continue
            used_g.add(gi); used_p.add(pi); matches.append({"video": v, "gt_track": G[gi]["track_id"], "latency_s": lat,
                                                            "start_inside": G[gi]["start_inside"]})
        rows.append({"video": v, "set": "dev" if v in split["dev"] else "test", "gt_events": len(G), "alerts": len(P),
                     "tp": len(used_g), "fn": len(G) - len(used_g), "fp": len(P) - len(used_p),
                     "fps": timing.get(v, {}).get("fps_end_to_end", ""), "inference_ms": timing.get(v, {}).get("inference_ms", "")})
    with open(os.path.join(out, "event_eval.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    with open(os.path.join(out, "matches.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(matches[0].keys()) if matches else ["video"]); w.writeheader(); w.writerows(matches)
    summ = {}
    for s in ("dev", "test", "all"):
        R = [r for r in rows if s == "all" or r["set"] == s]
        tp, fn, fp = (sum(r[k] for r in R) for k in ("tp", "fn", "fp"))
        lat = [m["latency_s"] for m in matches if s == "all" or (m["video"] in split[s])]
        summ[s] = {"gt": tp + fn, "tp": tp, "fn": fn, "fp": fp,
                   "event_recall": round(tp / (tp + fn), 3) if tp + fn else None,
                   "event_precision": round(tp / (tp + fp), 3) if tp + fp else None,
                   "latency_median_s": round(st.median(lat), 2) if lat else None,
                   "latency_max_s": round(max(lat), 2) if lat else None}
    inf = [float(r["inference_ms"]) for r in rows if r["inference_ms"]]
    fps = [float(r["fps"]) for r in rows if r["fps"]]
    summ["speed"] = {"inference_ms_mean": round(st.mean(inf), 2) if inf else None, "fps_end_to_end_mean": round(st.mean(fps), 2) if fps else None}
    json.dump(summ, open(os.path.join(out, "summary.json"), "w"), indent=1)
    for r in rows: print(r)
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
