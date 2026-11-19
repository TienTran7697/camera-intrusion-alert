"""Đo tốc độ suy luận có kiểm soát trên CPU: PyTorch FP32, OpenVINO FP32, OpenVINO INT8.

Điều kiện giống nhau cho mọi mô hình: cùng 300 khung hình (150 khung CAVIAR test + 150 khung cửa hàng giày,
nạp sẵn vào RAM), batch 1, ảnh 640, chạy khởi động 30 lần trước khi đo, mỗi mô hình chạy trong một tiến trình
riêng (đo RAM độc lập), cùng số luồng CPU.
Đo 2 mức:
  - "core": chỉ phần mô hình (tensor 1x3x640x640 đã tiền xử lý) -> so sánh thuần FP32 / INT8.
  - "e2e" : Ultralytics predict trên ảnh gốc (tiền xử lý + mô hình + NMS) -> gần với thời gian thật của hệ thống.
python bench.py --all --threads 0      (0 = để thư viện tự chọn số luồng; 4 = mô phỏng thiết bị biên 4 nhân)
Kết quả: code/optimize/results/bench_t<threads>.json
"""
import argparse, json, os, subprocess, sys, time, glob
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(HERE, "../models")
MODELS = {"pytorch_fp32": f"{M}/ft_v1.pt", "openvino_fp32": f"{M}/ft_v1_fp32_openvino_model",
          "openvino_int8": f"{M}/ft_v1_int8_c300_openvino_model"}
WARM, N = 30, 300
IMGSZ = int(os.environ.get("IMGSZ", 640))
if IMGSZ != 640:
    MODELS = {"openvino_fp32": f"{M}/ft_v1_fp32_{IMGSZ}_openvino_model", "openvino_int8": f"{M}/ft_v1_int8_c300_{IMGSZ}_openvino_model"}


def load_frames():
    cav = os.path.join(HERE, "../../Videos/CAVIAR"); shop = os.path.join(HERE, "../../Videos/cua_hang_giay")
    split = json.load(open(f"{cav}/split.json"))["test"]; out = []
    for v in split:                                       # 30 khung mỗi video CAVIAR test
        cap = cv2.VideoCapture(f"{cav}/{v}/{v}.mpg"); n = int(cap.get(7)); keep = set(np.linspace(0, n - 1, 30).astype(int))
        for f in range(n):
            ok, im = cap.read()
            if not ok: break
            if f in keep: out.append(im)
    cap = cv2.VideoCapture(f"{shop}/Video2.mp4"); keep = set(range(0, 150 * 60, 60))   # 150 khung, mỗi 2,4 s
    for f in range(150 * 60):
        ok, im = cap.read()
        if not ok: break
        if f in keep: out.append(cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA))
    return out


def letterbox(im, s=640):
    h, w = im.shape[:2]; r = min(s / h, s / w); nh, nw = round(h * r), round(w * r)
    c = np.full((s, s, 3), 114, np.uint8); t, l = (s - nh) // 2, (s - nw) // 2
    c[t:t + nh, l:l + nw] = cv2.resize(im, (nw, nh), interpolation=cv2.INTER_LINEAR)
    return np.ascontiguousarray(c[:, :, ::-1].transpose(2, 0, 1)[None], dtype=np.float32) / 255.0


def stats(ts):
    ts = np.array(ts) * 1000
    return {"median_ms": round(float(np.median(ts)), 2), "p95_ms": round(float(np.percentile(ts, 95)), 2),
            "mean_ms": round(float(ts.mean()), 2), "fps_median": round(1000 / float(np.median(ts)), 1)}


def run_one(name, threads):
    import psutil
    proc = psutil.Process(); rss0 = proc.memory_info().rss
    frames = load_frames(); tensors = [letterbox(f, IMGSZ) for f in frames]
    path = MODELS[name]; res = {"model": name, "path": os.path.relpath(path, HERE), "threads": threads, "n_frames": len(frames)}
    if os.path.isdir(path):
        res["size_mb"] = round(sum(os.path.getsize(p) for p in glob.glob(f"{path}/*.bin") + glob.glob(f"{path}/*.xml")) / 2**20, 2)
    else:
        res["size_mb"] = round(os.path.getsize(path) / 2**20, 2)
    rss_frames = proc.memory_info().rss
    # ---- core
    if name.startswith("openvino"):
        import openvino as ov
        core = ov.Core(); cfg = {"PERFORMANCE_HINT": "LATENCY"}
        if threads: cfg["INFERENCE_NUM_THREADS"] = threads
        cm = core.compile_model(core.read_model(glob.glob(f"{path}/*.xml")[0]), "CPU", cfg)
        req = cm.create_infer_request(); fwd = lambda x: req.infer({0: x})
    else:
        import torch
        if threads: torch.set_num_threads(threads)
        from ultralytics import YOLO
        net = YOLO(path).model.fuse().float().eval()   # gộp Conv+BN giống khi Ultralytics suy luận
        def fwd(x):
            with torch.inference_mode(): return net(torch.from_numpy(x))
    for i in range(WARM): fwd(tensors[i % len(tensors)])
    ts = []
    for x in tensors[:N]:
        t0 = time.perf_counter(); fwd(x); ts.append(time.perf_counter() - t0)
    res["core"] = stats(ts)
    res["ram_model_mb"] = round((proc.memory_info().rss - rss_frames) / 2**20, 1)
    # ---- e2e (Ultralytics)
    if threads and not name.startswith("openvino"):
        import torch; torch.set_num_threads(threads)
    from ultralytics import YOLO
    m = YOLO(path, task="detect")
    for i in range(WARM): m.predict(frames[i % len(frames)], classes=[0], conf=0.25, imgsz=IMGSZ, device="cpu", verbose=False)
    ts = []
    for f in frames[:N]:
        t0 = time.perf_counter(); m.predict(f, classes=[0], conf=0.25, imgsz=IMGSZ, device="cpu", verbose=False); ts.append(time.perf_counter() - t0)
    res["e2e"] = stats(ts)
    res["ram_peak_process_mb"] = round(proc.memory_info().rss / 2**20, 1)
    return res


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--model"); ap.add_argument("--all", action="store_true"); ap.add_argument("--threads", type=int, default=0)
    a = ap.parse_args()
    if a.all:
        out = []
        for name in MODELS:
            r = subprocess.run([sys.executable, __file__, "--model", name, "--threads", str(a.threads)], capture_output=True, text=True)
            line = [l for l in r.stdout.splitlines() if l.startswith("{")]
            if not line: print(r.stderr[-2000:]); sys.exit(1)
            out.append(json.loads(line[-1])); print(out[-1], flush=True)
        os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
        json.dump(out, open(os.path.join(HERE, "results", f"bench_t{a.threads}" + (f"_{IMGSZ}" if IMGSZ != 640 else "") + ".json"), "w"), indent=1)
    else:
        os.environ.setdefault("OMP_NUM_THREADS", str(a.threads) if a.threads else os.environ.get("OMP_NUM_THREADS", ""))
        print(json.dumps(run_one(a.model, a.threads)))
