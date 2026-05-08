#!/usr/bin/env python3
"""多模态融合节点：视觉跟踪 + 激光雷达距离融合，发布最终 /excavator/detected_obstacles"""

import rospy
import numpy as np
import message_filters

from excavator_msgs.msg import ObstacleInfo, ObstacleArray


class SensorFusionNode:
    def __init__(self):
        rospy.init_node("sensor_fusion", anonymous=False)

        # 距离关联阈值：视觉障碍物方向与激光雷达点方向夹角 ≤ 此值时匹配（rad）
        self.angle_thresh = rospy.get_param("~angle_thresh_rad", 0.2)

        self.fused_pub = rospy.Publisher(
            "/excavator/detected_obstacles", ObstacleArray, queue_size=5)

        # ApproximateTimeSynchronizer：视觉跟踪结果 + 激光雷达处理结果
        # decisions.md 规定 slop=0.05s
        track_sub = message_filters.Subscriber(
            "/excavator/tracked_obstacles", ObstacleArray)
        lidar_sub = message_filters.Subscriber(
            "/excavator/lidar_obstacles", ObstacleArray)

        self.sync = message_filters.ApproximateTimeSynchronizer(
            [track_sub, lidar_sub], queue_size=10, slop=0.05)
        self.sync.registerCallback(self._fusion_cb)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("[SensorFusion] 节点启动")

    def _fusion_cb(self, track_msg: ObstacleArray, lidar_msg: ObstacleArray):
        out_msg = ObstacleArray()
        out_msg.header = track_msg.header

        # 构建激光雷达点的角度查找表
        lidar_angles = []
        for lo in lidar_msg.obstacles:
            x = lo.pose.pose.position.x
            y = lo.pose.pose.position.y
            lidar_angles.append((np.arctan2(y, x), lo.distance))

        for obs in track_msg.obstacles:
            obs_fused = ObstacleInfo()
            obs_fused.header = obs.header
            obs_fused.obstacle_id = obs.obstacle_id
            obs_fused.obstacle_type = obs.obstacle_type
            obs_fused.risk_level = obs.risk_level
            obs_fused.pose = obs.pose
            obs_fused.velocity_vec = obs.velocity_vec

            # 障碍物方向角（视觉：归一化坐标 0~1，转为相对角度）
            cx_n = obs.pose.pose.position.x  # 0~1
            # 视觉坐标系：cx=0 左边，cx=1 右边；假设 FOV=90°，则角度范围 ±45°
            vis_angle = (cx_n - 0.5) * (np.pi / 2)

            # 找最近匹配的激光雷达点
            best_dist = obs.distance
            best_diff = self.angle_thresh + 1.0
            for la, ld in lidar_angles:
                diff = abs(la - vis_angle)
                if diff < self.angle_thresh and diff < best_diff:
                    best_diff = diff
                    best_dist = ld

            obs_fused.distance = best_dist
            out_msg.obstacles.append(obs_fused)

        # dominant_risk_level 由下游 risk_assessor 填充
        out_msg.dominant_risk_level = 0
        self.fused_pub.publish(out_msg)

    def _shutdown(self):
        rospy.loginfo("[SensorFusion] 节点关闭")


if __name__ == "__main__":
    node = SensorFusionNode()
    rospy.spin()
