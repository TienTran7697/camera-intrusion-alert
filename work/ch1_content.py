# Nội dung Chương 1. **đậm**, _nghiêng_.
# Trích dẫn: [1] Đặng Hoàng Phúc và cs. 2024; [2] Hoàng Đức Quý và cs. 2025;
#            [3] Phyo và cs. 2026; [4] Musa và cs. 2026.

S11 = [
    "Hiện nay, tại nhiều môi trường như công trường xây dựng, nhà xưởng, kho hàng, phòng máy hay khu vực có máy móc đang vận hành, luôn tồn tại những vùng mà người không có nhiệm vụ không được phép đi vào. Khi một người bước vào các vùng này, hậu quả có thể là mất an toàn cho chính người đó, hư hỏng thiết bị hoặc mất mát tài sản. Cách giám sát phổ biến hiện nay vẫn là lắp đặt camera và bố trí nhân viên theo dõi màn hình. Tuy nhiên, cách làm này phụ thuộc nhiều vào sự tập trung của con người: khi phải quan sát nhiều camera trong thời gian dài, đặc biệt vào ban đêm, người giám sát rất dễ bỏ sót những lần xâm nhập chỉ diễn ra trong vài giây.",

    "Cùng với sự phát triển của học sâu (Deep Learning) và thị giác máy tính (Computer Vision), camera không còn chỉ dùng để ghi hình mà có thể tự phân tích nội dung khung hình. Các mô hình phát hiện đối tượng thuộc họ YOLO (You Only Look Once) cho phép xác định vị trí của người trong ảnh với tốc độ cao. Từ vị trí này, chương trình có thể so sánh với một vùng cấm được định nghĩa trước để tự động phát cảnh báo mà không cần người trực liên tục trước màn hình.",

    "Trong nước, Đặng Hoàng Phúc và cộng sự [1] đã xây dựng hệ thống cảnh báo xâm nhập tại công trường bằng YOLOv5 và YOLOv8. Nhóm tác giả xác định vi phạm dựa trên tỷ lệ phần diện tích khung bao của người nằm trong đa giác giám sát; mô hình YOLOv8n đạt mAP@50 là 92,2% với tốc độ khoảng 15,6 khung hình/giây trên máy tính dùng CPU Intel Core i5-1135G7. Hoàng Đức Quý và cộng sự [2] kết hợp YOLOv11 với thuật toán theo dõi ByteTrack để giám sát và đếm người đi qua vùng cảnh báo, đạt Precision trung bình 94,2%, Recall 90,4% trên các video thử nghiệm và tốc độ 25–32 khung hình/giây trên laptop không dùng GPU. Ở ngoài nước, Phyo và cộng sự [3] ánh xạ vị trí chân của người xuống mặt phẳng sàn bằng phép biến đổi homography để dự đoán người sắp đi vào vùng hạn chế. Musa và cộng sự [4] triển khai hệ thống trên Raspberry Pi 4B, dùng cảm biến chuyển động PIR để chỉ kích hoạt mô hình AI khi cần, nhờ đó công suất trung bình giảm từ 6,5 W xuống 3,9 W trong thử nghiệm của tác giả.",

    "Khi tìm hiểu các nghiên cứu trên, nhóm nhận thấy hai vấn đề cần quan tâm. Thứ nhất, các hệ thống thường được đánh giá bằng chỉ số phát hiện đối tượng như mAP, Precision, Recall trên từng ảnh. Trong khi đó, với một hệ thống cảnh báo, câu hỏi quan trọng hơn là: có bao nhiêu lượt xâm nhập thật được báo, hệ thống báo nhầm bao nhiêu lần và cảnh báo phát ra chậm bao lâu sau khi người bước qua ranh giới. Phát hiện được người trong ảnh chưa đồng nghĩa với phát hiện đúng thời điểm người đó đi vào vùng cấm. Thứ hai, các nghiên cứu [1], [2] báo cáo kết quả với mô hình ở dạng gốc, chưa xem xét việc tối ưu hóa mô hình để chạy trên thiết bị có tài nguyên hạn chế. Đây lại là vấn đề cốt lõi của môn AI cho hệ thống nhúng, vì các thiết bị biên (edge device) thường không có GPU rời, bộ nhớ và điện năng đều bị giới hạn. Kết quả của [4] cũng cho thấy chi phí tính toán của mô hình AI ảnh hưởng trực tiếp đến mức tiêu thụ điện của thiết bị.",

    "Một kỹ thuật tối ưu hóa phổ biến cho vấn đề này là lượng tử hóa (quantization). Theo cách hiểu của nhóm, lượng tử hóa chuyển trọng số và phép tính của mô hình từ số thực 32 bit (FP32) sang số nguyên 8 bit (INT8), giúp giảm dung lượng mô hình và có thể tăng tốc độ suy luận trên CPU có hỗ trợ tính toán INT8. Tuy nhiên, INT8 không chắc chắn nhanh hơn trên mọi phần cứng và có thể làm giảm khả năng phát hiện, nhất là với người ở xa hoặc bị che khuất một phần. Nếu mô hình bỏ sót người trong vài khung hình đúng lúc họ bước qua ranh giới, hệ thống có thể báo chậm hoặc không báo. Vì vậy, nhóm cho rằng hiệu quả của lượng tử hóa cần được đo trên chính bài toán cảnh báo, chứ không chỉ dừng lại ở chỉ số phát hiện đối tượng.",

    "Xuất phát từ những lý do trên, nhóm chọn đề tài “Xây dựng hệ thống tự động phát hiện và cảnh báo khi có người xâm nhập khu vực cấm qua camera”. Hướng tiếp cận tổng quát của đồ án được trình bày trong Hình 1.1. Mô hình YOLO11n phát hiện người trong từng khung hình; thuật toán ByteTrack gán cho mỗi người một mã định danh (ID) để theo dõi qua nhiều khung hình; sau đó chương trình kiểm tra vị trí chân của người có nằm trong vùng cấm hay không và quyết định khi nào cần phát cảnh báo. Song song với đó, cùng một mô hình sau huấn luyện được chuyển sang các phiên bản FP32 và INT8 để so sánh trên cùng dữ liệu và cùng máy tính.",
]

FIG_11_TITLE = "Hướng tiếp cận tổng quát của đồ án"

S11_AFTER_FIG = [
    "Nhóm chọn điểm giữa cạnh dưới của khung bao làm vị trí đại diện cho người, thay vì tâm khung bao hay vị trí đầu. Lý do là camera giám sát thường đặt cao và nhìn xiên xuống, trong khi vùng cấm là một khu vực trên mặt sàn. Khi đó, một người đứng bên ngoài có thể cúi đầu vào trong đường biên trên ảnh dù chân chưa bước qua; ngược lại, người đã bước vào nhưng phần đầu vẫn nằm ngoài đa giác. Nghiên cứu [3] cũng dùng vị trí chân để xác định quan hệ giữa người và vùng hạn chế. Bảng 1.1 tóm tắt điểm khác nhau giữa các nghiên cứu nhóm tham khảo và định hướng của đồ án.",
]

TABLE_11_TITLE = "So sánh định hướng của các nghiên cứu tham khảo và đồ án"
TABLE_11 = [
    ["Nghiên cứu", "Mô hình, phương pháp", "Cách xác định xâm nhập", "Nội dung liên quan đến tối ưu hóa"],
    ["[1] 2024", "YOLOv5, YOLOv8 (các bản n, s, m)", "Tỷ lệ diện tích khung bao nằm trong đa giác vượt ngưỡng", "Chọn mô hình nhỏ YOLOv8n để cân bằng chất lượng và tốc độ"],
    ["[2] 2025", "YOLOv11 + ByteTrack", "Tâm khung bao đi qua đường ranh giữa hai khung hình liên tiếp", "Chạy trên CPU laptop, chưa lượng tử hóa"],
    ["[3] 2026", "YOLO11 + ByteTrack + homography", "Dự đoán quỹ đạo vị trí chân trên mặt phẳng sàn", "Giảm độ phân giải và số khung hình cần xử lý"],
    ["[4] 2026", "CNN trên Raspberry Pi 4B + cảm biến PIR", "Phân loại hoạt động bình thường hoặc đáng ngờ", "Chỉ chạy AI khi có chuyển động để giảm điện năng"],
    ["Đồ án", "YOLO11n + ByteTrack", "Điểm chân nằm trong đa giác, xác nhận theo thời gian, mỗi lượt vào báo một lần", "Lượng tử hóa INT8 và đánh giá ảnh hưởng lên cả mô hình lẫn cảnh báo"],
]

S12 = [
    "Mục tiêu tổng quát của đồ án là xây dựng một ứng dụng trên máy tính có khả năng tự động phát hiện người đi vào khu vực cấm từ video của camera cố định và phát cảnh báo kịp thời. Đồng thời, nhóm tối ưu hóa mô hình phát hiện người bằng lượng tử hóa INT8 và đánh giá sự đánh đổi giữa chất lượng phát hiện, tốc độ xử lý và dung lượng mô hình.",

    "Câu hỏi nghiên cứu chính mà nhóm đặt ra là: _lượng tử hóa INT8 giúp giảm thời gian xử lý và dung lượng của mô hình YOLO11n đến mức nào, và làm thay đổi khả năng cảnh báo xâm nhập ra sao?_",

    "Để trả lời câu hỏi trên, nhóm đặt ra các mục tiêu cụ thể như sau:",

    "**(1) Huấn luyện mô hình phát hiện người:** tinh chỉnh (fine-tune) mô hình YOLO11n đã huấn luyện sẵn cho lớp người trên bộ dữ liệu Human Dataset; ghi nhận các chỉ số mAP@50, mAP@50–95, Precision và Recall làm mốc so sánh cho phiên bản FP32.",

    "**(2) Tối ưu hóa và lượng tử hóa mô hình:** xây dựng quy trình chuyển mô hình từ PyTorch FP32 sang OpenVINO FP32 và OpenVINO INT8 bằng phương pháp lượng tử hóa sau huấn luyện (Post-Training Quantization – PTQ) với thư viện NNCF. Nhóm khảo sát thêm ảnh hưởng của số lượng ảnh hiệu chuẩn (100, 300 và 500 ảnh) và cách chọn ảnh hiệu chuẩn đến chất lượng của mô hình INT8.",

    "**(3) Xây dựng ứng dụng cảnh báo:** ứng dụng cho phép mở video, vẽ vùng cấm dạng đa giác, hiển thị khung bao, ID của từng người và trạng thái vùng; phát cảnh báo bằng hình ảnh và âm thanh khi có xâm nhập, lưu lại ảnh và thời điểm xảy ra sự kiện. Người dùng có thể chọn chạy phiên bản mô hình FP32 hoặc INT8.",

    "**(4) Đánh giá ở hai cấp độ:** ở cấp mô hình, nhóm đo dung lượng, thời gian suy luận, bộ nhớ sử dụng và độ chính xác phát hiện người; ở cấp hệ thống, nhóm đếm số lượt xâm nhập được phát hiện đúng, số lượt bỏ sót, số lần báo nhầm và đo độ trễ từ lúc người bước qua ranh giới đến lúc hệ thống phát cảnh báo.",

    "Về mặt kỹ thuật, nhóm đặt mục tiêu ban đầu là phiên bản INT8 có dung lượng và thời gian suy luận thấp hơn phiên bản OpenVINO FP32, trong khi mAP@50–95 và tỷ lệ phát hiện lượt xâm nhập không giảm quá khoảng 2 điểm phần trăm. Đây là tiêu chí nhóm tự đề ra để định hướng thực nghiệm và sẽ được điều chỉnh sau khi có kết quả đo của mô hình gốc.",
]

S13 = [
    "**Đối tượng nghiên cứu** của đồ án gồm: mô hình phát hiện đối tượng YOLO11n cho lớp người; kỹ thuật lượng tử hóa sau huấn luyện từ FP32 sang INT8 trên bộ công cụ OpenVINO; và quy tắc xác định xâm nhập dựa trên vị trí chân của người so với vùng cấm dạng đa giác, kết hợp với theo dõi đối tượng bằng ByteTrack.",

    "**Phạm vi nghiên cứu** được giới hạn để nhóm có thể tập trung vào phần tối ưu hóa mô hình, là trọng tâm mà môn học yêu cầu. Theo trao đổi với giảng viên hướng dẫn, hệ thống được phép triển khai dưới dạng ứng dụng trên máy tính và demo bằng video có sẵn. Chi tiết phạm vi được trình bày trong Bảng 1.2.",
]

TABLE_12_TITLE = "Phạm vi nghiên cứu của đồ án"
TABLE_12 = [
    ["Nội dung", "Phạm vi thực hiện"],
    ["Nền tảng triển khai", "Ứng dụng trên máy tính, viết bằng Python, giao diện PySide6. Mô hình được đo và chạy trên CPU để gần với điều kiện của thiết bị biên không có GPU."],
    ["Phần cứng", "Laptop Intel Core i7-12700H, RAM 16 GB. GPU NVIDIA RTX 3050 Ti Laptop (4 GB VRAM) chỉ dùng cho bước huấn luyện, không dùng khi so sánh FP32 và INT8."],
    ["Dữ liệu đầu vào", "Video từ camera đặt cố định: một số video trong bộ CAVIAR, MOT17 và video do nhóm tự quay."],
    ["Dữ liệu huấn luyện", "Human Dataset (Kaggle), khoảng 17.300 ảnh có nhãn khung bao người theo định dạng YOLO."],
    ["Đối tượng phát hiện", "Chỉ lớp người (person). Không nhận dạng danh tính hay khuôn mặt."],
    ["Vùng cấm", "Một vùng đa giác cố định cho mỗi video, do người dùng vẽ trên khung hình."],
    ["Định nghĩa xâm nhập", "Một người được theo dõi có điểm chân đi từ ngoài vào trong vùng cấm và ở trong vùng trong một khoảng thời gian xác nhận ngắn. Mọi người đi vào vùng đều được xem là vi phạm."],
    ["Tối ưu hóa", "Chuyển đổi sang OpenVINO và lượng tử hóa sau huấn luyện INT8 bằng NNCF. Huấn luyện có mô phỏng lượng tử hóa (QAT) và cắt tỉa mô hình (pruning) là hướng mở rộng nếu còn thời gian."],
    ["Ngoài phạm vi", "Vùng cấm thay đổi theo thời gian, dự đoán quỹ đạo, phân biệt người được phép và không được phép, triển khai trên bo mạch nhúng như Raspberry Pi."],
]

S13_AFTER_TABLE = [
    "Về quy tắc cảnh báo, hệ thống chỉ báo một lần cho mỗi lượt đi vào của một người và chỉ tạo sự kiện mới khi người đó đã ra khỏi vùng ổn định rồi quay lại. Ngưỡng thời gian xác nhận ban đầu được đặt khoảng 0,3 giây và sẽ được chọn lại trên tập dữ liệu kiểm định. Nhóm không chọn ngưỡng dài như vài giây vì một người có thể đi xuyên qua vùng cấm nhanh hơn thế. Thời gian được tính theo mốc thời gian của video, để kết quả không bị ảnh hưởng khi máy xử lý nhanh hoặc chậm hơn tốc độ phát của video.",
]

S14 = [
    "Báo cáo được tổ chức thành năm chương, nội dung chính của từng chương như sau:",

    "**Chương 1 – Tổng quan về đề tài:** trình bày bối cảnh, tính cấp thiết, mục tiêu, đối tượng và phạm vi nghiên cứu của đồ án.",

    "**Chương 2 – Cơ sở lý thuyết:** tổng quan các nghiên cứu liên quan trong và ngoài nước; trình bày lý thuyết về mô hình phát hiện đối tượng YOLO, thuật toán theo dõi ByteTrack, cách kiểm tra một điểm nằm trong đa giác, kỹ thuật lượng tử hóa mô hình và lý do triển khai AI tại biên (Edge AI).",

    "**Chương 3 – Phân tích và thiết kế hệ thống:** trình bày kiến trúc tổng thể, yêu cầu chức năng và phi chức năng, thiết kế phần mềm và luồng xử lý cảnh báo, quá trình chuẩn bị dữ liệu, huấn luyện và lượng tử hóa mô hình.",

    "**Chương 4 – Kết quả thực nghiệm:** mô tả môi trường triển khai, giao diện ứng dụng; so sánh các phiên bản PyTorch FP32, OpenVINO FP32 và OpenVINO INT8 về độ chính xác, tốc độ, dung lượng và chất lượng cảnh báo trên video thử nghiệm.",

    "**Chương 5 – Kết luận và hướng phát triển:** tổng kết những gì nhóm đã làm được so với mục tiêu đặt ra, các hạn chế còn tồn tại và hướng cải tiến trong tương lai.",
]
