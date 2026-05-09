#!/usr/bin/env python3
"""激光雷达处理节点：角度连续聚类 + TF 变换到 base_footprint，发布到 /excavator/lidar_obstacles

每个聚类输出一个 ObstacleInfo：
  - pose.position：lidar_link 坐标系下的笛卡尔质心（米）
  - world_x/y/z：base_footprint 坐标系下的笛卡尔质心（米）
  - distance：质心到 lidar 原点的距离（米）
"""

import math
import rospy
import numpy as np
from sensor_msgs.msg import LaserScan
from excavator_msgs.msg import ObstacleInfo, ObstacleArray

import tf2_ros
import tf2_geometry_msgs  # noqa: F401  (注册 PoseStamped 变换)
from geometry_msgs.msg import PoseStamped


class LidarProcessorNode:
    def __init__(self):
        rospy.init_node("lidar_processor", anonymous=False)

        self.min_range = rospy.get_param("~min_range", 0.1)        # 过滤噪声（m）
        self.max_range = rospy.get_param("~max_range", 15.0)       # 有效测量距离（m）
        # 角度连续聚类阈值：相邻射线距离差 > 此值视为新簇（m）
        self.cluster_break = rospy.get_param("~cluster_break_threshold", 0.5)
        # 聚类最小点数（过滤孤立噪声）
        self.min_cluster_points = rospy.get_param("~min_cluster_points", 2)
        # 目标坐标系
        self.target_frame = rospy.get_param("~target_frame", "base_footprint")

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        self.lidar_pub = rospy.Publisher(
            "/excavator/lidar_obstacles", ObstacleArray, queue_size=5)

        rospy.Subscriber("/lidar/scan", LaserScan,
                         self._scan_cb, queue_size=1)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("[LidarProc] 节点启动 cluster_break=%.2fm target=%s",
                      self.cluster_break, self.target_frame)

    # ------------------------------------------------------------------
    # 主回调
    # ------------------------------------------------------------------

    def _scan_cb(self, msg: LaserScan):
        ranges = np.array(msg.ranges, dtype=np.float32)
        n = len(ranges)
        if n == 0:
            return

        valid = (ranges >= self.min_range) & (ranges <= self.max_range) & np.isfinite(ranges)

        # 角度连续聚类：扫一遍，遇到无效或距离跳变就断簇
        clusters = []   # list of list of (angle, range)
        current = []
        prev_r = None
        for i in range(n):
            angle = msg.angle_min + i * msg.angle_increment
            if not valid[i]:
                if current:
                    clusters.append(current)
                    current = []
                prev_r = None
                continue
            r = float(ranges[i])
            if prev_r is not None and abs(r - prev_r) > self.cluster_break:
                clusters.append(current)
                current = []
            current.append((angle, r))
            prev_r = r
        if current:
            clusters.append(current)

        out_msg = ObstacleArray()
        out_msg.header = msg.header

        for ci, pts in enumerate(clusters):
            if len(pts) < self.min_cluster_points:
                continue
            # 质心（xy）：把每个射线点转笛卡尔后取均值
            xs = [r * math.cos(a) for a, r in pts]
            ys = [r * math.sin(a) for a, r in pts]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            cz = 0.0
            cdist = math.sqrt(cx * cx + cy * cy)

            obs = ObstacleInfo()
            obs.header = msg.header
            obs.obstacle_id = f"lidar_cluster_{ci}"
            obs.obstacle_type = "lidar_cluster"
            obs.distance = cdist
            obs.pose.header = msg.header
            obs.pose.pose.position.x = cx
            obs.pose.pose.position.y = cy
            obs.pose.pose.position.z = cz
            obs.pose.pose.orientation.w = 1.0

            # 变换质心到 base_footprint 系，写入 world_x/y/z
            wx, wy, wz = self._transform_to_target(msg.header.frame_id, cx, cy, cz)
            if wx is not None:
                obs.world_x = float(wx)
                obs.world_y = float(wy)
                obs.world_z = float(wz)

            out_msg.obstacles.append(obs)

        self.lidar_pub.publish(out_msg)

    # ------------------------------------------------------------------
    # TF 工具
    # ------------------------------------------------------------------

    def _transform_to_target(self, src_frame, x, y, z):
        """把 src_frame 下的点 (x,y,z) 变换到 self.target_frame。失败返回 (None,None,None)。"""
        try:
            ps = PoseStamped()
            ps.header.frame_id = src_frame or "lidar_link"
            ps.header.stamp = rospy.Time(0)   # 用最新可用 TF（避免 use_sim_time 早期 stamp=0 异常）
            ps.pose.position.x = x
            ps.pose.position.y = y
            ps.pose.position.z = z
            ps.pose.orientation.w = 1.0
            out = self.tf_buffer.transform(
                ps, self.target_frame, rospy.Duration(0.2))
            return (out.pose.position.x, out.pose.position.y, out.pose.position.z)
        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            rospy.logwarn_throttle(
                5.0, "[LidarProc] TF %s→%s 失败: %s",
                src_frame, self.target_frame, e)
            return (None, None, None)

    def _shutdown(self):
        rospy.loginfo("[LidarProc] 节点关闭")


if __name__ == "__main__":
    node = LidarProcessorNode()
    rospy.spin()
