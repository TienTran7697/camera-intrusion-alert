# -*- coding: utf-8 -*-
# Tuần 4–6: viết ngày 19/11/2026. Phần lớn việc của tuần 4 và một phần tuần 5, 6 nhóm đã làm sớm (số liệu thật);
# những việc CHƯA làm được để ở dạng {{...}} (tô vàng) để nhóm điền khi có kết quả.

TUAN4 = [
    ("sec", "Nội dung công việc trong tuần"),
    ("text", "**Tuần 4 (25/11/2026 – 01/12/2026):** Tối ưu hóa và lượng tử hóa mô hình, lưu bằng chứng vi phạm và xây dựng giao diện (Bước 4 và 5 trong quy trình thiết kế hệ thống AI nhúng). Phần lớn các việc dưới đây nhóm đã thực hiện sớm từ ngày 19/11/2026; số liệu cập nhật đến ngày 19/11/2026."),
    ("bul", "Chuyển mô hình đã fine-tune sang OpenVINO FP32 và lượng tử hóa INT8 (PTQ, NNCF) với tập hiệu chuẩn 100, 300, 500 ảnh."),
    ("bul", "Đo độ chính xác, tốc độ, dung lượng và RAM của PyTorch FP32, OpenVINO FP32 và OpenVINO INT8 trong cùng điều kiện."),
    ("bul", "Lưu bằng chứng vi phạm bằng SQLite; xây dựng giao diện PySide6."),

    ("sec", "Phân công thực hiện"),
    ("bul", "**Ngô Gia Bảo:** xuất OpenVINO FP32 và INT8, thí nghiệm tập hiệu chuẩn, đánh giá mAP trên tập test ảnh."),
    ("bul", "**Phan Minh Nhân:** viết chương trình đo tốc độ có kiểm soát; chạy đánh giá cảnh báo của FP32 và INT8 trên 12 video."),
    ("bul", "**Trần Đình Tiễn:** lưu bằng chứng vào SQLite (bảng events, ảnh, clip, luồng ghi riêng); giao diện PySide6 có thanh chỉnh ngưỡng tin cậy."),

    ("sec", "Báo cáo quá trình thực hiện"),
    ("bul", "**Môi trường:** cài OpenVINO 2026.4.1 và NNCF 3.4.0; trước khi cài, nhóm chạy thử ở chế độ không cài thật để chắc chắn không làm thay PyTorch như sự cố ở tuần 2."),
    ("bul", "**Lượng tử hóa:** cả FP32 và INT8 tạo từ cùng một checkpoint. Ảnh hiệu chuẩn được chọn ngẫu nhiên (seed 42) từ tập validation, không dùng tập test. Nhóm phát hiện tham số fraction của Ultralytics chỉ lấy N ảnh đầu tiên chứ không chọn ngẫu nhiên, nên tự tạo danh sách ảnh hiệu chuẩn. Dung lượng: OpenVINO FP32 10,4 MB, **INT8 3,3 MB (nhỏ hơn 3,2 lần)**."),
    ("bul", "**Độ chính xác trên tập test ảnh:** OpenVINO FP32 mAP@50–95 = 0,3445; INT8 với 100/300/500 ảnh hiệu chuẩn lần lượt 0,3425 / 0,3432 / 0,3429, tức **chỉ giảm 0,13–0,20 điểm phần trăm**. Số ảnh hiệu chuẩn gần như không ảnh hưởng; nhóm chọn bản 300 ảnh."),
    ("bul", "**Tốc độ trên CPU i7-12700H** (cùng 295 khung hình, batch 1, ảnh 640, chạy khởi động trước khi đo, mỗi mô hình một tiến trình riêng, giới hạn 4 luồng): PyTorch FP32 80,3 ms/khung, OpenVINO FP32 30,0 ms, **OpenVINO INT8 14,0 ms (khoảng 71 FPS), nhanh hơn FP32 khoảng 2,15 lần**. RAM dành cho mô hình: PyTorch khoảng 550 MB, OpenVINO khoảng 100–115 MB. Khi dùng tất cả các luồng, kết quả dao động giữa các lần đo vì CPU có hai loại nhân, nên nhóm dùng số liệu 4 luồng làm số liệu chính. Số 63 ms/khung ghi ở tuần 3 là PyTorch khi máy đang bận, không dùng để so sánh."),
    ("bul", "**Chất lượng cảnh báo của INT8 trên 12 video:** khi không lọc, INT8 tương đương FP32 (CAVIAR test 14/14 lượt đúng; video cửa hàng 56/63 so với 53/63 của FP32). Khi bật ngưỡng tin cậy 0,5, INT8 bỏ sót thêm 1 lượt sát mép ở Walk2; tổng cộng INT8 báo đúng 74/96 lượt so với 75/96 của FP32. Như vậy INT8 đạt mục tiêu đề ra (giảm không quá khoảng 2 điểm phần trăm)."),
    ("bul", "**Lưu bằng chứng (SQLite):** mỗi lượt vi phạm là một dòng trong bảng events (thời điểm vào, cảnh báo, ra theo thời gian video; độ tin cậy; khung bao; phiên bản mô hình; đường dẫn bằng chứng), kèm ảnh toàn cảnh, ảnh cắt người vi phạm và clip 6 giây. Việc ghi chạy ở luồng riêng qua hàng đợi: trên video cửa hàng, tốc độ toàn hệ thống chỉ giảm từ 40,7 xuống 39,1 FPS (khoảng 4%). Đã đổi việc “nhật ký CSV” trong kế hoạch Excel thành lưu bằng chứng vào SQLite."),
    ("bul", "**Giao diện PySide6:** mở video, vẽ và lưu vùng cấm bằng chuột, chọn mô hình INT8/FP32/PyTorch, thanh chỉnh ngưỡng tin cậy, trạng thái AN TOÀN/CẢNH BÁO kèm âm thanh, bảng vi phạm đọc từ SQLite (xem ảnh, mở clip, xuất CSV); giao diện theo màu và logo của trường. Với INT8, ứng dụng xử lý khoảng 48–54 FPS trên video cửa hàng 2K."),
    ("bul", "**Việc chưa hoàn thành, chuyển sang tuần 5:** kiểm tra chéo nhãn sự kiện; thử ảnh đầu vào 416; chỉnh ngưỡng tin cậy riêng cho INT8 trên tập dev."),
    ("bul", "**Khó khăn:** kết quả đo tốc độ khi dùng tất cả các luồng không ổn định; thư mục mô hình OpenVINO phải đặt tên kết thúc bằng _openvino_model thì Ultralytics mới nhận ra."),

    ("sec", "Dự kiến công việc tuần tiếp theo"),
    ("text", "**Tuần 5 (02/12/2026 – 08/12/2026):** Kiểm thử toàn hệ thống, hoàn thiện ứng dụng và các chương báo cáo."),
    ("bul", "**Ngô Gia Bảo:** chỉnh ngưỡng tin cậy riêng cho INT8 trên tập dev; thử ảnh đầu vào 416; hoàn thiện Chương 3 phần huấn luyện và lượng tử hóa."),
    ("bul", "**Phan Minh Nhân:** kiểm tra chéo 33 nhãn CAVIAR và 61 nhãn vùng Z3; phân tích các trường hợp sai; hoàn thiện Chương 4 phần đánh giá cảnh báo."),
    ("bul", "**Trần Đình Tiễn:** chạy thử và sửa lỗi ứng dụng; chụp hình giao diện (đã làm mờ khuôn mặt) cho báo cáo."),
]

TUAN5 = [
    ("sec", "Nội dung công việc trong tuần"),
    ("text", "**Tuần 5 (02/12/2026 – 08/12/2026):** Kiểm thử toàn hệ thống và hoàn thiện báo cáo (Bước 5 và 6 trong quy trình thiết kế hệ thống AI nhúng)."),
    ("bul", "Đánh giá FP32 và INT8 trên các video kiểm thử, phân tích các trường hợp sai."),
    ("bul", "Hoàn thiện ứng dụng, đo thời gian xử lý toàn hệ thống."),
    ("bul", "Hoàn thiện bản thảo báo cáo đồ án."),

    ("sec", "Phân công thực hiện"),
    ("bul", "**Ngô Gia Bảo:** chỉnh ngưỡng cho INT8, thử ảnh 416; viết Chương 3 phần huấn luyện và lượng tử hóa."),
    ("bul", "**Phan Minh Nhân:** kiểm tra chéo nhãn; phân tích trường hợp sai; viết Chương 4 phần đánh giá cảnh báo."),
    ("bul", "**Trần Đình Tiễn:** chạy thử, sửa lỗi ứng dụng; đo thời gian xử lý toàn hệ thống; chụp hình giao diện."),

    ("sec", "Báo cáo quá trình thực hiện"),
    ("bul", "**Bảng kết quả cảnh báo FP32/INT8 (đã có từ ngày 19/11/2026):** CAVIAR test 14/14 lượt đúng với cả FP32 và INT8 khi không lọc; khi bật ngưỡng 0,5, INT8 đạt 13/14, không báo nhầm. Trên video cửa hàng, ngưỡng 0,5 giảm báo nhầm từ 37–39 xuống 2–3 lần nhưng số lượt đúng giảm từ khoảng 54 xuống 43. Độ trễ cảnh báo trung vị khoảng 0,3 giây."),
    ("bul", "**Phân tích trường hợp sai:** (1) báo nhầm do vật thể giống người (quần áo treo phía sau bục Z1, khu sofa của CAVIAR) có khung bao chập chờn và đổi ID liên tục; (2) khách ngồi trên bục nhưng chân đặt dưới sàn nên điểm chân nằm ngoài vùng; (3) người đứng lâu trên mép vùng; (4) đoạn rất đông người, ByteTrack đổi ID nhiều. Nhóm vẽ đường cong số lượt đúng và báo nhầm theo ngưỡng tin cậy: trên video cửa hàng, ngưỡng 0,4 cho kết quả cân bằng (49/63 lượt đúng, 6 lần báo nhầm)."),
    ("bul", "**Thời gian xử lý toàn hệ thống:** với INT8 và 2 vùng cấm trên video cửa hàng 2K (gồm cả giải mã video và thu về 720p), hệ thống đạt 39,1 FPS khi lưu đầy đủ bằng chứng, nhanh hơn tốc độ 25 FPS của video."),
    ("bul", "**Bản thảo báo cáo:** đã hoàn thành bản thảo 62 trang gồm Chương 1–5, tóm tắt, mở đầu, danh mục từ viết tắt, 14 hình (ảnh cửa hàng đã làm mờ khuôn mặt) và 22 tài liệu tham khảo chuẩn IEEE; mục lục và danh mục hình, bảng có liên kết; xuất kèm bản PDF."),
    ("bul", "**Chỉnh ngưỡng riêng cho INT8 trên tập dev:** dò ngưỡng tin cậy 0,25–0,60 (bước 0,05), chỉ chọn theo 5 video phát triển của CAVIAR. FP32 chọn 0,50 (test 14/14, 0 báo nhầm; cửa hàng 43/63, 2 báo nhầm); INT8 chọn 0,55 (test 13/14, 0 báo nhầm; cửa hàng 39/63, 2 báo nhầm). Ngưỡng riêng không lấy lại được lượt sát mép bị sót ở Walk2 (lượt này chỉ được báo khi ngưỡng từ 0,45 trở xuống); nhóm không chọn 0,45 vì như vậy là dựa vào tập test. Ở cùng ngưỡng 0,40, INT8 trên video cửa hàng còn báo nhầm ít hơn FP32 (4 so với 7 lần)."),
    ("bul", "**Thử ảnh đầu vào 416:** xuất lại OpenVINO FP32 và INT8 ở kích thước 416 từ cùng checkpoint. INT8 ở 416 suy luận chỉ 8,0 ms/khung (khoảng 125 FPS, 4 luồng), nhanh hơn bản 640 khoảng 1,75 lần, nhưng mAP@50–95 giảm từ 0,343 xuống 0,309 (khoảng 3,5 điểm phần trăm), bỏ sót thêm người nhỏ (CAVIAR test còn 13/14) và trên video cửa hàng khi bật ngưỡng 0,5 chỉ còn 24/63 lượt đúng. Vì bản 640 đã đủ thời gian thực (INT8 14 ms/khung), nhóm **giữ kích thước 640**; 416 chỉ nên dùng khi thiết bị biên yếu hơn nhiều."),
    ("bul", "**Kiểm tra chéo nhãn:** {{số nhãn đã kiểm tra, số nhãn phải sửa, người kiểm tra}}"),
    ("bul", "**Sửa lỗi ứng dụng sau khi nhóm chạy thử:** {{các lỗi phát hiện và đã sửa}}"),
    ("bul", "**Việc chưa hoàn thành, chuyển sang tuần 6:** {{nếu có}}"),
    ("bul", "**Khó khăn:** {{khó khăn trong tuần}}"),

    ("sec", "Dự kiến công việc tuần tiếp theo"),
    ("text", "**Tuần 6 (09/12/2026 – 15/12/2026):** Hoàn thiện báo cáo, demo và nộp đồ án."),
    ("bul", "**Ngô Gia Bảo:** rà soát Chương 4 phần mô hình và lượng tử hóa; tổng hợp báo cáo, mục lục, tài liệu tham khảo."),
    ("bul", "**Phan Minh Nhân:** rà soát Chương 4 phần đánh giá cảnh báo và Chương 5; cập nhật kết quả kiểm tra chéo nhãn vào báo cáo."),
    ("bul", "**Trần Đình Tiễn:** quay video demo (làm mờ khuôn mặt khách hàng), làm slide thuyết trình, đóng gói mã nguồn và viết hướng dẫn chạy."),
]

TUAN6 = [
    ("sec", "Nội dung công việc trong tuần"),
    ("text", "**Tuần 6 (09/12/2026 – 15/12/2026):** Hoàn thiện báo cáo, demo và nộp đồ án."),
    ("bul", "Rà soát và hoàn thiện báo cáo cuối kỳ."),
    ("bul", "Quay video demo, làm slide thuyết trình."),
    ("bul", "Đóng gói mã nguồn, mô hình và hướng dẫn chạy."),

    ("sec", "Phân công thực hiện"),
    ("bul", "**Ngô Gia Bảo:** rà soát Chương 4 phần mô hình và lượng tử hóa; tổng hợp báo cáo, mục lục, tài liệu tham khảo."),
    ("bul", "**Phan Minh Nhân:** rà soát Chương 4 phần đánh giá cảnh báo và Chương 5."),
    ("bul", "**Trần Đình Tiễn:** video demo, slide thuyết trình, đóng gói mã nguồn và README."),

    ("sec", "Báo cáo quá trình thực hiện"),
    ("bul", "**Báo cáo cuối kỳ:** bản thảo 62 trang đã hoàn thành từ tuần 5, giữ đúng định dạng mẫu; mục lục, danh mục hình và bảng có liên kết tới từng mục; có bản PDF kèm thanh bookmark. Các chỉnh sửa trong tuần: {{các chỉnh sửa sau khi nhóm đọc duyệt và theo góp ý của thầy}}"),
    ("bul", "**Kết quả chính của đồ án:** YOLO11n sau fine-tune đạt mAP@50 = 0,604 trên tập test ảnh; báo đúng 14/14 lượt xâm nhập trên 5 video kiểm thử CAVIAR, độ trễ trung vị khoảng 0,3 giây; OpenVINO INT8 nhỏ hơn FP32 3,2 lần, nhanh hơn khoảng 2,15 lần trên CPU, mAP@50–95 chỉ giảm 0,13 điểm phần trăm."),
    ("bul", "**Video demo:** {{tên tệp, thời lượng, nội dung (CAVIAR và cửa hàng giày, so sánh INT8 với PyTorch), đã làm mờ khuôn mặt}}"),
    ("bul", "**Slide thuyết trình:** {{số slide, nội dung chính}}"),
    ("bul", "**Mã nguồn:** {{cấu trúc thư mục nộp, README, cách cài đặt và chạy}}"),
    ("bul", "**Nộp đồ án:** {{ngày nộp, các tệp đã nộp}}"),
    ("bul", "**Khó khăn:** {{khó khăn trong tuần}}"),

    ("sec", "Tự đánh giá và hướng phát triển"),
    ("bul", "**Đã đạt:** hệ thống chạy thời gian thực trên CPU, cảnh báo đúng trên video kiểm thử CAVIAR, lưu bằng chứng vào SQLite, giao diện hoàn chỉnh; lượng tử hóa INT8 đạt mục tiêu (nhanh hơn, nhẹ hơn, độ chính xác giảm không đáng kể)."),
    ("bul", "**Hạn chế:** mô hình chưa tổng quát tốt sang cảnh cửa hàng (nhận nhầm quần áo treo là người); điểm chân không xử lý được người ngồi trên vùng có độ cao; chưa triển khai trên thiết bị nhúng thật."),
    ("bul", "**Hướng phát triển:** bổ sung dữ liệu nhiều cảnh và ảnh âm tính khó; ngưỡng riêng cho từng vùng; thử QAT; triển khai trên thiết bị biên thật và nhận luồng camera trực tiếp."),
]
