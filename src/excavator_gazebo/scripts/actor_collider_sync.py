#!/usr/bin/env python3
"""
actor_collider_sync.py
每 10Hz 从 /gazebo/model_states 读取 Gazebo Actor 当前位置，
通过 /gazebo/set_model_state 把对应的物理碰撞 cylinder 模型移到同一坐标，
使激光雷达能探测到行人位置。

参数（ROS param）：
  ~actor_names_str   : str  逗号分隔的 Actor 模型名（与 collider_names_str 一一对应）
  ~collider_names_str: str  逗号分隔的碰撞体模型名
  ~sync_rate         : float  同步频率（Hz），默认 10
  ~collider_z        : float  碰撞体中心 Z 偏移（米），默认 0.9（半高，匹配 length=1.8）
"""
import rospy
from gazebo_msgs.msg import ModelStates, ModelState
from gazebo_msgs.srv import SetModelState


class ActorColliderSync:
    def __init__(self):
        rospy.init_node("actor_collider_sync", anonymous=False)

        actors_str    = rospy.get_param("~actor_names_str",    "")
        colliders_str = rospy.get_param("~collider_names_str", "")
        self.actor_names    = [s.strip() for s in actors_str.split(",")    if s.strip()]
        self.collider_names = [s.strip() for s in colliders_str.split(",") if s.strip()]
        self.sync_rate  = rospy.get_param("~sync_rate",  10.0)
        self.collider_z = rospy.get_param("~collider_z", 0.9)

        if len(self.actor_names) != len(self.collider_names):
            rospy.logerr("[ColliderSync] actor_names 与 collider_names 长度不匹配，退出")
            return

        if not self.actor_names:
            rospy.logwarn("[ColliderSync] actor_names_str 为空，节点空转（场景无行人）")
            rospy.spin()
            return

        # 等待 Gazebo 服务就绪
        rospy.loginfo("[ColliderSync] 等待 /gazebo/set_model_state ...")
        try:
            rospy.wait_for_service("/gazebo/set_model_state", timeout=30.0)
        except rospy.ROSException:
            rospy.logerr("[ColliderSync] /gazebo/set_model_state 30s 内未就绪，退出")
            return

        self._set_state = rospy.ServiceProxy("/gazebo/set_model_state", SetModelState)

        # model_states 缓存
        self._model_positions = {}
        rospy.Subscriber("/gazebo/model_states", ModelStates,
                         self._model_states_cb, queue_size=1)

        rospy.Timer(rospy.Duration(1.0 / self.sync_rate), self._sync_cb)
        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("[ColliderSync] 启动，同步 %d 组 Actor↔Collider @ %.0fHz",
                      len(self.actor_names), self.sync_rate)

    def _model_states_cb(self, msg: ModelStates):
        for name, pose in zip(msg.name, msg.pose):
            self._model_positions[name] = pose

    def _sync_cb(self, _event):
        for actor, collider in zip(self.actor_names, self.collider_names):
            pose = self._model_positions.get(actor)
            if pose is None:
                continue
            state = ModelState()
            state.model_name = collider
            state.pose.position.x = pose.position.x
            state.pose.position.y = pose.position.y
            state.pose.position.z = self.collider_z
            state.pose.orientation.w = 1.0
            state.reference_frame = "world"
            try:
                self._set_state(state)
            except rospy.ServiceException as e:
                rospy.logwarn_throttle(5.0, "[ColliderSync] set_model_state 失败: %s", e)

    def _shutdown(self):
        rospy.loginfo("[ColliderSync] 节点关闭")


if __name__ == "__main__":
    try:
        node = ActorColliderSync()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
