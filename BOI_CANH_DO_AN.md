# Bối cảnh đồ án — AI cho hệ thống nhúng (UIT)

Tổng hợp từ cuộc trò chuyện trước với ChatGPT/Codex. Dùng làm điểm xuất phát cho mọi việc tiếp theo.

## Đề tài
- VI: **Xây dựng hệ thống tự động phát hiện và cảnh báo khi có người xâm nhập khu vực cấm qua camera**
- EN: **Development of an Automated Camera-Based System for Detecting and Alerting Human Intrusion into Restricted Areas**
- Yêu cầu của thầy: chú trọng **tối ưu hóa và lượng tử hóa**. Ứng dụng có thể chạy trên máy tính hoặc điện thoại; được demo bằng video có sẵn. Đầu ra phải hiển thị người, vùng nguy hiểm và trạng thái cảnh báo.
- Quy trình thiết kế 6 bước của thầy: (1) định nghĩa bài toán và chọn phần cứng → (2) thu thập và tiền xử lý dữ liệu → (3) thiết kế và huấn luyện mô hình → (4) tối ưu hóa mô hình → (5) chuyển đổi và triển khai → (6) kiểm thử thực tế.
- Câu hỏi nghiên cứu: lượng tử hóa INT8 giúp giảm thời gian xử lý và dung lượng của YOLO11n bao nhiêu, và làm thay đổi khả năng cảnh báo xâm nhập như thế nào?

## Kiến trúc đã chốt
Video → **YOLO11n** (lớp person) → **ByteTrack** (ID) → điểm chân p = ((x1+x2)/2, y2) → kiểm tra điểm trong đa giác vùng cấm → logic cảnh báo → hiển thị, âm thanh, nhật ký CSV.
- Logic cảnh báo: xác nhận người ở trong vùng khoảng 0,3 giây (chọn lại bằng tập validation). Mỗi lượt vào của một ID chỉ báo một lần. Chỉ tạo lượt mới khi người đã ra ngoài ổn định. Có dung sai khi mất dấu ngắn. Thời gian tính theo mốc thời gian của video, không theo đồng hồ hệ thống.
- Tối ưu hóa: PyTorch FP32 → OpenVINO FP32 → **OpenVINO INT8 (lượng tử hóa sau huấn luyện, PTQ, bằng NNCF)**, tạo từ cùng một checkpoint.
  - Bắt buộc so sánh: OpenVINO FP32 ↔ INT8, cùng CPU, cùng video, batch 1, có chạy khởi động trước khi đo.
  - Thí nghiệm thêm: tập hiệu chuẩn 100/300/500 ảnh; chọn ngẫu nhiên hoặc chọn đa dạng; ảnh đầu vào 640 hoặc 416.
  - Mở rộng nếu còn thời gian: lượng tử hóa có kiểm soát độ chính xác, QAT, YOLOv8n làm mô hình đối chiếu.
- Công nghệ: Python, Ultralytics, OpenCV, OpenVINO/NNCF, PySide6.

## Lưu bằng chứng vi phạm (đã chốt 11/11/2026, làm ở tuần 4, viết vào mục 3.4 của Chương 3)
- Dùng **SQLite** qua thư viện `sqlite3` có sẵn của Python (máy đang có Python 3.12.4, SQLite 3.45.3), không cần cài đặt hay máy chủ. Toàn bộ dữ liệu nằm trong một tệp `events.db`, lưu cục bộ. Muốn xem bằng giao diện thì dùng DB Browser for SQLite (không bắt buộc).
- Bảng `events`, mỗi lượt xâm nhập là một dòng: `id`, `video_id`, `zone_id`, `track_id`, `t_enter`, `t_alert`, `t_exit` (tính theo thời gian trong video), `confidence`, `bbox`, `model_version` (fp32/int8), `snapshot_path`, `crop_path`, `clip_path`, `created_at`.
- Tệp bằng chứng lưu trên ổ đĩa, trong DB chỉ ghi đường dẫn: ảnh toàn cảnh có vẽ vùng cấm, khung người, ID và thời điểm; ảnh cắt riêng người vi phạm; clip ngắn khoảng 3 giây trước và 3 giây sau lúc cảnh báo (tùy chọn, dùng bộ đệm vòng).
- Ghi DB và ảnh ở luồng riêng thông qua hàng đợi, để không làm giảm FPS và không ảnh hưởng phép đo FP32/INT8.
- Bảng `events` còn dùng để đánh giá: so với nhãn chuẩn của video để tính đúng, bỏ sót, báo giả, độ trễ; so sánh FP32 và INT8 theo cột `model_version`. Có thể xuất CSV từ DB.
- **Đã làm xong (19/11/2026):** `code/core/evidence.py`, `code/core/pipeline.py`, `code/app/run_pipeline.py`; chậm hơn ~4 % khi bật cả clip. Đã đổi việc của Tiễn trong kế hoạch Excel (tuần 4) thành lưu bằng chứng vào SQLite.

## Dữ liệu
- Huấn luyện, hiệu chuẩn và test phát hiện người: **Human Dataset (Kaggle, fareselmenshawii)**, nằm ở `Claude/Dataset`. Bộ gốc chỉ có train và val (17.754 ảnh). Đã loại 111 ảnh val trùng với train và tách phần val còn lại làm đôi: **train 13.754 / val 1.944 / test 1.945** (seed 42, cấu hình ở `Dataset/data.yaml`). Chi tiết: `work/ket_qua_kiem_tra_dataset.md`.
- Video kiểm thử và demo: **CAVIAR** (Walk1–3, Browse1–4, Meet_WalkTogether1, Meet_WalkSplit, Meet_Crowd) và **MOT17-02/04/09** (mỗi cảnh chỉ lấy một bản).
- **Đã tải 10 video CAVIAR** vào `Claude/Videos/CAVIAR`. Cả 10 video cùng một camera, nhìn từ trên xuống, 384×288, 25 FPS, tổng khoảng 5,9 phút. **Đã chốt vùng A** (khu quầy và sofa bên trái, giữ nguyên cạnh trên) dùng chung cho cả 10 video. Đã tạo nhãn sự kiện tự động từ khung bao gốc của CAVIAR: 33 lượt vào, 6 ca sát mép (`Videos/CAVIAR/events_gt.csv`, script `code/labeling/`). Đề xuất chia dev/test trong `Videos/CAVIAR/split.json`. Nhãn đang chờ nhóm duyệt bằng video trong `Videos/_review`. Chi tiết: `Videos/THONG_TIN_VIDEO.md`. MOT17 chưa tải.
- **Video cửa hàng giày (nhóm bổ sung 18/11/2026):** 2 video camera giám sát thật (`Videos/cua_hang_giay/Video1.mp4`, `Video2.mp4`), 2560×1440, 25 FPS, HEVC, tổng khoảng 10,4 phút, cùng một góc máy nhìn chéo xuống, rất đông người. **Chỉ dùng làm test và demo.** Đã chốt hai vùng **Z1 (bục trưng bày)** và **Z3 (lối đi giữa, giả lập lối thoát hiểm)** trong `zones.json`. Đã có nhãn sự kiện (18/11/2026) trong `events_gt.csv`: Z1 gán tay (Video1 0, Video2 2 lượt ngồi trên bục, chân dưới sàn); Z3 bán tự động bằng YOLO11x rồi xem lại (Video1 36, Video2 25 lượt); `verified=0`, nhóm cần kiểm tra lại. Có mặt khách hàng thật: làm mờ khi đưa vào báo cáo hoặc slide.
- Nhóm tự vẽ vùng và gán nhãn thời điểm vào/ra. Video dùng để chỉnh ngưỡng phải tách riêng với video dùng cho kiểm thử cuối.

## Chỉ số đánh giá
- Mô hình: mAP50, mAP50–95, precision, recall, dung lượng, thời gian suy luận (trung vị và p95), RAM.
- Hệ thống: số lượt xâm nhập phát hiện đúng, bỏ sót, số lần báo giả mỗi giờ, độ trễ cảnh báo, thời gian xử lý toàn bộ một khung hình.
- Mục tiêu đề xuất: INT8 nhanh hơn và nhẹ hơn; mAP50–95 và recall xâm nhập giảm không quá khoảng 2 điểm phần trăm.

## Phần cứng
i7-12700H (20 luồng), RTX 3050 Ti Laptop 4 GB VRAM, RAM 16 GB. Huấn luyện bằng GPU với batch 2–4 và AMP. Đo tốc độ trên CPU bằng OpenVINO. Lưu dữ liệu ở ổ D.

## Bài báo tham khảo (trong `../DoAn/Paper`)
1. Đặng Hoàng Phúc và cộng sự (2024), Tạp chí KHCN GTVT 13(1):22–35. YOLOv5/v8, vùng đa giác, cảnh báo khi tỷ lệ diện tích khung người nằm trong vùng ≥ ngưỡng. YOLOv8n đạt mAP@50 92,2%, 15,62 FPS trên i5-1135G7.
2. Hoàng Đức Quý và cộng sự (2025), Tạp chí KHCN GTVT 14(6):121–129. YOLOv11 + ByteTrack, đếm người qua đường ranh, dùng Human Dataset. Toàn hệ thống: precision 94,2%, recall 90,4%, 25–32 FPS trên CPU.
3. Phyo và cộng sự (2026), IET Smart Cities, DOI 10.1049/smc2.70024. Vùng cấm động xác định bằng cọc tiêu, homography xuống mặt đất, dự đoán quỹ đạo.
4. Musa và cộng sự (2026), Journal of Sensors, DOI 10.1155/js/5344126. Raspberry Pi 4B, PIR kích hoạt CNN, công suất giảm từ 6,5 W xuống 3,9 W.

## Tài liệu của thầy (trong `../DoAn`)
- `4. Báo cáo đồ án.docx`: mẫu báo cáo. Giữ nguyên font, cỡ chữ và cấu trúc.
- `3. Mẫu Báo cáo tuần x.docx`, `2. Kế hoạch thực hiện đồ án, chuyên đề.xlsx`.

## Kết quả mốc (18/11/2026) – chi tiết trong `code/baseline/KET_QUA_MOC.md`
- YOLO11n COCO chưa fine-tune, trên tập test ảnh: P 0,647, R 0,527, mAP50 0,549, mAP50–95 0,319.
- Trên 10 video CAVIAR, CPU: báo đúng 2/33 lượt, 20 lần báo nhầm, khoảng 39 ms/khung, 23,6 FPS. Đã kiểm tra bộ chấm điểm bằng khung bao gốc: 33/33. Mô hình gốc bỏ sót người nhìn từ trên xuống và nhận nhầm khu sofa là người, nên bắt buộc phải fine-tune; cân nhắc thêm ảnh trích từ các video CAVIAR thuộc tập dev.
- Code: `code/core/alarm.py` (logic cảnh báo), `code/baseline/` (đánh giá), `code/labeling/` (nhãn chuẩn), `code/models/yolo11n.pt`.

## Lượng tử hóa INT8 (19/11/2026) – chi tiết `code/optimize/KET_QUA_TOI_UU.md`
- OpenVINO 2026.4.1 + NNCF 3.4.0 (cài không đụng PyTorch). Mô hình: `code/models/ft_v1_fp32_openvino_model`, `ft_v1_int8_c300_openvino_model` (đã chọn).
- INT8 nhỏ hơn FP32 3,2 lần (3,3 vs 10,4 MB), nhanh hơn ~2,15 lần trên CPU (14,0 vs 30,0 ms, 4 luồng), mAP50–95 chỉ giảm 0,13 điểm %; cảnh báo trên 12 video chênh ±1–2 sự kiện.

## Giao diện PySide6 (19/11/2026)
- `code/app/gui.py` (chạy: `python gui.py` trong `code/app`, hoặc `python gui.py <đường dẫn video>`). PySide6-Essentials 6.12 (cài không đụng PyTorch).
- Mở video, tự nạp vùng có sẵn; vẽ vùng bằng chuột (click trái thêm đỉnh, click phải đóng), lưu `<video>.zones.json`; chọn INT8/FP32/PyTorch; thanh ngưỡng tin cậy (mặc định 0,5); số khung xác nhận; bật/tắt clip, âm thanh, phát theo tốc độ gốc.
- Luồng xử lý chạy nền (QThread) dùng `core/pipeline.py`; trạng thái AN TOÀN/CẢNH BÁO, FPS, số cảnh báo; bảng vi phạm đọc từ SQLite (`outputs/gui/<thời điểm>/events.db`), xem ảnh bằng chứng, mở clip, xuất CSV.
- Đã thử tự động (Video2, INT8): ~54 FPS xử lý (~17–20 ms/khung, gồm giải mã 2K). Ảnh chụp: `work/hinh/giao_dien_dang_chay.png` (có mặt khách, cần làm mờ khi đưa vào báo cáo).

## Báo cáo hoàn chỉnh (19/11/2026)
- `Bao cao do an - Hoan chinh.docx` (62 trang, Chương 1–5, phần đầu, 22 tài liệu IEEE, 14 hình, nhiều bảng). Dựng bằng `work/report/build_report.py` từ `Bao cao do an - Chuong 1.docx`; nội dung ở `work/report/report_content.py`; hình ở `work/report/fig` (tạo bằng `make_figs.py`, ảnh cửa hàng đã làm mờ đầu người). Word đã cập nhật mục lục, danh mục hình/bảng.
- Sửa nội dung: sửa `report_content.py` rồi chạy lại `python build_report.py`, cập nhật trường bằng Word, rồi chạy `python post_fix.py "<tệp>"` để bỏ trang trắng sau mục lục. Bản hiện tại 62 trang (đã thêm ngưỡng riêng INT8 và ảnh 416 vào mục 4.3.5), đã chép (docx + pdf) sang `DoAn/`.
- Báo cáo tuần 4–6 (viết 19/11/2026): nội dung ở `work/tuan/noi_dung_tuan_456.py`; tuần 4 đủ số liệu thật; tuần 5–6 có các ô tô vàng {{...}} cho việc chưa làm (ngưỡng INT8, ảnh 416, kiểm tra chéo nhãn, video demo, slide, README, nộp bài). Đã chép sang `DoAn/Bao cao Tuan/`.

## Slide bảo vệ (19/11/2026)
- `Slide bao ve do an.pptx` (21 slide, dựng từ `Mẫu thực hiện đồ án/5. Mẫu Slide báo cáo.pptx` bằng `work/slide/build_slides.py`, python-pptx ở scratchpad pylib2). 15 phút: Bảo slide 1–7, Nhân 8–12, Tiễn 13–17; sau đó Tài liệu tham khảo, Hỏi đáp, 2 phụ lục. Mỗi slide có ghi chú lời nói (speaker notes) ghi rõ người trình bày. Đã chép sang `DoAn/`.

## Git (19/11/2026)
- Thư mục `Claude/` là repo git (nhánh main, remote origin = https://github.com/TienTran7697/camera-intrusion-alert.git, public theo yêu cầu). `.gitignore` bỏ ảnh dataset, yolo11x.pt, 720p, outputs/, log, thư mục tạm. ~384 MB, 277 tệp. README.md có Phần A (chạy demo) và Phần B (làm lại từng bước). Video CAVIAR KHÔNG đưa lên git (tải bằng `code/download_data.py`), chỉ 2 video cửa hàng có trong repo. Người dùng tự `git push`.

## Tiến độ
- Đã có bản nháp Chương 1 do Codex tạo: `C:/Users/Admin/Documents/Codex/2026-10-21/h/outputs/Bao cao do an - Du thao Chuong 1.docx`
- Việc tiếp theo: Chương 2 trở đi; code (huấn luyện, xuất INT8, ứng dụng, đo đạc).
