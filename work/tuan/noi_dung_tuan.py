# Nội dung báo cáo tuần — đã điền số liệu thật (cập nhật 18/11/2026).
# Nguồn số liệu: work/ket_qua_kiem_tra_dataset.md, Videos/THONG_TIN_VIDEO.md, code/baseline/KET_QUA_MOC.md

TUAN1 = [
    ("sec", "Nội dung công việc trong tuần"),
    ("text", "**Tuần 1 (04/11/2026 – 10/11/2026):** Tìm hiểu tổng quan về đề tài, định nghĩa bài toán và chọn phần cứng (Bước 1 trong quy trình thiết kế hệ thống AI nhúng)."),
    ("bul", "Tìm hiểu các nghiên cứu liên quan trong và ngoài nước về phát hiện, cảnh báo xâm nhập vùng cấm bằng camera."),
    ("bul", "Chốt phạm vi, kiến trúc hệ thống và định nghĩa thế nào là một lượt xâm nhập."),
    ("bul", "Chuẩn bị dữ liệu ảnh, video và môi trường lập trình; chạy thử mô hình có sẵn."),
    ("bul", "Viết Chương 1 của báo cáo và lập kế hoạch thực hiện 6 tuần."),

    ("sec", "Phân công thực hiện"),
    ("bul", "**Ngô Gia Bảo:** đọc 4 bài báo tham khảo, viết Chương 1 (Tổng quan về đề tài), chốt kiến trúc YOLO11n + ByteTrack + OpenVINO."),
    ("bul", "**Phan Minh Nhân:** tải Human Dataset và kiểm tra bộ dữ liệu cùng nhãn; tải video CAVIAR, MOT17 và chọn 10–20 video phù hợp."),
    ("bul", "**Trần Đình Tiễn:** cài môi trường (Python, Ultralytics, OpenVINO, NNCF), chạy thử YOLO11n có sẵn trên video và đo tốc độ trên CPU, viết đặc tả quy tắc xâm nhập."),

    ("sec", "Báo cáo quá trình thực hiện"),
    ("bul", "**Hướng đi của đề tài:** nhóm xây dựng ứng dụng trên máy tính, đầu vào là video từ camera cố định (được phép demo bằng video có sẵn). Trọng tâm của đồ án là tối ưu hóa mô hình bằng lượng tử hóa từ FP32 sang INT8 và đánh giá ảnh hưởng của việc này lên tốc độ, dung lượng và chất lượng cảnh báo."),
    ("bul", "**Tài liệu tham khảo:** nhóm đã đọc 4 bài báo. Hai bài trong nước (Tạp chí KHCN Giao thông vận tải, 2024 và 2025) dùng YOLOv8 và YOLOv11 + ByteTrack để cảnh báo xâm nhập và đếm người qua vùng giám sát. Hai bài ngoài nước (IET Smart Cities và Journal of Sensors, 2026) gợi ý dùng vị trí chân trên mặt sàn để xác định người vào vùng hạn chế, và cách giảm chi phí tính toán khi chạy AI trên thiết bị nhúng."),
    ("bul", "**Kiến trúc đã chốt:** Video → YOLO11n phát hiện người → ByteTrack gán ID và theo dõi → kiểm tra điểm chân có nằm trong đa giác vùng cấm → logic cảnh báo (hình ảnh, âm thanh, nhật ký). Mô hình sau huấn luyện được chuyển sang OpenVINO FP32 và lượng tử hóa INT8 (PTQ, thư viện NNCF) để so sánh."),
    ("bul", "**Định nghĩa xâm nhập:** điểm đại diện của người là trung điểm cạnh dưới khung bao p = ((x1 + x2)/2, y2). Một lượt xâm nhập được ghi nhận khi điểm này đi từ ngoài vào trong vùng cấm và ở trong khoảng 0,3 giây; mỗi lượt vào của một ID chỉ báo một lần."),
    ("bul", "**Phần cứng:** laptop Intel Core i7-12700H, RAM 16 GB, GPU RTX 3050 Ti 4 GB. GPU chỉ dùng để huấn luyện; việc so sánh FP32 và INT8 thực hiện trên CPU để gần với điều kiện thiết bị biên."),
    ("bul", "**Dữ liệu ảnh:** đã tải Human Dataset (Kaggle) và kiểm tra toàn bộ bằng script. Bộ dữ liệu có 17.754 ảnh (train 13.754, val 4.000) với 73.046 khung người, chỉ một lớp person. Mọi ảnh đều có tệp nhãn tương ứng, không có dòng nhãn sai định dạng hay tọa độ vượt khoảng [0, 1]. Khoảng 25% khung người có chiều cao nhỏ hơn 10% ảnh."),
    ("bul", "**Vấn đề phát hiện trong dữ liệu:** (1) 111 ảnh trong val trùng hoàn toàn với ảnh trong train; (2) bộ dữ liệu không có tập test riêng; (3) nhãn theo kiểu Open Images: có khung bao trùm cả nhóm người, có nhãn cho tranh vẽ, búp bê, tượng, và khoảng 15% khung chạm cạnh dưới ảnh (có thể bị cắt mất chân). Điểm (3) ảnh hưởng đến cách lấy vị trí chân, nên nhóm quyết định đánh giá cảnh báo bằng video thay vì chỉ dựa vào mAP."),
    ("bul", "**Báo cáo:** đã hoàn thành bản nháp Chương 1 (đặt vấn đề, mục tiêu, đối tượng và phạm vi, cấu trúc báo cáo) và bảng kế hoạch thực hiện 6 tuần."),
    ("bul", "**Việc chưa hoàn thành, chuyển sang tuần 2:** tải và chọn video kiểm thử; cài thư viện Ultralytics, OpenVINO, NNCF và chạy thử mô hình có sẵn để đo tốc độ."),
    ("bul", "**Khó khăn:** GPU chỉ có 4 GB VRAM nên khi huấn luyện phải dùng batch nhỏ; nhãn của Human Dataset có nhiều khung không bao toàn thân như đã nêu ở trên."),

    ("sec", "Dự kiến công việc tuần tiếp theo"),
    ("text", "**Tuần 2 (11/11/2026 – 17/11/2026):** Thu thập, tiền xử lý dữ liệu và xây dựng logic vùng cấm."),
    ("bul", "**Ngô Gia Bảo:** loại ảnh trùng, tách thêm tập test cho Human Dataset; đo kết quả mốc của mô hình có sẵn; viết mục tổng quan nghiên cứu (Chương 2)."),
    ("bul", "**Phan Minh Nhân:** tải video kiểm thử, vẽ vùng cấm, gán nhãn thời điểm người vào/ra vùng; tách video phát triển và video kiểm thử; viết lý thuyết YOLO và ByteTrack."),
    ("bul", "**Trần Đình Tiễn:** cài môi trường; lập trình ByteTrack, kiểm tra điểm chân trong đa giác và logic cảnh báo (xác nhận 0,3 giây, mỗi lượt vào báo một lần)."),
]

TUAN2 = [
    ("sec", "Nội dung công việc trong tuần"),
    ("text", "**Tuần 2 (11/11/2026 – 17/11/2026, số liệu cập nhật đến ngày báo cáo 18/11/2026):** Thu thập, tiền xử lý dữ liệu và xây dựng logic vùng cấm (Bước 2 trong quy trình thiết kế hệ thống AI nhúng)."),
    ("bul", "Làm sạch và chia lại bộ dữ liệu ảnh dùng để huấn luyện mô hình phát hiện người."),
    ("bul", "Xây dựng bộ video kiểm thử có vùng cấm và nhãn sự kiện xâm nhập."),
    ("bul", "Lập trình logic cảnh báo vùng cấm, chạy kết quả mốc với mô hình có sẵn trên cả ảnh và video."),

    ("sec", "Phân công thực hiện"),
    ("bul", "**Ngô Gia Bảo:** loại ảnh trùng, tách tập test cho Human Dataset; đo kết quả mốc của YOLO11n có sẵn trên tập ảnh; viết mục tổng quan nghiên cứu liên quan."),
    ("bul", "**Phan Minh Nhân:** tải video CAVIAR, vẽ vùng cấm, tạo nhãn thời điểm người vào/ra vùng; tách video phát triển và video kiểm thử; viết lý thuyết YOLO và ByteTrack."),
    ("bul", "**Trần Đình Tiễn:** cài môi trường; lập trình ByteTrack, kiểm tra điểm chân trong đa giác, logic cảnh báo và script đánh giá trên video."),

    ("sec", "Báo cáo quá trình thực hiện"),
    ("bul", "**Làm sạch và chia dữ liệu ảnh:** loại 111 ảnh val trùng với train (chuyển sang thư mục riêng, không xóa), còn 17.643 ảnh. Vì bộ gốc không có tập test, nhóm chia ngẫu nhiên phần val còn lại làm đôi (seed 42): **train 13.754 ảnh, validation 1.944 ảnh, test 1.945 ảnh**, tỷ lệ khoảng 78/11/11. Nhóm giữ nguyên tập train thay vì chia lại theo 70/15/15 như dự kiến. Sau khi chia đã kiểm tra lại: mọi ảnh đều có nhãn, không còn ảnh trùng giữa các tập. Cấu hình lưu trong data.yaml, mọi thao tác di chuyển tệp được ghi vào nhật ký để có thể tái lập."),
    ("bul", "**Kết quả mốc trên ảnh:** YOLO11n đã huấn luyện sẵn trên COCO (chưa fine-tune), đánh giá trên tập test 1.945 ảnh (7.964 người) cho lớp người: **mAP@50 = 0,549, mAP@50–95 = 0,319, Precision = 0,647, Recall = 0,527**; thời gian suy luận 3,8 ms/ảnh trên GPU. Đây là mốc để so sánh sau khi fine-tune ở tuần 3."),
    ("bul", "**Bộ video kiểm thử:** đã tải 10 video từ bộ dữ liệu CAVIAR (Đại học Edinburgh): 384 × 288, 25 FPS, tổng 8.844 khung hình (khoảng 5,9 phút), kèm nhãn khung bao và ID người do tác giả bộ dữ liệu gán. Cả 10 video quay từ cùng một camera đặt cao, nhìn gần như thẳng từ trên xuống."),
    ("bul", "**Vùng cấm và nhãn sự kiện:** nhóm chọn vùng A (khu quầy và sofa bên trái sảnh) dùng chung cho cả 10 video. Từ khung bao gốc của CAVIAR, nhóm tạo nhãn sự kiện theo đúng quy tắc cảnh báo, được **33 lượt vào vùng** và **6 trường hợp đi sát mép nhưng không vào**. Video được chia thành 5 video phát triển (19 lượt vào, 3 ca sát mép) và 5 video kiểm thử (14 lượt vào, 3 ca sát mép). Nhóm đã dựng video kiểm tra có vẽ vùng cấm và sự kiện để duyệt lại nhãn."),
    ("bul", "**Logic vùng cấm:** mỗi người được ByteTrack gán một ID; chương trình lấy trung điểm cạnh dưới khung bao và kiểm tra điểm này có nằm trong đa giác bằng hàm cv2.pointPolygonTest. Mỗi ID có hai trạng thái: ngoài vùng và đang cảnh báo. Hệ thống phát cảnh báo khi điểm chân ở trong vùng liên tục 8 khung hình (0,32 giây), và chỉ cho phép lượt mới khi người đó ở ngoài vùng liên tục 8 khung hình. Khung hình bị mất dấu không làm thay đổi trạng thái, để tránh báo lặp. Thời gian tính theo số thứ tự khung hình của video."),
    ("bul", "**Chạy thử trên video với mô hình có sẵn (CPU i7-12700H):** hệ thống chỉ báo đúng **2/33 lượt vào**, bỏ sót 31 lượt và báo nhầm 20 lần. Thời gian suy luận trung bình 39 ms/khung, toàn bộ luồng xử lý đạt trung bình 23,6 FPS. Để kiểm tra lại bộ chấm điểm, nhóm đưa khung bao gốc của CAVIAR vào cùng logic cảnh báo và đạt 33/33 lượt, 0 lần báo nhầm, độ trễ trung vị 0,28 giây. Như vậy logic cảnh báo và cách chấm đều đúng; kết quả thấp là do mô hình phát hiện."),
    ("bul", "**Phân tích nguyên nhân:** (1) người nhìn từ trên xuống, chỉ cao khoảng 20–45 px, hầu như không được phát hiện vì dữ liệu huấn luyện COCO và Human Dataset chủ yếu là ảnh chụp ngang; (2) 18/20 lần báo nhầm đến từ khu quầy và sofa, nơi mô hình nhận nhầm là một người lớn, khung này xuất hiện rồi mất nhiều lần và mỗi lần được gán ID mới. Kết quả này cho thấy bắt buộc phải fine-tune mô hình trước khi lượng tử hóa."),
    ("bul", "**Việc chưa hoàn thành, chuyển sang tuần 3:** viết Chương 2 (Cơ sở lý thuyết); duyệt lại nhãn sự kiện bằng video kiểm tra."),
    ("bul", "**Khó khăn:** khi cài Ultralytics, pip tự thay PyTorch bản CUDA bằng bản chỉ chạy CPU; nhóm đã cài lại đúng bản cũ (2.11.0+cu128) và sẽ dùng môi trường ảo riêng cho dự án. Ngoài ra, cả 10 video CAVIAR thuộc cùng một cảnh, nên cần bổ sung ít nhất một cảnh khác để đánh giá khả năng tổng quát; nhóm đã trích được 2 video camera thực tế từ một cửa hàng giày (nhận ngày 18/11/2026) và sẽ xử lý ở tuần 3."),

    ("sec", "Dự kiến công việc tuần tiếp theo"),
    ("text", "**Tuần 3 (18/11/2026 – 24/11/2026):** Huấn luyện mô hình, cải thiện cảnh báo và xây dựng giao diện."),
    ("bul", "**Ngô Gia Bảo:** fine-tune YOLO11n trên GPU RTX 3050 Ti (ảnh 640, batch 2–4) với Human Dataset kết hợp khung hình trích từ 5 video phát triển của CAVIAR (góc nhìn từ trên xuống); chọn checkpoint tốt nhất theo tập validation."),
    ("bul", "**Phan Minh Nhân:** duyệt lại 33 nhãn sự kiện; vẽ vùng cấm và gán nhãn cho 2 video cửa hàng giày; đánh giá mô hình sau fine-tune trên tập test ảnh và trên video; viết lý thuyết YOLO và ByteTrack (Chương 2)."),
    ("bul", "**Trần Đình Tiễn:** thêm bộ lọc kích thước khung người và điều kiện tuổi thọ ID vào logic cảnh báo để giảm báo nhầm; xây dựng giao diện PySide6 (mở video, vẽ và lưu vùng cấm, hiển thị khung người, ID và trạng thái); viết lý thuyết lượng tử hóa và Edge AI."),
]

TUAN3 = [
    ("sec", "Nội dung công việc trong tuần"),
    ("text", "**Tuần 3 (18/11/2026 – 24/11/2026, số liệu cập nhật đến 19/11/2026):** Huấn luyện mô hình và cải thiện chất lượng cảnh báo (Bước 3 trong quy trình thiết kế hệ thống AI nhúng)."),
    ("bul", "Bổ sung một cảnh thực tế: 2 video camera giám sát của một cửa hàng giày, vẽ vùng cấm và gán nhãn sự kiện."),
    ("bul", "Fine-tune YOLO11n với Human Dataset kết hợp khung hình từ các video phát triển của CAVIAR."),
    ("bul", "Đánh giá mô hình sau fine-tune trên ảnh và trên 12 video; thêm bộ lọc giảm báo nhầm vào logic cảnh báo."),

    ("sec", "Phân công thực hiện"),
    ("bul", "**Ngô Gia Bảo:** trích khung hình CAVIAR làm dữ liệu huấn luyện, fine-tune YOLO11n và đánh giá trên tập test ảnh."),
    ("bul", "**Phan Minh Nhân:** phân tích 2 video cửa hàng giày, chọn vùng cấm, gán nhãn thời điểm vào/ra; chạy đánh giá sự kiện trên video."),
    ("bul", "**Trần Đình Tiễn:** xây dựng công cụ gán nhãn; thêm các bộ lọc giảm báo nhầm vào logic cảnh báo và dò tham số trên video phát triển."),

    ("sec", "Báo cáo quá trình thực hiện"),
    ("bul", "**Video cửa hàng giày:** 2 video từ cùng một camera giám sát thật, 2560 × 1440, 25 FPS, tổng khoảng 10,4 phút, góc nhìn chéo từ trên cao, rất đông người (trung bình 7–8 người mỗi khung). Đây là cảnh thứ hai, khác hẳn CAVIAR, nên chỉ dùng để **kiểm thử và demo**, không dùng để huấn luyện hay chỉnh tham số. Video có khuôn mặt khách hàng nên khi đưa vào báo cáo và slide sẽ làm mờ mặt."),
    ("bul", "**Vùng cấm và nhãn:** nhóm chọn hai vùng: **Z1** là bục trưng bày bên trái (khách không được bước hoặc ngồi lên) và **Z3** là đoạn lối đi giữa, giả lập lối thoát hiểm phải để trống. Nhóm viết công cụ gán nhãn bằng OpenCV (tua từng khung, đánh dấu vào/ra bằng phím). Z1 được gán tay: Video1 không có lượt nào, Video2 có 2 lượt (một khách ngồi lên đầu bục để thử giày). Z3 đông người nên được gán bán tự động: mô hình lớn YOLO11x gợi ý, sau đó nhóm xem lại từng lượt, gộp các lượt bị đổi ID và bỏ các lượt sai. Tổng cộng **63 lượt vào** (Z1: 2, Z3: 61)."),
    ("bul", "**Dữ liệu fine-tune:** ngoài Human Dataset, nhóm trích **1.412 khung hình** (3.032 người) từ 4 video phát triển của CAVIAR làm dữ liệu huấn luyện và 119 khung từ video Walk1 làm dữ liệu kiểm định, nhãn lấy từ khung bao gốc của CAVIAR. 5 video kiểm thử của CAVIAR không được dùng."),
    ("bul", "**Huấn luyện:** YOLO11n khởi tạo từ trọng số COCO, 50 epoch, ảnh 640, batch 16, AMP, trên GPU RTX 3050 Ti, khoảng 2,5 giờ. Khi chạy thử, nhóm phát hiện nếu để chế độ một lớp thì Ultralytics khởi tạo lại phần phân loại và mô hình mất khả năng nhận người đã học (mAP gần 0 sau epoch đầu), nên nhóm giữ đủ 80 tên lớp của COCO (person là lớp 0) để dùng lại toàn bộ trọng số. Checkpoint tốt nhất ở khoảng epoch 40."),
    ("bul", "**Kết quả trên ảnh (tập test 1.945 ảnh):** **mAP@50 = 0,604, mAP@50–95 = 0,345, Precision = 0,671, Recall = 0,554**, tăng lần lượt 5,5; 2,6; 2,4 và 2,7 điểm phần trăm so với mô hình chưa fine-tune."),
    ("bul", "**Kết quả trên 10 video CAVIAR:** báo đúng **32/33 lượt** (trước fine-tune: 2/33), báo nhầm 6 lần (trước: 20), độ trễ cảnh báo trung vị **0,28 giây** (trước: 3,7 giây). Riêng 5 video kiểm thử: **14/14 lượt đúng, 1 lần báo nhầm**. Như vậy việc bổ sung ảnh góc nhìn từ trên xuống đã khắc phục được lỗi bỏ sót của tuần 2."),
    ("bul", "**Kết quả trên video cửa hàng giày:** mô hình sau fine-tune báo đúng 54/63 lượt nhưng báo nhầm 37 lần, gần như không khác mô hình gốc (57/63, 35 lần). Phần lớn báo nhầm nằm ở Z1: mô hình nhận **quần áo treo trên giá phía sau bục là người**, cạnh dưới khung rơi đúng mặt bục, khung chập chờn và mỗi lần nhận ID mới nên cảnh báo lặp lại. Vùng Z3 hoạt động tốt (khoảng 87–90% lượt vào được báo, độ trễ khoảng 0,3 giây)."),
    ("bul", "**Bộ lọc giảm báo nhầm:** nhóm thêm 4 bộ lọc vào logic cảnh báo: ngưỡng tin cậy tối thiểu, tuổi thọ ID, bỏ ID xuất hiện ngay trong vùng, bỏ vật đứng yên. Thử 54 tổ hợp và **chỉ chọn trên 5 video phát triển của CAVIAR**, cấu hình được chọn là ngưỡng tin cậy 0,5. Kết quả: CAVIAR kiểm thử đạt **14/14 lượt đúng, 0 lần báo nhầm**; video cửa hàng giảm báo nhầm từ **37 xuống 2 lần** (từ khoảng 217 xuống 12 lần mỗi giờ) nhưng số lượt báo đúng giảm từ 54 xuống 42 (người bị che hoặc ở xa có độ tin cậy thấp). Vì đây là đánh đổi giữa báo đủ và ít báo nhầm, nhóm sẽ để ngưỡng tin cậy là tham số chỉnh được trên giao diện."),
    ("bul", "**Ca khó cần phân tích trong báo cáo:** khách ngồi trên bục nhưng chân đặt dưới sàn nên điểm chân nằm ngoài vùng Z1, hệ thống dễ bỏ sót; người đứng lâu ngay trên mép vùng; đoạn rất đông người ở Video1."),
    ("bul", "**Việc chưa hoàn thành, chuyển sang tuần 4:** viết Chương 2 (Cơ sở lý thuyết); giao diện PySide6; kiểm tra chéo các nhãn sự kiện (hiện do một người gán, chưa có người thứ hai kiểm tra)."),
    ("bul", "**Khó khăn:** (1) trên Windows, script huấn luyện bị treo khi dùng nhiều luồng nạp dữ liệu nếu thiếu khối kiểm tra chương trình chính (if __name__ == \"__main__\"); (2) OpenCV 5.1 lỗi khi Ultralytics vẽ ảnh minh họa nên phải tắt chức năng này; (3) tốc độ đo trên CPU lần này (63 ms/khung) chậm hơn lần đo mốc (39 ms) dù cùng kiến trúc, nhiều khả năng do tải máy, nên nhóm sẽ đo lại tốc độ của các mô hình trong cùng điều kiện ở tuần 4; (4) mô hình chưa tổng quát tốt sang cảnh cửa hàng vì dữ liệu bổ sung chỉ có góc nhìn của CAVIAR."),

    ("sec", "Dự kiến công việc tuần tiếp theo"),
    ("text", "**Tuần 4 (25/11/2026 – 01/12/2026):** Tối ưu hóa và lượng tử hóa mô hình, lưu bằng chứng vi phạm (Bước 4 và 5 trong quy trình)."),
    ("bul", "**Ngô Gia Bảo:** chuyển mô hình đã fine-tune sang OpenVINO FP32 và lượng tử hóa INT8 (PTQ, thư viện NNCF); thử tập hiệu chuẩn 100/300/500 ảnh; so sánh mAP, dung lượng và tốc độ."),
    ("bul", "**Phan Minh Nhân:** đo tốc độ trên CPU trong cùng điều kiện (trung vị, p95, RAM) cho PyTorch, OpenVINO FP32 và INT8; chạy đánh giá sự kiện của INT8 trên 12 video; kiểm tra chéo nhãn sự kiện; viết Chương 2."),
    ("bul", "**Trần Đình Tiễn:** lưu bằng chứng vi phạm bằng SQLite (bảng events, ảnh toàn cảnh, ảnh cắt người, ghi ở luồng riêng); xây dựng giao diện PySide6 có thanh chỉnh ngưỡng tin cậy; bắt đầu viết Chương 3."),
]
from noi_dung_tuan_456 import TUAN4, TUAN5, TUAN6
