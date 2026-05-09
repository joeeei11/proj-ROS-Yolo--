std_msgs/Header header
string obstacle_id
string obstacle_type
float32 distance
float32 relative_velocity
float32 ttc
float32 risk_score
uint8 risk_level
geometry_msgs/PoseStamped pose
geometry_msgs/Vector3 velocity_vec

# 像素 bbox（YOLO 检测框，px；未填充时全 0）
float32 bbox_x1
float32 bbox_y1
float32 bbox_x2
float32 bbox_y2

# 世界坐标（base_footprint 系，米）；sensor_fusion 用相机内参 + lidar 深度反投影后填入
# 未填充时全 0；下游应优先使用 world_x/y/z 而非 pose.position（后者历史上为归一化像素）
float32 world_x
float32 world_y
float32 world_z
