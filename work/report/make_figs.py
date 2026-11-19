"""Tạo hình minh họa cho báo cáo đồ án (work/report/fig/). Ảnh có khách hàng thật được làm mờ vùng đầu."""
import os, sys, json, csv, collections
import cv2, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

R = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OUT = os.path.join(R, "work/report/fig"); os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(R, "code/labeling")); sys.path.insert(0, os.path.join(R, "code"))
plt.rcParams.update({"font.family": "Times New Roman", "font.size": 12, "axes.titlesize": 12})
CAV = os.path.join(R, "Videos/CAVIAR"); SHOP = os.path.join(R, "Videos/cua_hang_giay")
ZONE_A = json.load(open(f"{CAV}/zones.json"))["zones"]["Walk2"]["polygon"]
_X = None


def blur_heads(im):
    """Làm mờ vùng đầu của mọi người phát hiện được (YOLO11x) để bảo vệ quyền riêng tư."""
    global _X
    from ultralytics import YOLO
    if _X is None: _X = YOLO(os.path.join(R, "code/models/yolo11x.pt"))
    out = im.copy(); k0 = max(1.0, 960 / max(im.shape[:2]))          # ảnh nhỏ: phóng to để phát hiện người nhỏ
    big = cv2.resize(im, None, fx=k0, fy=k0, interpolation=cv2.INTER_CUBIC) if k0 > 1 else im
    for r in _X.predict(big, classes=[0], conf=0.08, imgsz=1280, device=0, verbose=False):
        for x1, y1, x2, y2 in (r.boxes.xyxy.cpu().numpy() / k0).astype(int):
            h = y2 - y1; w = x2 - x1; hh = int(max(0.28 * h, 0.6 * w))
            a, b = max(0, x1 - 2), max(0, y1 - 2); c, d = min(im.shape[1], x2 + 2), min(im.shape[0], y1 + hh)
            if d > b and c > a:
                k = max(9, (min(c - a, d - b) // 2) * 2 + 1)
                out[b:d, a:c] = cv2.GaussianBlur(out[b:d, a:c], (k, k), 0)
    return out


def read_frame(path, idx, size=None):
    cap = cv2.VideoCapture(path); f = -1
    while f < idx:
        ok, im = cap.read(); f += 1
        if not ok: return None
    return cv2.resize(im, size, interpolation=cv2.INTER_AREA) if size else im


def save(name, im): cv2.imwrite(os.path.join(OUT, name), im); print("->", name)


def box(ax, x, y, w, h, txt, fc="#dce8f8", ec="#1d4f9c", fs=11):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec, lw=1.5))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, wrap=True)


def arrow(ax, p, q, txt=None, style="-|>"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=14, lw=1.4, color="#333"))
    if txt: ax.text((p[0] + q[0]) / 2, (p[1] + q[1]) / 2 + 0.08, txt, ha="center", fontsize=9, color="#333")


# ---------------- Hình 2.1: điểm chân và điểm trong đa giác
def fig_foot():
    from caviar_gt import load_tracks
    T = load_tracks(f"{CAV}/Walk2"); ev = [r for r in csv.DictReader(open(f"{CAV}/events_gt.csv")) if r["video"] == "Walk2" and r["enter_frame"]][0]
    tid, f = int(ev["track_id"]), int(ev["enter_frame"]) + 15
    b = {fr: (xc, yc, w, h) for fr, xc, yc, w, h in T[tid]}[f]
    im = read_frame(f"{CAV}/Walk2/Walk2.mpg", f); s = 3
    im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    P = (np.array(ZONE_A) * s).astype(np.int32); ov = im.copy(); cv2.fillPoly(ov, [P], (0, 0, 255))
    im = cv2.addWeighted(ov, 0.25, im, 0.75, 0); cv2.polylines(im, [P], True, (0, 0, 255), 3)
    xc, yc, w, h = [v * s for v in b]; x1, y1, x2, y2 = int(xc - w / 2), int(yc - h / 2), int(xc + w / 2), int(yc + h / 2)
    cv2.rectangle(im, (x1, y1), (x2, y2), (0, 200, 0), 3); p = (int(xc), y2)
    cv2.line(im, p, (im.shape[1] - 5, p[1]), (255, 160, 0), 2, cv2.LINE_AA)
    cv2.circle(im, p, 9, (0, 255, 255), -1); cv2.circle(im, p, 9, (0, 0, 0), 2)
    cv2.putText(im, "p = ((x1+x2)/2, y2)", (p[0] + 14, p[1] + 34), 0, 0.9, (0, 0, 0), 4, cv2.LINE_AA)
    cv2.putText(im, "p = ((x1+x2)/2, y2)", (p[0] + 14, p[1] + 34), 0, 0.9, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(im, "Vung cam A", (P[:, 0].min() + 6, P[:, 1].min() - 12), 0, 1.0, (0, 0, 255), 3, cv2.LINE_AA)
    cv2.putText(im, "tia ngang tu p", (im.shape[1] - 260, p[1] - 12), 0, 0.8, (255, 160, 0), 2, cv2.LINE_AA)
    save("h2_1_diem_chan.png", im[max(0, y1 - 160):min(im.shape[0], y2 + 200), :])


# ---------------- Hình 2.2: lượng tử hóa affine
def fig_quant():
    rng = np.random.default_rng(0); x = np.concatenate([rng.normal(0, 0.6, 4000), rng.normal(1.8, 0.3, 600)])
    lo, hi = np.percentile(x, 0.1), np.percentile(x, 99.9); s = (hi - lo) / 255; z = int(round(-lo / s)) - 128
    xs = np.linspace(lo - 0.6, hi + 0.6, 2000); q = np.clip(np.round(xs / s) + z, -128, 127); xr = (q - z) * s
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    ax[0].hist(x, bins=120, color="#1d4f9c", alpha=0.8); ax[0].axvline(lo, color="r", ls="--"); ax[0].axvline(hi, color="r", ls="--")
    ax[0].set_title("(a) Phân bố giá trị FP32 và khoảng [α, β] chọn khi hiệu chuẩn"); ax[0].set_xlabel("giá trị thực x")
    ax[1].plot(xs, xs, "k:", lw=1, label="x (FP32)"); ax[1].plot(xs, xr, color="#c62828", lw=1.2, label="giải lượng tử từ INT8")
    ax[1].set_title("(b) x → q = round(x/s) + z → (q − z)·s"); ax[1].set_xlabel("giá trị thực x"); ax[1].legend(fontsize=9)
    ax[1].annotate("bị cắt (clipping)", (hi + 0.4, hi), (hi - 1.2, hi + 0.6), arrowprops=dict(arrowstyle="->"), fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "h2_2_luong_tu_hoa.png"), dpi=200); plt.close(fig); print("-> h2_2")


# ---------------- Hình 3.1: kiến trúc tổng thể
def fig_arch():
    fig, ax = plt.subplots(figsize=(11, 5.2)); ax.set_xlim(0, 11); ax.set_ylim(0, 5.2); ax.axis("off")
    y = 3.4
    box(ax, 0.1, y, 1.6, 1.0, "Video\n(camera cố định\nhoặc tệp video)")
    box(ax, 2.1, y, 1.8, 1.0, "Phát hiện người\nYOLO11n\n(FP32 / INT8)")
    box(ax, 4.3, y, 1.6, 1.0, "Theo dõi\nByteTrack\n(gán ID)")
    box(ax, 6.3, y, 1.8, 1.0, "Điểm chân p\ntrong đa giác\nvùng cấm?")
    box(ax, 8.5, y, 2.3, 1.0, "Logic cảnh báo\nxác nhận 8 khung\n+ bộ lọc tin cậy")
    for a, b in [((1.7, y + .5), (2.1, y + .5)), ((3.9, y + .5), (4.3, y + .5)), ((5.9, y + .5), (6.3, y + .5)), ((8.1, y + .5), (8.5, y + .5))]:
        arrow(ax, a, b)
    box(ax, 6.0, 1.3, 2.3, 1.1, "Hiển thị (PySide6)\nvùng, khung, ID,\ntrạng thái, âm thanh", fc="#e8f5e9", ec="#2e7d32")
    box(ax, 8.6, 1.3, 2.3, 1.1, "Lưu bằng chứng\nSQLite events.db\n+ ảnh + clip\n(luồng riêng)", fc="#fff3e0", ec="#ef6c00")
    arrow(ax, (9.65, y), (9.75, 2.4), "sự kiện"); arrow(ax, (9.0, y), (7.4, 2.4), "trạng thái")
    box(ax, 0.1, 1.0, 4.9, 1.6, "", fc="#f4f7fc", ec="#7a8fb0")
    ax.text(2.55, 2.35, "Tối ưu hóa mô hình (ngoại tuyến)", ha="center", fontsize=11, weight="bold")
    box(ax, 0.25, 1.15, 1.35, 0.9, "PyTorch\nFP32\n(ft_v1.pt)", fs=10)
    box(ax, 1.9, 1.15, 1.35, 0.9, "OpenVINO\nFP32", fs=10)
    box(ax, 3.55, 1.15, 1.35, 0.9, "OpenVINO\nINT8 (PTQ,\nNNCF)", fs=10, fc="#ffe0e0", ec="#c62828")
    arrow(ax, (1.6, 1.6), (1.9, 1.6)); arrow(ax, (3.25, 1.6), (3.55, 1.6)); arrow(ax, (4.2, 2.05), (3.0, y), "nạp mô hình")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "h3_1_kien_truc.png"), dpi=200); plt.close(fig); print("-> h3_1")


# ---------------- Hình 3.2: vùng A trên CAVIAR
def fig_zoneA():
    im = read_frame(f"{CAV}/Browse1/Browse1.mpg", 5); s = 2
    im = cv2.resize(im, None, fx=s, fy=s, interpolation=cv2.INTER_CUBIC)
    P = (np.array(ZONE_A) * s).astype(np.int32); ov = im.copy(); cv2.fillPoly(ov, [P], (0, 0, 255))
    im = cv2.addWeighted(ov, 0.3, im, 0.7, 0); cv2.polylines(im, [P], True, (0, 0, 255), 3)
    cv2.putText(im, "A", tuple(P.mean(0).astype(int) - [10, 0]), 0, 1.4, (255, 255, 255), 3, cv2.LINE_AA)
    save("h3_2_vung_A.png", im)


# ---------------- Hình 3.3: vùng Z1, Z3 trên nền cửa hàng (ảnh nền trung vị, đã loại người)
def fig_zoneShop():
    im = cv2.imread(f"{SHOP}/_zone_work/Video2_bg.png"); Z = json.load(open(f"{SHOP}/zones.json", encoding="utf-8"))["videos"]["Video2"]
    ov = im.copy(); col = {"Z1": (0, 0, 255), "Z3": (255, 0, 255)}
    for z in Z: cv2.fillPoly(ov, [np.array(z["polygon"], np.int32) // 2], col[z["zone_id"]])
    im = cv2.addWeighted(ov, 0.35, im, 0.65, 0)
    for z in Z:
        p = np.array(z["polygon"], np.int32) // 2; cv2.polylines(im, [p], True, col[z["zone_id"]], 3)
        cx, cy = p.mean(0).astype(int); cv2.putText(im, z["zone_id"], (cx - 18, cy + 8), 0, 1, (0, 0, 0), 5); cv2.putText(im, z["zone_id"], (cx - 18, cy + 8), 0, 1, (255, 255, 255), 2)
    save("h3_3_vung_cua_hang.png", im)


# ---------------- Hình 3.5: lưu đồ trạng thái
def fig_state():
    fig, ax = plt.subplots(figsize=(10, 3.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 3.6); ax.axis("off")
    box(ax, 0.6, 1.2, 2.6, 1.2, "NGOÀI VÙNG\n(out)", fc="#e8f5e9", ec="#2e7d32", fs=13)
    box(ax, 6.8, 1.2, 2.6, 1.2, "ĐANG CẢNH BÁO\n(in)", fc="#ffebee", ec="#c62828", fs=13)
    ax.add_patch(FancyArrowPatch((3.2, 2.15), (6.8, 2.15), connectionstyle="arc3,rad=-0.25", arrowstyle="-|>", mutation_scale=16, lw=1.5))
    ax.text(5.0, 3.15, "p trong vùng liên tục ≥ 8 khung\nvà qua bộ lọc (tin cậy ≥ ngưỡng)\n→ PHÁT CẢNH BÁO (1 lần/lượt), ghi bằng chứng",
            ha="center", fontsize=10)
    ax.add_patch(FancyArrowPatch((6.8, 1.45), (3.2, 1.45), connectionstyle="arc3,rad=-0.25", arrowstyle="-|>", mutation_scale=16, lw=1.5))
    ax.text(5.0, 0.2, "p ngoài vùng liên tục ≥ 8 khung → KẾT THÚC LƯỢT, cập nhật t_exit", ha="center", fontsize=10)
    ax.text(1.9, 0.75, "Khung mất dấu: giữ nguyên trạng thái", ha="center", fontsize=9, style="italic", color="#555")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "h3_5_trang_thai.png"), dpi=200); plt.close(fig); print("-> h3_5")


# ---------------- Hình 3.6: quá trình huấn luyện
def fig_train():
    rows = list(csv.DictReader(open(f"{R}/code/train/runs/ft_v1/results.csv")))
    e = [int(r["epoch"]) for r in rows]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    ax[0].plot(e, [float(r["train/box_loss"]) for r in rows], label="box loss (train)")
    ax[0].plot(e, [float(r["train/cls_loss"]) for r in rows], label="cls loss (train)")
    ax[0].set_xlabel("epoch"); ax[0].set_title("(a) Hàm mất mát trên tập huấn luyện"); ax[0].legend(fontsize=9); ax[0].set_ylim(0, 2.5)
    ax[1].plot(e, [float(r["metrics/mAP50(B)"]) for r in rows], label="mAP@50 (val)")
    ax[1].plot(e, [float(r["metrics/mAP50-95(B)"]) for r in rows], label="mAP@50–95 (val)")
    ax[1].axvline(40, color="gray", ls=":", lw=1); ax[1].text(40.5, 0.25, "tắt mosaic\n(10 epoch cuối)", fontsize=8)
    ax[1].set_xlabel("epoch"); ax[1].set_title("(b) Độ chính xác trên tập kiểm định gộp"); ax[1].legend(fontsize=9)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "h3_6_huan_luyen.png"), dpi=200); plt.close(fig); print("-> h3_6")


# ---------------- Hình 4.1: giao diện (làm mờ đầu khách)
def fig_gui():
    im = cv2.imread(f"{R}/work/hinh/giao_dien_dang_chay.png"); x0, y0, x1, y1 = 9, 89, 1065, 677
    im[y0:y1, x0:x1] = blur_heads(im[y0:y1, x0:x1]); save("h4_1_giao_dien.png", im)


# ---------------- Hình 4.2: ảnh bằng chứng
def fig_evidence():
    d = f"{R}/outputs/thu/evidence"; base = "Walk2_A_id32_f000877_openvino_int8"
    a = cv2.imread(f"{d}/{base}_full.jpg"); b = cv2.imread(f"{d}/{base}_crop.jpg")
    a = cv2.resize(a, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    b = cv2.resize(b, (int(b.shape[1] * a.shape[0] * 0.6 / b.shape[0]), int(a.shape[0] * 0.6)), interpolation=cv2.INTER_CUBIC)
    pad = np.full((a.shape[0], b.shape[1] + 30, 3), 255, np.uint8); pad[(a.shape[0] - b.shape[0]) // 2:(a.shape[0] + b.shape[0]) // 2, 15:15 + b.shape[1]] = b
    save("h4_2_bang_chung.png", np.hstack([a, pad]))


# ---------------- Hình 4.3: mô hình gốc vs fine-tune trên CAVIAR test
def fig_compare():
    from ultralytics import YOLO
    m0 = YOLO(f"{R}/code/models/yolo11n.pt"); m1 = YOLO(f"{R}/code/train/runs/ft_v1/weights/best.pt")
    picks = [("Walk2", 430), ("Meet_WalkTogether1", 380), ("Browse4", 700)]; rows = []
    for v, f in picks:
        im = read_frame(f"{CAV}/{v}/{v}.mpg", f); pair = []
        for m, name in ((m0, "YOLO11n goc (COCO)"), (m1, "Sau fine-tune (ft_v1)")):
            r = m.predict(im, classes=[0], conf=0.25, imgsz=640, device=0, verbose=False)[0]; x = im.copy()
            P = np.array(ZONE_A, np.int32); cv2.polylines(x, [P], True, (0, 0, 255), 1)
            for (a, b, c, d), cf in zip(r.boxes.xyxy.cpu().numpy().astype(int), r.boxes.conf.cpu().numpy()):
                cv2.rectangle(x, (a, b), (c, d), (0, 220, 0), 1); cv2.putText(x, f"{cf:.2f}", (a, b - 2), 0, 0.35, (0, 255, 255), 1)
            x = cv2.resize(x, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)
            cv2.rectangle(x, (0, 0), (x.shape[1], 24), (0, 0, 0), -1)
            cv2.putText(x, f"{name} - {len(r.boxes)} nguoi", (5, 17), 0, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
            pair.append(x)
        rows.append(np.hstack([pair[0], np.full((pair[0].shape[0], 8, 3), 255, np.uint8), pair[1]]))
    save("h4_3_so_sanh_phat_hien.png", np.vstack([np.vstack([r, np.full((8, r.shape[1], 3), 255, np.uint8)]) for r in rows])[:-8])


# ---------------- Hình 4.4: báo nhầm ở Z1 (làm mờ đầu)
def fig_z1():
    im = cv2.imread(f"{R}/code/baseline/results/ft_v1/z1_bao_nham.jpg"); h, w = im.shape[:2]; tw, th = w // 8, h // 2
    out = im.copy()
    for r in range(2):
        for c in range(8):
            out[r * th:(r + 1) * th, c * tw:(c + 1) * tw] = blur_heads(im[r * th:(r + 1) * th, c * tw:(c + 1) * tw])
    save("h4_4_bao_nham_Z1.png", np.vstack([out[:th, :tw * 3], out[:th, tw * 3:tw * 6]]))   # chỉ dùng 6 ô của Video1


# ---------------- Hình 4.5: đánh đổi theo ngưỡng tin cậy (phân tích, không dùng để chọn)
def fig_tradeoff():
    sys.argv = sys.argv[:1]
    sys.path.insert(0, f"{R}/code/baseline"); import tune_filters as T
    src = f"{R}/code/baseline/results/ft_v1"; tr = json.load(open(f"{src}/tracks.json")); res = []
    ths = [0.0, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.7]
    for t in ths:
        r = T.score("_tmp_tradeoff", src, *T.simulate(tr, {"min_conf": t} if t else {}), True); s = r["shop"]["total"]
        res.append((t, r["test"]["tp"], r["test"]["fp"], s["tp"], s["fp"]))
    import shutil; shutil.rmtree(f"{R}/code/baseline/results/_tmp_tradeoff", ignore_errors=True)
    json.dump(res, open(f"{OUT}/tradeoff.json", "w"))
    t = [x[0] for x in res]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    ax[0].plot(t, [x[1] for x in res], "o-", label="báo đúng (/14)"); ax[0].plot(t, [x[2] for x in res], "s-", label="báo nhầm")
    ax[0].set_title("(a) CAVIAR – 5 video kiểm thử"); ax[0].set_xlabel("ngưỡng tin cậy tối thiểu"); ax[0].legend(fontsize=9)
    ax[1].plot(t, [x[3] for x in res], "o-", label="báo đúng (/63)"); ax[1].plot(t, [x[4] for x in res], "s-", label="báo nhầm")
    ax[1].set_title("(b) Video cửa hàng giày"); ax[1].set_xlabel("ngưỡng tin cậy tối thiểu"); ax[1].legend(fontsize=9)
    for a in ax: a.axvline(0.5, color="gray", ls=":", lw=1)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "h4_5_danh_doi_nguong.png"), dpi=200); plt.close(fig); print("-> h4_5", res)


# ---------------- Hình 4.6: tốc độ và dung lượng
def fig_speed():
    B = json.load(open(f"{R}/code/optimize/results/bench_t4.json")); names = ["PyTorch\nFP32", "OpenVINO\nFP32", "OpenVINO\nINT8"]
    med = [b["core"]["median_ms"] for b in B]; p95 = [b["core"]["p95_ms"] for b in B]; size = [b["size_mb"] for b in B]
    col = ["#7a8fb0", "#1d4f9c", "#c62828"]
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
    bars = ax[0].bar(names, med, color=col); ax[0].errorbar(range(3), med, yerr=[[0] * 3, [p - m for p, m in zip(p95, med)]], fmt="none", ecolor="k", capsize=4)
    for bb, v in zip(bars, med): ax[0].text(bb.get_x() + bb.get_width() / 2, v + 3, f"{v:.1f} ms", ha="center", fontsize=10)
    ax[0].set_title("(a) Thời gian suy luận (trung vị, vạch: p95), CPU 4 luồng"); ax[0].set_ylabel("ms / khung")
    bars = ax[1].bar(names, size, color=col)
    for bb, v in zip(bars, size): ax[1].text(bb.get_x() + bb.get_width() / 2, v + 0.2, f"{v:.1f} MB", ha="center", fontsize=10)
    ax[1].set_title("(b) Dung lượng tệp mô hình"); ax[1].set_ylabel("MB")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "h4_6_toc_do.png"), dpi=200); plt.close(fig); print("-> h4_6")


if __name__ == "__main__":
    for fn in sys.argv[1:] or ["fig_foot", "fig_quant", "fig_arch", "fig_zoneA", "fig_zoneShop", "fig_state", "fig_train",
                               "fig_gui", "fig_evidence", "fig_compare", "fig_z1", "fig_tradeoff", "fig_speed"]:
        globals()[fn]()
