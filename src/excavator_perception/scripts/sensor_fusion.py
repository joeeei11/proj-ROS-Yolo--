#!/usr/bin/env python3
"""多模态融合节点：视觉跟踪 + 激光雷达深度融合，发布最终 /excavator/detected_obstacles

工作原理：
  1. 启动时订阅 /camera/camera_info，缓存 K 矩阵 (fx, fy, cx, cy) 与图像尺寸
  2. 用 tf2 lookup odom → camera_optical_link 变换
  3. 对每个 lidar 聚类（来自 lidar_processor，含 odom 系下的 world_x/y/z）：
     - 变换到 camera_optical_link 系（ROS 光学惯例 Z 朝前 X 朝右 Y 朝下）
     - 用 K 投影到像素 (u, v)
  4. 与每个视觉 track 的 bbox 做 point-in-bbox 匹配；命中则把 lidar 深度写入 obs.distance
     和 world_x/y/z；并取最近的 lidar cluster 作为该 track 的真实位置
  5. 未匹配的视觉 track：distance 保留默认大值（999.0），下游风险评估自然得出低分
"""

import math
import rospy
import numpy as np

from sensor_msgs.msg import CameraInfo
from excavator_msgs.msg import ObstacleInfo, ObstacleArray

import tf2_ros
import tf2_geometry_msgs  # noqa: F401
from geometry_msgs.msg import PoseStamped


class SensorFusionNode:
    def __init__(self):
        rospy.init_node("sensor_fusion", anonymous=False)

        self.camera_frame = rospy.get_param(
            "~camera_frame", "camera_optical_link")
        self.world_frame = rospy.get_param(
            "~world_frame", "odom")
        # 当视觉障碍物未匹配到任何 lidar 簇时使用的占位距离（米）
        self.unmatched_distance = float(rospy.get_param("~unmatched_distance", 999.0))

        # K 矩阵（启动时从 /camera/camera_info 一次性获取）
        self._K = None
        self._img_w = None
        self._img_h = None

        # TF
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        # 订阅 camera_info 一次
        rospy.loginfo("[SensorFusion] 等待 /camera/camera_info ...")
        try:
            cam_info = rospy.wait_for_message(
                "/camera/camera_info", CameraInfo, timeout=30.0)
            self._set_camera_info(cam_info)
        except rospy.ROSException:
            rospy.logwarn(
                "[SensorFusion] camera_info 30s 内未收到；将使用 sensors.xacro 默认参数")
            self._set_default_camera_info()

        # 同时订阅以应对 camera 切换或 frame_id 变化
        rospy.Subscriber("/camera/camera_info", CameraInfo,
                         self._camera_info_cb, queue_size=1)

        # 输出
        self.fused_pub = rospy.Publisher(
            "/excavator/detected_obstacles", ObstacleArray, queue_size=5)

        # 缓存最新 tracked_obstacles（初始为空数组，允许 lidar 先到达时直接发布）
        self._last_tracks = ObstacleArray()
        self._last_tracks_time = None

        # 独立订阅（不再依赖同步器，确保 lidar 每次到达都触发融合）
        rospy.Subscriber("/excavator/tracked_obstacles", ObstacleArray,
                         self._track_cb, queue_size=5)
        rospy.Subscriber("/excavator/lidar_obstacles", ObstacleArray,
                         self._lidar_cb, queue_size=5)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("[SensorFusion] 节点启动 K=%s img=%sx%s",
                      "OK" if self._K is not None else "MISSING",
                      self._img_w, self._img_h)

    # ------------------------------------------------------------------
    # 相机参数
    # ------------------------------------------------------------------

    def _camera_info_cb(self, msg: CameraInfo):
        if self._K is None:
            self._set_camera_info(msg)

    def _set_camera_info(self, msg: CameraInfo):
        # K = [fx, 0, cx, 0, fy, cy, 0, 0, 1]
        K = list(msg.K)
        if len(K) >= 9 and K[0] > 0:
            self._K = (K[0], K[4], K[2], K[5])  # (fx, fy, cx, cy)
            self._img_w = int(msg.width) or 640
            self._img_h = int(msg.height) or 480
            rospy.loginfo(
                "[SensorFusion] camera_info: fx=%.1f fy=%.1f cx=%.1f cy=%.1f size=%dx%d",
                self._K[0], self._K[1], self._K[2], self._K[3],
                self._img_w, self._img_h)
        else:
            self._set_default_camera_info()

    def _set_default_camera_info(self):
        # sensors.xacro：horizontal_fov=1.5708 (90°), 640x480
        # fx = (w/2) / tan(hfov/2) = 320 / tan(45°) = 320
        # fy = (h/2) / tan(vfov/2)；vfov ≈ 2*atan((h/2)/fx) ≈ 73.74°
        self._img_w = 640
        self._img_h = 480
        fx = 320.0
        fy = 320.0  # Gazebo 摄像头通常使用方形像素，与水平 fx 相同
        cx = self._img_w / 2.0
        cy = self._img_h / 2.0
        self._K = (fx, fy, cx, cy)
        rospy.loginfo("[SensorFusion] 默认相机参数 fx=%.1f fy=%.1f size=%dx%d",
                      fx, fy, self._img_w, self._img_h)

    # ------------------------------------------------------------------
    # 主回调
    # ------------------------------------------------------------------

    def _fusion_cb(self, track_msg: ObstacleArray, lidar_msg: ObstacleArray):
        out_msg = ObstacleArray()
        out_msg.header = track_msg.header

        # 把所有 lidar 聚类投影到像素，预先准备 (u, v, depth, world_xyz, cluster_idx)
        projected = []
        for li, lo in enumerate(lidar_msg.obstacles):
            uvz = self._project_cluster_to_image(lo)
            matched_flag = False
            if uvz is not None:
                u, v, depth = uvz
            else:
                u, v, depth = None, None, None
            projected.append({
                "lo": lo,
                "u": u, "v": v, "depth": depth,
                "world": (lo.world_x, lo.world_y, lo.world_z),
                "lidar_dist": lo.distance,
                "matched": matched_flag,
                "in_image": uvz is not None,
            })

        for tobs in track_msg.obstacles:
            obs_fused = ObstacleInfo()
            # 复制视觉跟踪的所有原始字段
            obs_fused.header = tobs.header
            obs_fused.obstacle_id = tobs.obstacle_id
            obs_fused.obstacle_type = tobs.obstacle_type
            obs_fused.risk_level = tobs.risk_level
            obs_fused.pose = tobs.pose
            obs_fused.velocity_vec = tobs.velocity_vec
            obs_fused.bbox_x1 = tobs.bbox_x1
            obs_fused.bbox_y1 = tobs.bbox_y1
            obs_fused.bbox_x2 = tobs.bbox_x2
            obs_fused.bbox_y2 = tobs.bbox_y2

            # bbox 全 0 且有 world 坐标 → actor_collider_sync 位置跟踪，用世界坐标匹配
            is_world_track = (tobs.bbox_x1 == 0.0 and tobs.bbox_y1 == 0.0 and
                              tobs.bbox_x2 == 0.0 and tobs.bbox_y2 == 0.0 and
                              (tobs.world_x != 0.0 or tobs.world_y != 0.0))

            best = None  # (sort_key, world_xyz, lidar_dist, proj_idx)
            if is_world_track:
                # 世界坐标匹配：找 XY 平面最近的 lidar 聚类（阈值 1.0m）
                for pi, p in enumerate(projected):
                    wx, wy, _ = p["world"]
                    if wx == 0.0 and wy == 0.0:
                        continue
                    dist_xy = math.sqrt((wx - tobs.world_x) ** 2 + (wy - tobs.world_y) ** 2)
                    if dist_xy < 1.0:
                        if best is None or p["lidar_dist"] < best[2]:
                            best = (dist_xy, p["world"], p["lidar_dist"], pi)
            else:
                # 正常像素 bbox 匹配
                for pi, p in enumerate(projected):
                    if not p["in_image"]:
                        continue
                    if (tobs.bbox_x1 <= p["u"] <= tobs.bbox_x2 and
                            tobs.bbox_y1 <= p["v"] <= tobs.bbox_y2):
                        if best is None or p["depth"] < best[0]:
                            best = (p["depth"], p["world"], p["lidar_dist"], pi)

            if best is not None:
                _depth, (wx, wy, wz), lidar_dist, pi = best
                obs_fused.distance = float(lidar_dist)
                obs_fused.world_x = float(wx)
                obs_fused.world_y = float(wy)
                obs_fused.world_z = float(wz)
                projected[pi]["matched"] = True
            else:
                # 未匹配：保留大距离（避免 distance=0 触发 critical_distance 满分）
                obs_fused.distance = self.unmatched_distance

            out_msg.obstacles.append(obs_fused)

        # 未被任何视觉 track 认领的 lidar 聚类 → 作为静态 "obstacle" 直通
        # 这使得围栏/建材堆/测试场景的静态障碍物能被 risk_assessor 和 RRT* 感知
        for p in projected:
            if p["matched"]:
                continue
            wx, wy, wz = p["world"]
            # 跳过 TF 变换失败（world_xyz 全零）的簇
            if wx == 0.0 and wy == 0.0:
                continue
            lo = p["lo"]
            obs_static = ObstacleInfo()
            obs_static.header = lidar_msg.header
            obs_static.obstacle_id = lo.obstacle_id
            obs_static.obstacle_type = "obstacle"
            obs_static.risk_level = 0
            obs_static.pose = lo.pose
            obs_static.distance = float(lo.distance)
            obs_static.world_x = float(wx)
            obs_static.world_y = float(wy)
            obs_static.world_z = float(wz)
            out_msg.obstacles.append(obs_static)

        out_msg.dominant_risk_level = 0
        self.fused_pub.publish(out_msg)

    # ------------------------------------------------------------------
    # 几何工具
    # ------------------------------------------------------------------

    def _project_cluster_to_image(self, lo: ObstacleInfo):
        """把 lidar cluster（odom 系的 world_x/y/z）投影到像素。
        失败（TF 不可用 / 点在相机后方 / 越界）返回 None。
        """
        if self._K is None:
            return None

        # 优先使用 world_x/y/z（已在 lidar_processor 中变换到 odom）
        # 若 world_x/y/z 全 0（旧消息），则回退到 lidar_link 系下的 pose 变换
        wx, wy, wz = lo.world_x, lo.world_y, lo.world_z
        if wx == 0.0 and wy == 0.0 and wz == 0.0:
            # 用 pose（lidar_link 系）做实时 TF
            try:
                ps = PoseStamped()
                ps.header.frame_id = lo.pose.header.frame_id or "lidar_link"
                ps.header.stamp = rospy.Time(0)
                ps.pose = lo.pose.pose
                out = self.tf_buffer.transform(
                    ps, self.world_frame, rospy.Duration(0.1))
                wx, wy, wz = (out.pose.position.x,
                              out.pose.position.y,
                              out.pose.position.z)
            except Exception:
                return None

        # odom → camera_optical_link
        try:
            ps = PoseStamped()
            ps.header.frame_id = self.world_frame
            ps.header.stamp = rospy.Time(0)
            ps.pose.position.x = wx
            ps.pose.position.y = wy
            ps.pose.position.z = wz
            ps.pose.orientation.w = 1.0
            in_cam = self.tf_buffer.transform(
                ps, self.camera_frame, rospy.Duration(0.1))
        except Exception:
            return None

        X = in_cam.pose.position.x
        Y = in_cam.pose.position.y
        Z = in_cam.pose.position.z

        # camera_optical_link 中 Z 朝前；点必须在相机前方（深度 > 一点点）
        if Z <= 0.05:
            return None

        fx, fy, cx, cy = self._K
        u = fx * X / Z + cx
        v = fy * Y / Z + cy

        if u < 0 or u >= self._img_w or v < 0 or v >= self._img_h:
            return None

        return (u, v, Z)

    def _track_cb(self, msg: ObstacleArray):
        self._last_tracks = msg
        self._last_tracks_time = rospy.Time.now()

    def _lidar_cb(self, msg: ObstacleArray):
        self._fusion_cb(self._last_tracks, msg)

    def _shutdown(self):
        rospy.loginfo("[SensorFusion] 节点关闭")


if __name__ == "__main__":
    node = SensorFusionNode()
    rospy.spin()
