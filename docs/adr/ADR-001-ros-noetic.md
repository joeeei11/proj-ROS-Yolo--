# ADR-001：机器人中间件选型 — ROS Noetic

**状态**：已接受  
**日期**：2026-05-08  
**作者**：ExcavatorSafeNav 开发团队

## 背景

需要为挖掘机避障系统选择机器人中间件，候选方案为 ROS Noetic（ROS 1）和 ROS 2 Humble。

## 决策

选用 **ROS Noetic**（Ubuntu 20.04 LTS）作为机器人中间件。

## 理由

1. **生态成熟**：Gazebo 11、nav_msgs/move_base、sensor_msgs 等核心包在 Noetic 下无需适配
2. **社区资源**：DeepSort、YOLOv5 的 ROS wrapper 均以 Noetic 为主要目标
3. **稳定性**：Noetic 为 ROS 1 最终 LTS 版本，bug 修复更积极
4. **工具链**：catkin_make/catkin build、roslaunch、rosbag 工具链完善

## 权衡

- ROS Noetic 官方维护截止 2025 年 5 月；本项目为论文验证，不需要长期维护
- ROS 2 DDS 通信延迟更低，但 Gazebo Classic 与 ROS 2 的集成不如 Noetic 稳定

## 结果

成功构建 8 个 ROS 包，catkin_make 零错误，所有话题/服务接口验证通过。
