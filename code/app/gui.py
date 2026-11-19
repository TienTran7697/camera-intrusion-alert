"""Giao diện ứng dụng cảnh báo xâm nhập vùng cấm (PySide6).

Chạy:  python gui.py            (trong thư mục code/app)

Chức năng:
- Mở video (CAVIAR, cửa hàng giày hoặc video bất kỳ). Vùng cấm có sẵn được nạp tự động.
- Vẽ vùng cấm bằng chuột: bấm "Vẽ vùng mới" -> click trái để thêm đỉnh -> click phải (hoặc "Hoàn tất vùng") để đóng.
  "Lưu vùng" ghi tệp <video>.zones.json cạnh video, lần sau mở lại tự nạp.
- Chọn mô hình: OpenVINO INT8 / OpenVINO FP32 / PyTorch FP32. Thanh chỉnh ngưỡng tin cậy (bộ lọc min_conf).
- Hiển thị trực tiếp: vùng cấm, khung người, ID, điểm chân, trạng thái AN TOÀN / CẢNH BÁO, FPS; phát âm thanh khi cảnh báo.
- Giao diện theo tông xanh dương của UIT; logo trường hiện ở thanh tiêu đề nếu có tệp code/app/assets/uit_logo.png.
- Lưu bằng chứng vào SQLite (outputs/gui/<thời điểm>/events.db) ở luồng riêng; bảng vi phạm cập nhật trực tiếp,
  nhấp đúp một dòng để xem ảnh bằng chứng, nút "Mở clip" để xem clip.
"""
import os, sys, time, json, sqlite3
from datetime import datetime
import cv2
import numpy as np
from PySide6.QtCore import Qt, QThread, Signal, QPoint
from PySide6.QtGui import QImage, QPixmap, QPainter, QPen, QColor, QPolygon, QFont, QIcon
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog, QComboBox, QSlider,
                               QSpinBox, QCheckBox, QHBoxLayout, QVBoxLayout, QGridLayout, QGroupBox, QTableWidget,
                               QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QSplitter, QAbstractItemView)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from core.pipeline import Pipeline, load_zones, model_version_of, MAX_W
from core.evidence import EvidenceStore

ROOT = os.path.abspath(os.path.join(HERE, "../.."))
M = os.path.join(HERE, "../models")
MODELS = {"OpenVINO INT8 (đã lượng tử hóa)": f"{M}/ft_v1_int8_c300_openvino_model",
          "OpenVINO FP32": f"{M}/ft_v1_fp32_openvino_model",
          "PyTorch FP32": f"{M}/ft_v1.pt"}
ZCOL = [QColor(255, 0, 0), QColor(255, 0, 255), QColor(255, 200, 0), QColor(0, 200, 255)]
LOGO = os.path.join(HERE, "assets", "uit_logo.png")   # đặt logo chính thức của trường vào đây (PNG nền trong suốt)

# Bảng màu theo tông xanh dương của UIT
UIT_BLUE, UIT_DARK, UIT_LIGHT, BG = "#1d4f9c", "#0b2f66", "#e8f0fb", "#f4f7fc"
STYLE = f"""
QMainWindow, QWidget#root {{ background: {BG}; }}
QWidget {{ color: #1b2a41; }}
QGroupBox {{ background: white; border: 1px solid #c9d6ea; border-radius: 8px; margin-top: 14px; padding: 10px 8px 8px 8px; font-weight: 600; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 6px; color: white; background: {UIT_BLUE}; border-radius: 4px; }}
QPushButton {{ background: {UIT_BLUE}; color: white; border: none; border-radius: 5px; padding: 6px 10px; font-weight: 600; }}
QPushButton:hover {{ background: #2a64bd; }}
QPushButton:pressed {{ background: {UIT_DARK}; }}
QPushButton:disabled {{ background: #b8c4d6; color: #eef2f8; }}
QPushButton#start {{ background: #2e7d32; }} QPushButton#start:hover {{ background: #388e3c; }}
QPushButton#stop {{ background: #c62828; }} QPushButton#stop:hover {{ background: #d32f2f; }}
QComboBox, QSpinBox {{ background: white; border: 1px solid #c9d6ea; border-radius: 4px; padding: 3px 6px; }}
QSlider::groove:horizontal {{ height: 6px; background: #c9d6ea; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {UIT_BLUE}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: white; border: 2px solid {UIT_BLUE}; width: 14px; margin: -6px 0; border-radius: 8px; }}
QTableWidget {{ background: white; gridline-color: #e1e8f3; border: 1px solid #c9d6ea; border-radius: 6px; selection-background-color: {UIT_LIGHT}; selection-color: #1b2a41; }}
QHeaderView::section {{ background: {UIT_BLUE}; color: white; padding: 5px; border: none; font-weight: 600; }}
QStatusBar {{ background: {UIT_DARK}; color: white; }}
QLabel#stats {{ background: white; border: 1px solid #c9d6ea; border-radius: 6px; padding: 8px; }}
"""


def make_header():
    """Thanh tiêu đề: logo trường (nếu có tệp assets/uit_logo.png) + tên trường, môn học, đề tài, nhóm."""
    bar = QWidget(); bar.setObjectName("header")
    bar.setStyleSheet(f"QWidget#header {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {UIT_DARK}, stop:1 {UIT_BLUE}); }}"
                      "QLabel { color: white; background: transparent; }")
    lay = QHBoxLayout(bar); lay.setContentsMargins(14, 8, 14, 8); lay.setSpacing(14)
    logo = QLabel()
    if os.path.exists(LOGO):
        logo.setPixmap(QPixmap(LOGO).scaled(58, 58, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignCenter); logo.setFixedSize(68, 68)    # logo nền trắng -> đặt trên ô trắng bo góc
        logo.setStyleSheet("background: white; border-radius: 10px;")
    else:                                     # chưa có logo: ô chữ "UIT" giữ chỗ
        logo.setText("UIT"); logo.setAlignment(Qt.AlignCenter); logo.setFixedSize(64, 64)
        logo.setStyleSheet("background: white; color: #1d4f9c; border-radius: 32px; font: bold 20px 'Segoe UI';")
    lay.addWidget(logo)
    txt = QVBoxLayout(); txt.setSpacing(0)
    t1 = QLabel("TRƯỜNG ĐẠI HỌC CÔNG NGHỆ THÔNG TIN – ĐHQG-HCM"); t1.setFont(QFont("Segoe UI", 10, QFont.Bold))
    t2 = QLabel("HỆ THỐNG CẢNH BÁO XÂM NHẬP KHU VỰC CẤM QUA CAMERA"); t2.setFont(QFont("Segoe UI", 16, QFont.Bold))
    t3 = QLabel("Đồ án môn Trí tuệ nhân tạo cho hệ thống nhúng · YOLO11n + ByteTrack + OpenVINO INT8")
    t3.setFont(QFont("Segoe UI", 9)); t3.setStyleSheet("color: #cfe0ff;")
    for t in (t1, t2, t3): txt.addWidget(t)
    lay.addLayout(txt, 1)
    grp = QLabel("GVHD: ThS. Phan Đình Duy" + chr(10) + "Ngô Gia Bảo · Phan Minh Nhân · Trần Đình Tiễn")
    grp.setAlignment(Qt.AlignRight | Qt.AlignVCenter); grp.setFont(QFont("Segoe UI", 9)); grp.setStyleSheet("color: #e3ecff;")
    lay.addWidget(grp)
    return bar


def to_qimage(bgr):
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB); h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, 3 * w, QImage.Format_RGB888).copy()


def beep():
    try:
        import winsound; winsound.Beep(1200, 250)
    except Exception:
        QApplication.beep()


# ---------------------------------------------------------------- luồng xử lý video (chạy nền)
class Worker(QThread):
    frame_ready = Signal(QImage, dict)
    new_alert = Signal(dict)
    finished_info = Signal(dict)

    def __init__(self, video, model_path, zones, proc_size, min_conf, confirm, out_dir, clip_s, realtime):
        super().__init__()
        self.video, self.model_path, self.zones, self.proc_size = video, model_path, zones, proc_size
        self.min_conf, self.confirm, self.out_dir, self.clip_s, self.realtime = min_conf, confirm, out_dir, clip_s, realtime
        self._stop = False; self._pause = False

    def stop(self): self._stop = True
    def toggle_pause(self): self._pause = not self._pause; return self._pause

    def run(self):
        cap = cv2.VideoCapture(self.video); fps_v = cap.get(cv2.CAP_PROP_FPS) or 25.0
        nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); vid = os.path.splitext(os.path.basename(self.video))[0]
        store = EvidenceStore(os.path.join(self.out_dir, "events.db"), os.path.join(self.out_dir, "evidence"),
                              model_version_of(self.model_path), fps=fps_v, clip_seconds=self.clip_s)
        P = Pipeline(self.model_path, self.zones, self.proc_size, filters={"min_conf": self.min_conf} if self.min_conf else None,
                     confirm=self.confirm, evidence=store, video_id=vid)
        times = []; n_alert = 0; t_play = time.perf_counter()
        while not self._stop:
            if self._pause: time.sleep(0.05); continue
            ok, frame = cap.read()
            if not ok: break
            fr, dets, new, ms = P.step(frame); times.append(ms)
            fps = 1000.0 / max(1e-3, float(np.median(times[-30:])))
            im = P.draw(fr, dets, fps)
            for e in new:
                if e["type"] == "alert":
                    n_alert += 1
                    self.new_alert.emit({"zone": e["zone_id"], "track": e["track_id"], "t": e["frame"] / fps_v})
            self.frame_ready.emit(to_qimage(im), {"frame": P.f, "total": nframes, "fps": fps, "ms": ms,
                                                  "alerting": bool(P.alerting_ids()), "n_alert": n_alert,
                                                  "model": P.model_version})
            if self.realtime:                         # phát theo tốc độ gốc của video (nếu xử lý nhanh hơn)
                t_play += 1.0 / fps_v; d = t_play - time.perf_counter()
                if d > 0: time.sleep(d)
                else: t_play = time.perf_counter()
        store.close()
        self.finished_info.emit({"frames": P.f + 1, "alerts": n_alert,
                                 "ms_median": round(float(np.median(times)), 1) if times else None})


# ---------------------------------------------------------------- khung hiển thị video + vẽ vùng
class VideoView(QLabel):
    def __init__(self):
        super().__init__(); self.setAlignment(Qt.AlignCenter); self.setMinimumSize(640, 400)
        self.setStyleSheet("background:#111; color:#aaa;"); self.setText("Mở một video để bắt đầu")
        self.img = None; self.zones = []; self.draft = None; self.drawing = False; self.on_zone_done = None
        self.show_overlay = True                    # vẽ vùng lên ảnh tĩnh khi chưa chạy (lúc chạy, khung đã có vùng)

    def set_image(self, qimg):
        self.img = qimg; self._render()

    def resizeEvent(self, e): self._render(); super().resizeEvent(e)

    def _geom(self):
        if self.img is None: return 1, 0, 0
        s = min(self.width() / self.img.width(), self.height() / self.img.height())
        return s, (self.width() - self.img.width() * s) / 2, (self.height() - self.img.height() * s) / 2

    def _render(self):
        if self.img is None: return
        s, ox, oy = self._geom()
        pm = QPixmap.fromImage(self.img).scaled(int(self.img.width() * s), int(self.img.height() * s),
                                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
        if self.show_overlay or self.drawing or self.draft:
            p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
            for i, (zid, poly) in enumerate(self.zones):
                p.setPen(QPen(ZCOL[i % 4], 2)); p.drawPolygon(QPolygon([QPoint(int(x * s), int(y * s)) for x, y in poly]))
                p.drawText(int(np.mean([x for x, _ in poly]) * s), int(np.mean([y for _, y in poly]) * s), zid)
            if self.draft:
                p.setPen(QPen(QColor(0, 255, 0), 2, Qt.DashLine))
                pts = [QPoint(int(x * s), int(y * s)) for x, y in self.draft]
                p.drawPolyline(QPolygon(pts))
                for q in pts: p.drawEllipse(q, 3, 3)
            p.end()
        self.setPixmap(pm)

    def mousePressEvent(self, e):
        if not self.drawing or self.img is None: return
        s, ox, oy = self._geom()
        x, y = (e.position().x() - ox) / s, (e.position().y() - oy) / s
        if e.button() == Qt.LeftButton and 0 <= x <= self.img.width() and 0 <= y <= self.img.height():
            self.draft = (self.draft or []) + [[round(x, 1), round(y, 1)]]; self._render()
        elif e.button() == Qt.RightButton:
            self.finish_zone()

    def finish_zone(self):
        if self.draft and len(self.draft) >= 3:
            used = {z for z, _ in self.zones}; k = 1
            while f"Z{k}" in used: k += 1
            zid = f"Z{k}"
            self.zones.append((zid, self.draft))
        self.draft = None; self.drawing = False; self._render()
        if self.on_zone_done: self.on_zone_done()


# ---------------------------------------------------------------- cửa sổ chính
class Main(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Cảnh báo xâm nhập vùng cấm – YOLO11n + ByteTrack + OpenVINO INT8")
        self.resize(1440, 920); self.video = None; self.proc_size = None; self.worker = None; self.out_dir = None
        self.view = VideoView(); self.view.on_zone_done = self._zones_changed

        # --- bảng điều khiển
        self.btn_open = QPushButton("Mở video…"); self.btn_open.clicked.connect(self.open_video)
        self.lbl_video = QLabel("Chưa chọn video"); self.lbl_video.setWordWrap(True)
        self.cmb_model = QComboBox(); self.cmb_model.addItems(MODELS.keys())
        self.sld_conf = QSlider(Qt.Horizontal); self.sld_conf.setRange(0, 90); self.sld_conf.setValue(50)
        self.lbl_conf = QLabel(); self.sld_conf.valueChanged.connect(self._conf_label); self._conf_label()
        self.spn_confirm = QSpinBox(); self.spn_confirm.setRange(1, 50); self.spn_confirm.setValue(8)
        self.spn_confirm.setSuffix(" khung"); self.spn_confirm.setToolTip("Số khung liên tục trong vùng trước khi cảnh báo (25 khung = 1 giây)")
        self.chk_clip = QCheckBox("Lưu clip 3 s trước/sau"); self.chk_clip.setChecked(True)
        self.chk_rt = QCheckBox("Phát theo tốc độ video gốc"); self.chk_rt.setChecked(True)
        self.chk_sound = QCheckBox("Âm thanh cảnh báo"); self.chk_sound.setChecked(True)
        self.btn_draw = QPushButton("Vẽ vùng mới"); self.btn_draw.clicked.connect(self.start_draw)
        self.btn_done = QPushButton("Hoàn tất vùng"); self.btn_done.clicked.connect(self.view.finish_zone)
        self.btn_clear = QPushButton("Xóa hết vùng"); self.btn_clear.clicked.connect(self.clear_zones)
        self.btn_save = QPushButton("Lưu vùng"); self.btn_save.clicked.connect(self.save_zones)
        self.lbl_zones = QLabel("Vùng cấm: –")
        self.btn_start = QPushButton("▶  Bắt đầu"); self.btn_start.clicked.connect(self.start); self.btn_start.setObjectName("start")
        self.btn_pause = QPushButton("⏸  Tạm dừng"); self.btn_pause.clicked.connect(self.pause); self.btn_pause.setEnabled(False)
        self.btn_stop = QPushButton("⏹  Dừng"); self.btn_stop.clicked.connect(self.stop); self.btn_stop.setEnabled(False); self.btn_stop.setObjectName("stop")
        self.lbl_state = QLabel("—"); self.lbl_state.setAlignment(Qt.AlignCenter)
        self.lbl_state.setFont(QFont("Segoe UI", 18, QFont.Bold)); self.lbl_state.setMinimumHeight(56)
        self._set_state(None)
        self.lbl_stats = QLabel("FPS: –\nKhung: –\nSố cảnh báo: 0"); self.lbl_stats.setFont(QFont("Consolas", 10)); self.lbl_stats.setObjectName("stats")

        g1 = QGroupBox("1. Video"); l1 = QVBoxLayout(g1); l1.addWidget(self.btn_open); l1.addWidget(self.lbl_video)
        g2 = QGroupBox("2. Vùng cấm"); l2 = QGridLayout(g2)
        l2.addWidget(self.btn_draw, 0, 0); l2.addWidget(self.btn_done, 0, 1); l2.addWidget(self.btn_clear, 1, 0)
        l2.addWidget(self.btn_save, 1, 1); l2.addWidget(self.lbl_zones, 2, 0, 1, 2)
        l2.addWidget(QLabel("Click trái: thêm đỉnh · Click phải: đóng vùng"), 3, 0, 1, 2)
        g3 = QGroupBox("3. Mô hình và cảnh báo"); l3 = QGridLayout(g3)
        l3.addWidget(QLabel("Mô hình:"), 0, 0); l3.addWidget(self.cmb_model, 0, 1)
        l3.addWidget(self.lbl_conf, 1, 0); l3.addWidget(self.sld_conf, 1, 1)
        l3.addWidget(QLabel("Xác nhận:"), 2, 0); l3.addWidget(self.spn_confirm, 2, 1)
        l3.addWidget(self.chk_clip, 3, 0, 1, 2); l3.addWidget(self.chk_rt, 4, 0, 1, 2); l3.addWidget(self.chk_sound, 5, 0, 1, 2)
        g4 = QGroupBox("4. Chạy"); l4 = QHBoxLayout(g4)
        for b in (self.btn_start, self.btn_pause, self.btn_stop): l4.addWidget(b)
        side = QWidget(); ls = QVBoxLayout(side)
        for w in (g1, g2, g3, g4, self.lbl_state, self.lbl_stats): ls.addWidget(w)
        ls.addStretch(1); side.setFixedWidth(360)

        # --- bảng vi phạm
        self.tbl = QTableWidget(0, 8)
        self.tbl.setHorizontalHeaderLabels(["#", "Video", "Vùng", "ID", "Vào (s)", "Cảnh báo (s)", "Ra (s)", "Tin cậy"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl.setEditTriggers(QAbstractItemView.NoEditTriggers); self.tbl.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl.cellDoubleClicked.connect(self.show_evidence)
        self.btn_img = QPushButton("Xem ảnh bằng chứng"); self.btn_img.clicked.connect(lambda: self.show_evidence(self.tbl.currentRow(), 0))
        self.btn_clip = QPushButton("Mở clip"); self.btn_clip.clicked.connect(self.open_clip)
        self.btn_folder = QPushButton("Mở thư mục bằng chứng"); self.btn_folder.clicked.connect(self.open_folder)
        self.btn_csv = QPushButton("Xuất CSV"); self.btn_csv.clicked.connect(self.export_csv)
        bottom = QWidget(); lb = QVBoxLayout(bottom); lb.setContentsMargins(0, 0, 0, 0)
        hb = QHBoxLayout(); hb.addWidget(QLabel("<b>Danh sách vi phạm (SQLite)</b>")); hb.addStretch(1)
        for b in (self.btn_img, self.btn_clip, self.btn_folder, self.btn_csv): hb.addWidget(b)
        lb.addLayout(hb); lb.addWidget(self.tbl)

        split = QSplitter(Qt.Vertical); split.addWidget(self.view); split.addWidget(bottom); split.setSizes([620, 220])
        body = QWidget(); lr = QHBoxLayout(body); lr.addWidget(split, 1); lr.addWidget(side)
        root = QWidget(); root.setObjectName("root"); lv = QVBoxLayout(root); lv.setContentsMargins(0, 0, 0, 0); lv.setSpacing(0)
        lv.addWidget(make_header()); lv.addWidget(body, 1)
        self.setCentralWidget(root); self._enable_edit(False); self.setStyleSheet(STYLE)
        if os.path.exists(LOGO): self.setWindowIcon(QIcon(LOGO))
        self.statusBar().showMessage("Sẵn sàng · Mở một video để bắt đầu")

    # ---------- tiện ích giao diện
    def _conf_label(self): self.lbl_conf.setText(f"Ngưỡng tin cậy: {self.sld_conf.value() / 100:.2f}")

    def _set_state(self, alerting):
        if alerting is None: txt, bg = "CHƯA CHẠY", "#555"
        elif alerting: txt, bg = "⚠  CẢNH BÁO XÂM NHẬP", "#c62828"
        else: txt, bg = "AN TOÀN", "#2e7d32"
        self.lbl_state.setText(txt); self.lbl_state.setStyleSheet(f"background:{bg}; color:white; border-radius:6px;")

    def _enable_edit(self, on):
        for b in (self.btn_draw, self.btn_done, self.btn_clear, self.btn_save, self.btn_start): b.setEnabled(on)

    def _zones_changed(self):
        self.lbl_zones.setText("Vùng cấm: " + (", ".join(z for z, _ in self.view.zones) or "chưa có"))

    # ---------- video và vùng
    def open_video(self):
        start = os.path.join(ROOT, "Videos")
        path, _ = QFileDialog.getOpenFileName(self, "Chọn video", start, "Video (*.mp4 *.avi *.mpg *.mov *.mkv);;Tất cả (*.*)")
        if path: self.load_video(path)

    def load_video(self, path):
        cap = cv2.VideoCapture(path); ok, fr = cap.read()
        if not ok: QMessageBox.warning(self, "Lỗi", "Không đọc được video."); return
        self.video = path; zones, size = load_zones(path)
        h, w = fr.shape[:2]
        if size is None and w > MAX_W: size = (MAX_W, round(h * MAX_W / w))
        self.proc_size = size
        if size: fr = cv2.resize(fr, size, interpolation=cv2.INTER_AREA)
        self.view.zones = [(z, [list(map(float, p)) for p in poly]) for z, poly in zones]
        self.view.drawing = False; self.view.draft = None
        self.view.show_overlay = True; self.view.set_image(to_qimage(fr))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)); fps = cap.get(cv2.CAP_PROP_FPS) or 25
        self.lbl_video.setText(f"{os.path.basename(path)}\n{w}×{h}, {fps:.0f} FPS, {n / fps:.0f} s"
                               + (f"\nXử lý ở {size[0]}×{size[1]}" if size else ""))
        self._zones_changed(); self._enable_edit(True)

    def start_draw(self):
        self.view.drawing = True; self.view.draft = []; self.view._render()

    def clear_zones(self):
        self.view.zones = []; self._zones_changed(); self.view._render()

    def save_zones(self):
        if not self.video or not self.view.zones: return
        W, H = self.view.img.width(), self.view.img.height()
        cap = cv2.VideoCapture(self.video); ow, oh = int(cap.get(3)), int(cap.get(4)); s = ow / W
        data = {"frame_size": [ow, oh], "zones": [{"zone_id": z, "polygon": [[round(x * s, 1), round(y * s, 1)] for x, y in p]}
                                                  for z, p in self.view.zones]}
        out = os.path.splitext(self.video)[0] + ".zones.json"
        json.dump(data, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
        QMessageBox.information(self, "Đã lưu", f"Đã lưu vùng cấm vào:\n{out}")

    # ---------- chạy
    def start(self):
        if not self.video: return
        if not self.view.zones:
            QMessageBox.warning(self, "Thiếu vùng cấm", "Hãy vẽ ít nhất một vùng cấm trước khi chạy."); return
        self.out_dir = os.path.join(ROOT, "outputs", "gui", datetime.now().strftime("%Y%m%d_%H%M%S"))
        os.makedirs(self.out_dir, exist_ok=True); self.tbl.setRowCount(0)
        self.worker = Worker(self.video, MODELS[self.cmb_model.currentText()], [(z, p) for z, p in self.view.zones],
                             self.proc_size, self.sld_conf.value() / 100, self.spn_confirm.value(), self.out_dir,
                             3.0 if self.chk_clip.isChecked() else 0.0, self.chk_rt.isChecked())
        self.worker.frame_ready.connect(self.on_frame); self.worker.new_alert.connect(self.on_alert)
        self.worker.finished_info.connect(self.on_finished); self.worker.start()
        self._enable_edit(False); self.btn_open.setEnabled(False); self.cmb_model.setEnabled(False)
        self.btn_pause.setEnabled(True); self.btn_stop.setEnabled(True); self._set_state(False)
        self.view.show_overlay = False

    def pause(self):
        if self.worker: self.btn_pause.setText("▶  Tiếp tục" if self.worker.toggle_pause() else "⏸  Tạm dừng")

    def stop(self):
        if self.worker: self.worker.stop()

    def on_frame(self, qimg, st):
        self.view.set_image(qimg); self._set_state(st["alerting"])
        self.lbl_stats.setText(f"Mô hình: {st['model']}\nFPS xử lý: {st['fps']:.1f}  ({st['ms']:.1f} ms/khung)\n"
                               f"Khung: {st['frame'] + 1}/{st['total']}\nSố cảnh báo: {st['n_alert']}")

    def on_alert(self, a):
        if self.chk_sound.isChecked(): beep()
        self.refresh_table()

    def on_finished(self, info):
        self._enable_edit(True); self.btn_open.setEnabled(True); self.cmb_model.setEnabled(True)
        self.btn_pause.setEnabled(False); self.btn_stop.setEnabled(False); self.btn_pause.setText("⏸  Tạm dừng")
        self._set_state(None); self.refresh_table(); self.view.show_overlay = True
        self.statusBar().showMessage(f"Xong: {info['frames']} khung, {info['alerts']} cảnh báo, "
                                     f"trung vị {info['ms_median']} ms/khung. Bằng chứng: {self.out_dir}")

    # ---------- bảng vi phạm
    def _db(self):
        p = os.path.join(self.out_dir or "", "events.db")
        return sqlite3.connect(p) if self.out_dir and os.path.exists(p) else None

    def refresh_table(self):
        con = self._db()
        if con is None: return
        rows = con.execute("SELECT id, video_id, zone_id, track_id, t_enter, t_alert, t_exit, confidence FROM events ORDER BY id").fetchall()
        con.close(); self.tbl.setRowCount(len(rows))
        for i, r in enumerate(rows):
            for j, v in enumerate(r):
                it = QTableWidgetItem("" if v is None else (f"{v:.2f}" if isinstance(v, float) else str(v)))
                it.setTextAlignment(Qt.AlignCenter); self.tbl.setItem(i, j, it)
        self.tbl.scrollToBottom()

    def _row_paths(self, row):
        if row < 0 or self.tbl.item(row, 0) is None: return None
        con = self._db(); r = con.execute("SELECT snapshot_path, crop_path, clip_path FROM events WHERE id=?",
                                          (int(self.tbl.item(row, 0).text()),)).fetchone(); con.close()
        return [os.path.join(self.out_dir, p) if p else None for p in r]

    def show_evidence(self, row, _col):
        p = self._row_paths(row)
        if not p or not p[0] or not os.path.exists(p[0]):
            QMessageBox.information(self, "Chưa có", "Ảnh bằng chứng đang được ghi, thử lại sau giây lát."); return
        d = QDialog(self); d.setWindowTitle(os.path.basename(p[0])); lay = QHBoxLayout(d)
        for path in p[:2]:
            lab = QLabel(); pm = QPixmap(path); lab.setPixmap(pm.scaled(900 if path == p[0] else 300, 600, Qt.KeepAspectRatio,
                                                                          Qt.SmoothTransformation)); lay.addWidget(lab)
        d.exec()

    def open_clip(self):
        p = self._row_paths(self.tbl.currentRow())
        if p and p[2] and os.path.exists(p[2]): os.startfile(p[2])
        else: QMessageBox.information(self, "Chưa có clip", "Clip được ghi sau khi đủ 3 giây sau cảnh báo, hoặc đã tắt lưu clip.")

    def open_folder(self):
        if self.out_dir: os.startfile(self.out_dir)

    def export_csv(self):
        if not self.out_dir: return
        from core.evidence import export_csv
        out = os.path.join(self.out_dir, "events.csv"); n = export_csv(os.path.join(self.out_dir, "events.db"), out)
        QMessageBox.information(self, "Đã xuất", f"{n} dòng -> {out}")

    def closeEvent(self, e):
        if self.worker and self.worker.isRunning(): self.worker.stop(); self.worker.wait(5000)
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv); app.setFont(QFont("Segoe UI", 10))
    w = Main(); w.show()
    if len(sys.argv) > 1: w.load_video(sys.argv[1])
    sys.exit(app.exec())
