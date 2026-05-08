#!/usr/bin/env python3
"""YOLOv5 检测节点：订阅相机图像，发布原始检测结果到 /excavator/raw_detections"""

import sys
import os
import rospy
import cv2
import torch
import numpy as np
from cv_bridge import CvBridge
from pathlib import Path

from sensor_msgs.msg import Image
from std_msgs.msg import Header
from excavator_msgs.msg import ObstacleInfo, ObstacleArray

# 将 yolov5 加入 Python path
_SCRIPT_DIR = Path(__file__).resolve().parent
_YOLO_DIR = _SCRIPT_DIR.parent / "models" / "yolov5"
if str(_YOLO_DIR) not in sys.path:
    sys.path.insert(0, str(_YOLO_DIR))

from models.common import DetectMultiBackend
from utils.general import check_img_size, non_max_suppression, scale_coords
from utils.torch_utils import select_device
from utils.augmentations import letterbox
from utils.plots import Annotator, colors


class YoloV5DetectorNode:
    def __init__(self):
        rospy.init_node("yolov5_detector", anonymous=False)

        # 读取参数
        weights_path = rospy.get_param("~weights_path",
            str(_SCRIPT_DIR.parent / "models" / "best.pt"))
        self.conf_thres = rospy.get_param("~conf_thres", 0.5)
        self.iou_thres = rospy.get_param("~iou_thres", 0.45)
        device_str = str(rospy.get_param("~device", "0"))
        img_size = rospy.get_param("~img_size", 640)
        self.class_names = rospy.get_param(
            "~class_names", ["person", "vehicle", "obstacle"])

        # 初始化设备与模型
        self.device = select_device(device_str)
        self.model = DetectMultiBackend(
            weights_path, device=self.device, dnn=False)
        self.stride = self.model.stride
        self.img_size = check_img_size(img_size, s=self.stride)

        # 半精度（GPU 模式）
        self.half = self.device.type != "cpu"
        if self.half:
            self.model.model.half()
        else:
            self.model.model.float()

        # 模型预热
        self.model.warmup(imgsz=(1, 3, self.img_size, self.img_size))
        rospy.loginfo("[YoloDetector] 模型加载完成，device=%s half=%s",
                      self.device, self.half)

        self.bridge = CvBridge()

        # 发布者
        self.det_pub = rospy.Publisher(
            "/excavator/raw_detections", ObstacleArray, queue_size=5)
        self.img_pub = rospy.Publisher(
            "/excavator/detection_image", Image, queue_size=1)

        # 订阅者（异步回调，无阻塞）
        rospy.Subscriber("/camera/image_raw", Image,
                         self._image_cb, queue_size=1, buff_size=2**24)

        rospy.on_shutdown(self._shutdown)
        rospy.loginfo("[YoloDetector] 节点启动，等待图像...")

    @torch.no_grad()
    def _image_cb(self, msg: Image):
        try:
            cv_img = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        except Exception as e:
            rospy.logerr("[YoloDetector] cv_bridge 转换失败: %s", e)
            return

        img, img0 = self._preprocess(cv_img)

        # 推理
        tensor = torch.from_numpy(img).to(self.device)
        tensor = tensor.half() if self.half else tensor.float()
        tensor /= 255.0
        if tensor.ndim == 3:
            tensor = tensor.unsqueeze(0)

        pred = self.model(tensor, augment=False, visualize=False)
        pred = non_max_suppression(
            pred, self.conf_thres, self.iou_thres,
            classes=None, agnostic_nms=False, max_det=50)

        # 构造消息
        array_msg = ObstacleArray()
        array_msg.header = msg.header

        det = pred[0]
        annotator = Annotator(img0.copy(),
                              line_width=2, example=str(self.class_names))

        if len(det):
            det[:, :4] = scale_coords(
                tensor.shape[2:], det[:, :4], img0.shape).round()
            det_cpu = det.cpu().numpy()

            for i, (*xyxy, conf, cls_id) in enumerate(det_cpu):
                c = int(cls_id)
                label = self.class_names[c] if c < len(self.class_names) \
                    else f"cls{c}"
                obs = ObstacleInfo()
                obs.header = msg.header
                obs.obstacle_id = f"det_{i}"
                obs.obstacle_type = label
                obs.distance = 0.0          # lidar 融合后填充
                obs.risk_level = 0          # risk assessor 填充
                # 归一化像素中心作为临时位姿占位
                cx = float((xyxy[0] + xyxy[2]) / 2) / img0.shape[1]
                cy = float((xyxy[1] + xyxy[3]) / 2) / img0.shape[0]
                obs.pose.header = msg.header
                obs.pose.pose.position.x = cx
                obs.pose.pose.position.y = cy
                obs.pose.pose.position.z = float(conf)
                array_msg.obstacles.append(obs)

                annotator.box_label(
                    xyxy, f"{label} {conf:.2f}", color=colors(c, True))

        self.det_pub.publish(array_msg)

        # 发布标注图像
        annotated = annotator.result()
        try:
            self.img_pub.publish(
                self.bridge.cv2_to_imgmsg(annotated, encoding="bgr8"))
        except Exception:
            pass

    def _preprocess(self, img):
        img0 = img.copy()
        img = np.array([letterbox(img, self.img_size,
                                  stride=self.stride, auto=True)[0]])
        img = img[..., ::-1].transpose((0, 3, 1, 2))
        img = np.ascontiguousarray(img)
        return img, img0

    def _shutdown(self):
        rospy.loginfo("[YoloDetector] 节点关闭")


if __name__ == "__main__":
    node = YoloV5DetectorNode()
    rospy.spin()
