"""Dò tham số bộ lọc báo nhầm (core/alarm.py) offline trên tracks.json đã lưu.

- CHỌN tham số chỉ dựa trên 5 video CAVIAR DEV: giữ số lượt báo đúng cao nhất, rồi ít báo nhầm nhất,
  hòa thì chọn cấu hình đơn giản hơn (ít bộ lọc bật hơn).
- Sau đó mới chấm cấu hình đã chọn trên CAVIAR TEST và 2 video cửa hàng giày (không dùng để chọn).
python tune_filters.py --tag ft_v1
-> results/<tag>/filter_grid.csv, results/<tag>_loc/ (kết quả cấu hình đã chọn)
"""
import argparse, csv, itertools, json, os, shutil, subprocess, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from core.alarm import ZoneAlarm

CAV = os.path.join(HERE, "../../Videos/CAVIAR"); SHOP = os.path.join(HERE, "../../Videos/cua_hang_giay")
GRID = {"min_conf": [0.0, 0.35, 0.5], "min_age": [0, 25, 50], "born_outside": [False, True], "min_move": [0.0, 0.5, 1.0]}


def simulate(T, cfg, confirm=8):
    zc = json.load(open(os.path.join(CAV, "zones.json")))["zones"]
    zs = json.load(open(os.path.join(SHOP, "zones.json"), encoding="utf-8"))
    cav, shop = [], []
    for v, dets in T.items():
        by = collections.defaultdict(list)
        for f, tid, x1, y1, x2, y2, c in dets: by[f].append((tid, x1, y1, x2, y2, c))
        if v.startswith("Video"):
            s = zs["frame_size"][0] / 1280
            alarms = {z["zone_id"]: ZoneAlarm([[x / s, y / s] for x, y in z["polygon"]], confirm, **cfg) for z in zs["videos"][v]}
        else:
            s = 1; alarms = {"A": ZoneAlarm(zc[v]["polygon"], confirm, **cfg)}
        for f in sorted(by):
            for zid, al in alarms.items():
                for e in al.update(f, by[f]):
                    if e["type"] != "alert": continue
                    r = {"video": v, "track_id": e["track_id"], "alert_frame": e["frame"], "enter_frame": e["enter_frame"],
                         "foot_x": round(e["foot"][0] * s, 1), "foot_y": round(e["foot"][1] * s, 1), "conf": round(e["conf"], 3)}
                    if v.startswith("Video"): r["zone_id"] = zid; shop.append(r)
                    else: cav.append(r)
    return cav, shop


def write(rows, path, keys):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)


def score(tag, src, cav, shop, do_shop):
    d = os.path.join(HERE, "results", tag); os.makedirs(d, exist_ok=True)
    write(cav, os.path.join(d, "pred_events.csv"), ["video", "track_id", "alert_frame", "enter_frame", "foot_x", "foot_y", "conf"])
    shutil.copy(os.path.join(src, "timing.csv"), d)
    subprocess.run([sys.executable, os.path.join(HERE, "eval_events.py"), "--tag", tag], capture_output=True, check=True)
    res = json.load(open(os.path.join(d, "summary.json")))
    if do_shop:
        write(shop, os.path.join(d, "shop_pred_events.csv"), ["video", "track_id", "alert_frame", "enter_frame", "foot_x", "foot_y", "conf", "zone_id"])
        shutil.copy(os.path.join(src, "shop_timing.csv"), d)
        subprocess.run([sys.executable, os.path.join(HERE, "eval_shop.py"), "--tag", tag], capture_output=True, check=True)
        res["shop"] = json.load(open(os.path.join(d, "shop_summary.json")))
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--tag", required=True); a = ap.parse_args()
    src = os.path.join(HERE, "results", a.tag)
    T = json.load(open(os.path.join(src, "tracks.json")))
    Tdev = {v: T[v] for v in json.load(open(os.path.join(CAV, "split.json")))["dev"]}
    grid = []
    for vals in itertools.product(*GRID.values()):
        cfg = dict(zip(GRID, vals)); cav, _ = simulate(Tdev, cfg)
        r = score("_tmp_grid", src, cav, [], False)["dev"]
        n_on = sum(1 for k, v in cfg.items() if v)
        grid.append({**cfg, "n_on": n_on, "dev_tp": r["tp"], "dev_fp": r["fp"], "dev_fn": r["fn"]})
    shutil.rmtree(os.path.join(HERE, "results", "_tmp_grid"))
    write(grid, os.path.join(src, "filter_grid.csv"), list(grid[0].keys()))
    best_tp = max(g["dev_tp"] for g in grid)
    best = min((g for g in grid if g["dev_tp"] == best_tp), key=lambda g: (g["dev_fp"], g["n_on"], g["min_age"], g["min_conf"], g["min_move"]))
    cfg = {k: best[k] for k in GRID}
    print("CAU HINH CHON (theo dev):", best)
    res_off = score(a.tag + "_khong_loc", src, *simulate(T, {}), True)
    res_on = score(a.tag + "_loc", src, *simulate(T, cfg), True)
    json.dump({"config": cfg, "khong_loc": res_off, "loc": res_on}, open(os.path.join(src, "filter_result.json"), "w"), indent=1)
    for name, r in (("KHONG LOC", res_off), ("CO LOC", res_on)):
        print(name, "dev", r["dev"], "\n   test", r["test"], "\n   shop", r["shop"]["total"])
