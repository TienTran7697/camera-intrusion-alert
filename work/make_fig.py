# Vẽ Hình 1.1: hướng tiếp cận tổng quát của đồ án
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "Times New Roman"

fig, ax = plt.subplots(figsize=(10, 4.6), dpi=200)
ax.set_xlim(0, 100)
ax.set_ylim(-1, 46)
ax.axis("off")

def box(x, y, w, h, title, sub, fc, ec="#333333", bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h * 0.66, title, ha="center", va="center", fontsize=11.5,
            fontweight="bold" if bold else "normal")
    ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=9.5, linespacing=1.15)

def arrow(x1, y1, x2, y2, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14,
                                 lw=1.3, color="#333333", linestyle=ls))

# Hàng trên: luồng xử lý trong ứng dụng
y, h, w = 27, 11, 14.5
xs = [1, 21, 41, 61, 81]
items = [
    ("Video camera", "camera cố định\n(video có sẵn)", "#E8EEF7"),
    ("YOLO11n", "phát hiện người\n(lớp person)", "#FCE9D9"),
    ("ByteTrack", "gán ID, theo dõi\nqua các khung hình", "#E8EEF7"),
    ("Kiểm tra vùng", "điểm chân p nằm\ntrong vùng cấm?", "#E8EEF7"),
    ("Cảnh báo", "hình ảnh, âm thanh,\nnhật ký sự kiện", "#E2F0E0"),
]
for x, (t, s, c) in zip(xs, items):
    box(x, y, w, h, t, s, c)
for i in range(4):
    arrow(xs[i] + w + 0.6, y + h / 2, xs[i + 1] - 0.6, y + h / 2)

ax.text(50, 43.5, "Ứng dụng phát hiện và cảnh báo xâm nhập (chạy trên CPU)", ha="center",
        fontsize=12, fontweight="bold")

# Hàng dưới: phần tối ưu hóa mô hình (trọng tâm)
yb, hb, wb = 6, 10, 22
xb = [5, 39, 73]
bot = [
    ("PyTorch FP32", "mô hình sau fine-tune\ntrên Human Dataset", "#F3F3F3"),
    ("OpenVINO FP32", "chuyển môi trường chạy\n(mốc so sánh)", "#F3F3F3"),
    ("OpenVINO INT8", "lượng tử hóa PTQ (NNCF)\nvới tập ảnh hiệu chuẩn", "#FCE9D9"),
]
for x, (t, s, c) in zip(xb, bot):
    box(x, yb, wb, hb, t, s, c)
arrow(xb[0] + wb + 0.6, yb + hb / 2, xb[1] - 0.6, yb + hb / 2)
arrow(xb[1] + wb + 0.6, yb + hb / 2, xb[2] - 0.6, yb + hb / 2)
ax.text(50, 0.8, "Tối ưu hóa mô hình: so sánh FP32 và INT8 (trọng tâm của đồ án)", ha="center",
        fontsize=11, fontstyle="italic")
# INT8 / FP32 được nạp vào khối YOLO11n
arrow(xb[2] + wb / 2, yb + hb + 0.6, xs[1] + w / 2 + 2, y - 0.6, ls="--")
ax.text(56, 21.2, "nạp mô hình FP32 hoặc INT8 để so sánh", ha="center", fontsize=9.5, fontstyle="italic", rotation=-9, color="#333333")

plt.savefig("hinh_1_1.png", bbox_inches="tight", facecolor="white")
print("ok")
