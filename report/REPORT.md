# Báo cáo Day 6: Độ nhạy của projection với lệch yaw

- **Họ tên:** Bùi Văn Quang
- **MSSV:** 2A202602688
- **Lớp:** AI20K-T4
- **Link repo:** https://github.com/Quang20040/BuiVanQuang-2A202602688-Track4-Day21
- **Topic:** A — LiDAR-camera projection QA
- **Dataset:** data/kitti_mini, data/nuscenes_mini_subset
- **Các frame đã dùng:** 000008, 000011, 000049 (KITTI) và scene-0103_010 (nuScenes)

## 1. Claim

Lệch góc xoay yaw 1° làm tỉ lệ điểm LiDAR của người đi bộ (vật thể hẹp ở cự ly 15–30 m) rơi đúng vào 2D box giảm hơn 20 điểm phần trăm, trong khi đối với xe ô tô (vật thể rộng) chỉ giảm dưới 5 điểm phần trăm; hiện tượng calibration drift này có thể được định lượng và phát hiện tự động bằng bounding-box point alignment score với ngưỡng 80%.

## 2. Evidence

Kết quả quét góc lệch yaw từ 0.0° đến 3.0° trên 3 tình huống tiêu biểu của `data/kitti_mini` (chi tiết tại `results/yaw_perturb_sweep.csv`):

| Mức lệch Yaw | Frame 000008 (Đông xe) | Frame 000011 (Nhiều người đi bộ) | Frame 000049 (Bị che khuất) | Nhận xét chi tiết |
|:---:|:---:|:---:|:---:|---|
| **0.0°** | 99.63% | 99.45% (Ped: 99.67%) | 99.25% | Baseline chuẩn của calibration gốc |
| **0.5°** | 99.57% | 91.88% (Ped: 85.67%) | 97.46% | Người đi bộ bắt đầu sụt giảm rõ |
| **1.0°** | 98.62% | 77.44% (Ped: 61.89%) | 93.50% | Frame 000011 giảm 22.01%, Ped giảm 37.78% |
| **2.0°** | 94.81% | 45.44% (Ped: 21.17%) | 84.74% | Hơn một nửa số điểm người đi bộ rơi ra ngoài |
| **3.0°** | 90.98% | 21.23% (Ped: 5.21%) | 74.32% | Hầu như mất dấu hoàn toàn người đi bộ |

![yaw sweep](../results/figures/yaw_sweep.png)

- **Phân tích số liệu:** Lệch yaw 1.0° làm điểm LiDAR trượt ngang trên ảnh xấp xỉ $\Delta u \approx f \cdot \tan(1^\circ) \approx 721.5 \cdot 0.01745 \approx 12.6$ pixel. Với người đi bộ ở cự ly 15–30 m chỉ rộng khoảng 15–20 pixel trên ảnh KITTI, độ trượt 12.6 pixel khiến tỉ lệ điểm rơi vào box của người đi bộ giảm sâu từ 99.67% xuống 61.89% (sụt giảm 37.78 điểm phần trăm). Trong khi đó, với ô tô con rộng 60–120 pixel, độ trượt này chỉ làm sụt giảm 1.01% ở frame 000008 (vẫn giữ 98.62%).
- **Ngưỡng phát hiện:** Thiết lập ngưỡng cảnh báo sớm tại `hit_ratio < 80%` phát hiện chính xác lỗi lệch yaw từ 1.0° trở lên trên các frame có đối tượng hẹp (người đi bộ) mà không bị báo động giả ở trạng thái chuẩn (baseline > 99%).
- **[B5] So sánh giữa KITTI và nuScenes:** nuScenes có tiêu cự camera trước lớn hơn nhiều ($f \approx 1253$ px so với $f \approx 721$ px của KITTI). Do đó, cùng một góc lệch 1° yaw, điểm LiDAR trên nuScenes bị trượt tới $\Delta u \approx 1253 \cdot \tan(1^\circ) \approx 21.9$ pixel (gấp 1.74 lần KITTI). Dù độ phân giải ảnh nuScenes lớn hơn ($1600 \times 900$ so với $1242 \times 375$), mật độ LiDAR 32 beam thưa hơn khiến độ nhạy và rủi ro mất dấu vật thể nhỏ khi lệch calibration trên nuScenes còn cao hơn trên KITTI.

## 3. Failure case

![failure](../results/figures/fail_01_nusc_no_ego_motion.png)

- **Trường hợp:** nuScenes, frame `scene-0103_010`, chiếu LiDAR lên camera trước khi tắt cơ chế bù chuyển động xe (`--ignore-ego-motion`).
- **Quan sát:** Số điểm chiếu lọt vào ảnh giảm từ 3120 điểm xuống 2911 điểm (mất 209 điểm, giảm 6.7%). Các điểm LiDAR trên thân xe phía trước và biển báo ở gần bị trượt lệch vị trí so với hình ảnh thực tế của camera.
- **Nguyên nhân:** Camera trước chụp sớm hơn LiDAR 35.6 ms. Khi xe di chuyển với tốc độ đô thị 36 km/h (10 m/s), trong 35.6 ms xe đã di chuyển được một quãng đường $\Delta d \approx 0.36$ m. Nếu không dùng ego pose để bù chuyển động này (deskew), toạ độ các điểm LiDAR ở gần sẽ bị lệch lớn trên ảnh.
- **Lớp debug:** **Time (Thời gian & Đồng bộ cảm biến)**.
- **Cách phát hiện khi chạy thật:** Theo dõi độ chênh lệch timestamp giữa các cảm biến ($\Delta t = |t_{\text{cam}} - t_{\text{lidar}}|$). Cảnh báo nếu $\Delta t > 10$ ms mà xe đang di chuyển với vận tốc $v > 5$ km/h mà không có module deskew bằng IMU/Odom hoạt động.

*(Tham khảo thêm: [fail_02_yaw_2deg_pedestrian.png](../results/figures/fail_02_yaw_2deg_pedestrian.png) minh hoạ lỗi lớp **Geometry** khi lệch yaw 2.0° làm 78.8% điểm của người đi bộ trượt khỏi 2D box).*

## 4. Khuyến nghị nếu triển khai thật

- **Use-case cụ thể:** Hệ thống xe tự hành giao hàng đô thị (Urban Delivery AGV/Robot) di chuyển ở dải tốc độ dưới 35 km/h, liên tục hoạt động trong môi trường có nhiều người đi bộ, trẻ em và xe đạp ở cự ly gần đến trung bình (5–30 m).
- **Đánh đổi khi triển khai (Trade-offs):**
  - *Tài nguyên tính toán:* Theo benchmark [B3] trên CPU AMD Ryzen 7 5800H, thuật toán kiểm tra projection tốn trung bình $p_{50} = 15.63$ ms ($p_{95} = 18.91$ ms) cho mỗi frame 108k điểm. Để tiết kiệm tài nguyên CPU cho hệ thống điều khiển và tránh chạy liên tục 10 Hz, giải pháp tối ưu là chạy kiểm tra QA định kỳ: mỗi khi xe dừng đèn đỏ, hoặc mỗi 15 giây/lần khi xe đang chạy trên đoạn đường thẳng ổn định.
  - *Độ an toàn:* Khi phát hiện `hit_ratio < 80%` liên tục qua 3 frame, hệ thống tự động phát cờ nguy hiểm `CALIB_DEGRADED`, lập tức giảm tốc độ xe về chế độ dự phòng an toàn (creep mode < 10 km/h) và tạm dừng tính năng Early/Deep Sensor Fusion, chuyển sang dùng LiDAR 3D Bounding Box độc lập để bảo đảm an toàn.
- **Chỉ số cần ghi log & giám sát:**
  - `hit_ratio` theo từng class vật thể (đặc biệt theo dõi riêng nhánh Pedestrian).
  - Độ chênh lệch timestamp giữa Camera - LiDAR ($\Delta t$).
  - Ghi log liên tục nhiệt độ vỏ giá đỡ cảm biến (bracket temperature) và cảm biến chấn động IMU (g-force spike) để hệ thống tự chẩn đoán nguyên nhân trôi lệch là do giãn nở nhiệt cơ học hay do va đập vật lý.

## 5. Cách chạy lại

Toàn bộ kết quả có thể tái tạo từ repo sạch bằng các lệnh sau:

```bash
# 1. Tự kiểm tra 2 hàm velo_to_cam và cam_to_image (CP2 self-test)
python -m src.test_projection

# 2. Tạo ảnh demo baseline overlay trên KITTI mini và nuScenes (CP2)
python -m starter.projection --data-root data/kitti_mini --frame 000011
python -m starter.projection --data-root data/kitti_mini --frame 000008
python -m starter.projection --data-root data/kitti_mini --frame 000049
python -m starter.projection --data-root data/synthetic --frame 000000
python -m starter.projection --data-root data/nuscenes_mini_subset --frame scene-0103_010

# 3. Chạy thí nghiệm quét góc lệch yaw (CP3 benchmark)
python -m src.exp_yaw_sweep --data-root data/kitti_mini --frames 000008 000011 000049

# 4. Vẽ biểu đồ phân tích thí nghiệm yaw sweep (CP3)
python -m src.plot_yaw_sweep

# 5. Tạo ảnh phân tích các failure cases (CP4)
python -m src.generate_failure_cases

# 6. [Bonus B3] Đo latency chuẩn khoa học (bỏ warm-up, 24 runs, xuất p50/p95)
python -m src.benchmark_latency

# 7. [Bonus B4] Chạy công cụ tự động kiểm tra chất lượng cân chỉnh (Calibration QA CLI Tool)
python -m src.calibration_qa --data-root data/kitti_mini --frame 000011 --threshold 0.80
```

## 6. Khai báo sử dụng AI

| Công cụ | Dùng cho việc gì | Bạn đã kiểm chứng thế nào |
|---|---|---|
| Gemini / Antigravity Agent | Hỗ trợ giải thích hệ toạ độ và kiểm tra ma trận chiếu velo_to_cam, cam_to_image | Chạy `src.test_projection` pass chính xác với $z_{\text{cam}} = 9.73$ m và toạ độ pixel $(614, 175)$ |
| Codelab Day 6 | Cung cấp khung thuật toán ban đầu trong `src/exp_yaw_sweep.py` | Tự mở rộng phân rã theo class (Pedestrian vs Car), chạy lại ra kết quả hoàn toàn trùng khớp bảng chuẩn |
| Python / Matplotlib / OpenCV | Tự động hóa trích xuất dữ liệu, vẽ biểu đồ và ghép ảnh phân tích failure case | So sánh từng giá trị điểm đo trên biểu đồ với file `results/yaw_perturb_sweep.csv` |
