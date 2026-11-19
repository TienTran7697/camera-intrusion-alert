# -*- coding: utf-8 -*-
"""Tải 10 video CAVIAR (Đại học Edinburgh, CC BY-SA) vào Videos/CAVIAR/<tên>/<tên>.mpg.
Nhãn gốc (*gt.xml), vùng cấm và nhãn sự kiện đã có sẵn trong repo; script chỉ tải video (~100 MB).
Video đã có thì bỏ qua. Chạy từ thư mục gốc repo:  python code/download_data.py
"""
import os, sys, urllib.request

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BASE = "https://homepages.inf.ed.ac.uk/rbf/CAVIARDATA1"
CLIPS = {"Walk1": "wk1gt.xml", "Walk2": "wk2gt.xml", "Walk3": "wk3gt.xml",
         "Browse1": "br1gt.xml", "Browse2": "br2gt.xml", "Browse3": "br3gt.xml", "Browse4": "br4gt.xml",
         "Meet_WalkTogether1": "mwt1gt.xml", "Meet_WalkSplit": "mws1gt.xml", "Meet_Crowd": "mc1gt.xml"}


def get(url, dst):
    if os.path.exists(dst) and os.path.getsize(dst) > 0:
        print("  đã có   ", os.path.relpath(dst, ROOT)); return
    os.makedirs(os.path.dirname(dst), exist_ok=True); tmp = dst + ".part"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (camera-intrusion-alert)"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b: break
            f.write(b)
    os.replace(tmp, dst); print(f"  đã tải   {os.path.relpath(dst, ROOT)} ({os.path.getsize(dst) / 1e6:.1f} MB)")


if __name__ == "__main__":
    print("Tải video CAVIAR từ", BASE)
    for clip, gt in CLIPS.items():
        d = os.path.join(ROOT, "Videos", "CAVIAR", clip)
        get(f"{BASE}/{clip}/{clip}.mpg", os.path.join(d, f"{clip}.mpg"))
        get(f"{BASE}/{clip}/{gt}", os.path.join(d, gt))
    print("Xong. Human Dataset (ảnh) cần tải tay từ Kaggle – xem mục B1 trong README.")
