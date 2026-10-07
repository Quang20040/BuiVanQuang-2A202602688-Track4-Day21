"""Bonus [B3]: Đo latency của pipeline projection đúng phương pháp khoa học.

Chạy từ gốc repo:
    python -m src.benchmark_latency
"""
from pathlib import Path
import platform
import sys
import time

import numpy as np
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from starter.datasets import load_frame
from starter.projection import project_velo_to_image


def main() -> None:
    data_root = "data/kitti_mini"
    frame_id = "000011"
    fr = load_frame(data_root, frame_id)
    points = fr["points"]
    calib = fr["calib"]
    shape = fr["image"].shape

    runs = 25
    latencies_s = []

    print(f"Bắt đầu đo latency trên frame {frame_id} ({len(points)} điểm, image {shape})...")

    for i in range(runs):
        t0 = time.perf_counter()
        uv, depth, mask = project_velo_to_image(points, calib, shape)
        t1 = time.perf_counter()
        latencies_s.append(t1 - t0)

    # Bỏ lần chạy đầu (warm-up)
    warmup_s = latencies_s[0]
    valid_latencies_ms = np.array(latencies_s[1:]) * 1000

    p50 = float(np.percentile(valid_latencies_ms, 50))
    p95 = float(np.percentile(valid_latencies_ms, 95))
    mean = float(np.mean(valid_latencies_ms))
    min_val = float(np.min(valid_latencies_ms))

    print(f"Warm-up run: {warmup_s * 1000:.2f} ms")
    print(f"Kết quả (24 runs): p50 = {p50:.2f} ms, p95 = {p95:.2f} ms, mean = {mean:.2f} ms, min = {min_val:.2f} ms")

    rows = []
    for i, dur_ms in enumerate(valid_latencies_ms, start=1):
        rows.append({
            "run_index": i,
            "latency_ms": round(dur_ms, 3),
            "cpu": "AMD Ryzen 7 5800H",
            "ram_gb": 16,
            "os": platform.system() + " " + platform.release(),
        })

    df = pd.DataFrame(rows)
    out = Path("results/latency_benchmark.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"-> Đã lưu bảng đo latency tại: {out}")


if __name__ == "__main__":
    main()
