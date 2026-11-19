# Kết quả kiểm tra Human Dataset (05/11/2026)

Thư mục: `Claude/Dataset` (định dạng YOLO; script: `work/check_dataset.py`; ảnh mẫu: `work/grid_train.png`, `work/grid_val.png`)

| | train | val |
|---|---|---|
| Số ảnh | 13.754 | 4.000 |
| Số tệp nhãn | 13.754 | 4.000 |
| Ảnh thiếu nhãn / nhãn thiếu ảnh | 0 / 0 | 0 / 0 |
| Lớp | chỉ lớp 0 (person) | chỉ lớp 0 |
| Số khung bao | 56.669 | 16.377 |
| Số khung trên mỗi ảnh (trung vị / lớn nhất) | 2 / 291 | 2 / 171 |
| Dòng sai định dạng, tọa độ ngoài [0, 1] | 0 | 0 |
| Khung có chiều cao < 10% ảnh | 13.973 (24,7%) | 4.126 (25,2%) |
| Khung chạm cạnh dưới ảnh (có thể bị cắt chân) | 15,1% | 15,0% |
| Khung chiếm > 50% diện tích ảnh | 4,4% | 4,5% |

Tổng cộng 17.754 ảnh, khác một chút so với con số 17.300 ghi trong mô tả trên Kaggle và trong bài báo năm 2025.

## Đã sắp xếp lại (05/11/2026, script `work/split_dataset.py`, seed 42)
- Chuyển 111 ảnh val trùng với train sang `Dataset/_removed/val_duplicates_of_train` (không xóa).
- Chia ngẫu nhiên phần val còn lại thành **val 1.944 ảnh** và **test 1.945 ảnh**; giữ nguyên **train 13.754 ảnh**. Tổng 17.643 ảnh, tỷ lệ khoảng 78/11/11.
- Đã kiểm tra lại: mỗi ảnh đều có tệp nhãn tương ứng, không còn ảnh trùng giữa các tập.
- Cấu hình cho Ultralytics nằm ở `Dataset/data.yaml`. Mọi lần di chuyển tệp được ghi trong `Dataset/moves.csv`.

## Vấn đề cần xử lý
1. **111 ảnh trùng hoàn toàn giữa train và val** (trùng mã MD5). Cần loại 111 ảnh này khỏi val để tránh rò rỉ dữ liệu.
2. **Chưa có tập test riêng.** Cần tách thêm tập test, ví dụ lấy một nửa val, để có tỷ lệ 70/15/15.
3. **Nhãn kiểu Open Images:** có các khung bao trùm cả một nhóm người (khán giả, đám đông), có nhãn cho người trong tranh vẽ, búp bê, tượng, nhân vật game, và nhiều ảnh chân dung cận cảnh hoặc chỉ thấy một phần cơ thể.
   - Ảnh hưởng đến đồ án: mô hình vẫn học được việc phát hiện người, nhưng các khung không bao toàn thân sẽ làm vị trí "điểm chân" kém chính xác. Vì vậy cần bổ sung ảnh hoặc video đúng bối cảnh camera giám sát, và đánh giá cảnh báo bằng video chứ không chỉ bằng mAP.
   - Hướng xử lý có thể làm: loại bớt ảnh có khung > 50% diện tích (thường là ảnh cận cảnh) khỏi tập hiệu chuẩn INT8, để tập hiệu chuẩn giống ảnh camera giám sát hơn.
