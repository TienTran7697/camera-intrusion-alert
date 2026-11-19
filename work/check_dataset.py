# Kiểm tra bộ Human Dataset dạng YOLO: số ảnh/nhãn, ghép cặp, lớp, tọa độ, ảnh trùng.
import os, sys, hashlib, random, json
from collections import Counter
from PIL import Image

ROOT = sys.argv[1]
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
report = {}
all_hash = {}
for split in ("train", "val"):
    idir, ldir = os.path.join(ROOT, "images", split), os.path.join(ROOT, "labels", split)
    imgs = {os.path.splitext(f)[0]: f for f in os.listdir(idir) if os.path.splitext(f)[1].lower() in IMG_EXT}
    other = [f for f in os.listdir(idir) if os.path.splitext(f)[1].lower() not in IMG_EXT]
    labs = {os.path.splitext(f)[0] for f in os.listdir(ldir) if f.endswith(".txt")}
    cls, nbox, empty, bad, out_of_range = Counter(), [], 0, [], 0
    widths, heights, aspect = [], [], []
    for stem in labs & imgs.keys():
        lines = [l.split() for l in open(os.path.join(ldir, stem + ".txt"), encoding="utf-8").read().splitlines() if l.strip()]
        if not lines: empty += 1
        nbox.append(len(lines))
        for l in lines:
            if len(l) != 5: bad.append(stem); continue
            c, x, y, w, h = l[0], *map(float, l[1:])
            cls[c] += 1
            if not all(0 <= v <= 1.0001 for v in (x, y, w, h)): out_of_range += 1
            widths.append(w); heights.append(h)
    # kích thước ảnh, tỷ lệ box (mẫu 400 ảnh)
    sizes = Counter()
    sample = random.Random(0).sample(sorted(imgs), min(400, len(imgs)))
    for s in sample:
        with Image.open(os.path.join(idir, imgs[s])) as im: sizes[im.size] += 1
    # trùng lặp tuyệt đối (md5)
    dup_in = 0
    for s, f in imgs.items():
        h = hashlib.md5(open(os.path.join(idir, f), "rb").read()).hexdigest()
        if h in all_hash: dup_in += 1
        all_hash.setdefault(h, []).append(f"{split}/{f}")
    nb = sorted(nbox)
    report[split] = {
        "images": len(imgs), "labels": len(labs), "non_image_files": other[:5],
        "img_without_label": len(imgs.keys() - labs), "label_without_img": len(labs - imgs.keys()),
        "classes": dict(cls), "boxes": sum(nbox), "empty_label_files": empty,
        "boxes_per_img_median": nb[len(nb)//2] if nb else 0, "boxes_per_img_max": nb[-1] if nb else 0,
        "malformed_lines_files": len(set(bad)), "coords_out_of_range": out_of_range,
        "box_h_median": round(sorted(heights)[len(heights)//2], 3) if heights else None,
        "box_w_median": round(sorted(widths)[len(widths)//2], 3) if widths else None,
        "small_boxes_h<0.1": sum(h < 0.1 for h in heights),
        "boxes_touch_bottom": None,
        "top_image_sizes": sizes.most_common(5),
        "dup_files_seen_before": dup_in,
    }
cross = sum(1 for v in all_hash.values() if {p.split('/')[0] for p in v} == {"train", "val"})
report["duplicate_groups_total"] = sum(1 for v in all_hash.values() if len(v) > 1)
report["duplicates_across_train_val"] = cross
print(json.dumps(report, ensure_ascii=False, indent=1))
