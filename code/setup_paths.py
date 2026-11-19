# -*- coding: utf-8 -*-
"""Chạy MỘT LẦN sau khi tải repo về máy: ghi đường dẫn tuyệt đối của thư mục Dataset trên máy bạn
vào Dataset/data.yaml và Dataset/data_ft.yaml (Ultralytics cần đường dẫn này để tìm ảnh).
python code/setup_paths.py
"""
import os, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # in tiếng Việt được trên mọi cửa sổ lệnh

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DS = os.path.join(ROOT, "Dataset").replace(os.sep, "/")
for name in ("data.yaml", "data_ft.yaml"):
    p = os.path.join(ROOT, "Dataset", name)
    s = open(p, encoding="utf-8").read()
    s2 = re.sub(r"(?m)^path:.*$", f"path: {DS}", s, count=1)
    open(p, "w", encoding="utf-8").write(s2)
    print(f"{name}: path = {DS}")
for sub in ("images/train", "images/val", "images/test"):
    ok = os.path.isdir(os.path.join(ROOT, "Dataset", sub))
    print(f"  Dataset/{sub}: {'có' if ok else 'CHƯA CÓ – xem mục B1 trong README (chỉ cần khi huấn luyện / đánh giá trên ảnh)'}")
