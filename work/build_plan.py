# Điền kế hoạch 6 tuần vào bản sao file Excel của thầy, giữ định dạng.
import copy, math
import openpyxl

SRC = "../../DoAn/2. Kế hoạch thực hiện đồ án, chuyên đề.xlsx"
OUT = "../Ke hoach thuc hien do an - 6 tuan.xlsx"

BAO, NHAN, TIEN = "Ngô Gia Bảo", "Phan Minh Nhân", "Trần Đình Tiễn"

WEEKS = [
    ("04/11 - 10/11", "11/11/2026",
     "Bước 1 – Tìm hiểu tổng quan, định nghĩa bài toán và chọn phần cứng",
     [(BAO, "Đọc 4 bài báo tham khảo, viết Chương 1 (Tổng quan về đề tài); chốt kiến trúc YOLO11n + ByteTrack + OpenVINO."),
      (NHAN, "Tải Human Dataset, kiểm tra ngẫu nhiên 100–200 ảnh cùng nhãn; tải video CAVIAR, MOT17 và chọn 10–20 video phù hợp."),
      (TIEN, "Cài môi trường (Python, Ultralytics, OpenVINO, NNCF); chạy thử YOLO11n có sẵn trên 3 video và đo FPS trên CPU; viết đặc tả quy tắc xâm nhập.")],
     "Chương 1, đặc tả bài toán, cấu hình máy, danh sách video, video chạy thử mô hình có sẵn."),
    ("11/11 - 17/11", "18/11/2026",
     "Bước 2 – Thu thập, tiền xử lý dữ liệu và xây dựng logic vùng cấm",
     [(BAO, "Làm sạch Human Dataset, loại ảnh trùng, chia train/val/test 70/15/15; đo kết quả mốc của mô hình có sẵn; viết mục 2.1 (tổng quan nghiên cứu)."),
      (NHAN, "Vẽ vùng cấm cho từng video, gán nhãn thời điểm người vào/ra vùng; tách video phát triển và video kiểm thử; viết lý thuyết YOLO và ByteTrack."),
      (TIEN, "Lập trình ByteTrack + kiểm tra điểm chân trong đa giác + logic cảnh báo (xác nhận 0,3 giây, mỗi lượt vào báo một lần).")],
     "Bộ dữ liệu đã chia, nhãn sự kiện của video, demo cảnh báo vùng cấm với mô hình có sẵn."),
    ("18/11 - 24/11", "25/11/2026",
     "Bước 3 – Huấn luyện mô hình và xây dựng giao diện",
     [(BAO, "Fine-tune YOLO11n trên GPU RTX 3050 Ti (ảnh 640, batch 2–4, 50–100 epoch); chọn checkpoint tốt nhất theo tập validation."),
      (NHAN, "Đánh giá checkpoint FP32 trên tập test (mAP50, mAP50–95, Precision, Recall); viết script đánh giá cảnh báo (đúng, bỏ sót, báo giả, độ trễ)."),
      (TIEN, "Xây dựng giao diện PySide6: mở video, vẽ và lưu vùng cấm, hiển thị khung người, ID và trạng thái; viết lý thuyết lượng tử hóa và Edge AI.")],
     "Mô hình FP32 đã huấn luyện kèm bảng kết quả mốc, giao diện bản đầu, Chương 2 hoàn chỉnh."),
    ("25/11 - 01/12", "02/12/2026",
     "Bước 4 – Tối ưu hóa và lượng tử hóa mô hình (trọng tâm)",
     [(BAO, "Chuyển mô hình sang OpenVINO FP32; lượng tử hóa INT8 (PTQ) bằng NNCF với tập hiệu chuẩn 100, 300, 500 ảnh."),
      (NHAN, "Đo PyTorch FP32, OpenVINO FP32, OpenVINO INT8 trên cùng CPU: dung lượng, thời gian suy luận (trung vị, p95), RAM, mAP; thử ảnh đầu vào 640 và 416."),
      (TIEN, "Tích hợp lựa chọn mô hình FP32/INT8 vào ứng dụng; thêm âm thanh cảnh báo, lưu ảnh sự kiện và nhật ký CSV; viết Chương 3 phần kiến trúc và phần mềm.")],
     "Các phiên bản mô hình FP32/INT8, bảng so sánh chất lượng – tốc độ – dung lượng."),
    ("02/12 - 08/12", "09/12/2026",
     "Bước 5, 6 – Triển khai ứng dụng và kiểm thử toàn hệ thống",
     [(BAO, "Chọn cấu hình INT8 tốt nhất trên tập validation; nếu chất lượng giảm nhiều thì thử lượng tử hóa có kiểm soát độ chính xác; viết Chương 3 phần huấn luyện và lượng tử hóa."),
      (NHAN, "Chạy FP32 và INT8 trên các video kiểm thử, đếm lượt phát hiện đúng, bỏ sót, báo giả, đo độ trễ cảnh báo; phân tích các trường hợp sai."),
      (TIEN, "Hoàn thiện và sửa lỗi ứng dụng; đo thời gian xử lý toàn hệ thống trên mỗi khung hình; chụp hình giao diện cho báo cáo.")],
     "Ứng dụng hoàn chỉnh, bảng kết quả cảnh báo FP32/INT8, Chương 3 hoàn chỉnh."),
    ("09/12 - 15/12", "16/12/2026",
     "Hoàn thiện báo cáo, demo và nộp đồ án",
     [(BAO, "Viết Chương 4 phần kết quả mô hình và lượng tử hóa; tổng hợp báo cáo, mục lục, tài liệu tham khảo."),
      (NHAN, "Viết Chương 4 phần đánh giá hệ thống cảnh báo và Chương 5 (Kết luận, hướng phát triển)."),
      (TIEN, "Quay video demo, làm slide thuyết trình, đóng gói mã nguồn và hướng dẫn chạy (README).")],
     "Báo cáo cuối kỳ, video demo, slide thuyết trình, mã nguồn."),
]

import json
wb = openpyxl.load_workbook(SRC)
ws = wb.active

def copy_style(src, dst):
    dst.font = copy.copy(src.font); dst.fill = copy.copy(src.fill)
    dst.border = copy.copy(src.border); dst.alignment = copy.copy(src.alignment)
    dst.number_format = src.number_format; dst.protection = copy.copy(src.protection)

spans = []   # [ô, vị trí bắt đầu (1-based), độ dài, kiểu]
for k, (rng, date, title, tasks, result) in enumerate(WEEKS):
    r = 9 + k
    if r != 9:
        for col in "BCDEF":
            copy_style(ws[f"{col}9"], ws[f"{col}{r}"])
    num = str(k + 1)
    ws[f"B{r}"].value = f"{num} ({rng})"
    spans.append([f"B{r}", 1, len(num), "num"])
    text = title + ":"
    spans.append([f"C{r}", 1, len(text), "b"])
    lines = [text]
    for name, task in tasks:
        text += "\n- "
        spans.append([f"C{r}", len(text) + 1, len(name) + 1, "b"])
        text += f"{name}: {task}"
        lines.append(f"- {name}: {task}")
    res = "→ Sản phẩm đánh giá: " + result
    text += "\n"
    spans.append([f"C{r}", len(text) + 1, len(res), "i"])
    text += res
    lines.append(res)
    ws[f"C{r}"].value = text
    ws[f"D{r}"].value = date
    ws[f"E{r}"].value = None
    ws[f"F{r}"].value = None
    nlines = sum(math.ceil(len(t) / 92) for t in lines)
    ws.row_dimensions[r].height = nlines * 18.5 + 8

for r in range(15, 20):
    for col in "BCDEF":
        ws[f"{col}{r}"].value = None
    ws.row_dimensions[r].hidden = True

note = "Ghi chú: \nThời gian thực hiện là 6 tuần (04/11/2026 – 15/12/2026); báo cáo tiến độ vào thứ Tư hằng tuần."
ws["A22"].value = note
spans.append(["A22", 1, len("Ghi chú:"), "b"])

wb.save(OUT)
json.dump(spans, open("plan_spans.json", "w", encoding="utf-8"), ensure_ascii=False)
print("saved", OUT, len(spans), "spans")
