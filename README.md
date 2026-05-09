# 挖掘机作业智能避障系统 (ExcavatorSafeNav)

> **状态**：v1.1-real-sim — Phase 7 真实 Gazebo 端到端仿真验证通过（G1/G2/G3 全部通过）

基于 **YOLOv5 + DeepSort + ROS Noetic + Gazebo 11** 的挖掘机智能避障系统。  
通过激光雷达 + 视觉双模态感知，实时识别行人、车辆和静态障碍物，经多因子风险评估驱动有限状态机，实现绕行 / 减速 / 紧急停止三级差异化避障策略，并经 RRT* 路径规划绕过静态障碍物。

---

## 系统要求

| 项目 | 要求 |
|------|------|
| 操作系统 | **Ubuntu 20.04 LTS**（原生或 WSL2） |
| ROS | Noetic 1.16.x |
| Gazebo | 11 |
| Python | 3.8 |
| PyTorch | 1.12.1（GPU：CUDA 11.6；CPU 模式亦可运行） |
| 内存 | ≥ 8 GB RAM |
| 磁盘 | ≥ 20 GB 可用空间 |

> **Windows 用户**：推荐通过 WSL2 Ubuntu 20.04 运行，参见文末 [WSL2 说明](#wsl2windows-用户)。

---

## 快速开始（3 步）

### 第一步：克隆仓库

```bash
git clone https://github.com/joeeei11/proj-ROS-Yolo--.git excavator_ws
cd excavator_ws
```

### 第二步：一键安装

```bash
# 有 NVIDIA GPU（推荐）
bash install.sh

# 无 GPU / CPU 模式（视觉检测 ~1Hz，激光雷达链路不受影响）
bash install.sh --cpu
```

安装耗时约 15~30 分钟（首次需下载 ROS / Gazebo 约 1.5 GB）。

```bash
source ~/.bashrc
```

### 第三步：运行 G3 验证（静态障碍物绕行）

```bash
# 启动仿真
~/kill_all.sh && ~/start_g3.sh

# 等待 45 秒启动完成，确认 13 个节点在线
sleep 45 && rosnode list | wc -l    # 期望：13

# 传送机器人回原点（仿真启动后会自动行驶，拉回起点再观测）
rosservice call /gazebo/set_model_state '{model_state: {model_name: excavator, pose: {position: {x: 0.0, y: 0.0, z: 0.1}, orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}}, twist: {linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}, reference_frame: world}}'

# 等 4 秒，读取验证结果
sleep 4
echo "=== 障碍物（期望 3 个，距离 3~10m）===" && \
  timeout 8 rostopic echo /excavator/detected_obstacles -n 1 2>/dev/null | grep -E 'obstacle_type|distance:' && \
echo "=== 风险状态（期望 level=1，距离~3.7m）===" && \
  timeout 5 rostopic echo /excavator/risk_state -n 1 2>/dev/null | grep -E 'current_level|min_distance' && \
echo "=== FSM 状态（期望 state=1 CAUTION）===" && \
  timeout 5 rostopic echo /excavator/system_state -n 1 2>/dev/null | grep 'state:'
```

---

## 架构概览

```
Gazebo 仿真世界
  ├── 虚拟摄像头（640×480 @ 30Hz）→ YOLOv5(CPU/GPU) → DeepSort 跟踪
  └── 虚拟激光雷达（360° @ 10Hz）  → lidar_processor（角度聚类 + TF 坐标变换）
                                              ↓
                              sensor_fusion（独立订阅 + 缓存融合）
                                              ↓
                              trajectory_predictor（卡尔曼速度 + TTC）
                                              ↓
                              risk_assessor → risk_state（LOW/MEDIUM/HIGH）
                                              ↓
                              FSM 状态机 → 状态切换 → /cmd_vel
                                              ↓
                              RRT* planner → /planned_path + /planned_cmd_vel
```

### FSM 三级状态

| state | 名称 | 触发条件 | cmd_vel |
|-------|------|---------|---------|
| `0` | NORMAL | 风险 LOW | 1.0 m/s 正常行进 |
| `1` | CAUTION | 风险 MEDIUM（距离 < 5m） | 0.7 m/s 减速 |
| `3` | EMERGENCY_STOP | 风险 HIGH（距离 < 2.5m 或 TTC < 1.5s） | 0，锁定 |

---

## 测试场景

| 场景 | 启动 | 验证结论 |
|------|------|---------|
| G1 headless 烟雾测试 | `roslaunch excavator_gazebo full_simulation.launch headless:=true rviz:=false` | ✅ 13 节点在线，lidar 10Hz |
| G2 行人紧急停止 | `~/start_g2.sh` | ✅ 行人靠近 2.1m → EMERGENCY_STOP → resume → NORMAL |
| G3 静态障碍物绕行 | `~/start_g3.sh` | ✅ 3 障碍物检测，RRT* 路径 0→9.9m |
| G4 高速车辆 | `roslaunch excavator_gazebo full_simulation.launch world_file:=$(rospack find excavator_gazebo)/worlds/test_scenarios/test_vehicle.world scenario:=vehicle rviz:=false` | 可自行验证 |
| G5 多重威胁 | `roslaunch excavator_gazebo full_simulation.launch world_file:=$(rospack find excavator_gazebo)/worlds/test_scenarios/test_multi_threat.world scenario:=multi_threat rviz:=false` | 可自行验证 |

---

## 常用监控命令

```bash
source ~/excavator_ws/devel/setup.bash

# 系统状态快照
echo "=== 节点 ===" && rosnode list
echo "=== FSM ===" && timeout 5 rostopic echo /excavator/system_state -n 1 | grep state:
echo "=== 风险 ===" && timeout 5 rostopic echo /excavator/risk_state -n 1 | grep -E 'current_level|min_distance'

# 持续监控（15 次采样，每 2 秒）
~/monitor_g2.sh

# Web 面板（仿真运行时自动可用）
# 浏览器访问：http://localhost:8080

# 手动恢复（EMERGENCY_STOP 后必须手动解锁）
rosservice call /excavator/resume "{}"

# 停止所有进程
~/kill_all.sh
```

---

## 目录结构

```
excavator_ws/
├── install.sh                          # 一键安装脚本
├── CONTEXT.md                          # 领域背景（施工场景 / 术语定义）
├── src/
│   ├── excavator_msgs/                 # 自定义消息/服务（4 msg + 2 srv）
│   ├── excavator_description/          # URDF 机器人模型（11 连杆）
│   ├── excavator_perception/           # YOLOv5 + DeepSort + 激光雷达融合
│   ├── excavator_risk/                 # 多因子风险评估
│   ├── excavator_decision/             # FSM 状态机
│   ├── excavator_planner/              # RRT* 路径规划（C++17）
│   ├── excavator_gazebo/               # Gazebo 世界文件 + 场景脚本
│   └── excavator_monitor/              # Web 监控面板（Flask，端口 8080）
├── tasks/                              # 开发进度与技术决策（ADR-001~012）
├── docs/                               # 操作手册 / ADR / 设计文档
└── results/                            # 性能测试数据与论文图表
```

---

## 单元测试

```bash
cd ~/excavator_ws && source devel/setup.bash
pytest src/excavator_perception/test/ -v   # 10 项
pytest src/excavator_risk/test/ -v         # 42 项（覆盖率 79%）
pytest src/excavator_decision/test/ -v     # 30 项
```

---

## WSL2（Windows 用户）

1. 在 PowerShell（管理员）中启用 WSL2 并安装 Ubuntu 20.04：
   ```powershell
   wsl --install -d Ubuntu-20.04
   ```
2. 重启后打开 Ubuntu 20.04 终端，完成用户名/密码设置。
3. 在 **Ubuntu 终端**内（不是 PowerShell）按上方快速开始步骤操作即可。

---

## 技术栈

| 组件 | 版本 |
|------|------|
| ROS | Noetic 1.16.x |
| Gazebo | 11 |
| PyTorch | 1.12.1 (CUDA 11.6 / CPU) |
| YOLOv5 | v6.x（yolov5s.pt 权重） |
| DeepSort | deep-sort-realtime 1.3.2 |
| FilterPy | 1.4.5（卡尔曼滤波） |
| C++ | 17（RRT* 规划器） |
| Flask | 2.3.3（Web 监控） |

---

*ExcavatorSafeNav v1.1-real-sim — 2026-05-09*
