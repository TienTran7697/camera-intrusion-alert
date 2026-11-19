# -*- coding: utf-8 -*-
"""Dựng slide bảo vệ đồ án từ mẫu của thầy (5. Mẫu Slide báo cáo.pptx), giữ nguyên layout, font, màu của mẫu.
15 phút, 3 người: Bảo (slide 1–7), Nhân (8–12), Tiễn (13–17); sau đó Tài liệu tham khảo, Hỏi đáp, Phụ lục.
Chạy: PYTHONPATH=<thư mục có python-pptx> python build_slides.py
"""
import copy, os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../.."))
FIG = os.path.join(ROOT, "work/report/fig")
TPL = os.path.join(HERE, "mau_slide.pptx")
OUT = os.path.join(ROOT, "Slide bao ve do an.pptx")

BLUE = RGBColor(0x01, 0x5D, 0xCF)     # màu tiêu đề của mẫu
BRIGHT = RGBColor(0x00, 0x72, 0xFF)   # màu trang trí của mẫu
CYAN = RGBColor(0x00, 0xC6, 0xFF)
LIGHT = RGBColor(0xE6, 0xF1, 0xFF)
TEXT = RGBColor(0x1B, 0x2A, 0x41)
GREY = RGBColor(0x5F, 0x6B, 0x7A)
RED = RGBColor(0xC6, 0x28, 0x28)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation(TPL)
TEMPLATE = list(prs.slides)            # 13 slide gốc của mẫu
T_TITLE, T_AGENDA, T_CONTENT, T_QA = TEMPLATE[0], TEMPLATE[1], TEMPLATE[2], TEMPLATE[11]
NEW = []


def dup(src):
    """Nhân bản một slide của mẫu (cùng layout, chép nguyên các hình của slide)."""
    s = prs.slides.add_slide(src.slide_layout)
    for ph in list(s.placeholders): ph._element.getparent().remove(ph._element)
    rmap = {}
    for rid, rel in src.part.rels.items():        # ảnh trong slide gốc (vd: slide Hỏi đáp)
        if "image" in rel.reltype: rmap[rid] = s.part.relate_to(rel._target, rel.reltype)
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
    for sh in src.shapes:
        el = copy.deepcopy(sh._element)
        for b in el.iter():
            if b.get(R) in rmap: b.set(R, rmap[b.get(R)])
        s.shapes._spTree.insert_element_before(el, "p:extLst")
    NEW.append(s); return s


def ph(s, idx_or_type):
    for p in s.placeholders:
        if p.placeholder_format.idx == idx_or_type: return p
    raise KeyError(idx_or_type)


def set_text(shape, text):
    """Đổi chữ của một khung, giữ định dạng của run đầu tiên."""
    tf = shape.text_frame; p0 = tf.paragraphs[0]
    r0 = p0.runs[0] if p0.runs else p0.add_run()
    r0.text = text
    for r in p0.runs[1:]: r._r.getparent().remove(r._r)
    for p in tf.paragraphs[1:]: p._p.getparent().remove(p._p)


def title(s, text): set_text(ph(s, 0), text)


def body(s, items, size=None):
    """items: [(cấp, chữ)]; chữ có thể là list các (đoạn, đậm). Giữ định dạng từng cấp của mẫu."""
    shp = ph(s, 1); tf = shp.text_frame
    tmpl = {}
    for p in tf.paragraphs: tmpl.setdefault(p.level, p._p)
    base0 = tmpl.get(0); base1 = tmpl.get(1, base0)
    for p in list(tf.paragraphs): p._p.getparent().remove(p._p)
    for lvl, txt in items:
        src = base1 if lvl else base0
        np_ = copy.deepcopy(src)
        for r in np_.findall("{http://schemas.openxmlformats.org/drawingml/2006/main}r"): np_.remove(r)
        tf._txBody.append(np_)
        para = tf.paragraphs[-1]
        for seg, b in (txt if isinstance(txt, list) else [(txt, False)]):
            r = para.add_run(); r.text = seg
            if b: r.font.bold = True
            if size: r.font.size = Pt(size)
    return shp


def remove_body(s):
    b = ph(s, 1); b._element.getparent().remove(b._element)


def box(s, x, y, w, h, fill=LIGHT, line=None, shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None: sh.line.fill.background()
    else: sh.line.color.rgb = line; sh.line.width = Pt(1.25)
    sh.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: sh.adjustments[0] = 0.12
    sh.text_frame.text = ""
    return sh


def text(s, x, y, w, h, runs, size=16, color=TEXT, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font="Arial"):
    """runs: chuỗi hoặc list đoạn; mỗi đoạn là chuỗi hoặc list (chữ, {tùy chọn})."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame
    tf.word_wrap = True; tf.vertical_anchor = anchor
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"): setattr(tf, m, Inches(0.04))
    paras = runs if isinstance(runs, list) else [runs]
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph(); p.alignment = align
        for seg in (para if isinstance(para, list) else [(para, {})]):
            t, o = seg if isinstance(seg, tuple) else (seg, {})
            r = p.add_run(); r.text = t; f = r.font
            f.name = font; f.size = Pt(o.get("size", size)); f.bold = o.get("bold", bold)
            f.color.rgb = o.get("color", color); f.italic = o.get("italic", False)
        p.space_after = Pt(o.get("after", 4) if paras else 4)
    return tb


def picture(s, fname, x, y, w=None, h=None):
    path = os.path.join(FIG, fname); W, H = Image.open(path).size
    if w and h:                                   # vừa khung, giữ tỷ lệ, căn giữa
        k = min(w / W, h / H); ww, hh = W * k, H * k; x, y = x + (w - ww) / 2, y + (h - hh) / 2; w, h = ww, hh
    elif w: h = w * H / W
    else: w = h * W / H
    return s.shapes.add_picture(path, Inches(x), Inches(y), Inches(w), Inches(h))


def table(s, x, y, w, rows, colw, size=13, rowh=0.36):
    t = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(rowh * len(rows))).table
    for j, cw in enumerate(colw): t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rowh)
        for j, val in enumerate(row):
            c = t.cell(i, j); c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid(); c.fill.fore_color.rgb = BLUE if i == 0 else (LIGHT if i % 2 == 0 else WHITE)
            tf = c.text_frame; tf.text = ""; p = tf.paragraphs[0]
            hl = isinstance(val, tuple); v = val[0] if hl else val
            r = p.add_run(); r.text = str(v); r.font.size = Pt(size); r.font.name = "Arial"
            r.font.bold = i == 0 or hl; r.font.color.rgb = WHITE if i == 0 else (RED if hl else TEXT)
            p.alignment = PP_ALIGN.CENTER if (i == 0 or j > 0) else PP_ALIGN.LEFT
    return t


def stat(s, x, y, w, big, small, color=BLUE, bigsize=36):
    box(s, x, y, w, 1.45, fill=LIGHT)
    text(s, x + 0.1, y + 0.08, w - 0.2, 0.75, [[(big, {"size": bigsize, "bold": True, "color": color})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    text(s, x + 0.1, y + 0.85, w - 0.2, 0.55, small, size=13, color=GREY, align=PP_ALIGN.CENTER)


def notes(s, who, t):
    s.notes_slide.notes_text_frame.text = f"[{who}] {t}"


def content(t, who, note):
    s = dup(T_CONTENT); title(s, t); notes(s, who, note); return s


# =========================================================== 1. TRANG BÌA
s = dup(T_TITLE)
set_text(ph(s, 1), "TRÍ TUỆ NHÂN TẠO CHO HỆ THỐNG NHÚNG")
set_text(ph(s, 2), "XÂY DỰNG HỆ THỐNG TỰ ĐỘNG PHÁT HIỆN VÀ CẢNH BÁO KHI CÓ NGƯỜI XÂM NHẬP KHU VỰC CẤM QUA CAMERA")
for r in ph(s, 2).text_frame.paragraphs[0].runs: r.font.size = Pt(24)
info = [sh for sh in s.shapes if sh.shape_type == 17][0]
tf = info.text_frame; ps = tf.paragraphs
gv, sv = ps[0]._p, ps[1]._p
for p in list(ps): p._p.getparent().remove(p._p)
tf._txBody.append(copy.deepcopy(gv)); tf.paragraphs[-1].runs[0].text = "GVHD: ThS. Phan Đình Duy"
for r in tf.paragraphs[-1].runs[1:]: r._r.getparent().remove(r._r)
for name, ms in (("Ngô Gia Bảo", "25210061"), ("Phan Minh Nhân", "25210153"), ("Trần Đình Tiễn", "25210216")):
    tf._txBody.append(copy.deepcopy(sv)); runs = tf.paragraphs[-1].runs
    runs[0].text = name
    for r in runs[1:]: r.text = ""
    if len(runs) > 1: runs[-1].text = "\t" + ms
notes(s, "Bảo", "Chào thầy. Nhóm gồm Bảo, Nhân, Tiễn trình bày đồ án xây dựng hệ thống phát hiện và cảnh báo người xâm nhập khu vực cấm qua camera, trọng tâm là tối ưu hóa và lượng tử hóa mô hình. Bảo trình bày tổng quan và cơ sở lý thuyết, Nhân trình bày thiết kế, Tiễn trình bày kết quả và kết luận.")

# =========================================================== 2. NỘI DUNG
s = dup(T_AGENDA)
notes(s, "Bảo", "Bài trình bày gồm năm phần theo đúng cấu trúc báo cáo.")

# =========================================================== 3. TỔNG QUAN – vấn đề
s = content("1. TỔNG QUAN ĐỀ TÀI", "Bảo",
            "Nhiều nơi có vùng cấm nhưng việc giám sát vẫn dựa vào người nhìn màn hình, dễ bỏ sót. Học sâu cho phép camera tự phát hiện người. Tuy nhiên muốn chạy trên thiết bị biên không có GPU thì mô hình phải được tối ưu – đây là trọng tâm môn học. Hình bên phải là một trong hai cảnh nhóm thử nghiệm: camera thật của một cửa hàng giày với hai vùng cấm.")
body(s, [(0, [("Vấn đề", True)]),
         (1, "Nhà xưởng, công trường, cửa hàng có những vùng người không phận sự không được vào"),
         (1, "Giám sát bằng người nhìn màn hình dễ bỏ sót những lần xâm nhập chỉ vài giây"),
         (0, [("Tính cấp thiết", True)]),
         (1, "Cảnh báo tự động bằng học sâu: phát hiện người → kiểm tra vùng cấm → cảnh báo"),
         (1, "Thiết bị biên thường không có GPU, tài nguyên hạn chế → cần tối ưu hóa mô hình"),
         (1, "Các nghiên cứu trong nước mới đánh giá mô hình gốc, chưa lượng tử hóa")], size=17)
ph(s, 1).width = Inches(6.7)
picture(s, "h3_3_vung_cua_hang.png", 7.75, 2.15, w=4.9, h=3.6)
text(s, 7.75, 5.8, 4.9, 0.4, "Vùng cấm Z1 (bục trưng bày), Z3 (lối đi) – camera cửa hàng", size=12, color=GREY, align=PP_ALIGN.CENTER)

# =========================================================== 4. MỤC TIÊU
s = content("1. MỤC TIÊU ĐỀ TÀI", "Bảo",
            "Câu hỏi nghiên cứu: lượng tử hóa INT8 giúp YOLO11n nhanh, nhẹ hơn bao nhiêu và có làm giảm khả năng cảnh báo không. Bốn mục tiêu cụ thể như trên slide. Tiêu chí tự đặt: INT8 giảm không quá khoảng 2 điểm phần trăm. Phạm vi: ứng dụng trên máy tính, demo bằng video có sẵn, đo trên CPU.")
remove_body(s)
box(s, 0.85, 1.9, 11.65, 1.0, fill=BLUE)
text(s, 1.05, 1.95, 11.25, 0.9, [[("Câu hỏi nghiên cứu: ", {"bold": True, "color": WHITE}),
                                  ("lượng tử hóa INT8 giúp YOLO11n nhanh và nhẹ hơn bao nhiêu, và có làm giảm khả năng cảnh báo xâm nhập không?", {"color": WHITE, "italic": True})]],
     size=18, anchor=MSO_ANCHOR.MIDDLE)
goals = [("1", "Huấn luyện", "Fine-tune YOLO11n cho lớp người (Human Dataset + CAVIAR)"),
         ("2", "Lượng tử hóa", "PyTorch FP32 → OpenVINO FP32 → INT8 (PTQ, NNCF), khảo sát 100/300/500 ảnh hiệu chuẩn"),
         ("3", "Ứng dụng", "Vẽ vùng cấm, cảnh báo hình ảnh + âm thanh, lưu bằng chứng vào SQLite"),
         ("4", "Đánh giá 2 cấp", "Mô hình: mAP, tốc độ, dung lượng · Hệ thống: báo đúng, bỏ sót, báo nhầm, độ trễ")]
for i, (n, h, d) in enumerate(goals):
    x = 0.85 + (i % 2) * 5.9; y = 3.15 + (i // 2) * 1.55
    box(s, x, y, 5.75, 1.4, fill=LIGHT)
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + 0.2), Inches(y + 0.35), Inches(0.7), Inches(0.7)); c.fill.solid(); c.fill.fore_color.rgb = BRIGHT; c.line.fill.background()
    c.text_frame.text = n; r = c.text_frame.paragraphs[0].runs[0]; r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = WHITE; c.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    text(s, x + 1.1, y + 0.12, 4.5, 1.2, [[(h, {"bold": True, "color": BLUE, "size": 17})], [(d, {"size": 14})]])
text(s, 0.85, 6.3, 11.65, 0.4, "Tiêu chí tự đặt: INT8 nhỏ hơn và nhanh hơn FP32; mAP@50–95 và recall theo sự kiện giảm không quá ~2 điểm %", size=13, color=GREY)

# =========================================================== 5. CSLT – nghiên cứu liên quan
s = content("2. NGHIÊN CỨU LIÊN QUAN", "Bảo",
            "Hai bài trong nước dùng YOLO kết hợp vùng đa giác và ByteTrack, kết quả tốt nhưng chỉ đánh giá mô hình gốc trên ảnh. Hai bài ngoài nước gợi ý dùng vị trí chân trên mặt sàn và quan tâm chi phí tính toán trên thiết bị biên. Đồ án kế thừa YOLO + ByteTrack, bổ sung lượng tử hóa INT8 và đánh giá ở cấp sự kiện cảnh báo.")
remove_body(s)
table(s, 0.85, 1.95, 11.65, [
    ["Nghiên cứu", "Phương pháp", "Xác định xâm nhập", "Tối ưu hóa"],
    ["[1] Đặng Hoàng Phúc 2024", "YOLOv5, YOLOv8", "Tỷ lệ diện tích khung bao trong đa giác", "Chọn YOLOv8n, chưa lượng tử hóa"],
    ["[2] Hoàng Đức Quý 2025", "YOLOv11 + ByteTrack", "Tâm khung bao qua đường ranh", "Chạy CPU, chưa lượng tử hóa"],
    ["[3] Phyo 2026", "YOLO11 + homography", "Quỹ đạo vị trí chân trên mặt sàn", "Giảm độ phân giải, số khung"],
    ["[4] Musa 2026", "CNN + cảm biến PIR", "Phân loại hành vi", "Chỉ chạy AI khi có chuyển động"],
    [("Đồ án", ), ("YOLO11n + ByteTrack",), ("Điểm chân trong đa giác + xác nhận 8 khung",), ("Lượng tử hóa INT8, đánh giá cảnh báo",)]],
    [2.6, 2.6, 3.45, 3.0], size=14, rowh=0.55)
text(s, 0.85, 5.5, 11.65, 0.9, [[("Khoảng trống: ", {"bold": True, "color": BLUE}),
                                 ("các hệ thống thường chỉ báo cáo mAP trên ảnh và tốc độ mô hình gốc – chưa đo ảnh hưởng của lượng tử hóa lên chính khả năng cảnh báo (báo đúng, báo nhầm, độ trễ).", {})]], size=15)

# =========================================================== 6. CSLT – phát hiện, theo dõi, vùng cấm
s = content("2. PHÁT HIỆN VÀ THEO DÕI NGƯỜI", "Bảo",
            "YOLO11n là bản nhỏ nhất của YOLO11, 2,6 triệu tham số. ByteTrack gán ID và ghép hai lần, giữ được người bị che khuất. Điểm đại diện là điểm giữa cạnh dưới khung bao – điểm chân – vì vùng cấm nằm trên mặt sàn. Kiểm tra điểm trong đa giác bằng phương pháp chiếu tia (cv2.pointPolygonTest).")
remove_body(s)
rows = [("YOLO11n", "Phát hiện một giai đoạn, không dùng hộp neo; 2,6 triệu tham số, 6,5 GFLOPs – nhỏ nhất họ YOLO11"),
        ("ByteTrack", "Bộ lọc Kalman + ghép IoU hai lần (khung tin cậy cao, rồi thấp) → gán ID ổn định qua các khung"),
        ("Điểm chân", "p = ((x1 + x2)/2, y2); kiểm tra p trong đa giác bằng chiếu tia; ở trong liên tục 8 khung → cảnh báo")]
for i, (h, d) in enumerate(rows):
    y = 2.0 + i * 1.45
    c = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.85), Inches(y + 0.2), Inches(0.75), Inches(0.75)); c.fill.solid(); c.fill.fore_color.rgb = BRIGHT; c.line.fill.background()
    c.text_frame.text = str(i + 1); r = c.text_frame.paragraphs[0].runs[0]; r.font.size = Pt(20); r.font.bold = True; r.font.color.rgb = WHITE; c.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    text(s, 1.8, y, 4.8, 1.35, [[(h, {"bold": True, "color": BLUE, "size": 18})], [(d, {"size": 14})]])
picture(s, "h2_1_diem_chan.png", 6.9, 1.95, w=5.6, h=3.9)
text(s, 6.9, 5.9, 5.6, 0.4, "Điểm chân p và vùng cấm A trên video CAVIAR", size=12, color=GREY, align=PP_ALIGN.CENTER)

# =========================================================== 7. CSLT – Edge AI, lượng tử hóa
s = content("2. EDGE AI VÀ LƯỢNG TỬ HÓA INT8", "Bảo",
            "Xử lý tại biên giúp độ trễ thấp, tiết kiệm băng thông, giữ riêng tư. Lượng tử hóa ánh xạ số thực sang số nguyên 8 bit theo hệ số tỷ lệ s và điểm không z. Nhóm chọn PTQ: chỉ cần vài trăm ảnh hiệu chuẩn, không huấn luyện lại; OpenVINO và NNCF hiện thực trên CPU Intel. Theo Krishnamoorthi, PTQ 8 bit thường giảm độ chính xác trong khoảng 2%. Hết phần của Bảo, mời Nhân trình bày phần thiết kế.")
remove_body(s)
text(s, 0.85, 1.95, 5.6, 1.6, [[("Vì sao xử lý tại biên? ", {"bold": True, "color": BLUE, "size": 18})],
                               [("Độ trễ thấp · tiết kiệm băng thông · riêng tư · chạy khi mất mạng – nhưng thiết bị không có GPU", {"size": 15})]])
box(s, 0.85, 3.55, 5.6, 1.1, fill=LIGHT)
text(s, 0.95, 3.6, 5.4, 1.0, [[("q = clamp( round(x / s) + z , −128 , 127 )", {"size": 18, "bold": True, "color": BLUE, "font": "Cambria"})],
                              [("x̂ = s · (q − z)   –   s: hệ số tỷ lệ, z: điểm không", {"size": 13, "color": GREY})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
text(s, 0.85, 4.85, 5.6, 1.5, [[("PTQ (chọn): ", {"bold": True, "color": BLUE}), ("vài trăm ảnh hiệu chuẩn, không huấn luyện lại, vài phút trên CPU", {})],
                               [("QAT: ", {"bold": True, "color": GREY}), ("huấn luyện lại có mô phỏng lượng tử hóa – hướng mở rộng", {})],
                               [("Công cụ: ", {"bold": True, "color": BLUE}), ("OpenVINO (IR .xml/.bin) + NNCF, preset MIXED", {})]], size=14)
picture(s, "h2_2_luong_tu_hoa.png", 6.75, 2.2, w=5.75, h=3.6)

# =========================================================== 8. 3.1 KIẾN TRÚC
s = content("3.1 THIẾT KẾ KIẾN TRÚC TỔNG THỂ", "Nhân",
            "Hệ thống gồm hai phần. Phần tối ưu hóa làm một lần: từ cùng một checkpoint tạo ba phiên bản PyTorch FP32, OpenVINO FP32, INT8. Phần xử lý trực tuyến: khung hình qua YOLO11n, ByteTrack gán ID, kiểm tra điểm chân với từng vùng cấm, logic cảnh báo quyết định thời điểm báo; kết quả hiển thị trên giao diện và ghi bằng chứng vào SQLite ở luồng riêng.")
remove_body(s)
picture(s, "h3_1_kien_truc.png", 0.85, 1.85, w=11.65, h=4.55)
text(s, 0.85, 6.45, 11.65, 0.4, "Yêu cầu chính: xử lý ≥ 25 FPS trên CPU · độ trễ cảnh báo < 1 s · INT8 giảm ≤ ~2 điểm % · dữ liệu lưu cục bộ", size=13, color=GREY, align=PP_ALIGN.CENTER)

# =========================================================== 9. 3.2 PHẦN CỨNG
s = content("3.2 THIẾT KẾ PHẦN CỨNG", "Nhân",
            "Theo trao đổi với thầy, hệ thống chạy trên máy tính và demo bằng video, nên không thiết kế mạch riêng. GPU chỉ dùng để huấn luyện. Mọi phép đo và so sánh FP32 – INT8 đều trên CPU. Nhóm giới hạn 4 luồng để mô phỏng thiết bị nhúng 4 nhân; chế độ này cũng cho kết quả ổn định hơn vì CPU có hai loại nhân.")
remove_body(s)
table(s, 0.85, 2.0, 7.0, [
    ["Thành phần", "Thông số", "Vai trò"],
    ["CPU", "Intel i7-12700H, 20 luồng, AVX2/VNNI", "Chạy hệ thống, đo tốc độ"],
    ["GPU", "RTX 3050 Ti Laptop, 4 GB", "Chỉ huấn luyện, gán nhãn"],
    ["RAM", "16 GB", ""],
    ["Camera / video", "CAVIAR 384×288; cửa hàng 2560×1440", "Đầu vào cố định"]],
    [1.6, 3.2, 2.2], size=14, rowh=0.62)
box(s, 8.2, 2.0, 4.3, 3.1, fill=LIGHT)
text(s, 8.4, 2.1, 3.9, 2.9, [[("Vì sao đo trên CPU 4 luồng?", {"bold": True, "color": BLUE, "size": 17})],
                             [("Thiết bị biên thường không có GPU rời", {})],
                             [("4 luồng ≈ máy tính nhúng 4 nhân", {})],
                             [("Kết quả ổn định giữa các lần đo (CPU có nhân P và nhân E)", {})]], size=14)
text(s, 0.85, 5.45, 11.65, 0.8, [[("Ghi chú: ", {"bold": True, "color": BLUE}), ("không thiết kế mạch phần cứng riêng – theo trao đổi với giảng viên, hệ thống được triển khai trên máy tính và demo bằng video có sẵn.", {})]], size=14, color=GREY)

# =========================================================== 10. 3.3 DỮ LIỆU
s = content("3.3 THIẾT KẾ PHẦN MỀM – DỮ LIỆU", "Nhân",
            "Human Dataset: loại 111 ảnh trùng, tách thêm tập test 1.945 ảnh. CAVIAR: 10 video cùng một camera nhìn từ trên xuống, nhãn sự kiện tạo từ khung bao gốc, chia 5 video phát triển và 5 video kiểm thử. Video cửa hàng giày: cảnh thực tế hoàn toàn khác, nhóm tự viết công cụ gán nhãn, chỉ dùng để kiểm thử. Dữ liệu chỉnh tham số luôn tách riêng với dữ liệu đánh giá.")
remove_body(s)
stat(s, 0.85, 1.95, 3.7, "17.643 ảnh", "Human Dataset: train 13.754 / val 1.944 / test 1.945 (đã loại 111 ảnh trùng)", bigsize=24)
stat(s, 4.83, 1.95, 3.7, "10 video · 33 lượt", "CAVIAR: 5 video phát triển (19 lượt), 5 video kiểm thử (14 lượt)", bigsize=24)
stat(s, 8.8, 1.95, 3.7, "2 video · 63 lượt", "Cửa hàng giày: Z1 (2), Z3 (61) – chỉ dùng kiểm thử", bigsize=24)
picture(s, "h3_2_vung_A.png", 0.85, 3.6, w=5.6, h=2.75)
picture(s, "h3_3_vung_cua_hang.png", 6.9, 3.6, w=5.6, h=2.75)
text(s, 0.85, 6.35, 11.65, 0.4, "Fine-tune bổ sung 1.412 khung hình CAVIAR (4 video phát triển) để mô hình học góc nhìn từ trên xuống", size=13, color=GREY, align=PP_ALIGN.CENTER)

# =========================================================== 11. 3.3 HUẤN LUYỆN VÀ LƯỢNG TỬ HÓA
s = content("3.3 HUẤN LUYỆN VÀ LƯỢNG TỬ HÓA", "Nhân",
            "Fine-tune 50 epoch trên GPU khoảng 2,5 giờ. Lưu ý quan trọng: phải giữ 80 tên lớp COCO, nếu khai báo một lớp thư viện khởi tạo lại phần phân loại và mất khả năng nhận người. Sau đó xuất OpenVINO FP32 và lượng tử hóa INT8 bằng NNCF với ảnh hiệu chuẩn chọn ngẫu nhiên từ tập validation, không dùng tập test.")
remove_body(s)
steps = [("Dữ liệu", "Human + 1.412 khung CAVIAR"), ("Fine-tune", "50 epoch, ảnh 640, AMP, ~2,5 giờ"),
         ("OpenVINO FP32", "IR .xml/.bin, 10,4 MB"), ("INT8 (NNCF)", "PTQ, 300 ảnh hiệu chuẩn ngẫu nhiên")]
for i, (h, d) in enumerate(steps):
    x = 0.85 + i * 2.98
    box(s, x, 1.95, 2.7, 1.25, fill=BLUE if i == 3 else LIGHT)
    text(s, x + 0.1, 2.0, 2.5, 1.15, [[(h, {"bold": True, "size": 16, "color": WHITE if i == 3 else BLUE})], [(d, {"size": 13, "color": WHITE if i == 3 else TEXT})]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 2.72), Inches(2.4), Inches(0.24), Inches(0.35)); a.fill.solid(); a.fill.fore_color.rgb = CYAN; a.line.fill.background()
picture(s, "h3_6_huan_luyen.png", 0.85, 3.4, w=7.4, h=2.95)
box(s, 8.5, 3.45, 4.0, 2.85, fill=LIGHT)
text(s, 8.65, 3.55, 3.7, 2.7, [[("Bài học khi huấn luyện", {"bold": True, "color": BLUE, "size": 16})],
                              [("Khai báo 1 lớp → mất trọng số phân loại, mAP ≈ 0 sau epoch đầu", {})],
                              [("Giữ 80 lớp COCO → nhận đủ 499/499 tham số", {})],
                              [("Checkpoint tốt nhất ~ epoch 40: mAP@50 0,607 (val)", {})]], size=13)

# =========================================================== 12. 3.3 LOGIC CẢNH BÁO + SQLITE
s = content("3.3 CẢNH BÁO VÀ LƯU BẰNG CHỨNG", "Nhân",
            "Mỗi ID có máy trạng thái riêng cho từng vùng: ở trong liên tục 8 khung thì cảnh báo một lần, ra ngoài liên tục 8 khung thì kết thúc lượt. Bốn bộ lọc giảm báo nhầm được dò trên video phát triển; chọn ngưỡng tin cậy 0,5. Mỗi lượt được lưu vào SQLite kèm ảnh và clip 6 giây, ghi ở luồng riêng nên chỉ chậm khoảng 4%. Hết phần của Nhân, mời Tiễn trình bày kết quả.")
remove_body(s)
picture(s, "h3_5_trang_thai.png", 0.85, 1.9, w=6.6, h=2.4)
text(s, 0.85, 4.4, 6.6, 1.95, [[("Bộ lọc giảm báo nhầm ", {"bold": True, "color": BLUE, "size": 16}), ("(chỉ dò trên CAVIAR phát triển)", {"size": 13, "color": GREY})],
                               [("Ngưỡng tin cậy tối thiểu · tuổi thọ ID · bỏ ID sinh ra trong vùng · độ dịch chuyển", {})],
                               [("54 tổ hợp → chọn ", {}), ("ngưỡng tin cậy 0,5", {"bold": True})]], size=14)
box(s, 7.75, 1.9, 4.75, 4.45, fill=LIGHT)
text(s, 7.9, 2.0, 4.45, 4.3, [[("SQLite – bảng events", {"bold": True, "color": BLUE, "size": 16})],
                              [("Mỗi lượt vi phạm = 1 dòng: video, vùng, ID, t_enter / t_alert / t_exit, độ tin cậy, khung bao, phiên bản mô hình", {})],
                              [("Bằng chứng: ảnh toàn cảnh, ảnh cắt người, clip 6 s (3 s trước + 3 s sau)", {})],
                              [("Ghi ở luồng riêng qua hàng đợi: 40,7 → 39,1 FPS (chỉ chậm ~4%)", {"bold": True})]], size=14)

# =========================================================== 13. KẾT QUẢ TRIỂN KHAI
s = content("4. KẾT QUẢ TRIỂN KHAI", "Tiễn",
            "Môi trường: Python, Ultralytics, OpenCV, OpenVINO, NNCF, PySide6, SQLite trên Windows. Giao diện: mở video, vẽ vùng bằng chuột, chọn mô hình, chỉnh ngưỡng, trạng thái an toàn hoặc cảnh báo kèm âm thanh, bảng vi phạm đọc từ SQLite. Với INT8 ứng dụng chạy khoảng 48–54 FPS trên video 2K. Khuôn mặt khách đã được làm mờ.")
remove_body(s)
picture(s, "h4_1_giao_dien.png", 0.85, 1.85, w=8.3, h=4.6)
text(s, 9.4, 1.95, 3.1, 4.4, [[("Môi trường", {"bold": True, "color": BLUE, "size": 16})],
                              [("Python 3.12 · Ultralytics 8.4 · OpenCV 5.1 · OpenVINO 2026.4 · NNCF 3.4 · PySide6 6.12 · SQLite", {"size": 13})],
                              [("Ứng dụng", {"bold": True, "color": BLUE, "size": 16})],
                              [("Vẽ nhiều vùng cấm, chọn INT8/FP32, thanh chỉnh ngưỡng, âm thanh cảnh báo, xem ảnh và clip bằng chứng", {"size": 13})],
                              [("~48–54 FPS", {"bold": True, "color": GREEN, "size": 22})],
                              [("INT8 trên video 2K (CPU)", {"size": 12, "color": GREY})]])

# =========================================================== 14. ĐÁNH GIÁ CAVIAR
s = content("4. ĐÁNH GIÁ TRÊN VIDEO CAVIAR", "Tiễn",
            "Trên ảnh, mAP@50 chỉ tăng 5,5 điểm. Nhưng trên video góc nhìn từ trên xuống, mô hình gốc chỉ báo đúng 2/33 lượt vì không thấy người nhỏ và nhận nhầm khu sofa. Sau fine-tune báo đúng 32/33, riêng 5 video kiểm thử 14/14, có bộ lọc thì không báo nhầm, độ trễ khoảng 0,3 giây. Bài học: mAP trên ảnh chưa phản ánh đúng khả năng cảnh báo.")
remove_body(s)
stat(s, 0.85, 1.95, 2.75, "0,549 → 0,604", "mAP@50 trên 1.945 ảnh test", bigsize=26)
stat(s, 3.8, 1.95, 2.75, "2 → 32 / 33", "Lượt báo đúng (10 video CAVIAR)", color=GREEN, bigsize=28)
stat(s, 0.85, 3.6, 2.75, "14 / 14", "5 video kiểm thử – 0 báo nhầm khi lọc ngưỡng 0,5", color=GREEN, bigsize=32)
stat(s, 3.8, 3.6, 2.75, "3,7 → 0,28 s", "Độ trễ cảnh báo (trung vị)", bigsize=28)
text(s, 0.85, 5.25, 5.7, 1.1, [[("Nguyên nhân mô hình gốc kém: ", {"bold": True, "color": RED}),
                               ("người nhìn từ trên xuống chỉ cao 20–45 px; khu sofa bị nhận nhầm là người, mỗi lần một ID mới", {})]], size=13)
picture(s, "h4_3_so_sanh_phat_hien.png", 6.9, 1.9, w=5.6, h=4.5)

# =========================================================== 15. VIDEO CỬA HÀNG + BỘ LỌC
s = content("4. VIDEO CỬA HÀNG VÀ BỘ LỌC", "Tiễn",
            "Trên cảnh cửa hàng chưa từng huấn luyện, vùng Z3 vẫn báo được khoảng 87–90% lượt. Báo nhầm chủ yếu ở Z1: quần áo treo sau bục bị nhận là người. Ngưỡng tin cậy 0,5 giảm báo nhầm từ 37 xuống 2 nhưng mất 12 lượt đúng – đây là đánh đổi, nên nhóm để ngưỡng là thanh trượt trên giao diện. Hạn chế: fine-tune bằng dữ liệu một cảnh chưa tổng quát sang cảnh khác.")
remove_body(s)
picture(s, "h4_5_danh_doi_nguong.png", 0.85, 1.9, w=7.3, h=2.6)
table(s, 0.85, 4.65, 7.3, [
    ["Cửa hàng giày (63 lượt)", "Báo đúng", "Báo nhầm", "Nhầm / giờ"],
    ["Sau fine-tune, không lọc", "54", "37", "217"],
    [("Ngưỡng tin cậy 0,5",), ("42",), ("2",), ("11,7",)]],
    [3.1, 1.4, 1.4, 1.4], size=14, rowh=0.5)
box(s, 8.45, 1.9, 4.05, 4.45, fill=LIGHT)
text(s, 8.6, 2.0, 3.75, 4.3, [[("Nhận xét", {"bold": True, "color": BLUE, "size": 17})],
                              [("Z3 (lối đi): báo được ~87–90% lượt, độ trễ ~0,3 s", {})],
                              [("Z1: quần áo treo sau bục bị nhận nhầm là người → báo lặp", {})],
                              [("Ngưỡng cao: ít báo nhầm nhưng bỏ sót người bị che, ở xa", {})],
                              [("→ Ngưỡng là thanh trượt trên giao diện", {"bold": True})]], size=14)

# =========================================================== 16. LƯỢNG TỬ HÓA INT8
s = content("4. ĐÁNH GIÁ LƯỢNG TỬ HÓA INT8", "Tiễn",
            "Đây là kết quả trả lời câu hỏi nghiên cứu. INT8 nhỏ hơn FP32 3,2 lần, nhanh hơn khoảng 2,15 lần trên CPU 4 luồng, đạt 71 FPS; mAP@50–95 chỉ giảm 0,13 điểm; số lượt cảnh báo đúng trên 12 video gần như không đổi. Số ảnh hiệu chuẩn 100 hay 500 gần như không ảnh hưởng. Thử ảnh 416 thì nhanh hơn nữa nhưng mất 3,5 điểm mAP, nên giữ 640.")
remove_body(s)
stat(s, 0.85, 1.95, 2.75, "3,2× nhỏ hơn", "10,4 MB → 3,3 MB", color=BLUE, bigsize=24)
stat(s, 3.8, 1.95, 2.75, "2,15× nhanh hơn", "30,0 → 14,0 ms/khung (71 FPS, CPU 4 luồng)", color=GREEN, bigsize=21)
stat(s, 0.85, 3.6, 2.75, "−0,13 điểm %", "mAP@50–95: 0,3445 → 0,3432", color=BLUE, bigsize=24)
stat(s, 3.8, 3.6, 2.75, "75 → 74 / 96", "Lượt báo đúng trên 12 video (lọc 0,5)", color=BLUE, bigsize=24)
text(s, 0.85, 5.25, 5.7, 1.1, [[("Kết luận: ", {"bold": True, "color": GREEN}),
                               ("đạt tiêu chí (giảm ≤ ~2 điểm %). Ảnh 416 nhanh hơn nữa (8 ms) nhưng mất ~3,5 điểm mAP → giữ 640.", {})]], size=13)
picture(s, "h4_6_toc_do.png", 6.9, 2.0, w=5.6, h=4.3)

# =========================================================== 17. KẾT LUẬN
s = content("5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", "Tiễn",
            "Nhóm đạt cả bốn mục tiêu, trả lời được câu hỏi nghiên cứu. Hạn chế lớn nhất là dữ liệu một cảnh và trường hợp người ngồi trên vùng có độ cao. Hướng phát triển như trên slide. Nhóm xin cảm ơn thầy đã lắng nghe.")
remove_body(s)
for k, (hd, col, items) in enumerate([
        ("Đã đạt được", GREEN, ["Hệ thống hoàn chỉnh: phát hiện, theo dõi, cảnh báo, lưu bằng chứng SQLite, giao diện",
                                "CAVIAR kiểm thử: 14/14 lượt, độ trễ ~0,3 s",
                                "INT8: nhỏ hơn 3,2×, nhanh hơn 2,15×, mAP chỉ giảm 0,13 điểm %",
                                "Thời gian thực trên CPU: 39–54 FPS toàn hệ thống"]),
        ("Hạn chế", RED, ["Dữ liệu bổ sung chỉ từ một cảnh → còn báo nhầm ở cảnh cửa hàng",
                          "Điểm chân không xử lý được người ngồi trên vùng có độ cao",
                          "Chưa triển khai trên thiết bị nhúng thật"]),
        ("Hướng phát triển", BLUE, ["Thêm dữ liệu nhiều cảnh, ảnh âm tính khó (quần áo treo, ma-nơ-canh)",
                                    "Ngưỡng riêng từng vùng; kết hợp tư thế hoặc homography",
                                    "Thử QAT; chạy trên thiết bị biên, camera RTSP"])]):
    x = 0.85 + k * 3.95
    box(s, x, 1.95, 3.75, 4.4, fill=LIGHT)
    text(s, x + 0.15, 2.05, 3.45, 4.2, [[(hd, {"bold": True, "color": col, "size": 18})]] + [[("• " + t, {})] for t in items], size=14)

# =========================================================== 18. TÀI LIỆU THAM KHẢO
s = content("Tài liệu tham khảo", "Tiễn", "Một số tài liệu chính; danh sách đầy đủ 22 tài liệu nằm trong báo cáo.")
body(s, [(0, "[1] Đặng Hoàng Phúc và cs., “Nghiên cứu và phát triển hệ thống cảnh báo xâm nhập…,” Tạp chí KHCN GTVT, 13(1), 2024."),
         (0, "[2] Hoàng Đức Quý và cs., “Nghiên cứu phát triển hệ thống giám sát an ninh theo thời gian thực…,” Tạp chí KHCN GTVT, 14(6), 2025."),
         (0, "[3] C. N. Phyo et al., “Deep learning-driven intrusion prediction system using ground-plane homography…,” IET Smart Cities, 2026."),
         (0, "[4] A. Musa et al., “An energy-efficient intelligent edge surveillance expert system…,” Journal of Sensors, 2026."),
         (0, "[5] G. Jocher and J. Qiu, Ultralytics YOLO11, 2024.   [6] Y. Zhang et al., “ByteTrack,” ECCV, 2022."),
         (0, "[7] B. Jacob et al., “Quantization and training of neural networks for efficient integer-arithmetic-only inference,” CVPR, 2018."),
         (0, "[8] R. Krishnamoorthi, “Quantizing deep convolutional networks for efficient inference: A whitepaper,” arXiv:1806.08342, 2018."),
         (0, "[9] Intel, OpenVINO Toolkit; A. Kozlov et al., “Neural Network Compression Framework,” arXiv:2002.08679, 2020."),
         (0, "[10] R. B. Fisher, “The PETS04 surveillance ground-truth data sets” (CAVIAR), PETS, 2004.")], size=13)

# =========================================================== 19. HỎI ĐÁP
s = dup(T_QA); notes(s, "Cả nhóm", "Mời thầy đặt câu hỏi. Các slide phụ lục phía sau dùng khi cần giải thích chi tiết.")

# =========================================================== 20. PHỤ LỤC 1
s = content("Phụ lục 1 – Tốc độ, ảnh 416, ngưỡng INT8", "Cả nhóm", "Dùng khi thầy hỏi chi tiết về phép đo tốc độ, kích thước ảnh hoặc chọn ngưỡng.")
remove_body(s)
table(s, 0.85, 1.95, 11.65, [
    ["Phiên bản", "Dung lượng", "mAP@50–95", "4 luồng: trung vị / p95 (ms)", "RAM mô hình", "CAVIAR test", "Cửa hàng (ngưỡng 0,5)"],
    ["PyTorch FP32, 640", "5,3 MB", "0,345", "80,3 / 88,9", "~550 MB", "14/14", "42 / 2"],
    ["OpenVINO FP32, 640", "10,4 MB", "0,3445", "30,0 / 35,2", "~115 MB", "14/14", "43 / 2"],
    [("OpenVINO INT8, 640",), ("3,3 MB",), ("0,3432",), ("14,0 / 16,0",), ("~100 MB",), ("13/14",), ("43 / 3",)],
    ["OpenVINO FP32, 416", "10,4 MB", "0,310", "18,5 / 28,3", "~100 MB", "13/14", "22 / 3"],
    ["OpenVINO INT8, 416", "3,3 MB", "0,309", "8,0 / 10,6", "~93 MB", "12/14", "24 / 3"]],
    [2.45, 1.25, 1.35, 2.3, 1.4, 1.3, 1.6], size=13, rowh=0.48)
text(s, 0.85, 5.0, 11.65, 1.4, [[("Phương pháp đo: ", {"bold": True, "color": BLUE}), ("cùng 295 khung, batch 1, khởi động 30 lần, mỗi mô hình một tiến trình, chỉ tính phần mô hình.", {})],
                                [("Ngưỡng riêng (chọn trên tập phát triển): ", {"bold": True, "color": BLUE}), ("FP32 = 0,50; INT8 = 0,55 (test 13/14, 0 nhầm). Lượt sát mép ở Walk2 chỉ được báo khi ngưỡng ≤ 0,45 – không chọn vì như vậy là dựa vào tập test.", {})]], size=14)

# =========================================================== 21. PHỤ LỤC 2
s = content("Phụ lục 2 – So sánh và các trường hợp khó", "Cả nhóm", "Dùng khi thầy hỏi so sánh với các nghiên cứu khác hoặc các trường hợp hệ thống làm sai.")
remove_body(s)
table(s, 0.85, 1.95, 11.65, [
    ["Nghiên cứu", "Chất lượng", "Tốc độ, tối ưu hóa"],
    ["[1] YOLOv8n", "mAP@50 92,2% (ảnh)", "15,6 FPS, CPU i5; chưa lượng tử hóa"],
    ["[2] YOLOv11 + ByteTrack", "P 94,2%, R 90,4% (toàn hệ thống)", "25–32 FPS, CPU; chưa lượng tử hóa"],
    [("Đồ án",), ("mAP@50 60,4% (ảnh); 14/14 lượt, độ trễ ~0,3 s",), ("INT8 14 ms/khung (71 FPS); hệ thống 39–54 FPS",)]],
    [3.2, 4.4, 4.05], size=14, rowh=0.5)
text(s, 0.85, 4.25, 11.65, 2.1, [[("Lưu ý: ", {"bold": True, "color": GREY}), ("dữ liệu và cách đánh giá khác nhau nên không so sánh trực tiếp con số.", {"color": GREY})],
                                 [("Trường hợp khó: ", {"bold": True, "color": BLUE}), ("khách ngồi trên bục nhưng chân đặt dưới sàn (điểm chân ngoài vùng); người đứng lâu trên mép vùng; cảnh rất đông làm ByteTrack đổi ID → cảnh báo lặp.", {})],
                                 [("Nhãn: ", {"bold": True, "color": BLUE}), ("CAVIAR từ khung bao gốc; Z3 cửa hàng gán bán tự động bằng YOLO11x rồi xem lại từng lượt.", {})]], size=14)

# =========================================================== sắp xếp: bỏ 13 slide mẫu, giữ các slide mới
sldIdLst = prs.slides._sldIdLst
ids = list(sldIdLst)
for el in ids[:len(TEMPLATE)]:
    rId = el.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    prs.part.drop_rel(rId); sldIdLst.remove(el)
prs.save(OUT)
print("saved", OUT, len(prs.slides), "slide")
