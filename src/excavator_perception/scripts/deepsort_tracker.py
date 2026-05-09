#!/usr/bin/env python3
"""DeepSort 跟踪节点：融合检测框与相机图像，发布带稳定 track_id 的 ObstacleArray"""

import rospy
import cv2
import numpy as np
import message_filters
from cv_bridge import CvBridge

from sensor_msgs.msg import Image
from excavator_msgs.msg import ObstacleInfo, ObstacleArray

from deep_sort_realtime.deepsort_tracker import DeepSort


class DeepSortTrackerNode:
    def __init__(self):
        rospy.init_node("deepsort_tracker", anonymous=False)

        max_age = rospy.get_param("~max_age", 50)
        n_init = rospy.get_param("~n_init", 3)
        max_iou_distance = rospy.get_param("~max_iou_distance", 0.7)
        max_cosine_distance = rospy.get_param("~max_cosine_distance", 0.2)
        embedder_gpu = rospy.get_param("~embedder_gpu", True)

        self.tracker = DeepSort(
            max_age=max_age,
            n_init=n_init,
            max_iou_distance=max_iou_distance,
            max_cosine_distance=max_cosine_distance,
            embedder="mobilenet",
            half=True,
            bgr=True,
            embedder_gpu=embedder_gpu,
        )
        rospy.loginfo("[DeepSort] 初始化完成 max_age=%d n_init=%d", max_age, n_init)

        self.bridge = CvBridge()

        # 发布者
        self.track_pub = rospy.Publisher(
            "/excavator/tracked_obstacles", ObstacleArray, queue_size=5)

        # 时间同步订阅（slop=0.05s，符合 decisions.md 规范）
        det_sub = message_filters.Subscriber(
            "/excavator/raw_detections", ObstacleArray)
        img_sub = message_filters.Subscriber(
            "/camera/image_raw", Image)

        self.sync = message_filters.ApproximateTimeSynchronizer(
            [det_sub, img_sub], queue_size=5, slop=0.05)
        self.sync.registerCallback(self._sync_cb)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("[DeepSort] 节点启动，等待检测+图像同步...")

    def _sync_cb(self, det_msg: ObstacleArray, img_msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(img_msg, desired_encoding="bgr8")
        except Exception as e:
            rospy.logerr("[DeepSort] 图像转换失败: %s", e)
            return

        # 构造 DeepSort 输入格式：[([x1,y1,x2,y2], conf, class_name), ...]
        raw_dets = []
        obs_meta = []  # 保留原始 ObstacleInfo 中的其他字段
        h, w = frame.shape[:2]

        for obs in det_msg.obstacles:
            conf = obs.pose.pose.position.z

            # 优先使用 yolov5_detector 写入的真实像素 bbox
            has_real_bbox = (obs.bbox_x2 > obs.bbox_x1) and (obs.bbox_y2 > obs.bbox_y1)
            if has_real_bbox:
                x1 = int(max(0, obs.bbox_x1))
                y1 = int(max(0, obs.bbox_y1))
                x2 = int(min(w, obs.bbox_x2))
                y2 = int(min(h, obs.bbox_y2))
            else:
                # Fallback：旧消息（bbox 全零）→ 按归一化中心 + 10% 估算
                cx_n = obs.pose.pose.position.x
                cy_n = obs.pose.pose.position.y
                bw = int(w * 0.1)
                bh = int(h * 0.1)
                cx = int(cx_n * w)
                cy = int(cy_n * h)
                x1 = max(0, cx - bw // 2)
                y1 = max(0, cy - bh // 2)
                x2 = min(w, cx + bw // 2)
                y2 = min(h, cy + bh // 2)

            raw_dets.append(([x1, y1, x2, y2], float(conf), obs.obstacle_type))
            obs_meta.append(obs)

        if not raw_dets:
            # 无检测时仍需调用 tracker 以更新内部状态（允许轨迹老化）
            self.tracker.update_tracks([], frame=frame)
            # 发布空数组保持话题活跃
            empty = ObstacleArray()
            empty.header = det_msg.header
            self.track_pub.publish(empty)
            return

        tracks = self.tracker.update_tracks(raw_dets, frame=frame)

        out_msg = ObstacleArray()
        out_msg.header = det_msg.header
        max_risk = 0

        for track in tracks:
            if not track.is_confirmed():
                continue

            # 构造已跟踪的 ObstacleInfo
            obs_out = ObstacleInfo()
            obs_out.header = det_msg.header
            obs_out.obstacle_id = f"track_{track.track_id}"
            obs_out.obstacle_type = track.det_class or "unknown"
            obs_out.distance = 0.0      # lidar 融合节点填充
            obs_out.risk_level = 0      # risk assessor 填充
            # 跟踪框中心（像素，归一化，向后兼容旧下游）
            ltrb = track.to_ltrb()
            cx_t = float((ltrb[0] + ltrb[2]) / 2) / w
            cy_t = float((ltrb[1] + ltrb[3]) / 2) / h
            obs_out.pose.header = det_msg.header
            obs_out.pose.pose.position.x = cx_t
            obs_out.pose.pose.position.y = cy_t
            obs_out.pose.pose.position.z = float(track.det_conf or 0.0)

            # 透传真实像素 bbox（供 sensor_fusion 用相机内参 + lidar TF 投影匹配）
            obs_out.bbox_x1 = float(max(0.0, ltrb[0]))
            obs_out.bbox_y1 = float(max(0.0, ltrb[1]))
            obs_out.bbox_x2 = float(min(float(w), ltrb[2]))
            obs_out.bbox_y2 = float(min(float(h), ltrb[3]))

            out_msg.obstacles.append(obs_out)

        out_msg.dominant_risk_level = max_risk
        self.track_pub.publish(out_msg)

    def _shutdown(self):
        rospy.loginfo("[DeepSort] 节点关闭")


if __name__ == "__main__":
    node = DeepSortTrackerNode()
    rospy.spin()
