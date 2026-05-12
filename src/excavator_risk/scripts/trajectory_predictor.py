#!/usr/bin/env python3
"""
trajectory_predictor.py
订阅 /excavator/detected_obstacles，用卡尔曼滤波估算各障碍物速度并计算 TTC，
发布 /excavator/predicted_obstacles（ObstacleArray，ttc 字段已更新）。

状态向量: [x, y, vx, vy]  (坐标来自 ObstacleInfo.world_x/y 的 odom 米制坐标)
观测向量: [x, y]
"""
import math
import rospy
import numpy as np
from filterpy.kalman import KalmanFilter
from nav_msgs.msg import Odometry
from excavator_msgs.msg import ObstacleArray, ObstacleInfo

# 卡尔曼滤波器工厂：4状态(x,y,vx,vy) 2观测(x,y)
def _make_kf(dt, proc_noise=0.1, meas_noise=0.5):
    kf = KalmanFilter(dim_x=4, dim_z=2)
    kf.F = np.array([[1, 0, dt, 0],
                     [0, 1, 0, dt],
                     [0, 0, 1,  0],
                     [0, 0, 0,  1]], dtype=float)
    kf.H = np.array([[1, 0, 0, 0],
                     [0, 1, 0, 0]], dtype=float)
    kf.R = np.eye(2) * meas_noise
    q = proc_noise
    kf.Q = np.array([[dt**4/4, 0, dt**3/2, 0],
                     [0, dt**4/4, 0, dt**3/2],
                     [dt**3/2, 0, dt**2,   0],
                     [0, dt**3/2, 0,  dt**2]], dtype=float) * q
    kf.P = np.eye(4) * 10.0
    return kf


class TrajectoryPredictor:
    def __init__(self):
        rospy.init_node("trajectory_predictor")

        self.dt = rospy.get_param("~dt", 0.1)
        self.proc_noise = rospy.get_param("~proc_noise", 0.1)
        self.meas_noise = rospy.get_param("~meas_noise", 0.5)
        self.max_missing_frames = rospy.get_param("~max_missing_frames", 10)
        self.excavator_speed = rospy.get_param("~excavator_speed", 1.0)  # m/s，平均作业速度

        # track_id -> {kf, missing_count}
        self._trackers = {}
        self._robot_x = 0.0
        self._robot_y = 0.0

        self.sub = rospy.Subscriber(
            "/excavator/detected_obstacles", ObstacleArray, self._callback, queue_size=10
        )
        self.pub = rospy.Publisher(
            "/excavator/predicted_obstacles", ObstacleArray, queue_size=10
        )
        rospy.Subscriber("/odom", Odometry, self._odom_cb, queue_size=10)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("TrajectoryPredictor initialized, dt=%.2fs", self.dt)

    def _shutdown(self):
        rospy.loginfo("TrajectoryPredictor shutting down")

    def _odom_cb(self, msg):
        self._robot_x = msg.pose.pose.position.x
        self._robot_y = msg.pose.pose.position.y

    def _get_or_create_tracker(self, obs_id, init_x, init_y):
        if obs_id not in self._trackers:
            kf = _make_kf(self.dt, self.proc_noise, self.meas_noise)
            kf.x = np.array([[init_x], [init_y], [0.0], [0.0]])
            self._trackers[obs_id] = {"kf": kf, "missing": 0}
        return self._trackers[obs_id]["kf"]

    def _cleanup_missing(self, seen_ids):
        to_del = []
        for oid, info in self._trackers.items():
            if oid not in seen_ids:
                info["missing"] += 1
                if info["missing"] >= self.max_missing_frames:
                    to_del.append(oid)
        for oid in to_del:
            del self._trackers[oid]

    def _compute_ttc(self, distance, vx, vy, wx, wy):
        """
        TTC = distance / approach_speed
        approach_speed = excavator_speed + (障碍物速度向量 投影到 障碍物→挖掘机方向)
          - 障碍物朝挖掘机靠近：投影为正 → approach_speed 增大
          - 障碍物横向通过：投影为 0 → approach_speed = excavator_speed
          - 障碍物远离：投影为负 → approach_speed 减小，可能为负
        wx, wy 是障碍物世界坐标（odom 系，米）。
        若 approach_speed <= 0 返回 -1（安全）。
        """
        rel_x = wx - self._robot_x
        rel_y = wy - self._robot_y
        d = math.sqrt(rel_x * rel_x + rel_y * rel_y)
        if d < 1e-6:
            if distance <= 0.0:
                return 0.0
            return min(distance / max(self.excavator_speed, 1e-3), 999.0)
        # 单位向量：障碍物 → 挖掘机原点
        ux = -rel_x / d
        uy = -rel_y / d
        radial = vx * ux + vy * uy  # 速度径向分量；>0 表示靠近

        approach = self.excavator_speed + radial
        if approach <= 0.0:
            return -1.0
        if distance <= 0.0:
            return 0.0
        return min(distance / approach, 999.0)

    def _callback(self, msg):
        seen_ids = set()
        out = ObstacleArray()
        out.header = msg.header
        out.dominant_risk_level = msg.dominant_risk_level

        if not msg.obstacles:
            self._cleanup_missing(seen_ids)
            self.pub.publish(out)
            return

        for obs in msg.obstacles:
            oid = obs.obstacle_id
            seen_ids.add(oid)

            # 优先使用 sensor_fusion 写入的世界坐标（米；odom 系）
            # 若 world_xyz 全零（视觉 track 未匹配到 lidar）则跳过卡尔曼预测，仅透传
            has_world = not (
                obs.world_x == 0.0 and obs.world_y == 0.0 and obs.world_z == 0.0
            )

            if has_world:
                meas_x = obs.world_x
                meas_y = obs.world_y

                kf = self._get_or_create_tracker(oid, meas_x, meas_y)
                self._trackers[oid]["missing"] = 0

                kf.predict()
                kf.update(np.array([[meas_x], [meas_y]]))

                vx = float(kf.x[2])
                vy = float(kf.x[3])
                obs.velocity_vec.x = vx
                obs.velocity_vec.y = vy
                obs.velocity_vec.z = 0.0
                obs.relative_velocity = math.sqrt(vx * vx + vy * vy)
                obs.ttc = self._compute_ttc(obs.distance, vx, vy, meas_x, meas_y)
            else:
                # 无 world 坐标 → 速度未知，TTC 设为大值（自然得低风险）
                obs.relative_velocity = 0.0
                obs.velocity_vec.x = 0.0
                obs.velocity_vec.y = 0.0
                obs.velocity_vec.z = 0.0
                obs.ttc = 999.0

            out.obstacles.append(obs)

        self._cleanup_missing(seen_ids)
        self.pub.publish(out)


if __name__ == "__main__":
    try:
        TrajectoryPredictor()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
