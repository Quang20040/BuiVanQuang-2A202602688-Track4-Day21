"""Bonus [B4]: Tool kiểm tra chất lượng cân chỉnh (Calibration QA Tool) tái sử dụng được.

CLI Tool nhận frame và ngưỡng đánh giá, tự động kiểm tra xem điểm LiDAR của vật thể
có bị trượt khỏi 2D Bounding Box (do va chạm, lệch bracket) hay không.

Chạy thử:
    python -m src.calibration_qa --help
    python -m src.calibration_qa --data-root data/kitti_mini --frame 000011 --threshold 0.80
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from src.exp_yaw_sweep import run_one
from starter.datasets import load_frame


def main() -> int:
    parser = argparse.ArgumentParser(
        description="LiDAR-Camera Calibration QA Automated Tool - Kiểm tra độ lệch calibration từ dữ liệu",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--data-root", default="data/kitti_mini", help="Thư mục chứa dữ liệu KITTI/nuScenes")
    parser.add_argument("--frame", default="000011", help="ID của frame cần kiểm tra chất lượng")
    parser.add_argument("--threshold", type=float, default=0.80, help="Ngưỡng hit_ratio tối thiểu để PASS (0.0 - 1.0)")
    parser.add_argument("--sim-yaw", type=float, default=0.0, help="Giả lập góc lệch yaw thêm vào để kiểm tra (độ)")
    args = parser.parse_args()

    print(f"=== LiDAR-Camera Calibration QA Tool ===")
    print(f"Dataset: {args.data_root} | Frame: {args.frame} | Ngưỡng yêu cầu: {args.threshold:.1%}")
    if args.sim_yaw != 0.0:
        print(f"Giả lập thêm lệch yaw: {args.sim_yaw:+.2f}°")

    fr = load_frame(args.data_root, args.frame)
    res = run_one(fr, yaw_deg=args.sim_yaw)

    hit_ratio = res["hit_ratio"]
    ped_ratio = res["ped_hit_ratio"]
    car_ratio = res["car_hit_ratio"]

    print(f"\nKết quả đo đạc:")
    print(f"- Tổng số điểm LiDAR hợp lệ: {res['n_points']}")
    print(f"- Số điểm lọt vào khung hình camera: {res['inside_image']}")
    print(f"- Số điểm nằm trên các vật thể được gán nhãn: {res['object_points']}")
    print(f"- Tỉ lệ điểm rơi đúng vào 2D box (hit_ratio): {hit_ratio:.2%}")
    if not (ped_ratio != ped_ratio):  # not nan
        print(f"  + Người đi bộ (Pedestrian): {ped_ratio:.2%}")
    if not (car_ratio != car_ratio):
        print(f"  + Xe ô tô (Car/Van): {car_ratio:.2%}")

    if hit_ratio >= args.threshold:
        print(f"\n[PASS] Calibration ĐẠT CHUẨN (hit_ratio {hit_ratio:.2%} >= {args.threshold:.2%}).")
        return 0
    elif hit_ratio >= args.threshold - 0.15:
        print(f"\n[WARN] CẢNH BÁO: Calibration có dấu hiệu trôi lệch (hit_ratio {hit_ratio:.2%} < {args.threshold:.2%}).")
        print("Khuyến nghị: Tiến hành re-calibration tự động hoặc kiểm tra giá đỡ cảm biến.")
        return 1
    else:
        print(f"\n[FAIL] NGUY HIỂM: Calibration bị lệch nghiêm trọng (hit_ratio {hit_ratio:.2%} << {args.threshold:.2%})!")
        print("Khuyến nghị: Cảm biến có thể vừa va chạm hoặc bracket biến dạng. Dừng tính năng sensor fusion.")
        return 2


if __name__ == "__main__":
    sys.exit(main())
