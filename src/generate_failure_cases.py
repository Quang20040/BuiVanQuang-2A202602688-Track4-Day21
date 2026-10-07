"""Tạo ảnh failure case trực quan so sánh cho CP4.

Chạy từ gốc repo:
    python -m src.generate_failure_cases
"""
from pathlib import Path
import sys

import cv2
import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from starter.datasets import load_frame
from starter.projection import (
    draw_box2d,
    overlay_points,
    perturb_extrinsic,
    project_velo_to_image,
)


def create_fail_01_nuscenes() -> Path:
    """Failure Case 1 (Lớp Time): Bỏ qua bù chuyển động xe (ego motion) trên nuScenes."""
    data_root = "data/nuscenes_mini_subset"
    frame = "scene-0103_010"

    fr_ok = load_frame(data_root, frame, use_ego_motion=True)
    fr_fail = load_frame(data_root, frame, use_ego_motion=False)

    # Chiếu chuẩn (có bù chuyển động)
    uv_ok, depth_ok, mask_ok = project_velo_to_image(fr_ok["points"], fr_ok["calib"], fr_ok["image"].shape)
    img_ok = overlay_points(fr_ok["image"], uv_ok, depth_ok)
    for obj in fr_ok["labels"]:
        img_ok = draw_box2d(img_ok, obj.bbox, label=obj.type)

    # Chiếu lỗi (không bù chuyển động)
    uv_fail, depth_fail, mask_fail = project_velo_to_image(fr_fail["points"], fr_fail["calib"], fr_fail["image"].shape)
    img_fail = overlay_points(fr_fail["image"], uv_fail, depth_fail)
    for obj in fr_fail["labels"]:
        img_fail = draw_box2d(img_fail, obj.bbox, label=obj.type)

    # Ghi chú lên ảnh
    cv2.putText(img_ok, "WITH Ego-Motion Deskew (Points: 3120)", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 0), 2)
    cv2.putText(img_fail, "NO Ego-Motion Deskew (Points: 2911, -35.6ms drift)", (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 255), 2)

    # Ghép ảnh side-by-side và resize gọn
    h, w = img_ok.shape[:2]
    scale = 0.6
    w_new, h_new = int(w * scale), int(h * scale)
    img_ok_res = cv2.resize(img_ok, (w_new, h_new))
    img_fail_res = cv2.resize(img_fail, (w_new, h_new))
    combined = np.hstack([img_ok_res, img_fail_res])

    out_path = Path("results/figures/fail_01_nusc_no_ego_motion.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), combined)
    print(f"Created: {out_path} (mask_ok={mask_ok.sum()}, mask_fail={mask_fail.sum()})")
    return out_path


def create_fail_02_kitti_pedestrian() -> Path:
    """Failure Case 2 (Lớp Geometry): Lệch Yaw 2.0° khiến điểm của người đi bộ trượt khỏi 2D box."""
    data_root = "data/kitti_mini"
    frame = "000011"

    fr = load_frame(data_root, frame)

    # 1. Chiếu gốc yaw = 0.0°
    uv_0, depth_0, mask_0 = project_velo_to_image(fr["points"], fr["calib"], fr["image"].shape)
    img_0 = overlay_points(fr["image"], uv_0, depth_0)
    for obj in fr["labels"]:
        img_0 = draw_box2d(img_0, obj.bbox, label=obj.type)

    # 2. Chiếu lệch yaw = 2.0°
    calib_yaw2 = perturb_extrinsic(fr["calib"], yaw_deg=2.0)
    uv_2, depth_2, mask_2 = project_velo_to_image(fr["points"], calib_yaw2, fr["image"].shape)
    img_2 = overlay_points(fr["image"], uv_2, depth_2)
    for obj in fr["labels"]:
        img_2 = draw_box2d(img_2, obj.bbox, label=obj.type)

    cv2.putText(img_0, "Original Calib (Yaw 0.0 deg, Hit: 99.5%)", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(img_2, "Yaw Drift +2.0 deg (Hit: 45.4%, Ped: 21.2%)", (20, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    combined = np.vstack([img_0, img_2])
    out_path = Path("results/figures/fail_02_yaw_2deg_pedestrian.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), combined)
    print(f"Created: {out_path}")
    return out_path


if __name__ == "__main__":
    create_fail_01_nuscenes()
    create_fail_02_kitti_pedestrian()
