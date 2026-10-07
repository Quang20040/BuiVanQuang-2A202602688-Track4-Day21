"""Vẽ kết quả quét góc lệch yaw (Topic A).

Chạy từ gốc repo:
    python -m src.plot_yaw_sweep
"""
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import pandas as pd

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Calibri"]
plt.rcParams["axes.unicode_minus"] = False

csv_path = Path("results/yaw_perturb_sweep.csv")
if not csv_path.exists():
    raise FileNotFoundError(f"Không tìm thấy {csv_path}. Hãy chạy src.exp_yaw_sweep trước.")

df = pd.read_csv(csv_path, dtype={"frame": str})

frame_labels = {
    "000008": "Frame 000008 (Đông xe ô tô)",
    "000011": "Frame 000011 (Nhiều người đi bộ)",
    "000049": "Frame 000049 (Nhiều vật bị che khuất)",
}

fig, ax = plt.subplots(figsize=(7, 4.8), dpi=150)

colors = {"000008": "#1f77b4", "000011": "#d62728", "000049": "#2ca02c"}
markers = {"000008": "s", "000011": "o", "000049": "^"}

for frame, g in df.groupby("frame"):
    label = frame_labels.get(frame, f"Frame {frame}")
    color = colors.get(frame, None)
    marker = markers.get(frame, "o")
    ax.plot(
        g["yaw_deg"],
        100 * g["hit_ratio"],
        marker=marker,
        linewidth=2,
        markersize=6,
        color=color,
        label=label,
    )

# Ngưỡng cảnh báo 80% (Advanced Topic A)
ax.axhline(80, color="gray", linestyle="--", alpha=0.7, label="Ngưỡng cảnh báo (80%)")

ax.set_title("Ảnh hưởng của góc lệch Yaw tới tỉ lệ điểm trong 2D Box", fontsize=12, fontweight="bold")
ax.set_xlabel("Góc lệch Yaw (độ)", fontsize=10)
ax.set_ylabel("Tỉ lệ điểm LiDAR rơi đúng vào 2D box (%)", fontsize=10)
ax.set_ylim(0, 105)
ax.set_xlim(-0.1, 3.1)
ax.grid(True, linestyle="--", alpha=0.5)
ax.legend(loc="lower left", framealpha=0.9)
fig.tight_layout()

out = Path("results/figures/yaw_sweep.png")
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=150)
print(f"-> {out}")
