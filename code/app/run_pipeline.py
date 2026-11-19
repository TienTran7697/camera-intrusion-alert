"""Chạy hệ thống hoàn chỉnh trên một hoặc nhiều video, lưu bằng chứng vào SQLite.

Ví dụ:
  python run_pipeline.py --videos ../../Videos/CAVIAR/Walk2/Walk2.mpg --model int8 --out ../../outputs/demo --save-video
  python run_pipeline.py --videos ../../Videos/cua_hang_giay/Video2.mp4 --model int8 --min-conf 0.5
  python run_pipeline.py --export ../../outputs/demo/events.db       # xuất bảng events ra CSV
--model: pt | fp32 | int8 | <đường dẫn mô hình>
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from core.pipeline import run_video
from core.evidence import export_csv

M = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../models")
ALIAS = {"pt": f"{M}/ft_v1.pt", "fp32": f"{M}/ft_v1_fp32_openvino_model", "int8": f"{M}/ft_v1_int8_c300_openvino_model"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--videos", nargs="*"); ap.add_argument("--model", default="int8")
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../outputs/demo"))
    ap.add_argument("--min-conf", type=float, default=0.5); ap.add_argument("--clip", type=float, default=3.0)
    ap.add_argument("--no-evidence", action="store_true"); ap.add_argument("--save-video", action="store_true")
    ap.add_argument("--max-frames", type=int); ap.add_argument("--export")
    a = ap.parse_args()
    if a.export:
        out = os.path.splitext(a.export)[0] + ".csv"; print(export_csv(a.export, out), "dong ->", out); sys.exit()
    model = ALIAS.get(a.model, a.model)
    for v in a.videos:
        r = run_video(v, model, a.out, filters={"min_conf": a.min_conf} if a.min_conf else None, clip_seconds=a.clip,
                      evidence=not a.no_evidence, save_video=a.save_video, max_frames=a.max_frames)
        print(json.dumps(r, ensure_ascii=False), flush=True)
