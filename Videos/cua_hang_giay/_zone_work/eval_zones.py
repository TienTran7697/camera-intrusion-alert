# Đếm số cảnh báo (lượt vào) của từng vùng đề xuất từ track đã lưu, dùng đúng logic ZoneAlarm
import json, sys, collections
sys.path.insert(0, "../../../code/core"); from alarm import ZoneAlarm
T = json.load(open("tracks_pretrained.json")); Z = json.load(open("zones_candidates.json"))["zones"]
res = {}
for k, z in Z.items():
    row = {}
    for v, dets in T.items():
        by = collections.defaultdict(list)
        for f, tid, x1, y1, x2, y2, cf in dets: by[f].append((tid, x1, y1, x2, y2, cf))
        al = ZoneAlarm(z["polygon"], 8); ev = []
        for f in sorted(by): ev += [e for e in al.update(f, by[f]) if e["type"] == "alert"]
        row[v] = {"alerts": len(ev), "ids": len({e["track_id"] for e in ev}), "frames": [e["frame"] for e in ev]}
    res[k] = row
    print(k, z["ten"], {v: (r["alerts"]) for v, r in row.items()})
json.dump(res, open("zone_alert_counts.json", "w"), indent=1)
