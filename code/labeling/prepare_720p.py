"""Chuyển video cửa hàng giày (2560x1440, HEVC) sang 1280x720 để tua tới/lui được khi gán nhãn.

Video HEVC gốc báo lỗi khi nhảy tới khung bất kỳ, nên ở đây đọc tuần tự rồi ghi lại bằng MJPG (.avi):
mỗi khung là một ảnh JPEG độc lập nên tua chính xác tới từng khung. Số thứ tự khung giữ nguyên như video gốc
(khung i ở bản 720p = khung i khi đọc tuần tự bản gốc), nên nhãn gán trên bản 720p dùng thẳng cho bản gốc.

Ví dụ: python prepare_720p.py
"""
import cv2, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "../../Videos/cua_hang_giay")
DST = os.path.join(SRC, "720p")
os.makedirs(DST, exist_ok=True)

for name in sys.argv[1:] or ["Video1", "Video2"]:
    cap = cv2.VideoCapture(os.path.join(SRC, f"{name}.mp4"))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    out_path = os.path.join(DST, f"{name}_720p.avi")
    wr = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*"MJPG"), fps, (1280, 720))
    wr.set(cv2.VIDEOWRITER_PROP_QUALITY, 80)
    n = 0
    while True:
        ok, im = cap.read()
        if not ok:
            break
        wr.write(cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA))
        n += 1
        if n % 1000 == 0:
            print(name, n, flush=True)
    wr.release()
    print(f"{name}: {n} khung -> {out_path}", flush=True)
