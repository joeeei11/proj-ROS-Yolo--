#!/usr/bin/env python3
"""
obstacle_spawner.py

动态障碍物控制器节点。
- 订阅/发布：控制 Gazebo 中已存在的 vehicle 模型做直线运动
- 服务：/excavator/spawn_obstacle（SpawnObstacle.srv）
- 行人（Actor）由 Gazebo world 自身的 <script> 控制，无需此节点干预
"""

import math
import rospy
from geometry_msgs.msg import Twist, Pose
from gazebo_msgs.msg import ModelState
from gazebo_msgs.srv import SetModelState, GetModelState
from std_srvs.srv import Trigger, TriggerResponse
from excavator_msgs.srv import SpawnObstacle, SpawnObstacleResponse


class ObstacleSpawner:
    def __init__(self):
        rospy.init_node("obstacle_spawner", anonymous=False)

        # 参数
        self._vehicle_speed = rospy.get_param("~vehicle_speed", 3.0)       # m/s
        self._vehicle_model = rospy.get_param("~vehicle_model", "vehicle")
        self._update_rate = rospy.get_param("~update_rate", 10.0)           # Hz

        # 车辆运动状态
        self._vehicle_active = False
        self._vehicle_start_x = 20.0
        self._vehicle_start_y = 0.0
        self._vehicle_target_x = 0.0
        self._vehicle_target_y = 0.0
        self._vehicle_x = self._vehicle_start_x
        self._vehicle_y = self._vehicle_start_y

        # Gazebo 服务（带重试，避免 Gazebo 启动慢于 spawner 时永久退出）
        wait_total = rospy.get_param("~gazebo_wait_total_sec", 60.0)
        wait_step = 5.0
        elapsed = 0.0
        ready = False
        while not rospy.is_shutdown() and elapsed < wait_total:
            try:
                rospy.wait_for_service("/gazebo/set_model_state", timeout=wait_step)
                ready = True
                break
            except rospy.ROSException:
                elapsed += wait_step
                rospy.logwarn(
                    "[ObstacleSpawner] /gazebo/set_model_state 未就绪 (%.1fs/%.1fs)，继续等待...",
                    elapsed, wait_total,
                )
        if not ready:
            # 抛出异常让 launch 的 respawn 机制再起一次（避免永久退出）
            raise rospy.ROSException(
                "Gazebo SetModelState 超过 %.1fs 仍不可用" % wait_total
            )

        self._set_model_state = rospy.ServiceProxy(
            "/gazebo/set_model_state", SetModelState
        )
        self._get_model_state = rospy.ServiceProxy(
            "/gazebo/get_model_state", GetModelState
        )

        # 服务：spawn_obstacle
        rospy.Service(
            "/excavator/spawn_obstacle", SpawnObstacle, self._handle_spawn
        )

        # 服务：reset_obstacles（将车辆复位到起点）
        rospy.Service(
            "/excavator/reset_obstacles", Trigger, self._handle_reset
        )

        # 控制循环
        self._timer = rospy.Timer(
            rospy.Duration(1.0 / self._update_rate), self._control_loop
        )

        rospy.loginfo("[ObstacleSpawner] 初始化完成，vehicle_speed=%.1f m/s", self._vehicle_speed)

    # ------------------------------------------------------------------
    # 服务处理
    # ------------------------------------------------------------------

    def _handle_spawn(self, req):
        """
        SpawnObstacle.srv：
          string obstacle_type   # 'vehicle' | 'static'
          float64 x
          float64 y
          float64 speed          # 仅 vehicle 有效
        """
        resp = SpawnObstacleResponse()
        try:
            if req.obstacle_type == "vehicle":
                self._vehicle_x = req.x
                self._vehicle_y = req.y
                self._vehicle_start_x = req.x
                self._vehicle_start_y = req.y
                if req.speed > 0:
                    self._vehicle_speed = req.speed
                self._vehicle_active = True
                self._teleport_vehicle(req.x, req.y)
                resp.success = True
                resp.message = "vehicle spawned at (%.1f, %.1f) speed=%.1f" % (
                    req.x, req.y, self._vehicle_speed
                )
            else:
                resp.success = False
                resp.message = "只支持 obstacle_type='vehicle'"
        except Exception as e:
            resp.success = False
            resp.message = str(e)
        rospy.loginfo("[ObstacleSpawner] spawn: %s", resp.message)
        return resp

    def _handle_reset(self, req):
        """复位车辆到初始位置并停止运动。"""
        self._vehicle_active = False
        self._vehicle_x = self._vehicle_start_x
        self._vehicle_y = self._vehicle_start_y
        self._teleport_vehicle(self._vehicle_start_x, self._vehicle_start_y)
        return TriggerResponse(success=True, message="obstacles reset")

    # ------------------------------------------------------------------
    # 运动控制循环
    # ------------------------------------------------------------------

    def _control_loop(self, event):
        if not self._vehicle_active:
            return

        dt = 1.0 / self._update_rate
        dx = self._vehicle_target_x - self._vehicle_x
        dy = self._vehicle_target_y - self._vehicle_y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 0.5:
            # 到达目标：停止
            self._vehicle_active = False
            rospy.loginfo("[ObstacleSpawner] 车辆到达目标点，停止")
            return

        # 朝目标方向以固定速度移动
        vx = (dx / dist) * self._vehicle_speed
        vy = (dy / dist) * self._vehicle_speed
        self._vehicle_x += vx * dt
        self._vehicle_y += vy * dt

        # 计算朝向角（朝运动方向）
        yaw = math.atan2(-dy, -dx)  # 车头朝反向（面向来源方向）

        self._teleport_vehicle(self._vehicle_x, self._vehicle_y, yaw)

    def _teleport_vehicle(self, x, y, yaw=None):
        """通过 Gazebo SetModelState 直接设置车辆位置。"""
        if yaw is None:
            yaw = math.pi  # 默认朝 -x 方向

        state = ModelState()
        state.model_name = self._vehicle_model
        state.reference_frame = "world"
        state.pose.position.x = x
        state.pose.position.y = y
        state.pose.position.z = 1.5  # 车辆模型中心 z=1.5m（高3.0m），覆盖激光雷达扫描面 z≈2.95m
        # 将 yaw 转为四元数（绕 Z 轴）
        state.pose.orientation.z = math.sin(yaw / 2.0)
        state.pose.orientation.w = math.cos(yaw / 2.0)
        # 设置速度（让 Gazebo 物理感知速度，用于 TTC 计算）
        if self._vehicle_active:
            dx = self._vehicle_target_x - x
            dy = self._vehicle_target_y - y
            dist = math.sqrt(dx * dx + dy * dy) + 1e-6
            state.twist.linear.x = (dx / dist) * self._vehicle_speed
            state.twist.linear.y = (dy / dist) * self._vehicle_speed
        try:
            self._set_model_state(state)
        except rospy.ServiceException as e:
            rospy.logwarn_throttle(5.0, "[ObstacleSpawner] set_model_state 失败: %s", e)

    def spin(self):
        rospy.spin()


# ------------------------------------------------------------------
# 测试场景快速启动函数（供 launch 文件调用）
# ------------------------------------------------------------------

def start_vehicle_scenario():
    """vehicle 场景：车辆从 x=20 以 3m/s 驶向 x=0。"""
    spawner = ObstacleSpawner()
    rospy.sleep(2.0)  # 等待 Gazebo 稳定

    spawner._vehicle_x = 20.0
    spawner._vehicle_y = 0.0
    spawner._vehicle_target_x = -2.0
    spawner._vehicle_target_y = 0.0
    spawner._vehicle_active = True
    rospy.loginfo("[ObstacleSpawner] 车辆场景启动：x=20 → x=-2, speed=%.1f", spawner._vehicle_speed)
    spawner.spin()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "vehicle":
        start_vehicle_scenario()
    else:
        node = ObstacleSpawner()
        node.spin()
