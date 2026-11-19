"""Dò mịn ngưỡng tin cậy tối thiểu (bước 0,05) cho từng phiên bản mô hình. CHỌN chỉ theo CAVIAR dev:
nhiều lượt đúng nhất -> ít báo nhầm nhất -> ngưỡng thấp nhất (giữ recall). Test và cửa hàng chỉ để báo cáo.
python tune_conf_fine.py ov_fp32 ov_int8_c300"""
import json, os, sys, shutil
tags = sys.argv[1:]; sys.argv = sys.argv[:1]
import tune_filters as T
HERE = os.path.dirname(os.path.abspath(__file__)); out = {}
for tag in tags:
    src = os.path.join(HERE, "results", tag); tr = json.load(open(os.path.join(src, "tracks.json"))); rows = []
    for th in [0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
        r = T.score("_tmp_fine", src, *T.simulate(tr, {"min_conf": th} if th > 0.25 else {}), True); s = r["shop"]["total"]
        rows.append({"th": th, "dev": [r["dev"]["tp"], r["dev"]["fp"]], "test": [r["test"]["tp"], r["test"]["fp"]], "shop": [s["tp"], s["fp"]],
                     "lat_test": r["test"]["latency_median_s"]})
    best = min(rows, key=lambda x: (-x["dev"][0], x["dev"][1], x["th"]))
    out[tag] = {"rows": rows, "chon": best}
    for x in rows: print(tag, x["th"], "dev", x["dev"], "test", x["test"], "shop", x["shop"])
    print("CHON", tag, best)
shutil.rmtree(os.path.join(HERE, "results", "_tmp_fine"), ignore_errors=True)
json.dump(out, open(os.path.join(HERE, "results", "nguong_rieng.json"), "w"), indent=1)
