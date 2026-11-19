# Dữ liệu video kiểm thử

## CAVIAR (tải ngày 18/11/2026)
- Nguồn: https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1/ (EC Funded CAVIAR project/IST 2001 37540). Khi dùng phải trích dẫn nguồn trong báo cáo.
- Đã kiểm tra: cả 10 video đều đọc được bằng OpenCV; số khung hình trong tệp nhãn XML khớp với video (XML ít hơn 1 khung).
- Định dạng: MPEG-1, 384×288, 25 FPS. Tệp `*gt.xml` là nhãn gốc, có khung bao và ID của từng người qua từng khung hình.
- Ảnh xem trước một khung của mỗi video: `preview_caviar.png`.

| Video | Số khung | Thời lượng (giây) | Số người (ID) |
|---|---|---|---|
| Walk1 | 612 | 24,5 | 4 |
| Walk2 | 1.056 | 42,2 | 6 |
| Walk3 | 1.380 | 55,2 | 5 |
| Browse1 | 1.044 | 41,8 | 4 |
| Browse2 | 876 | 35,0 | 4 |
| Browse3 | 912 | 36,5 | 5 |
| Browse4 | 1.140 | 45,6 | 3 |
| Meet_WalkTogether1 | 708 | 28,3 | 6 |
| Meet_WalkSplit | 624 | 25,0 | 9 |
| Meet_Crowd | 492 | 19,7 | 4 |
| **Tổng** | **8.844** | **khoảng 354 giây (5,9 phút)** | |

## Lưu ý khi dùng
1. **Cả 10 video đều quay từ cùng một camera, ở cùng sảnh INRIA.** Tính theo bối cảnh thì đây chỉ là **một cảnh**. Chia video phát triển và video kiểm thử vẫn được, nhưng kết quả chỉ đại diện cho một góc camera. Nên bổ sung ít nhất một cảnh khác, ví dụ một chuỗi MOT17 hoặc video nhóm tự quay.
2. **Camera đặt cao, nhìn gần như thẳng từ trên xuống và có méo ống kính góc rộng (fisheye).** Người trong ảnh nhỏ, khoảng 30–60 px. Ảnh trong Human Dataset chủ yếu chụp ngang, nên mô hình có thể phát hiện kém hơn với góc nhìn này. Đây là điểm cần đo khi chạy kết quả mốc, và có thể đưa vào phần phân tích. Với góc nhìn từ trên xuống, trung điểm cạnh dưới khung bao vẫn gần vị trí chân, nhưng nên kiểm tra lại bằng mắt.
3. Có thể chọn vùng cấm hợp lý trên sàn sảnh, ví dụ khu ghế sofa bên trái, khu cửa kính phía dưới hoặc lối vào bên phải. Mỗi video dùng một đa giác cố định.

## Vùng cấm và nhãn sự kiện (18/11/2026, bản nháp chờ duyệt)
- Đã chốt **vùng A**, khu quầy và sofa bên trái, dùng chung cho cả 10 video. Tọa độ đa giác lưu trong `CAVIAR/zones.json`.
- Nhãn sự kiện `CAVIAR/events_gt.csv` được tạo tự động từ khung bao gốc của CAVIAR bằng script `code/labeling/make_gt_events.py`:
  - Điểm chân = trung điểm cạnh dưới khung bao.
  - VÀO khi điểm chân ở trong vùng liên tục từ 8 khung hình (0,32 giây); RA khi ở ngoài liên tục từ 8 khung hình. Phải RA ổn định mới tính lượt VÀO mới.
  - Người xuất hiện sẵn trong vùng vẫn tính là một lượt vào, và được đánh dấu cột `start_inside = 1`.
- Kết quả: **33 lượt vào** và **6 ca sát mép nhưng không vào** (cách vùng dưới 15 px).
- Video kiểm tra để duyệt: `_review/<video>_review.mp4`, khung đỏ là người đang ở trong vùng. Ảnh tổng hợp khung hình tại các lượt vào: `_review/review_events.png`.
- Đề xuất chia video (`CAVIAR/split.json`):

| Tập | Video | Lượt vào | Sát mép |
|---|---|---|---|
| dev (chỉnh ngưỡng) | Browse1, Browse2, Meet_Crowd, Meet_WalkSplit, Walk1 | 19 | 3 |
| test (đánh giá cuối) | Browse3, Browse4, Meet_WalkTogether1, Walk2, Walk3 | 14 | 3 |

- **Cần người duyệt:** xem 10 video `_review`, mỗi dòng trong `events_gt.csv` đúng thì đổi cột `verified` thành 1, sai thì ghi vào cột `note`.
- **Điểm cần chú ý khi duyệt:** cạnh trên của vùng A nằm gần cửa ra vào phía trên bên trái. Một số lượt "vào" thực chất là người vừa đi qua cửa và chạm mép vùng (ví dụ Meet_Crowd, Meet_WalkTogether1 id5 và id6, Walk2 id4). **Đã quyết định (18/11/2026): giữ nguyên vùng A.** Theo quy tắc "chạm vào vùng là vi phạm", các lượt này vẫn hợp lệ; nhóm xem chúng là ca khó ngay trên mép vùng, và trong báo cáo có thể phân tích riêng nhóm này.

## Video cửa hàng giày (nhóm bổ sung 18/11/2026) – `cua_hang_giay/`
| Video | Độ phân giải | FPS | Thời lượng | Mã hóa |
|---|---|---|---|---|
| Video1.mp4 | 2560×1440 | 25 | 241,7 s (6.042 khung) | HEVC (H.265) |
| Video2.mp4 | 2560×1440 | 25 | 382,2 s (9.556 khung) | HEVC (H.265) |

- Cùng một camera giám sát thật, đặt cao, nhìn chéo xuống (khác hẳn góc nhìn thẳng từ trên xuống của CAVIAR). Có dấu thời gian và tên cửa hàng trên hình. Rất đông người.
- Chạy thử YOLO11n chưa fine-tune trên 30 giây đầu (1/5 khung, CPU): trung bình 7–8 người được phát hiện mỗi khung (tối đa 12–13); chiều cao khung người trung vị khoảng 300 px trên ảnh gốc; độ tin cậy trung bình 0,55; khoảng 55 ms/khung. Người ở gần và giữa khung được phát hiện tốt; người ở xa phía quầy hộp giày, trẻ em và người bị giá treo che khuất thường bị bỏ sót.
- Đọc tuần tự bằng OpenCV không lỗi; nhảy tới khung bất kỳ (seek) thì bộ giải mã HEVC báo lỗi tham chiếu, nên khi xử lý phải đọc tuần tự.
- Chưa có vùng cấm và chưa có nhãn sự kiện. Video có khuôn mặt khách hàng thật: khi đưa hình vào báo cáo hoặc slide nên làm mờ mặt.
- Video1 khai báo 6.042 khung nhưng OpenCV chỉ đọc được 5.793 khung (khoảng 10 giây cuối không giải mã được).
- **Đề xuất vùng cấm (18/11/2026):** ảnh `cua_hang_giay/de_xuat_vung_cam.png`, tọa độ trong `cua_hang_giay/zones_de_xuat.json` (khung 1280×720). Số cảnh báo khi chạy mô hình chưa fine-tune + ByteTrack (xác nhận 8 khung), Video1 + Video2: Z1 bục trưng bày 1 + 14; Z2 sàn góc dưới trái 30 + 51; Z3 lối đi giữa 35 + 28; Z4 trước quầy hộp giày 53 + 50. Đây **không phải số lượt vào thật**: mô hình đổi ID rất nhiều (410 ID trong Video1, 612 ID trong Video2), nên con số bị thổi phồng. Nhãn thật phải gán tay.
- Quan sát: mô hình nhận nhầm hình người trên bảng quảng cáo bên trái là người (khung đứng yên), điểm chân nằm sát vùng Z2. Khách thường đứng sát hoặc ngồi lên mép bục trưng bày (Z1), là các ca khó tự nhiên.
- **Đã chốt (18/11/2026): dùng hai vùng Z1 (bục trưng bày bên trái) và Z3 (lối đi giữa, giả lập lối thoát hiểm)** cho cả Video1 và Video2. Tọa độ theo video gốc 2560×1440 trong `cua_hang_giay/zones.json`, ảnh `cua_hang_giay/vung_cam_da_chot.png`. Hai video chỉ dùng làm test và demo, không dùng để huấn luyện. Bước tiếp theo: nhóm gán nhãn tay thời điểm vào/ra cho từng lượt trong Z1 và Z3.
- **Công cụ gán nhãn (18/11/2026):** `code/labeling/label_tool.py`, hướng dẫn ở `cua_hang_giay/HUONG_DAN_GAN_NHAN.md`. Công cụ dùng bản 720p tua được do `code/labeling/prepare_720p.py` tạo (`cua_hang_giay/720p/*.avi`, MJPG, tổng khoảng 4,6 GB, tạo lại được nên có thể xóa sau khi gán nhãn xong). Nhãn ghi vào `cua_hang_giay/events_gt.csv`.
- **Nhãn sự kiện (18/11/2026) trong `cua_hang_giay/events_gt.csv`, tổng 63 lượt:**
  - Z1 (xem tay từng khung, phóng to chỗ khó): Video1 **0 lượt**, Video2 **2 lượt** (một ông khách ngồi lên đầu bục thử giày hai lần, chân vẫn đặt dưới sàn → ca khó đối với cách xét điểm chân). Vùng Z1 đã sửa lại cho khớp mép bục.
  - Z3 (bán tự động): gợi ý bằng **YOLO11x + ByteTrack** (`code/labeling/preannotate_z3.py`, `z3_candidates.py`), sau đó xem lại từng lượt bằng ảnh ghép 0,5 giây/ô và sửa tay (`finalize_z3.py`: gộp lượt bị đổi ID, bỏ em bé được bế, bỏ lượt chân ở ngoài vùng, sửa thời điểm ra). Kết quả: Video1 **36 lượt**, Video2 **25 lượt**. Đoạn 46–69 s của Video1 rất đông, độ chính xác nhãn thấp hơn (ghi chú `dong_nguoi`).
  - Cột `verified = 0`: nhóm nên kiểm tra lại nhanh bằng `label_tool.py` (phím G để nhảy tới từng lượt). YOLO11x chỉ dùng để gợi ý nhãn, khác với mô hình YOLO11n được đánh giá.
