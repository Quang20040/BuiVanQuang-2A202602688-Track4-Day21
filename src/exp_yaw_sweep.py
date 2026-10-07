"""Topic A: Quét góc lệch yaw, đo % điểm LiDAR của vật thể rơi đúng vào 2D box.

Chạy từ gốc repo:
    python -m src.exp_yaw_sweep --data-root data/kitti_mini --frames 000008 000011 000049
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from starter.datasets import load_frame
from starter.projection import perturb_extrinsic, project_velo_to_image, velo_to_cam

CLASSES = ("Car", "Van", "Pedestrian", "Cyclist")


def points_in_box(points_cam: np.ndarray, obj) -> np.ndarray:
    """Mask (N,) các điểm (đã ở camera frame) nằm trong 3D box của label."""
    h, w, l = obj.dimensions
    c, s = np.cos(obj.rotation_y), np.sin(obj.rotation_y)
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    local = (points_cam - obj.location) @ R  # toạ độ trong hệ trục gắn với box
    return (
        (np.abs(local[:, 0]) <= l / 2)
        & (local[:, 1] <= 0)
        & (local[:, 1] >= -h)
        & (np.abs(local[:, 2]) <= w / 2)
    )


def run_one(fr: dict, yaw_deg: float) -> dict:
    pts = fr["points"][np.isfinite(fr["points"]).all(axis=1)]
    cam_true = velo_to_cam(pts[:, :3], fr["calib"])  # vị trí thật theo calib gốc
    calib = perturb_extrinsic(fr["calib"], yaw_deg=yaw_deg)  # calib đã bị lệch
    uv, _, mask = project_velo_to_image(pts, calib, fr["image"].shape)
    uv_all = np.full((len(pts), 2), np.nan)
    uv_all[mask] = uv

    obj_pts = hits = 0
    ped_pts = ped_hits = 0
    car_pts = car_hits = 0

    for obj in fr["labels"]:
        if obj.type not in CLASSES:
            continue
        sel = points_in_box(cam_true, obj) & mask
        if not np.any(sel):
            continue
        u, v = uv_all[sel, 0], uv_all[sel, 1]
        x1, y1, x2, y2 = obj.bbox
        in_bbox = (u >= x1) & (u <= x2) & (v >= y1) & (v <= y2)
        n_hit = int(in_bbox.sum())
        n_sel = int(sel.sum())

        hits += n_hit
        obj_pts += n_sel

        if obj.type == "Pedestrian":
            ped_hits += n_hit
            ped_pts += n_sel
        elif obj.type in ("Car", "Van"):
            car_hits += n_hit
            car_pts += n_sel

    return {
        "n_points": len(pts),
        "inside_image": int(mask.sum()),
        "object_points": obj_pts,
        "hit_ratio": round(hits / obj_pts, 4) if obj_pts else float("nan"),
        "ped_points": ped_pts,
        "ped_hit_ratio": round(ped_hits / ped_pts, 4) if ped_pts else float("nan"),
        "car_points": car_pts,
        "car_hit_ratio": round(car_hits / car_pts, 4) if car_pts else float("nan"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Quét góc lệch yaw, đo % điểm của vật thể nằm trong 2D box")
    ap.add_argument("--data-root", default="data/kitti_mini", help="Đường dẫn thư mục dữ liệu")
    ap.add_argument("--frames", nargs="+", default=["000008", "000011", "000049"], help="Danh sách frame_id")
    ap.add_argument("--yaw-levels", nargs="+", type=float, default=[0.0, 0.5, 1.0, 2.0, 3.0], help="Các mức yaw (độ)")
    ap.add_argument("--out", default="results/yaw_perturb_sweep.csv", help="Đường dẫn file CSV xuất ra")
    args = ap.parse_args()

    rows = []
    for frame in args.frames:
        fr = load_frame(args.data_root, frame)
        for yaw in args.yaw_levels:
            res = run_one(fr, yaw)
            row = {
                "dataset": Path(args.data_root).name,
                "frame": frame,
                "yaw_deg": yaw,
                "n_points": res["n_points"],
                "inside_image": res["inside_image"],
                "object_points": res["object_points"],
                "hit_ratio": res["hit_ratio"],
                "ped_points": res["ped_points"],
                "ped_hit_ratio": res["ped_hit_ratio"],
                "car_points": res["car_points"],
                "car_hit_ratio": res["car_hit_ratio"],
            }
            rows.append(row)
            print(f"[{row['dataset']}|{row['frame']}] yaw={yaw:3.1f} deg | hit_ratio={row['hit_ratio']:.4f} "
                  f"(ped: {row['ped_hit_ratio']}, car: {row['car_hit_ratio']})")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\n-> {out} ({len(rows)} dòng)")


if __name__ == "__main__":
    main()
