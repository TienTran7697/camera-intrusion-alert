# Sắp xếp lại Human Dataset: bỏ ảnh val trùng với train, tách val gốc thành val/test (seed cố định).
# Không xóa ảnh nào: ảnh trùng và file cache cũ được chuyển vào Dataset/_removed. Mọi thao tác ghi vào moves.csv.
import os, sys, shutil, hashlib, random, csv

ROOT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else "../Dataset")
SEED = 42
IMG_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
I, L = os.path.join(ROOT, "images"), os.path.join(ROOT, "labels")
assert not os.path.exists(os.path.join(I, "test")), "Đã có images/test — dataset có vẻ đã được sắp xếp rồi, dừng lại."

log = []
def move(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    assert not os.path.exists(dst), dst
    shutil.move(src, dst)
    log.append((os.path.relpath(src, ROOT), os.path.relpath(dst, ROOT)))

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

def stems(split):
    return {os.path.splitext(f)[0]: f for f in os.listdir(os.path.join(I, split)) if os.path.splitext(f)[1].lower() in IMG_EXT}

# 1) cache cũ của Ultralytics (sẽ tự tạo lại)
for f in ("train.cache", "val.cache"):
    p = os.path.join(L, f)
    if os.path.exists(p): move(p, os.path.join(ROOT, "_removed", "cache", f))

# 2) ảnh val trùng nội dung với train
train_hash = {md5(os.path.join(I, "train", f)) for f in stems("train").values()}
val = stems("val")
dups = sorted(s for s, f in val.items() if md5(os.path.join(I, "val", f)) in train_hash)
for s in dups:
    move(os.path.join(I, "val", val[s]), os.path.join(ROOT, "_removed", "val_duplicates_of_train", "images", val[s]))
    move(os.path.join(L, "val", s + ".txt"), os.path.join(ROOT, "_removed", "val_duplicates_of_train", "labels", s + ".txt"))

# 3) tách phần val còn lại thành val/test (một nửa mỗi bên)
val = stems("val")
keys = sorted(val)
random.Random(SEED).shuffle(keys)
test_keys = sorted(keys[len(keys) // 2:])
for s in test_keys:
    move(os.path.join(I, "val", val[s]), os.path.join(I, "test", val[s]))
    move(os.path.join(L, "val", s + ".txt"), os.path.join(L, "test", s + ".txt"))

# 4) data.yaml cho Ultralytics
yaml = f"""# Human Dataset (Kaggle, fareselmenshawii) - đã sắp xếp lại bởi work/split_dataset.py (seed={SEED})
path: {ROOT.replace(os.sep, '/')}
train: images/train
val: images/val
test: images/test
names:
  0: person
"""
open(os.path.join(ROOT, "data.yaml"), "w", encoding="utf-8").write(yaml)

with open(os.path.join(ROOT, "moves.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["from", "to"]); w.writerows(log)

counts = {sp: len(stems(sp)) for sp in ("train", "val", "test")}
print("duplicates removed from val:", len(dups))
print("counts:", counts, "total:", sum(counts.values()))
print("moves logged:", len(log))
