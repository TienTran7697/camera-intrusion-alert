# Kết quả tối ưu hóa và lượng tử hóa INT8 – 19/11/2026

Môi trường: OpenVINO 2026.4.1, NNCF 3.4.0, Ultralytics 8.4.215, PyTorch 2.11.0. CPU Intel i7-12700H (6 nhân P + 8 nhân E, 20 luồng), RAM 16 GB, cắm sạc, chế độ điện Performance.

## 1. Mô hình (cùng một checkpoint `ft_v1`)
`export_openvino.py`. INT8 = lượng tử hóa sau huấn luyện (PTQ) bằng NNCF qua Ultralytics (preset MIXED, bỏ qua phần hậu xử lý của đầu Detect). Ảnh hiệu chuẩn chọn **ngẫu nhiên** (seed 42) từ tập validation, không dùng tập test (`Dataset/calib/calib_<N>.txt`, 100 ⊂ 300 ⊂ 500). Không dùng tham số `fraction` của Ultralytics vì nó chỉ lấy N ảnh đầu tiên.

| Mô hình | Thư mục | Dung lượng |
|---|---|---|
| PyTorch | `models/ft_v1.pt` | 5,3 MB (trọng số lưu FP16) |
| OpenVINO FP32 | `models/ft_v1_fp32_openvino_model` | 10,4 MB |
| OpenVINO INT8 | `models/ft_v1_int8_c{100,300,500}_openvino_model` | 3,3 MB (**nhỏ hơn FP32 3,2 lần**) |

## 2. Độ chính xác trên tập test ảnh (1.945 ảnh, `baseline/results/ov_*`)
| Mô hình | P | R | mAP50 | mAP50–95 | Δ mAP50–95 |
|---|---|---|---|---|---|
| OpenVINO FP32 | 0,670 | 0,553 | 0,6041 | 0,3445 | – |
| INT8 – 100 ảnh hiệu chuẩn | 0,662 | 0,557 | 0,6022 | 0,3425 | −0,20 điểm % |
| **INT8 – 300 ảnh (chọn)** | 0,671 | 0,554 | 0,6028 | 0,3432 | **−0,13 điểm %** |
| INT8 – 500 ảnh | 0,660 | 0,556 | 0,6019 | 0,3429 | −0,16 điểm % |

Số ảnh hiệu chuẩn từ 100 đến 500 gần như không ảnh hưởng (chênh < 0,1 điểm %). Chọn 300 ảnh.

## 3. Tốc độ CPU có kiểm soát (`bench.py`, `results/bench_t0.json`, `bench_t4.json`)
Cùng 295 khung (150 khung CAVIAR test + 145 khung cửa hàng giày) nạp sẵn vào RAM, batch 1, đầu vào 640×640, khởi động 30 lần, mỗi mô hình một tiến trình riêng. "Chỉ mô hình" = thời gian forward trên tensor đã tiền xử lý (so sánh công bằng). PyTorch đã gộp Conv+BN.

| Mô hình | 4 luồng: trung vị / p95 (ms) | FPS | Hết luồng: trung vị (2 lần đo) | RAM mô hình |
|---|---|---|---|---|
| PyTorch FP32 | 80,3 / 88,9 | 12,5 | 79,5–80,6 | ~550 MB |
| OpenVINO FP32 | 30,0 / 35,2 | 33 | 26,4–38,4 | ~115 MB |
| **OpenVINO INT8** | **14,0 / 16,0** | **71** | 12,2–17,6 | ~100 MB |

- **INT8 nhanh hơn OpenVINO FP32 ~2,15 lần**, nhanh hơn PyTorch ~5,7 lần (4 luồng).
- Ở chế độ dùng hết luồng, kết quả dao động giữa các lần đo (CPU lai nhân P/E, Windows phân luồng không ổn định); ở 4 luồng hai lần đo gần trùng nhau (30,0 vs 31,1 và 14,0 vs 14,1 ms) → **dùng 4 luồng làm số liệu chính**, cũng gần với thiết bị biên.
- Đo cả hệ thống (Ultralytics predict trên ảnh gốc): PyTorch ~44 ms nhưng được dùng ảnh chữ nhật nhỏ hơn (vd 640×384), OpenVINO dùng ảnh vuông cố định 640×640 (FP32 ~42 ms, INT8 ~22 ms ở 4 luồng) → không so PyTorch ở mức này.
- Số 63 ms/khung đo ở tuần 3 là PyTorch khi máy đang bận, không dùng.

## 4. Chất lượng cảnh báo trên 12 video (`baseline/compare_variants.py`, `results/so_sanh_fp32_int8.json`)
Cùng logic cảnh báo (xác nhận 8 khung), có/không bộ lọc min_conf 0,5 (chọn trên CAVIAR dev ở tuần 3). Đúng/tổng, số báo nhầm:

| Mô hình | Bộ lọc | CAVIAR dev (19) | CAVIAR test (14) | Cửa hàng giày (63) |
|---|---|---|---|---|
| PyTorch FP32 | không | 18 / 5 nhầm | 14 / 1 | 54 / 37 |
| PyTorch FP32 | 0,5 | 18 / 3 | 14 / 0 | 42 / 2 |
| OpenVINO FP32 | không | 18 / 5 | 14 / 0 | 53 / 39 |
| OpenVINO FP32 | 0,5 | 18 / 2 | 14 / 0 | 43 / 2 |
| OpenVINO INT8 | không | 18 / 6 | 14 / 1 | 56 / 39 |
| **OpenVINO INT8** | **0,5** | 18 / 4 | **13 / 0** | **43 / 3** |

- INT8 giữ được chất lượng cảnh báo: chênh lệch so với FP32 chỉ khoảng ±1–2 sự kiện mỗi tập, độ trễ trung vị vẫn ~0,28–0,34 s.
- Có lọc, INT8 bỏ sót thêm 1 lượt ở Walk2 (CAVIAR test) – lượt ở sát mép cửa; nguyên nhân hợp lý là lượng tử hóa làm độ tin cậy dịch nhẹ quanh ngưỡng 0,5. Nên kiểm tra lại ngưỡng riêng cho INT8 trên tập dev.
- Không lọc, INT8 trên cửa hàng còn báo đúng nhiều hơn FP32 (56 vs 53) → khác biệt nằm trong mức dao động.

## Kết luận cho câu hỏi nghiên cứu
Lượng tử hóa INT8 (PTQ, 300 ảnh hiệu chuẩn) giảm dung lượng **3,2 lần**, tăng tốc suy luận trên CPU **~2,15 lần** so với OpenVINO FP32 (14 ms, 71 FPS ở 4 luồng), trong khi mAP50–95 chỉ giảm **0,13 điểm %** và chất lượng cảnh báo gần như không đổi (chênh ±1–2 sự kiện). Đạt mục tiêu đề ra (giảm không quá 2 điểm %).

## 5. Lưu bằng chứng vi phạm bằng SQLite (19/11/2026)
Code: `code/core/evidence.py` (EvidenceStore, luồng ghi riêng + hàng đợi), `code/core/pipeline.py` (luồng xử lý hoàn chỉnh, dùng chung cho giao diện), `code/app/run_pipeline.py` (dòng lệnh; `--export` xuất CSV).
- Bảng `events`: id, video_id, zone_id, track_id, frame_enter/alert/exit, t_enter/t_alert/t_exit (giây theo video), confidence, bbox (JSON), model_version, snapshot_path, crop_path, clip_path (tương đối theo thư mục chứa events.db), created_at.
- Mỗi lượt: ảnh toàn cảnh (vùng cấm, khung người, ID, vùng, thời điểm, độ tin cậy), ảnh cắt người, clip 6 s (3 s trước + 3 s sau cảnh báo, bộ đệm vòng). t_exit được cập nhật khi người ra khỏi vùng; để trống nếu hết video vẫn còn trong vùng.
- Thử trên CAVIAR Walk2 + Meet_WalkTogether1 (INT8, min_conf 0,5): 7 dòng, đủ ảnh và clip (150 khung).
- **Ảnh hưởng tới tốc độ** (Video2 cửa hàng giày, 9.556 khung, INT8, 2 vùng, gồm cả giải mã HEVC 2K và thu về 720p): không lưu 40,7 FPS (16,1 ms/khung) → có lưu ảnh + clip 39,1 FPS (17,1 ms/khung), **chậm hơn ~4 %**, chủ yếu do sao chép khung vào bộ đệm vòng cho clip; ghi đĩa/DB không chặn luồng xử lý. 25 cảnh báo, bằng chứng chiếm ~190 MB (chủ yếu là clip) → có thể tắt clip khi cần tiết kiệm dung lượng.

## 6. Bổ sung tuần 5 (19/11/2026)
### 6.1 Ngưỡng tin cậy riêng cho INT8 (`baseline/tune_conf_fine.py`, `results/nguong_rieng.json`)
Dò 0,25–0,60 bước 0,05, chọn chỉ theo CAVIAR dev (nhiều lượt đúng → ít báo nhầm → ngưỡng thấp nhất).
- OpenVINO FP32: chọn 0,50 → dev 18/2, test 14/0, cửa hàng 43/2.
- OpenVINO INT8: chọn 0,55 → dev 18/3, test 13/0, cửa hàng 39/2. Lượt bị sót ở Walk2 chỉ được báo khi ngưỡng ≤ 0,45 (test 14/0) – không chọn vì như vậy là chọn theo tập test. Ở cùng ngưỡng 0,40, INT8 trên cửa hàng báo nhầm ít hơn FP32 (4 so với 7).
### 6.2 Ảnh đầu vào 416 (`models/ft_v1_*_416_openvino_model`, `results/bench_t4_416.json`, `baseline/results/so_sanh_416.json`)
| | mAP50 | mAP50–95 | 4 luồng: trung vị / p95 (ms) | CAVIAR test (không lọc) | Cửa hàng (không lọc / ngưỡng 0,5) |
|---|---|---|---|---|---|
| OpenVINO FP32 640 | 0,6041 | 0,3445 | 30,0 / 35,2 | 14/14, 0 nhầm | 53/39 · 43/2 |
| OpenVINO INT8 640 | 0,6028 | 0,3432 | 14,0 / 16,0 | 14/14, 1 nhầm | 56/39 · 43/3 |
| OpenVINO FP32 416 | 0,5514 | 0,3096 | 18,5 / 28,3 | 13/14, 1 nhầm | 49/15 · 22/3 |
| OpenVINO INT8 416 | 0,5495 | 0,3087 | **8,0 / 10,6** | 13/14, 2 nhầm | 49/21 · 24/3 |
- 416 nhanh hơn 640 khoảng 1,75 lần (INT8 8,0 ms ≈ 125 FPS) nhưng mAP50–95 giảm ~3,5 điểm %, bỏ sót thêm người nhỏ (CAVIAR test 13/14) và trên cửa hàng khi bật ngưỡng 0,5 chỉ còn 22–24/63 lượt đúng. **Giữ 640** vì 640 đã đủ thời gian thực (INT8 14 ms); 416 chỉ nên dùng nếu thiết bị biên yếu hơn nhiều.
