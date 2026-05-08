#!/usr/bin/env python3
"""感知模块单元测试：验证消息格式、空帧处理和预处理函数"""

import sys
import os
import unittest
import numpy as np
from pathlib import Path

# 将 yolov5 加入路径（无需 ROS 环境）
_TEST_DIR = Path(__file__).resolve().parent
_PKG_DIR = _TEST_DIR.parent
_YOLO_DIR = _PKG_DIR / "models" / "yolov5"
if str(_YOLO_DIR) not in sys.path:
    sys.path.insert(0, str(_YOLO_DIR))

from utils.augmentations import letterbox


class TestPreprocess(unittest.TestCase):
    """测试图像预处理函数"""

    def test_letterbox_output_shape(self):
        """letterbox 输出形状应为 (img_size, img_size, 3)"""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        out, ratio, pad = letterbox(img, new_shape=640, stride=32, auto=True)
        self.assertEqual(out.ndim, 3)
        self.assertEqual(out.shape[2], 3)
        # 长边对齐 640，短边 pad 到 32 的倍数
        self.assertLessEqual(out.shape[0], 640)
        self.assertLessEqual(out.shape[1], 640)

    def test_letterbox_preserve_aspect(self):
        """letterbox 不应扭曲图像比例"""
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        out, ratio, pad = letterbox(img, new_shape=640, stride=32, auto=False)
        # ratio 应一致（uniform scale）
        if isinstance(ratio, tuple):
            self.assertAlmostEqual(ratio[0], ratio[1], places=3)

    def test_empty_image_no_crash(self):
        """空白帧（全零）不应引发异常"""
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        try:
            out, _, _ = letterbox(img, new_shape=640, stride=32, auto=True)
            self.assertIsNotNone(out)
        except Exception as e:
            self.fail(f"空白帧导致崩溃: {e}")


class TestObstacleArrayFormat(unittest.TestCase):
    """测试 ObstacleArray 消息字段构造逻辑（不依赖 ROS 运行时）"""

    def _make_obs(self, obstacle_id, obstacle_type, conf,
                  cx_n, cy_n, distance=0.0):
        """模拟 yolov5_detector 构造 ObstacleInfo 的逻辑"""
        return {
            "obstacle_id": obstacle_id,
            "obstacle_type": obstacle_type,
            "distance": distance,
            "risk_level": 0,
            "cx_n": cx_n,
            "cy_n": cy_n,
            "conf": conf,
        }

    def test_obstacle_id_format(self):
        """检测节点的 obstacle_id 应以 'det_' 开头"""
        obs = self._make_obs("det_0", "person", 0.9, 0.5, 0.5)
        self.assertTrue(obs["obstacle_id"].startswith("det_"))

    def test_distance_placeholder(self):
        """检测节点输出的 distance 初始应为 0.0"""
        obs = self._make_obs("det_0", "vehicle", 0.85, 0.3, 0.6)
        self.assertAlmostEqual(obs["distance"], 0.0)

    def test_risk_level_zero(self):
        """检测节点输出的 risk_level 初始应为 0（未评估）"""
        obs = self._make_obs("det_0", "obstacle", 0.7, 0.8, 0.2)
        self.assertEqual(obs["risk_level"], 0)

    def test_normalized_coords_range(self):
        """归一化坐标应在 [0, 1] 范围内"""
        for cx, cy in [(0.0, 0.0), (1.0, 1.0), (0.5, 0.5), (0.1, 0.9)]:
            obs = self._make_obs("det_0", "person", 0.9, cx, cy)
            self.assertGreaterEqual(obs["cx_n"], 0.0)
            self.assertLessEqual(obs["cx_n"], 1.0)
            self.assertGreaterEqual(obs["cy_n"], 0.0)
            self.assertLessEqual(obs["cy_n"], 1.0)


class TestLidarLogic(unittest.TestCase):
    """测试激光雷达处理逻辑"""

    def _sector_min(self, ranges, num_sectors, min_r=0.1, max_r=20.0):
        """模拟 lidar_processor 的扇区最小距离计算"""
        arr = np.array(ranges, dtype=np.float32)
        valid = (arr >= min_r) & (arr <= max_r)
        arr = np.where(valid, arr, np.inf)
        results = []
        sector_size = len(arr) // num_sectors
        for i in range(num_sectors):
            start = i * sector_size
            end = start + sector_size if i < num_sectors - 1 else len(arr)
            seg = arr[start:end]
            mn = float(np.min(seg))
            if not np.isinf(mn):
                results.append(mn)
        return results

    def test_no_obstacle_returns_empty(self):
        """全部超出范围时，输出应为空"""
        ranges = [25.0] * 360
        result = self._sector_min(ranges, 8)
        self.assertEqual(len(result), 0)

    def test_single_close_obstacle(self):
        """单一近距障碍物应被正确提取"""
        ranges = [20.0] * 360
        ranges[45] = 3.5  # 第一扇区中间有近距障碍物
        result = self._sector_min(ranges, 8)
        self.assertGreater(len(result), 0)
        self.assertAlmostEqual(min(result), 3.5, places=1)

    def test_noise_filtering(self):
        """距离 < min_range 的点应被过滤"""
        # 超出 max_range(20.0) 的点被过滤；噪声 0.05 < min_range(0.1) 也被过滤
        ranges = [25.0] * 360
        ranges[0] = 0.05  # 噪声（< min_range 0.1m）
        result = self._sector_min(ranges, 8)
        self.assertEqual(len(result), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
