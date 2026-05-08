#!/usr/bin/env python3
import rospy
from excavator_msgs.msg import ObstacleArray, ObstacleInfo, RiskState

LEVEL_LOW = RiskState.LEVEL_LOW
LEVEL_MEDIUM = RiskState.LEVEL_MEDIUM
LEVEL_HIGH = RiskState.LEVEL_HIGH

INF_FLOAT32 = 999.0


class RiskAssessor:
    def __init__(self):
        rospy.init_node("risk_assessor")

        self.w_distance = rospy.get_param("~w_distance", 0.6)
        self.w_ttc = rospy.get_param("~w_ttc", 0.4)
        self.type_weights = rospy.get_param("~type_weights", {
            "person": 1.5, "vehicle": 1.2, "obstacle": 1.0
        })
        self.risk_low_threshold = rospy.get_param("~risk_low_threshold", 0.3)
        self.risk_high_threshold = rospy.get_param("~risk_high_threshold", 0.7)
        self.safe_distance = rospy.get_param("~safe_distance", 5.0)
        self.critical_distance = rospy.get_param("~critical_distance", 1.0)
        self.safe_ttc = rospy.get_param("~safe_ttc", 5.0)
        self.critical_ttc = rospy.get_param("~critical_ttc", 1.5)

        input_topic = rospy.get_param("~input_topic", "/excavator/predicted_obstacles")
        self.sub = rospy.Subscriber(input_topic, ObstacleArray, self._callback, queue_size=10)
        self.risk_pub = rospy.Publisher("/excavator/risk_state", RiskState, queue_size=10)
        self.assessed_pub = rospy.Publisher("/excavator/assessed_obstacles", ObstacleArray, queue_size=10)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("RiskAssessor initialized, input: %s", input_topic)

    def _shutdown(self):
        rospy.loginfo("RiskAssessor shutting down")

    def _distance_score(self, distance):
        if distance <= self.critical_distance:
            return 1.0
        if distance >= self.safe_distance:
            return 0.0
        span = self.safe_distance - self.critical_distance
        return (self.safe_distance - distance) / span

    def _ttc_score(self, ttc):
        if ttc < 0.0:
            return 0.0
        if ttc <= self.critical_ttc:
            return 1.0
        if ttc >= self.safe_ttc:
            return 0.0
        span = self.safe_ttc - self.critical_ttc
        return (self.safe_ttc - ttc) / span

    def _type_weight(self, obstacle_type):
        return self.type_weights.get(obstacle_type, 1.0)

    def _compute_risk(self, obs):
        d_score = self._distance_score(obs.distance)
        t_score = self._ttc_score(obs.ttc)
        raw = self.w_distance * d_score + self.w_ttc * t_score
        score = min(1.0, raw * self._type_weight(obs.obstacle_type))
        if score >= self.risk_high_threshold:
            level = LEVEL_HIGH
        elif score >= self.risk_low_threshold:
            level = LEVEL_MEDIUM
        else:
            level = LEVEL_LOW
        return score, level

    def _callback(self, msg):
        state = RiskState()
        state.header = msg.header
        assessed = ObstacleArray()
        assessed.header = msg.header

        if not msg.obstacles:
            state.current_level = LEVEL_LOW
            state.min_distance = INF_FLOAT32
            state.min_ttc = INF_FLOAT32
            state.primary_threat_id = ""
            assessed.dominant_risk_level = LEVEL_LOW
            self.risk_pub.publish(state)
            self.assessed_pub.publish(assessed)
            return

        max_score = -1.0
        primary_id = ""
        min_dist = INF_FLOAT32
        min_ttc = INF_FLOAT32

        for obs in msg.obstacles:
            score, level = self._compute_risk(obs)
            obs.risk_score = score
            obs.risk_level = level
            assessed.obstacles.append(obs)

            if score > max_score:
                max_score = score
                primary_id = obs.obstacle_id
            if obs.distance < min_dist:
                min_dist = obs.distance
            if 0.0 < obs.ttc < min_ttc:
                min_ttc = obs.ttc

        if max_score >= self.risk_high_threshold:
            dominant = LEVEL_HIGH
        elif max_score >= self.risk_low_threshold:
            dominant = LEVEL_MEDIUM
        else:
            dominant = LEVEL_LOW

        assessed.dominant_risk_level = dominant
        state.current_level = dominant
        state.min_distance = min_dist
        state.min_ttc = min_ttc
        state.primary_threat_id = primary_id

        self.risk_pub.publish(state)
        self.assessed_pub.publish(assessed)


if __name__ == "__main__":
    try:
        RiskAssessor()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass
