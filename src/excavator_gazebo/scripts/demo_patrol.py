#!/usr/bin/env python3
"""动态演示：挖掘机持续来回行驶，循环生成障碍物触发避障响应"""

import rospy
import time
from geometry_msgs.msg import Twist
from excavator_msgs.msg import SystemState

NORMAL        = SystemState.NORMAL
CAUTION       = SystemState.CAUTION
EMERGENCY_STOP = SystemState.EMERGENCY_STOP

class DemoPatrol:
    def __init__(self):
        rospy.init_node('demo_patrol', anonymous=False)

        self.speed      = rospy.get_param('~speed',      0.8)   # m/s
        self.seg_time   = rospy.get_param('~seg_time',  10.0)   # 每段行驶秒数
        self.resume_wait = rospy.get_param('~resume_wait', 3.0) # EMERGENCY_STOP 后等待秒数

        self.fsm_state = NORMAL
        self.direction = 1   # 1=前进  -1=后退
        self.seg_start = None
        self.stopped_at = None

        self.cmd_pub = rospy.Publisher('/cmd_vel', Twist, queue_size=1)
        rospy.Subscriber('/excavator/system_state', SystemState, self._state_cb)

        rospy.on_shutdown(lambda: self.cmd_pub.publish(Twist()))
        rospy.loginfo('[DemoPatrol] 启动：速度=%.1f m/s  每段=%.0fs', self.speed, self.seg_time)

    def _state_cb(self, msg):
        prev = self.fsm_state
        self.fsm_state = msg.state
        if prev != EMERGENCY_STOP and msg.state == EMERGENCY_STOP:
            self.stopped_at = rospy.Time.now()
            rospy.logwarn('[DemoPatrol] 检测到 EMERGENCY_STOP，等待 %.0f 秒后恢复...', self.resume_wait)

    def _try_resume(self):
        """EMERGENCY_STOP 超过 resume_wait 秒后调用 resume 服务"""
        if self.stopped_at is None:
            return
        elapsed = (rospy.Time.now() - self.stopped_at).to_sec()
        if elapsed >= self.resume_wait:
            try:
                from std_srvs.srv import Trigger
                resume = rospy.ServiceProxy('/excavator/resume', Trigger)
                resp = resume()
                if resp.success:
                    rospy.loginfo('[DemoPatrol] 已恢复 NORMAL，继续行驶')
                    self.stopped_at = None
                    self.seg_start = rospy.Time.now()
            except rospy.ServiceException:
                pass

    def run(self):
        rate = rospy.Rate(10)
        self.seg_start = rospy.Time.now()

        while not rospy.is_shutdown():
            now = rospy.Time.now()

            if self.fsm_state == EMERGENCY_STOP:
                # 发零速（FSM 已经发了，这里双保险）
                self.cmd_pub.publish(Twist())
                self._try_resume()
                rate.sleep()
                continue

            # 每段时间到了就换方向
            elapsed = (now - self.seg_start).to_sec()
            if elapsed >= self.seg_time:
                self.direction *= -1
                self.seg_start = now
                rospy.loginfo('[DemoPatrol] 换向 → %s', '前进' if self.direction > 0 else '后退')

            cmd = Twist()
            cmd.linear.x = self.speed * self.direction
            self.cmd_pub.publish(cmd)
            rate.sleep()

if __name__ == '__main__':
    DemoPatrol().run()
