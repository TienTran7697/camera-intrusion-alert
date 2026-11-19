"""So sánh chất lượng cảnh báo của PyTorch FP32, OpenVINO FP32 và OpenVINO INT8 trên 12 video,
cùng logic cảnh báo, có và không có bộ lọc đã chọn ở tuần 3 (min_conf = 0,5, chọn trên CAVIAR dev).
Dùng tracks.json đã lưu bởi dump_tracks.py.
python compare_variants.py  -> results/so_sanh_fp32_int8.json và bảng in ra màn hình
"""
import json, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = sys.argv[:1]
import tune_filters as T

VARIANTS = {"PyTorch FP32": "ft_v1", "OpenVINO FP32": "ov_fp32", "OpenVINO INT8": "ov_int8_c300"}
CFGS = {"khong loc": {}, "min_conf 0,5": {"min_conf": 0.5}}

if __name__ == "__main__":
    out = {}
    for vname, tag in VARIANTS.items():
        src = os.path.join(HERE, "results", tag)
        tracks = json.load(open(os.path.join(src, "tracks.json")))
        for cname, cfg in CFGS.items():
            r = T.score(f"_cmp_{tag}", src, *T.simulate(tracks, cfg), True)
            s = r["shop"]["total"]
            out[f"{vname} | {cname}"] = {"dev": r["dev"], "test": r["test"], "shop": s}
            print(f"{vname:14s} {cname:13s} | dev {r['dev']['tp']}/{r['dev']['gt']} nham {r['dev']['fp']}"
                  f" | test {r['test']['tp']}/{r['test']['gt']} nham {r['test']['fp']} tre {r['test']['latency_median_s']}s"
                  f" | shop {s['tp']}/{s['gt']} nham {s['fp']} (R {s['recall']}, P {s['precision']})", flush=True)
        shutil.rmtree(os.path.join(HERE, "results", f"_cmp_{tag}"), ignore_errors=True)
    json.dump(out, open(os.path.join(HERE, "results", "so_sanh_fp32_int8.json"), "w"), indent=1)
