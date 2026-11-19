# Hướng dẫn gán nhãn vào/ra vùng cấm – video cửa hàng giày

Mục tiêu: tạo nhãn chuẩn `events_gt.csv` cho Video1 và Video2, hai vùng **Z1** (bục trưng bày bên trái) và **Z3** (lối đi giữa). Nhãn này dùng để chấm điểm hệ thống (đúng, bỏ sót, báo nhầm, độ trễ), so sánh FP32 với INT8. Vì vậy nhãn phải do người xem video, **không** chép từ kết quả của mô hình.

## 1. Chuẩn bị (chỉ làm một lần)
Mở PowerShell trong thư mục `Claude/code/labeling`, chạy:
```
python prepare_720p.py
```
Lệnh này tạo `Videos/cua_hang_giay/720p/Video1_720p.avi` và `Video2_720p.avi`. Video gốc HEVC không tua được, nên phải có bản này. Số thứ tự khung giữ nguyên như video gốc.

## 2. Chạy công cụ
```
python label_tool.py --video Video1
```
Làm xong Video1 thì chạy lại với `--video Video2`. Nhãn của cả hai video nằm chung trong `Videos/cua_hang_giay/events_gt.csv` và được **lưu ngay sau mỗi thao tác**. Có thể tắt giữa chừng, lần sau mở lại sẽ làm tiếp.

Lưu ý: **tắt bộ gõ tiếng Việt (Unikey/EVKey)** trước khi bấm phím, và bấm khi cửa sổ video đang được chọn.

## 3. Quy ước gán nhãn
- Chỉ xét **điểm chân** (giữa hai bàn chân), không xét thân người hay tay.
- **VÀO** là khung đầu tiên điểm chân nằm trong vùng. **RA** là khung đầu tiên điểm chân đã ra khỏi vùng.
- Mỗi người, mỗi lần vào là **một dòng**. Ra hẳn rồi vào lại thì gán lượt mới.
- Người chỉ chạm mép vùng trong chớp mắt, chưa tới khoảng 0,3 giây (8 khung), thì vẫn gán, nhưng bấm **M** để ghi chú `sat_mep`.
- Bị che khuất (giá treo, người khác đứng trước), phải đoán vị trí chân: vẫn gán, bấm **N** để ghi chú `khuat`.
- Người đã ở trong vùng từ đầu video: bấm VÀO ở khung 0, công cụ tự ghi `start_inside=1`.
- Hết video mà người vẫn còn trong vùng: để trống RA.
- Z1 là **bục trưng bày**: chỉ tính khi chân đặt **lên** bục, hoặc khi người ngồi lên bục. Đứng sát mép bục nhưng chân vẫn ở trên sàn thì **không** tính.
- Không bật gợi ý mô hình (phím **H**) khi gán nhãn lần đầu. Chỉ bật để kiểm tra lại sau khi đã gán xong.

## 4. Cách làm nhanh
1. Bấm **1** chọn Z1 (hoặc **2** chọn Z3). Bấm **Space** để phát, có thể bấm **]** cho phát nhanh x2, x4.
2. Thấy có người sắp vào vùng thì bấm **Space** dừng. Dùng **←/→** lùi/tới từng khung để tìm đúng khung chân vừa vào vùng.
3. (Nên làm) **click vào chân người đó** trên hình, rồi bấm **E**. Một lượt mới được tạo, ví dụ `P5`, và vòng vàng sẽ đánh dấu người này trong suốt thời gian ở trong vùng.
4. Phát tiếp. Khi người đó ra khỏi vùng, dừng lại, tìm đúng khung, bấm **X**. Nếu đang có nhiều người trong vùng, bấm **Tab** để chuyển dấu `>` tới đúng người trước khi bấm **X**.
5. Gán sai thì bấm **U** để hoàn tác, hoặc **Backspace** để xóa lượt đang chọn.

Nên làm từng vùng một: xem hết video cho Z1, rồi tua lại từ đầu làm Z3. Z3 đông người hơn, có thể chia đôi video cho hai người làm.

## 5. Bảng phím tắt
| Phím | Chức năng | Phím | Chức năng |
|---|---|---|---|
| Space | Phát / tạm dừng | ← / → | Lùi / tới 1 khung |
| ↑ / ↓ | Tới / lùi 1 giây | J / L | Lùi / tới 5 giây |
| [ / ] | Giảm / tăng tốc độ | Click thanh dưới | Nhảy tới thời điểm đó |
| 1 / 2 | Chọn Z1 / Z3 | Click vào hình | Đánh dấu điểm chân |
| E | Gán VÀO | X | Gán RA cho lượt đang chọn |
| Tab | Chọn lượt khác | G | Nhảy tới lúc VÀO của lượt đang chọn |
| M | Ghi chú `sat_mep` | N | Ghi chú `khuat` |
| Backspace | Xóa lượt đang chọn | U | Hoàn tác |
| H | Bật/tắt gợi ý mô hình | Q / Esc | Lưu và thoát |

## 6. Kiểm tra chéo (nên có)
Người thứ hai mở lại công cụ, bấm **G** trên từng lượt để xem nhanh, sửa nếu thấy sai lệch quá khoảng 0,5 giây. Có thể ghi vào báo cáo: "nhãn do một thành viên gán, một thành viên khác kiểm tra lại".

## 7. Tệp kết quả `events_gt.csv`
`video, zone_id, track_id, enter_frame, enter_time_s, exit_frame, exit_time_s, start_inside, verified, note, foot_x, foot_y`
Các cột giống nhãn CAVIAR, thêm `foot_x, foot_y` là tọa độ điểm chân đã click, theo video gốc 2560×1440. Thời gian tính theo khung hình, 25 FPS.
