#!/usr/bin/env python3
"""模拟行人从10m走近至1m再离开，演示完整避障流程"""
import rospy, math, time
from excavator_msgs.msg import ObstacleInfo, ObstacleArray
from geometry_msgs.msg import PoseStamped

def make_pedestrian(dist, ttc):
    obs = ObstacleInfo()
    obs.header.stamp = rospy.Time.now()
    obs.header.frame_id = 'base_link'
    obs.obstacle_id = 'pedestrian_0'
    obs.obstacle_type = 'person'
    obs.distance = dist
    obs.relative_velocity = dist / ttc if ttc > 0 else 0.0
    obs.ttc = ttc
    obs.risk_score = 0.0
    obs.risk_level = 0
    obs.pose.header = obs.header
    obs.pose.pose.position.x = dist
    obs.pose.pose.position.y = 0.0
    obs.pose.pose.orientation.w = 1.0
    return obs

def main():
    rospy.init_node('inject_pedestrian', anonymous=True)
    pub = rospy.Publisher('/excavator/detected_obstacles', ObstacleArray, queue_size=5)
    rospy.sleep(1.0)

    rate = rospy.Rate(5)

    rospy.logwarn('=== 演示开始：行人从10m走近 ===')

    # 阶段1：行人从10m走近到2m（约15秒）
    for dist in [10, 9, 8, 7, 6, 5, 4.5, 4, 3.5, 3, 2.8, 2.5, 2.3, 2.1, 2.0]:
        if rospy.is_shutdown():
            return
        speed = 0.8
        ttc = dist / speed
        msg = ObstacleArray()
        msg.header.stamp = rospy.Time.now()
        msg.obstacles = [make_pedestrian(dist, ttc)]
        pub.publish(msg)
        rospy.loginfo('行人距离 %.1fm  TTC=%.1fs', dist, ttc)
        rospy.sleep(1.0)

    # 阶段2：行人在危险区停留3秒
    rospy.logwarn('=== 行人进入危险区，保持3秒 ===')
    for _ in range(6):
        if rospy.is_shutdown():
            return
        msg = ObstacleArray()
        msg.header.stamp = rospy.Time.now()
        msg.obstacles = [make_pedestrian(1.8, 2.0)]
        pub.publish(msg)
        rospy.sleep(0.5)

    # 阶段3：行人离开（2m→10m）
    rospy.logwarn('=== 行人离开 ===')
    for dist in [2.5, 3, 4, 5, 6, 8, 10]:
        if rospy.is_shutdown():
            return
        ttc = 99.0
        msg = ObstacleArray()
        msg.header.stamp = rospy.Time.now()
        msg.obstacles = [make_pedestrian(dist, ttc)]
        pub.publish(msg)
        rospy.loginfo('行人离开 %.1fm', dist)
        rospy.sleep(0.8)

    # 阶段4：发空消息，清除障碍物
    rospy.logwarn('=== 障碍物消失，恢复正常 ===')
    for _ in range(5):
        msg = ObstacleArray()
        msg.header.stamp = rospy.Time.now()
        pub.publish(msg)
        rospy.sleep(0.5)

    rospy.logwarn('=== 演示结束 ===')

if __name__ == '__main__':
    main()
