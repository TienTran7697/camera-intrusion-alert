"""Xuất mô hình đã fine-tune sang OpenVINO FP32 và INT8 (lượng tử hóa sau huấn luyện - PTQ, bằng NNCF).

Cả FP32 và INT8 đều tạo từ CÙNG một checkpoint (code/models/ft_v1.pt = code/train/runs/ft_v1/weights/best.pt).
INT8 dùng cơ chế xuất của Ultralytics (NNCF, preset MIXED, bỏ qua phần hậu xử lý của đầu Detect).
Ảnh hiệu chuẩn: chọn NGẪU NHIÊN (seed 42) N ảnh từ tập VALIDATION của data_ft.yaml (Human val + CAVIAR Walk1),
không dùng tập test. Danh sách lưu ở Dataset/calib/calib_<N>.txt (tập nhỏ nằm trong tập lớn: 100 ⊂ 300 ⊂ 500).
(Không dùng tham số fraction của Ultralytics vì nó chỉ lấy N ảnh ĐẦU TIÊN, không ngẫu nhiên.)

python export_openvino.py               # FP32 + INT8 với 100, 300, 500 ảnh hiệu chuẩn
Kết quả: code/models/ft_v1_fp32_openvino_model/, ft_v1_int8_c100_openvino_model/, ..._c300_..., ..._c500_...
"""
import os, shutil, sys
from ultralytics import YOLO

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "../models")
DATA = os.path.join(HERE, "../../Dataset/data_ft.yaml")
CAL = os.path.join(HERE, "../../Dataset/calib")


def calib_yaml(n, seed=42):
    import glob, random
    D = os.path.join(HERE, "../../Dataset")
    pool = sorted(glob.glob(f"{D}/images/val/*.jpg")) + sorted(glob.glob(f"{D}/caviar_dev/images/val/*.jpg"))
    random.Random(seed).shuffle(pool)
    os.makedirs(CAL, exist_ok=True)
    lst = os.path.join(CAL, f"calib_{n}.txt")
    NL = chr(10)
    open(lst, "w").write(NL.join(os.path.abspath(p).replace(os.sep, "/") for p in pool[:n]) + NL)
    y = os.path.join(CAL, f"calib_{n}.yaml")
    names = YOLO(SRC).names
    txt = f"train: {os.path.abspath(lst)}{NL}val: {os.path.abspath(lst)}{NL}names:{NL}"
    txt += "".join(f"  {k}: {v}{NL}" for k, v in names.items())
    open(y, "w", encoding="utf-8").write(txt)
    n_cav = sum("caviar_dev" in p for p in pool[:n])
    print(f"calib {n}: {n_cav} anh CAVIAR, {n - n_cav} anh Human", flush=True)
    return y
SRC = os.path.join(HERE, "../train/runs/ft_v1/weights/best.pt")


IMGSZ = int(os.environ.get("IMGSZ", 640))   # vd: IMGSZ=416 python export_openvino.py fp32 c300


def export(name, **kw):
    if IMGSZ != 640: name = f"{name}_{IMGSZ}"
    tmp = os.path.join(M, f"_tmp_{name}"); os.makedirs(tmp, exist_ok=True)
    pt = os.path.join(tmp, "ft_v1.pt"); shutil.copy(SRC, pt)
    out = YOLO(pt).export(format="openvino", imgsz=IMGSZ, batch=1, dynamic=False, half=False, **kw)
    dst = os.path.join(M, f"ft_v1_{name}_openvino_model")
    shutil.rmtree(dst, ignore_errors=True); shutil.move(out, dst); shutil.rmtree(tmp)
    print("->", dst, flush=True)


if __name__ == "__main__":
    shutil.copy(SRC, os.path.join(M, "ft_v1.pt"))
    which = sys.argv[1:] or ["fp32", "c100", "c300", "c500"]
    for w in which:
        if w == "fp32":
            export("fp32")
        else:
            n = int(w[1:])
            export(f"int8_{w}", int8=True, data=calib_yaml(n), fraction=1.0)
