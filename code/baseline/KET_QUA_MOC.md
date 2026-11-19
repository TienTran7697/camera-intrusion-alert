# Kết quả mốc: YOLO11n có sẵn (COCO, chưa fine-tune), FP32 – 18/11/2026

Môi trường: Python 3.12.4, Ultralytics 8.4.215, PyTorch 2.11.0+cu128, OpenCV 5.1. Laptop i7-12700H, RTX 3050 Ti 4 GB, RAM 16 GB.
Mô hình: `code/models/yolo11n.pt` (Ultralytics), chỉ giữ lớp 0 (person), ảnh đầu vào 640, ngưỡng tin cậy 0,25.

## 1. Phát hiện người trên ảnh (Human Dataset, tập test 1.945 ảnh, 7.964 người)
Chạy trên GPU, script `eval_images.py`, kết quả trong `results/pretrained_fp32/image_metrics_test.json`.

| Precision | Recall | mAP@50 | mAP@50–95 | Thời gian suy luận (GPU) |
|---|---|---|---|---|
| 0,647 | 0,527 | 0,549 | 0,319 | 3,8 ms/ảnh |

## 2. Cảnh báo xâm nhập trên 10 video CAVIAR (vùng A, 33 lượt vào chuẩn)
Pipeline: YOLO11n → ByteTrack → điểm chân trong vùng → xác nhận 8 khung. Chạy trên **CPU**.
Script: `run_videos.py`, chấm điểm bằng `eval_events.py`. Kết quả trong `results/pretrained_fp32/event_eval.csv` và `summary.json`.

| Tập | Lượt vào chuẩn | Báo đúng | Bỏ sót | Báo nhầm | Recall sự kiện | Precision sự kiện |
|---|---|---|---|---|---|---|
| dev (5 video) | 19 | 2 | 17 | 10 | 0,105 | 0,167 |
| test (5 video) | 14 | 0 | 14 | 10 | 0,000 | 0,000 |
| Tổng | 33 | 2 | 31 | 20 | 0,061 | 0,091 |

- Độ trễ cảnh báo của 2 lượt báo đúng: trung vị 3,7 giây.
- Tốc độ trên CPU: suy luận trung bình **39,0 ms/khung**; toàn pipeline (đọc video, tiền xử lý, mô hình, theo dõi, kiểm tra vùng) đạt trung bình **23,6 FPS**, dao động 21,3–25,2 FPS. Video gốc là 25 FPS.

## 3. Kiểm tra độ tin cậy của phép đo
- **Kiểm tra bộ chấm điểm:** đưa khung bao gốc của CAVIAR vào cùng logic cảnh báo (`results/oracle_gt`) cho 33/33 lượt báo đúng, 0 báo nhầm, độ trễ trung vị 0,28 giây, xấp xỉ thời gian xác nhận 8 khung. Như vậy bộ chấm điểm và logic cảnh báo hoạt động đúng; kết quả thấp ở bảng 2 là do mô hình phát hiện.
- **Nguyên nhân quan sát được** (ảnh `results/pretrained_fp32/vi_du_phat_hien_caviar.png`):
  1. **Bỏ sót:** người nhìn từ trên xuống, nhỏ khoảng 20–45 px, hầu như không được phát hiện, kể cả khi hạ ngưỡng tin cậy xuống 0,05.
  2. **Báo nhầm:** 18/22 cảnh báo dự đoán có điểm chân gần (46, 177). Đó là một khung "person" lớn mô hình nhận nhầm ở khu quầy và sofa, xuất hiện rồi biến mất nhiều lần, mỗi lần nhận một ID mới.
- **Kết luận cho đồ án:** mô hình COCO có sẵn không dùng được cho góc camera này. Cần fine-tune ở tuần 3. Lưu ý: Human Dataset chủ yếu là ảnh chụp ngang, nên có thể phải bổ sung ảnh góc nhìn từ trên xuống, ví dụ trích khung hình từ các video CAVIAR thuộc tập **dev** (không lấy từ tập test), để mô hình học được góc nhìn này.

## Sự cố môi trường đã xử lý
Khi cài `ultralytics`, pip tự thay PyTorch 2.11.0+cu128 bằng 2.15.0+cpu. Đã cài lại `torch==2.11.0`, `torchvision==0.26.0` từ index cu128; CUDA hoạt động bình thường. Lần sau nên cài thêm gói vào môi trường ảo riêng của dự án.

## Tuần 3 – fine-tune (bắt đầu 18/11/2026)
- Dữ liệu: Human Dataset + 1.412 khung hình CAVIAR từ 4 video dev (train) và 119 khung từ Walk1 (val), nhãn lấy từ khung bao gốc của CAVIAR (`code/train/extract_caviar_frames.py`, `Dataset/data_ft.yaml`). Video tập test không được dùng.
- Cấu hình: YOLO11n khởi tạo từ COCO, giữ đủ 80 tên lớp để dùng lại toàn bộ đầu phân loại (499/499 trọng số; nếu để một lớp thì đầu phân loại bị khởi tạo lại và mất khả năng nhận người đã học). 50 epoch, imgsz 640, batch 16, AMP, patience 15. Script `code/train/train_ft.py`, kết quả `code/train/runs/ft_v1/`.
- Sự cố đã xử lý: trên Windows script huấn luyện phải có khối `if __name__ == "__main__"`, nếu không tiến trình nạp dữ liệu bị treo; OpenCV 5.1 lỗi khi Ultralytics vẽ ảnh minh họa, nên tắt `plots`.

## Tuần 3 – kết quả mô hình fine-tune ft_v1 (19/11/2026), `results/ft_v1/`
**Ảnh (tập test Human Dataset):** P 0,671 · R 0,554 · mAP50 0,604 · mAP50–95 0,345 (mốc: 0,647 · 0,527 · 0,549 · 0,319).

**10 video CAVIAR (CPU):** báo đúng 32/33, bỏ sót 1, báo nhầm 6; recall sự kiện 0,970, precision 0,842, độ trễ trung vị 0,28 s (mốc: 2/33, 20 báo nhầm, 3,7 s). Riêng 5 video test: 14/14 đúng, 1 báo nhầm (Walk3). Dev: 18/19, 5 báo nhầm (4 ở Walk1).
- Tốc độ lần này 63 ms/khung (14,8 FPS), chậm hơn lần đo mốc 39 ms dù cùng kiến trúc, dao động 54–75 ms giữa các video → do tải máy/chế độ điện, không dùng để so sánh. Đo lại có kiểm soát ở tuần 4.

**2 video cửa hàng giày (GPU, chỉ đo độ chính xác; `run_shop.py`, `eval_shop.py`, ghép theo vùng + thời gian):**

| Mô hình | Z1 đúng/2 | Z1 báo nhầm | Z3 đúng/61 | Z3 báo nhầm | Recall | Precision |
|---|---|---|---|---|---|---|
| YOLO11n gốc | 2 | 27 | 55 | 8 | 0,905 | 0,620 |
| ft_v1 | 1 | 27 | 53 | 10 | 0,857 | 0,593 |

- Fine-tune **không cải thiện** trên cảnh cửa hàng (góc nhìn chéo, người lớn, khác hẳn CAVIAR); Z3 vẫn tốt ở cả hai mô hình (~87–90 % lượt vào được báo, độ trễ ~0,3 s).
- **Nguyên nhân báo nhầm chính ở Z1** (`results/ft_v1/z1_bao_nham.jpg`): mô hình nhận nhầm quần áo treo trên giá phía sau bục là người, cạnh dưới khung rơi đúng mặt bục; khung chập chờn nên mỗi lần lại có ID mới → cảnh báo lặp. Cùng loại lỗi với khu sofa của CAVIAR. Hướng xử lý (không được huấn luyện bằng video test): lọc khung đứng yên, điều kiện tuổi thọ ID, ngưỡng tin cậy riêng trong vùng; hoặc bổ sung ảnh âm tính quần áo treo từ nguồn khác.

## Tuần 3 – bộ lọc giảm báo nhầm (19/11/2026)
Bộ lọc thêm vào `core/alarm.py` (mặc định tắt): `min_conf` (bỏ khung tin cậy thấp), `min_age` (ID phải tồn tại đủ lâu), `born_outside` (bỏ ID sinh ra ngay trong vùng), `min_move` (bỏ vật đứng yên). Track của 12 video được lưu một lần (`dump_tracks.py`, GPU) rồi thử 54 cấu hình offline (`tune_filters.py`). **Chỉ chọn cấu hình trên 5 video CAVIAR dev** (giữ số báo đúng cao nhất, rồi ít báo nhầm nhất, rồi đơn giản nhất) → **ft_v1 + `min_conf = 0,5`**.

| ft_v1 | CAVIAR dev (19) | CAVIAR test (14) | Cửa hàng giày (63) |
|---|---|---|---|
| Không lọc | 18 đúng / 5 nhầm | 14 / 1 | 54 / 37 (217 nhầm/giờ) |
| **min_conf 0,5 (đã chọn)** | 18 / 3 | **14 / 0** | 42 / **2** (11,7 nhầm/giờ) |

Phân tích độ nhạy (KHÔNG dùng để chọn, `results/ft_v1/filter_sensitivity.json`), dạng đúng/nhầm:

| Cấu hình | dev | test | cửa hàng |
|---|---|---|---|
| min_conf 0,35 | 18/4 | 14/1 | 51/15 |
| min_conf 0,5 | 18/3 | 14/0 | 42/2 |
| born_outside | 15/1 | 10/0 | 47/4 |
| min_age 25 | 17/4 | 13/1 | 51/29 |
| min_move 0,5 | 17/2 | 13/0 | 46/2 |

- Nâng ngưỡng tin cậy loại gần hết "người ảo" (quần áo treo ở Z1, khu sofa CAVIAR) nhưng trên cảnh cửa hàng cũng làm mất ~12 lượt thật (người bị che, ở xa) → đánh đổi recall 0,857 → 0,667 lấy precision 0,593 → 0,955. Nên để ngưỡng là tham số chỉnh được trong giao diện.
- `born_outside` làm mất lượt thật trên CAVIAR (người bị đổi ID ngay khi bước vào vùng) nên không chọn.
- Mô hình gốc dù có lọc vẫn hỏng trên CAVIAR (dev 3/19, test 0/14) → giữ ft_v1.
