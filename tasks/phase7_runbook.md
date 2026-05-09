# Phase 7 验证 Runbook — Claude Code 自动执行

> **给 Claude Code 的说明**：按本文件从上到下依次执行。每节有「预期输出」和「失败处置」，
> 遇到失败先按指引修复，再继续下一节。用户只看结果，无需询问。

---

## 0. 背景与当前状态

| 项目 | 说明 |
|------|------|
| 工作空间 | `\\wsl.localhost\Ubuntu2004\home\excavator\excavator_ws` |
| Windows 项目根 | `D:\MYSOFTWAREOFtechnology\ClaudeCodeFile\Projects\YoloWithROS` |
| ROS 发行版 | Noetic / Gazebo 11 / Ubuntu 20.04 (WSL2 Ubuntu2004) |
| 当前 git 分支 | master（Windows 侧）/ excavator_ws 在 WSL2 内 |

**Phase 7 已完成的代码修改（无需再做）：**
- A1 gazebo_world.launch 加 joint_state_publisher ✅
- A2 test_multi_threat.world 车辆名改为 `vehicle` ✅
- A3 obstacle_spawner respawn 容错 ✅
- B1 ObstacleInfo.msg 新增 7 字段 ✅
- C1-C5 感知链真实化（YOLO 类别映射、lidar 聚类、TF 坐标、卡尔曼） ✅
- D1-D3 控制层（FSM 唯一发布 /cmd_vel、RRT* 订阅 /odom、世界坐标） ✅
- E1 行人物理碰撞体 ped_collider + actor_collider_sync.py ✅
- F1 catkin_make 0 ERROR ✅
- **sensor_fusion.py 未匹配 lidar 聚类直通** ✅（最后一次会话已修改）

**待验证（本 Runbook 的目标）：**
- [ ] G1 headless 烟雾测试
- [ ] G2 行人场景 GUI 端到端（EMERGENCY_STOP + cmd_vel = 0）
- [ ] G3 静态场景 RRT\* 真实绕障

---

## 1. 准备：重新编译

```bash
# 在 WSL2 终端执行（用户名 excavator）
cd ~/excavator_ws
catkin_make -DCMAKE_BUILD_TYPE=Release 2>&1 | tail -20
source devel/setup.bash
```

**预期输出**：最后几行含 `[100%]` 且无 `error:`。

**失败处置**：
- 若有 `excavator_msgs` 相关编译错误 → 先 `catkin_make --only-pkg-with-deps excavator_msgs`，再全量编译。
- 若有 C++ 错误 → 读取 `src/excavator_planner/src/rrt_star_planner.cpp` 定位报错行修复。

---

## 2. G1：headless 烟雾测试

### 2.1 启动系统

```bash
# 终端 A（主仿真进程，保持运行）
cd ~/excavator_ws && source devel/setup.bash
roslaunch excavator_gazebo full_simulation.launch \
    headless:=true rviz:=false scenario:=main
```

等待日志出现 `[ObstacleSpawner] 初始化完成` 或 `[SensorFusion] 节点启动`（约 15-30 秒）。

### 2.2 逐项检查（终端 B）

```bash
source ~/excavator_ws/devel/setup.bash

echo "=== 节点列表 ===" && rosnode list

echo "=== 话题频率 ===" && \
    timeout 6 rostopic hz /camera/image_raw & \
    timeout 6 rostopic hz /lidar/scan & \
    timeout 6 rostopic hz /odom & \
    timeout 6 rostopic hz /excavator/detected_obstacles & \
    wait

echo "=== lidar 聚类样本 ===" && \
    timeout 8 rostopic echo /excavator/lidar_obstacles -n 1

echo "=== detected_obstacles 样本 ===" && \
    timeout 8 rostopic echo /excavator/detected_obstacles -n 1 | head -40

echo "=== TF 树 ===" && \
    timeout 5 rosrun tf tf_echo base_footprint camera_optical_link 2>&1 | head -10
```

**G1 通过标准**：

| 检查项 | 预期 |
|--------|------|
| rosnode list 含 | `yolov5_detector` `deepsort_tracker` `lidar_processor` `sensor_fusion` `trajectory_predictor` `risk_assessor` `fsm_controller` `rrt_star_planner` `joint_state_publisher` `robot_state_publisher` `monitor_server` |
| /camera/image_raw | ≈ 30 Hz |
| /lidar/scan | ≈ 10 Hz |
| /odom | ≥ 20 Hz |
| /excavator/detected_obstacles | ≥ 1 Hz（含 `obstacle_type: "obstacle"` 的围栏聚类） |
| TF tf_echo | 输出有效变换，无 `ExtrapolationException` |

**失败处置**：

- `detected_obstacles` 无消息 → `rosnode info /sensor_fusion` 看订阅话题是否有发布者；若 `tracked_obstacles` 无发布者则检查 deepsort_tracker 是否崩溃（`rosnode info /deepsort_tracker`）。
- `lidar_obstacles` 全 inf → 障碍物高度问题，检查 `construction_site.world` 围栏 box size z 是否为 5.0m（应覆盖激光雷达安装高度 z≈2.95m）。
- TF 报错 → 检查 `gazebo_world.launch` 是否含 `joint_state_publisher` 节点。
- 某节点崩溃（not in rosnode list）→ `rosrun <pkg> <node>.py` 单独启动看报错，修复后重启全系统。

---

## 3. G2：行人场景 GUI 端到端验证

> 本步骤需要 WSLg 图形界面（用户确认 WSLg 已就绪）。

### 3.1 停止 G1 仿真

```bash
# 终端 A 按 Ctrl+C；若残留进程：
pkill -f "gzserver\|gzclient" 2>/dev/null; sleep 3
```

### 3.2 启动行人场景

```bash
# 终端 A
cd ~/excavator_ws && source devel/setup.bash
roslaunch excavator_gazebo full_simulation.launch \
    scenario:=pedestrian rviz:=true record_bag:=true
```

等待 Gazebo GUI 和 RViz 窗口打开（约 30 秒）。

### 3.3 监控关键话题（终端 B）

```bash
source ~/excavator_ws/devel/setup.bash

# 持续监控风险状态和速度指令（Ctrl+C 手动停止）
echo "--- 监控 risk_state + system_state + cmd_vel ---"
rostopic echo /excavator/risk_state &   PID1=$!
rostopic echo /excavator/system_state & PID2=$!
rostopic echo /cmd_vel &                PID3=$!
wait $PID1 $PID2 $PID3
```

### 3.4 等待并验证

行人 Actor 初始在 y=8m，约 **6-8 秒**后走近至 y≈1.5m（最近距离）。

**G2 通过标准**：

| 时间节点 | 预期行为 |
|----------|---------|
| 行人距离 > 5m | `risk_state.current_level = 0`（LOW），`system_state.state = 0`（NORMAL），`cmd_vel.linear.x > 0` |
| 行人距离 2.5-5m | `risk_state.current_level = 1`（MEDIUM），`system_state.state = 1`（CAUTION），`cmd_vel.linear.x` 减半 |
| 行人距离 < 2.5m | `risk_state.current_level = 2`（HIGH），`system_state.state = 3`（EMERGENCY_STOP），`cmd_vel.linear.x == 0` |
| 行人离开后手动恢复 | `rosservice call /excavator/resume "{}"` → `system_state.state = 0` |

**rosbag 录制确认**：
```bash
ls -lh ~/.ros/*.bag 2>/dev/null || ls -lh ~/excavator_data/*.bag 2>/dev/null
```
应有新生成的 `.bag` 文件。

**失败处置**：

- EMERGENCY_STOP 不触发 → 检查 `rostopic echo /excavator/detected_obstacles -n 3`，确认行人接近时出现 `obstacle_type: "person"` 且 `distance < 2.5`。若无 → actor_collider_sync.py 没有同步 ped_collider 位置，检查该节点是否启动。
- cmd_vel 不归零 → `rostopic list | grep cmd_vel`，确认只有 `/cmd_vel` 一个话题。若 RRT\* 还在发布 `/cmd_vel` → 检查 `rrt_star_planner.cpp` 中 `cmd_vel_pub_` 的话题名应为 `/excavator/planned_cmd_vel`。
- Gazebo GUI 打不开 → 确认 `echo $DISPLAY` 输出 `:0`，`echo $WAYLAND_DISPLAY` 输出 `wayland-0`。

---

## 4. G3：静态场景 RRT\* 真实绕障验证

### 4.1 停止 G2 仿真

```bash
pkill -f "gzserver\|gzclient" 2>/dev/null; sleep 3
```

### 4.2 启动静态场景

```bash
cd ~/excavator_ws && source devel/setup.bash
roslaunch excavator_gazebo full_simulation.launch \
    scenario:=static rviz:=true
```

### 4.3 验证（终端 B）

```bash
source ~/excavator_ws/devel/setup.bash

# 看 detected_obstacles 是否含静态障碍物
timeout 10 rostopic echo /excavator/detected_obstacles -n 1 | grep -E "obstacle_type|distance|world_x|world_y"

# 看规划路径是否绕障
timeout 10 rostopic echo /planned_path -n 1 | head -20
```

**G3 通过标准**：

| 检查项 | 预期 |
|--------|------|
| detected_obstacles | 含 3 个 `obstacle_type: "obstacle"`，distance ≈ 3~10m（测试场景障碍物位于 (4,0), (6,2), (5,-2) 附近） |
| /planned_path | 路径点不全在 (0,0) 附近；x 坐标覆盖 0→10m 范围，有明显绕障弯曲 |
| RViz 观察 | `/planned_path` 绿色线条绕开橙色/蓝色障碍物方块，终点指向 (10, 0) |

**失败处置**：

- `detected_obstacles` 空 → `test_static.world` 中 obstacle_A/B/C 的 box z 中心应为 1.75m，height=3.5m（覆盖激光雷达 z≈2.95m）。若不符合，参考 `tasks/decisions.md` ADR-010 修改。
- `/planned_path` 路径点都在 (0~1m) 附近 → RRT\* 的 `obstacleCb` 未使用 `world_x/world_y`，检查 `rrt_star_planner.cpp` 中 `obstacleCb` 函数，`co.cx` 应赋值 `obs.world_x`。

---

## 5. 收尾工作

所有 G1/G2/G3 通过后执行：

### 5.1 更新 progress.md

修改 `tasks/progress.md`（Windows 路径 `D:\MYSOFTWAREOFtechnology\ClaudeCodeFile\Projects\YoloWithROS\tasks\progress.md`）：

- 将顶部 Phase 7 状态行改为 `## 当前状态：Phase 7 ✅ 已完成（2026-05-09）`
- 将 G1/G2/G3 的 `[ ]` 全部改为 `[x]`

### 5.2 在 WSL2 git 中提交并打 tag

```bash
cd ~/excavator_ws
git add -A
git commit -m "feat: Phase 7 完成 - 真实端到端仿真验证通过 (G1/G2/G3)"
git tag v1.1-real-sim
git log --oneline -3
```

### 5.3 在 Windows git 中提交（可选）

```powershell
# Windows PowerShell（D:\MYSOFTWAREOFtechnology\ClaudeCodeFile\Projects\YoloWithROS）
git add tasks/progress.md tasks/phase7_runbook.md
git commit -m "docs: Phase 7 验证 runbook + progress 更新"
```

---

## 6. 快速参考

### 常用诊断命令

```bash
# 查看所有节点
rosnode list

# 查看某节点订阅/发布
rosnode info /sensor_fusion

# 实时看所有话题
rostopic list | grep excavator

# 强制触发 EMERGENCY_STOP
rosservice call /excavator/emergency_stop "{}"

# 手动恢复
rosservice call /excavator/resume "{}"

# 重置障碍物（vehicle 场景）
rosservice call /excavator/reset_obstacles "{}"

# 查看 TF 树（输出 pdf）
rosrun tf view_frames && evince frames.pdf
```

### 关键话题说明

| 话题 | 发布者 | 说明 |
|------|--------|------|
| `/camera/image_raw` | Gazebo 相机插件 | 640×480 30Hz |
| `/lidar/scan` | Gazebo 激光雷达插件 | 360° 10Hz，安装高度 z≈2.95m |
| `/excavator/lidar_obstacles` | lidar_processor | 角度聚类输出，含 world_x/y/z |
| `/excavator/tracked_obstacles` | deepsort_tracker | YOLO+DeepSort 视觉跟踪 |
| `/excavator/detected_obstacles` | sensor_fusion | 融合输出（含未匹配 lidar 静态障碍物） |
| `/excavator/predicted_obstacles` | trajectory_predictor | 含卡尔曼速度和 TTC |
| `/excavator/risk_state` | risk_assessor | current_level: 0=LOW 1=MED 2=HIGH |
| `/excavator/system_state` | fsm_controller | state: 0=NORMAL 1=CAUTION 2=PAUSED 3=EMSTOP |
| `/excavator/planned_cmd_vel` | rrt_star_planner | RRT\* 规划速度（FSM 仲裁后发 /cmd_vel） |
| `/cmd_vel` | fsm_controller **唯一** | 最终速度指令 |

### sensor_fusion 静态直通逻辑（最新修改）

```
lidar_obstacles → 投影到像素空间
    ├─ 命中某视觉 track bbox → 匹配，写入真实 distance/world_xyz
    └─ 未命中 → obstacle_type="obstacle" 直通到 detected_obstacles
```

这使得围栏、建材堆、静态测试方块能被 risk_assessor 和 RRT\* 感知，无需 YOLO 检测。

---

*生成于 2026-05-09，Phase 7 验证阶段*
