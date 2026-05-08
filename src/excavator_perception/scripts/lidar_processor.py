#!/usr/bin/env python3
"""激光雷达处理节点：计算各角度扇区最小距离，发布到 /excavator/lidar_obstacles"""

import rospy
import numpy as np
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Header
from excavator_msgs.msg import ObstacleInfo, ObstacleArray


class LidarProcessorNode:
    def __init__(self):
        rospy.init_node("lidar_processor", anonymous=False)

        # 参数：扇区数（将 360° 分成 N 个扇区，每扇区独立报告最近障碍物）
        self.num_sectors = rospy.get_param("~num_sectors", 8)
        self.min_range = rospy.get_param("~min_range", 0.1)   # 过滤噪声（m）
        self.max_range = rospy.get_param("~max_range", 20.0)  # 有效测量距离（m）

        self.lidar_pub = rospy.Publisher(
            "/excavator/lidar_obstacles", ObstacleArray, queue_size=5)

        rospy.Subscriber("/lidar/scan", LaserScan,
                         self._scan_cb, queue_size=1)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("[LidarProc] 节点启动 num_sectors=%d", self.num_sectors)

    def _scan_cb(self, msg: LaserScan):
        ranges = np.array(msg.ranges, dtype=np.float32)
        angles = (msg.angle_min
                  + np.arange(len(ranges)) * msg.angle_increment)

        # 过滤无效值
        valid = (ranges >= self.min_range) & (ranges <= self.max_range)
        ranges = np.where(valid, ranges, np.inf)

        out_msg = ObstacleArray()
        out_msg.header = msg.header
        min_dist_overall = np.inf

        sector_size = len(ranges) // self.num_sectors

        for i in range(self.num_sectors):
            start = i * sector_size
            end = start + sector_size if i < self.num_sectors - 1 else len(ranges)
            sector_ranges = ranges[start:end]
            min_idx = np.argmin(sector_ranges)
            min_dist = float(sector_ranges[min_idx])

            if np.isinf(min_dist):
                continue

            angle = float(angles[start + min_idx])
            obs = ObstacleInfo()
            obs.header = msg.header
            obs.obstacle_id = f"lidar_sector_{i}"
            obs.obstacle_type = "lidar_point"
            obs.distance = min_dist
            # 极坐标 → 笛卡尔（激光雷达坐标系）
            obs.pose.header = msg.header
            obs.pose.pose.position.x = min_dist * np.cos(angle)
            obs.pose.pose.position.y = min_dist * np.sin(angle)
            obs.pose.pose.position.z = 0.0
            out_msg.obstacles.append(obs)

            if min_dist < min_dist_overall:
                min_dist_overall = min_dist

        self.lidar_pub.publish(out_msg)

        if not np.isinf(min_dist_overall):
            rospy.logdebug("[LidarProc] 最近障碍物 %.2f m", min_dist_overall)

    def _shutdown(self):
        rospy.loginfo("[LidarProc] 节点关闭")


if __name__ == "__main__":
    node = LidarProcessorNode()
    rospy.spin()
