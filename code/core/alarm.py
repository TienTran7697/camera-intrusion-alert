"""Logic cảnh báo xâm nhập vùng cấm (dùng chung cho ứng dụng và đánh giá).

Quy tắc:
- Điểm đại diện của người: trung điểm cạnh dưới khung bao p = ((x1 + x2) / 2, y2).
- Mỗi ID bắt đầu ở trạng thái "out".
- out -> in: điểm chân trong vùng liên tục >= confirm_frames khung -> phát CẢNH BÁO (một lần cho lượt vào này).
- in -> out: điểm chân ngoài vùng liên tục >= confirm_frames khung -> kết thúc lượt, cho phép lượt mới.
- Khung hình mà ID bị mất dấu không làm thay đổi bộ đếm (giữ trạng thái), tránh báo lặp khi mất dấu ngắn.
- Thời gian tính theo số thứ tự khung hình của video, không theo đồng hồ hệ thống.

Bộ lọc giảm báo nhầm (tuần 3, mặc định TẮT để giữ nguyên kết quả mốc):
- min_conf: khung có độ tin cậy thấp hơn ngưỡng này không được tính là "đang trong vùng" (coi như mất dấu).
- min_age: ID phải xuất hiện ít nhất min_age khung (kể từ lần đầu thấy) mới được phép cảnh báo.
- born_outside: chỉ cảnh báo ID được thấy lần đầu ở NGOÀI vùng (người thật đi từ ngoài vào); ID "sinh ra" ngay
  trong vùng (vật thể bị nhận nhầm là người, hoặc người bị đổi ID khi đang đứng trong vùng) bị bỏ qua,
  trừ khi ID xuất hiện từ những khung đầu video (khung < start_grace).
- min_move: điểm chân phải dịch chuyển tổng cộng ít nhất min_move lần chiều cao khung (tính từ lần đầu thấy)
  -> loại vật đứng yên bị nhận nhầm là người.
"""
from dataclasses import dataclass, field
import cv2
import numpy as np


def foot_point(x1, y1, x2, y2):
    return ((x1 + x2) / 2.0, float(y2))


@dataclass
class _TrackState:
    state: str = "out"
    run_in: int = 0
    run_out: int = 0
    enter_start: int = -1
    first_frame: int = -1
    born_inside: bool = False
    first_foot: tuple = None
    max_disp: float = 0.0


@dataclass
class ZoneAlarm:
    polygon: list
    confirm_frames: int = 8
    min_conf: float = 0.0
    min_age: int = 0
    born_outside: bool = False
    min_move: float = 0.0
    start_grace: int = 5
    tracks: dict = field(default_factory=dict)

    def __post_init__(self):
        self._poly = np.array(self.polygon, np.float32)

    def inside(self, pt):
        return cv2.pointPolygonTest(self._poly, (float(pt[0]), float(pt[1])), False) >= 0

    def update(self, frame_idx, detections):
        """detections: list of (track_id, x1, y1, x2, y2, conf). Trả về danh sách sự kiện mới trong khung này."""
        events = []
        for tid, x1, y1, x2, y2, conf in detections:
            st = self.tracks.setdefault(int(tid), _TrackState())
            p = foot_point(x1, y1, x2, y2)
            if conf < self.min_conf:
                continue                                   # coi như mất dấu ở khung này
            if st.first_frame < 0:
                st.first_frame, st.first_foot = frame_idx, p
                st.born_inside = self.inside(p) and frame_idx >= self.start_grace
            h = max(1.0, y2 - y1)
            st.max_disp = max(st.max_disp, ((p[0] - st.first_foot[0]) ** 2 + (p[1] - st.first_foot[1]) ** 2) ** 0.5 / h)
            if self.inside(p):
                st.run_in += 1; st.run_out = 0
                if st.run_in == 1:
                    st.enter_start = frame_idx
                ok = (frame_idx - st.first_frame + 1 >= self.min_age
                      and not (self.born_outside and st.born_inside)
                      and st.max_disp >= self.min_move)
                if st.state == "out" and st.run_in >= self.confirm_frames and ok:
                    st.state = "in"
                    events.append({"type": "alert", "track_id": int(tid), "frame": frame_idx,
                                   "enter_frame": st.enter_start, "foot": p, "bbox": (x1, y1, x2, y2), "conf": conf})
            else:
                st.run_out += 1; st.run_in = 0
                if st.state == "in" and st.run_out >= self.confirm_frames:
                    st.state = "out"
                    events.append({"type": "exit", "track_id": int(tid), "frame": frame_idx})
        return events

    def is_alerting(self, tid):
        st = self.tracks.get(int(tid))
        return st is not None and st.state == "in"
