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
from gazebo_msgs.srv import GetModelState, SetModelState, SpawnModel, SpawnModelRequest
from std_srvs.srv import Trigger, TriggerResponse
from excavator_msgs.srv import SpawnObstacle, SpawnObstacleResponse


class ObstacleSpawner:
    def __init__(self):
        rospy.init_node("obstacle_spawner", anonymous=False)

        # 参数
        self._vehicle_speed = rospy.get_param("~vehicle_speed", 3.0)       # m/s
        self._vehicle_model = rospy.get_param("~vehicle_model", "vehicle")
        self._update_rate = rospy.get_param("~update_rate", 10.0)           # Hz
        self._box_size_x = rospy.get_param("~box_size_x", 1.0)
        self._box_size_y = rospy.get_param("~box_size_y", 1.0)
        self._box_size_z = rospy.get_param("~box_size_z", 2.0)
        self._cylinder_radius = rospy.get_param("~cylinder_radius", 0.3)
        self._cylinder_height = rospy.get_param("~cylinder_height", 2.0)
        self._spawned_obstacle_seq = 0

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
        self._wait_for_gazebo_service("/gazebo/set_model_state", wait_total)
        self._wait_for_gazebo_service("/gazebo/spawn_sdf_model", wait_total)

        self._set_model_state = rospy.ServiceProxy(
            "/gazebo/set_model_state", SetModelState
        )
        self._get_model_state = rospy.ServiceProxy(
            "/gazebo/get_model_state", GetModelState
        )
        self._spawn_sdf_model = rospy.ServiceProxy(
            "/gazebo/spawn_sdf_model", SpawnModel
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
          string obstacle_type   # 'vehicle' | 'box' | 'cylinder'
          geometry_msgs/Pose pose
        """
        resp = SpawnObstacleResponse()
        log_message = ""
        try:
            obstacle_type = req.obstacle_type.strip().lower()
            pose = self._request_pose(req)
            x = pose.position.x
            y = pose.position.y

            if obstacle_type == "vehicle":
                self._vehicle_x = x
                self._vehicle_y = y
                self._vehicle_start_x = x
                self._vehicle_start_y = y
                speed = getattr(req, "speed", 0.0)
                if speed > 0:
                    self._vehicle_speed = speed
                self._vehicle_active = True
                self._teleport_vehicle(x, y)
                obstacle_id = self._vehicle_model
                log_message = "vehicle spawned at (%.1f, %.1f) speed=%.1f" % (
                    x,
                    y,
                    self._vehicle_speed,
                )
                self._set_spawn_response(resp, True, obstacle_id, log_message)
            elif obstacle_type in ("box", "cylinder"):
                obstacle_id = self._spawn_static_obstacle(obstacle_type, pose, req)
                log_message = "%s spawned as %s at (%.1f, %.1f, %.1f)" % (
                    obstacle_type,
                    obstacle_id,
                    pose.position.x,
                    pose.position.y,
                    pose.position.z,
                )
                self._set_spawn_response(resp, True, obstacle_id, log_message)
            else:
                log_message = "unsupported obstacle_type='%s'" % req.obstacle_type
                self._set_spawn_response(resp, False, "", log_message)
        except Exception as e:
            log_message = str(e)
            self._set_spawn_response(resp, False, "", log_message)
        rospy.loginfo("[ObstacleSpawner] spawn: %s", log_message)
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

    def _wait_for_gazebo_service(self, service_name, wait_total):
        wait_step = 5.0
        elapsed = 0.0
        while not rospy.is_shutdown() and elapsed < wait_total:
            try:
                rospy.wait_for_service(service_name, timeout=wait_step)
                return
            except rospy.ROSException:
                elapsed += wait_step
                rospy.logwarn(
                    "[ObstacleSpawner] %s 未就绪 (%.1fs/%.1fs)，继续等待...",
                    service_name,
                    elapsed,
                    wait_total,
                )
        raise rospy.ROSException(
            "%s 超过 %.1fs 仍不可用" % (service_name, wait_total)
        )

    def _request_pose(self, req):
        if hasattr(req, "pose"):
            pose = req.pose
            if (
                pose.orientation.x == 0.0
                and pose.orientation.y == 0.0
                and pose.orientation.z == 0.0
                and pose.orientation.w == 0.0
            ):
                pose.orientation.w = 1.0
            return pose

        pose = Pose()
        pose.position.x = getattr(req, "x", 0.0)
        pose.position.y = getattr(req, "y", 0.0)
        pose.position.z = getattr(req, "z", 0.0)
        pose.orientation.w = 1.0
        return pose

    def _request_scale(self, req):
        return max(float(getattr(req, "scale", 1.0)), 0.01)

    def _set_spawn_response(self, resp, success, obstacle_id, message):
        resp.success = success
        if hasattr(resp, "obstacle_id"):
            resp.obstacle_id = obstacle_id
        if hasattr(resp, "message"):
            resp.message = message

    def _next_obstacle_name(self, obstacle_type):
        self._spawned_obstacle_seq += 1
        return "%s_dynamic_%03d" % (obstacle_type, self._spawned_obstacle_seq)

    def _spawn_static_obstacle(self, obstacle_type, pose, req):
        scale = self._request_scale(req)
        model_name = self._next_obstacle_name(obstacle_type)
        spawn_pose = Pose()
        spawn_pose.position.x = pose.position.x
        spawn_pose.position.y = pose.position.y
        spawn_pose.position.z = pose.position.z
        spawn_pose.orientation = pose.orientation
        if obstacle_type == "box":
            model_xml = self._box_sdf(model_name, scale)
            if spawn_pose.position.z == 0.0:
                spawn_pose.position.z = self._box_size_z * scale / 2.0
        else:
            model_xml = self._cylinder_sdf(model_name, scale)
            if spawn_pose.position.z == 0.0:
                spawn_pose.position.z = self._cylinder_height * scale / 2.0

        spawn_req = SpawnModelRequest()
        spawn_req.model_name = model_name
        spawn_req.model_xml = model_xml
        spawn_req.robot_namespace = ""
        spawn_req.initial_pose = spawn_pose
        spawn_req.reference_frame = "world"
        result = self._spawn_sdf_model(spawn_req)
        if not result.success:
            raise rospy.ServiceException(result.status_message)
        return model_name

    def _box_sdf(self, model_name, scale):
        size_x = self._box_size_x * scale
        size_y = self._box_size_y * scale
        size_z = self._box_size_z * scale
        return """<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <static>true</static>
    <link name="link">
      <collision name="collision">
        <geometry>
          <box><size>{x:.3f} {y:.3f} {z:.3f}</size></box>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <box><size>{x:.3f} {y:.3f} {z:.3f}</size></box>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>""".format(name=model_name, x=size_x, y=size_y, z=size_z)

    def _cylinder_sdf(self, model_name, scale):
        radius = self._cylinder_radius * scale
        height = self._cylinder_height * scale
        return """<?xml version="1.0"?>
<sdf version="1.6">
  <model name="{name}">
    <static>true</static>
    <link name="link">
      <collision name="collision">
        <geometry>
          <cylinder>
            <radius>{radius:.3f}</radius>
            <length>{height:.3f}</length>
          </cylinder>
        </geometry>
      </collision>
      <visual name="visual">
        <geometry>
          <cylinder>
            <radius>{radius:.3f}</radius>
            <length>{height:.3f}</length>
          </cylinder>
        </geometry>
      </visual>
    </link>
  </model>
</sdf>""".format(name=model_name, radius=radius, height=height)

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


# CHANGES:
# - Added /gazebo/spawn_sdf_model support for dynamic box and cylinder
#   obstacles while preserving the existing vehicle teleport/control path.
# - Kept compatibility with the actual SpawnObstacle.srv pose/obstacle_id
#   fields and older x/y/z/scale/message-style callers where present.
