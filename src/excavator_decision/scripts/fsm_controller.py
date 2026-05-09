#!/usr/bin/env python3
import rospy
from geometry_msgs.msg import Twist
from std_srvs.srv import Trigger, TriggerResponse
from excavator_msgs.msg import ObstacleArray, RiskState, SystemState
from excavator_msgs.srv import SetMode, SetModeResponse

NORMAL = SystemState.NORMAL
CAUTION = SystemState.CAUTION
PAUSED = SystemState.PAUSED
EMERGENCY_STOP = SystemState.EMERGENCY_STOP

STATE_NAMES = {
    NORMAL: "NORMAL",
    CAUTION: "CAUTION",
    PAUSED: "PAUSED",
    EMERGENCY_STOP: "EMERGENCY_STOP",
}

# Double-threshold hysteresis for state transitions
_N2C = 0.30   # NORMAL -> CAUTION entry
_C2N = 0.20   # CAUTION -> NORMAL exit
_C2P = 0.60   # CAUTION -> PAUSED entry
_P2C = 0.45   # PAUSED -> CAUTION exit (auto-resume)
_P2E = 0.85   # PAUSED -> EMERGENCY_STOP entry


def quintic_polynomial_velocity(v0, vf, t0, tf, t):
    """Smooth velocity from v0 to vf using 5th-order polynomial over [t0, tf]."""
    if tf <= t0:
        return vf
    tau = max(0.0, min(1.0, (t - t0) / (tf - t0)))
    return v0 + (vf - v0) * (10.0 * tau**3 - 15.0 * tau**4 + 6.0 * tau**5)


class FSMController:
    def __init__(self):
        rospy.init_node("fsm_controller")

        self.nominal_speed = rospy.get_param("~nominal_speed", 1.0)
        self.max_deceleration = rospy.get_param("~max_deceleration", 0.5)
        self.paused_check_interval = rospy.get_param("~paused_check_interval", 5.0)
        self.publish_rate = rospy.get_param("~publish_rate", 10.0)

        # FSM state
        self.state = NORMAL
        self.state_entry_time = None       # set in spin()
        self.operation_mode = "walk"

        # Risk score updated from /excavator/assessed_obstacles
        self.current_risk_score = 0.0

        # Velocity smoothing state
        self.current_linear_vel = 0.0
        self.v_trans_start = 0.0
        self.v_trans_target = self.nominal_speed
        self.trans_t0 = None               # set in spin()
        self.trans_duration = 0.0

        # Timer for PAUSED periodic check
        self.last_paused_check = None      # set in spin()

        self.cmd_vel_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=10)
        self.state_pub = rospy.Publisher(
            "/excavator/system_state", SystemState, queue_size=10
        )

        # 来自 RRT* 的规划指令（FSM 仲裁后才转发到 /cmd_vel；FSM 是 /cmd_vel 唯一发布者）
        # 没有规划输入时（即 last_planned_cmd 为 None）默认零速度，避免突发前进
        self.last_planned_cmd = Twist()
        self.last_planned_cmd_time = None
        self.planned_cmd_timeout = rospy.get_param("~planned_cmd_timeout", 0.5)  # s
        rospy.Subscriber(
            "/excavator/planned_cmd_vel", Twist, self._planned_cmd_cb, queue_size=10
        )

        # Subscribe to assessed_obstacles for numeric risk score
        rospy.Subscriber(
            "/excavator/assessed_obstacles",
            ObstacleArray,
            self._assessed_cb,
            queue_size=10,
        )
        # risk_state subscribed for potential future use / logging
        rospy.Subscriber(
            "/excavator/risk_state", RiskState, self._risk_state_cb, queue_size=10
        )

        rospy.Service("/excavator/emergency_stop", Trigger, self._srv_emergency_stop)
        rospy.Service("/excavator/resume", Trigger, self._srv_resume)
        rospy.Service("/excavator/set_mode", SetMode, self._srv_set_mode)

        rospy.on_shutdown(self._on_shutdown)
        rospy.loginfo("FSMController initialized. State: NORMAL")

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def _on_shutdown(self):
        self.cmd_vel_pub.publish(Twist())
        rospy.loginfo("FSMController shutdown: published zero velocity")

    # ── Callbacks ─────────────────────────────────────────────────────────────

    def _assessed_cb(self, msg):
        if msg.obstacles:
            self.current_risk_score = max(obs.risk_score for obs in msg.obstacles)
        else:
            self.current_risk_score = 0.0
        self._evaluate_transitions()

    def _risk_state_cb(self, msg):
        pass  # informational; transitions driven by _assessed_cb

    def _planned_cmd_cb(self, msg):
        """缓存 RRT* 最新规划指令；超时后视为陈旧并自然失效。"""
        self.last_planned_cmd = msg
        self.last_planned_cmd_time = rospy.Time.now()

    def _planned_cmd_fresh(self):
        if self.last_planned_cmd_time is None:
            return False
        return (rospy.Time.now() - self.last_planned_cmd_time).to_sec() <= self.planned_cmd_timeout

    def _arbitrated_cmd(self, linear_cap):
        """仲裁后的速度指令：取 RRT* 规划方向 + FSM 决定的线速度上限。
        linear_cap：FSM 当前允许的最大前进线速度（米/秒，可为 0）。
        """
        out = Twist()
        if not self._planned_cmd_fresh() or linear_cap <= 0.0:
            return out  # 全零（保留 angular=0 防转向漂移）

        plan = self.last_planned_cmd
        # 线速度：受 FSM 上限钳制，且不允许后退（仅前进/停车）
        out.linear.x = max(0.0, min(plan.linear.x, linear_cap))
        # 角速度：直接采用规划值（FSM 不修正方向）
        out.angular.z = plan.angular.z
        return out

    # ── FSM Transition Logic ──────────────────────────────────────────────────

    def _evaluate_transitions(self):
        """Apply hysteresis-guarded state transitions. EMERGENCY_STOP is manual-only."""
        if self.state == EMERGENCY_STOP:
            return

        score = self.current_risk_score

        if self.state == NORMAL:
            if score >= _N2C:
                self._do_transition(CAUTION, "score %.3f >= %.2f" % (score, _N2C))

        elif self.state == CAUTION:
            if score >= _C2P:
                self._do_transition(PAUSED, "score %.3f >= %.2f" % (score, _C2P))
            elif score < _C2N:
                self._do_transition(NORMAL, "score %.3f < %.2f" % (score, _C2N))

        elif self.state == PAUSED:
            if score >= _P2E:
                self._do_transition(
                    EMERGENCY_STOP, "score %.3f >= %.2f" % (score, _P2E)
                )
            # PAUSED -> CAUTION auto-resume is done in _handle_paused (periodic)

    def _do_transition(self, new_state, reason=""):
        old_name = STATE_NAMES[self.state]
        new_name = STATE_NAMES[new_state]

        self.v_trans_start = self.current_linear_vel
        self.v_trans_target = self._target_speed_for(new_state)
        self.trans_t0 = rospy.Time.now()
        delta_v = abs(self.v_trans_target - self.v_trans_start)
        self.trans_duration = (
            delta_v / self.max_deceleration if self.max_deceleration > 0 else 0.0
        )

        self.state = new_state
        self.state_entry_time = rospy.Time.now()
        self.last_paused_check = rospy.Time.now()

        if new_state == EMERGENCY_STOP:
            rospy.logerr("FSM -> EMERGENCY_STOP: %s (was %s)", reason, old_name)
        else:
            rospy.logwarn("FSM %s -> %s: %s", old_name, new_name, reason)

    def _target_speed_for(self, state):
        if state == NORMAL:
            return self.nominal_speed
        if state == CAUTION:
            return self.nominal_speed * 0.7
        return 0.0

    # ── State Handlers ────────────────────────────────────────────────────────

    def _handle_normal(self):
        # NORMAL：以 RRT* 规划方向行驶；线速度上限为 quintic 平滑后的当前允许值
        cap = self._smoothed_vel()
        self.current_linear_vel = cap
        cmd = self._arbitrated_cmd(linear_cap=cap)
        self.cmd_vel_pub.publish(cmd)

    def _handle_caution(self):
        # CAUTION：保留 RRT* 转向，线速度额外乘 0.5 安全系数（基于 _smoothed_vel 已限到 70% nominal）
        cap = self._smoothed_vel() * 0.5
        self.current_linear_vel = cap
        cmd = self._arbitrated_cmd(linear_cap=cap)
        self.cmd_vel_pub.publish(cmd)

    def _handle_paused(self):
        self.current_linear_vel = 0.0
        self.cmd_vel_pub.publish(Twist())
        # Periodically check whether risk dropped enough to auto-resume
        now = rospy.Time.now()
        if (now - self.last_paused_check).to_sec() >= self.paused_check_interval:
            self.last_paused_check = now
            if self.current_risk_score < _P2C:
                rospy.loginfo(
                    "FSM PAUSED auto-resume: score %.3f < %.2f",
                    self.current_risk_score,
                    _P2C,
                )
                self._do_transition(CAUTION, "periodic check, risk cleared")

    def _handle_emergency(self):
        # Publish zero velocity every cycle; no auto-recovery allowed
        self.current_linear_vel = 0.0
        self.cmd_vel_pub.publish(Twist())

    def _smoothed_vel(self):
        now = rospy.Time.now().to_sec()
        t0 = self.trans_t0.to_sec()
        tf = t0 + self.trans_duration
        return quintic_polynomial_velocity(
            self.v_trans_start, self.v_trans_target, t0, tf, now
        )

    # ── Services ──────────────────────────────────────────────────────────────

    def _srv_emergency_stop(self, req):
        self._do_transition(
            EMERGENCY_STOP, "manual /excavator/emergency_stop service"
        )
        return TriggerResponse(success=True, message="Emergency stop activated")

    def _srv_resume(self, req):
        if self.state != EMERGENCY_STOP:
            return TriggerResponse(
                success=False,
                message="Not in EMERGENCY_STOP (current: %s)" % STATE_NAMES[self.state],
            )
        self._do_transition(NORMAL, "manual /excavator/resume service")
        return TriggerResponse(success=True, message="Resumed to NORMAL")

    def _srv_set_mode(self, req):
        valid_modes = {"walk", "rotate", "dig"}
        if req.mode not in valid_modes:
            return SetModeResponse(success=False, message="Unknown mode: %s" % req.mode)
        self.operation_mode = req.mode
        self._publish_system_state()
        rospy.loginfo("Operation mode: %s", req.mode)
        return SetModeResponse(success=True, message="Mode set to: %s" % req.mode)

    # ── Publish ───────────────────────────────────────────────────────────────

    def _publish_system_state(self):
        msg = SystemState()
        msg.header.stamp = rospy.Time.now()
        msg.state = self.state
        msg.reason = STATE_NAMES[self.state]
        if self.state_entry_time is not None:
            msg.state_duration = (rospy.Time.now() - self.state_entry_time).to_sec()
        self.state_pub.publish(msg)

    # ── Main Loop ─────────────────────────────────────────────────────────────

    def spin(self):
        now = rospy.Time.now()
        self.state_entry_time = now
        self.trans_t0 = now
        self.last_paused_check = now

        rate = rospy.Rate(self.publish_rate)
        while not rospy.is_shutdown():
            if self.state == NORMAL:
                self._handle_normal()
            elif self.state == CAUTION:
                self._handle_caution()
            elif self.state == PAUSED:
                self._handle_paused()
            elif self.state == EMERGENCY_STOP:
                self._handle_emergency()
            self._publish_system_state()
            rate.sleep()


if __name__ == "__main__":
    try:
        controller = FSMController()
        controller.spin()
    except rospy.ROSInterruptException:
        pass
