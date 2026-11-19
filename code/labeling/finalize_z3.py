"""Chốt nhãn Z3 từ gợi ý YOLO11x sau khi đã xem lại bằng ảnh ghép (18/11/2026). Ghi thêm vào events_gt.csv (giữ dòng Z1)."""
import csv, json, collections
B = "../../Videos/cua_hang_giay"; W = f"{B}/_label_work"
T = json.load(open(f"{W}/z3_tracks_x.json")); C = json.load(open(f"{W}/z3_candidates.json"))
last = {v: collections.defaultdict(int) for v in T}
for v in T:
    for f, tid, *_ in T[v]: last[v][tid] = max(last[v][tid], f)

def base(v):
    out = []
    for c in C[v]:
        e = dict(c, note=["goi_y_yolo11x"])
        if e["exit"] is None: e["exit"] = last[v][c["id"]] + 1; e["note"].append("mat_dau_trong_vung")
        out.append(e)
    # gộp các lượt cùng ID cách nhau <= 25 khung (rung điểm chân ở mép vùng)
    out.sort(key=lambda e: (e["id"], e["enter"])); m = []
    for e in out:
        if m and m[-1]["id"] == e["id"] and e["enter"] - m[-1]["exit"] <= 25:
            m[-1]["exit"] = max(m[-1]["exit"], e["exit"]); m[-1]["c"] += "+" + e["c"]
        else: m.append(e)
    return {e["c"].split("+")[0]: e for e in m}

def merge(d, keys, note):
    ks = []
    for k in keys:
        kk = next(x for x in d if k in d[x]["c"].split("+"))
        if kk not in ks: ks.append(kk)
    es = [d.pop(k) for k in ks]; keys = ks
    e = es[0]; e["enter"] = min(x["enter"] for x in es); e["exit"] = max(x["exit"] for x in es)
    e["c"] = "+".join(x["c"] for x in es); e["note"].append(note); d[keys[0]] = e

V1 = base("Video1")
for e in V1.values():
    if 1150 <= e["enter"] <= 1720: e["note"].append("dong_nguoi")
V2 = base("Video2")
merge(V2, ["C5", "C9"], "gop_doi_ID")                  # người đàn ông áo xám đứng lâu
merge(V2, ["C7", "C8", "C10", "C11"], "gop_doi_ID")    # người phụ nữ váy đen đi cùng
for k in ["C6", "C18", "C19"]:
    kk = next(x for x in V2 if k in V2[x]["c"].split("+")); print("bo", kk, V2[kk]["c"]); V2.pop(kk)               # C6 trùng người, C18 là em bé được bế, C19 chân ở ngoài vùng
V2["C17"]["exit"] = 5412; V2["C17"]["note"].append("be_tre_tren_tay")
V2["C20"]["exit"] = 6036; V2["C20"]["note"].append("mat_dau_sat_ke")
V2["C23"]["note"].append("dung_lau_tren_mep")

rows = [r for r in csv.DictReader(open(f"{B}/events_gt.csv", encoding="utf-8")) if r["zone_id"] != "Z3"]
cols = list(rows[0].keys()) if rows else None
cols = cols or ["video","zone_id","track_id","enter_frame","enter_time_s","exit_frame","exit_time_s","start_inside","verified","note","foot_x","foot_y"]
for v, d in (("Video1", V1), ("Video2", V2)):
    for i, e in enumerate(sorted(d.values(), key=lambda e: e["enter"])):
        if e["exit"] - e["enter"] < 8: e["note"].append("sat_mep")
        rows.append({"video": v, "zone_id": "Z3", "track_id": f"Q{i+1}", "enter_frame": e["enter"], "enter_time_s": round(e["enter"]/25, 2),
                     "exit_frame": e["exit"], "exit_time_s": round(e["exit"]/25, 2), "start_inside": int(e["enter"] == 0), "verified": 0,
                     "note": ";".join(e["note"]) + f";goc={e['c']}", "foot_x": "", "foot_y": ""})
with open(f"{B}/events_gt.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
cnt = collections.Counter((r["video"], r["zone_id"]) for r in rows)
print(dict(cnt)); print("sat_mep:", collections.Counter(r["video"] for r in rows if "sat_mep" in r["note"]))
