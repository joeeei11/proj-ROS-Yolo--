# 当前状态：G3 三大缺陷全部修复（ADR-029/030/031，2026-05-21）

## ADR-031（最新综合修复）解决 3 个独立问题

| 问题 | 根因 | 修复 |
|------|------|------|
| 偶发碰撞 | lidar cluster 中心偏向机器人 ~0.5m，排除圆覆盖不到 obs 远端 | `obstacleCb` 加 LIDAR_FACE_BIAS=0.5m 偏移修正；`robot_radius: 2.5→3.5` |
| RViz 路径走完不消失 | `followingTimerCb` goal reached 时未 publish 空 path（path_pub 是 latched） | goal reached 时同时 publish 空 `nav_msgs::Path` |
| 2D Nav Goal 失效 | plan 失败时 RViz 没视觉反馈 | `goalCb` 立即 publish 空 path（视觉提示"goal 收到"）；planningTimerCb plan 失败时也 publish 空 path + WARN_THROTTLE |

## 当前参数（ADR-031）

```yaml
robot_radius:    3.5     # 接近矩形外接圆 sqrt(13)=3.606
obstacle_margin: 0.3
goal_x:          24.0    # 距 obs_C 7m，远超 4.3m 排除圆
# cpp 内：cluster_radius=0.5 (hardcoded), LIDAR_FACE_BIAS=0.5m
```

排除圆 = 0.5+3.5+0.3 = **4.3m**，机器人转弯角部到 obs 真实边界富余 **0.19m**。

## 验证（WSL Gazebo + RViz, 50s+）

- ✅ G3 端到端：goal reached @ 36.0s, dist=0.231m
- ✅ 13 次 new path 发布
- ✅ 0 次 EMERGENCY_STOP
- ✅ 测试不可达 goal：机器人按 fallback 继续走
- ✅ 测试 path 清空：`/planned_path` 在 goal reached 后 poses=0

---

## 已验证通过（WSL Gazebo + RViz）

| 验证项 | 结果 |
|--------|------|
| G3 端到端绕障（spawn (0,0) → goal (22,0)）| ✅ 38.1s reached, dist=0.298m |
| 启动期偶发 no path（obs 列表抖动）自愈 | ✅ 下个周期恢复 |
| 手动 2D Nav Goal 切换可达目标 | ✅ 切换成功 |
| 手动发**不可达 goal**（如 obs 中心）| ✅ 机器人不卡死，继续走旧路径（ADR-030 效果）|
| 全程 EMERGENCY_STOP 次数 | ✅ 0 次 |

## 改动汇总

| ADR | 文件 | 改动 | 状态 |
|-----|------|------|------|
| ADR-029 | `rrt_star_planner.h/cpp` + `planner_params.yaml` | 引入 `robot_radius` 参数（圆盘机器人模型） | ✅ 双侧 |
| ADR-029 修订 | `planner_params.yaml` | robot_radius=2.5, margin=0.3, goal_x=22 | ✅ 双侧 |
| ADR-030 | `rrt_star_planner.cpp:goalCb` | 不提前清旧 path，由 planningTimerCb 成功后才替换 | ✅ 双侧 |

## 备份文件（如需回滚）

```
~/excavator_ws/src/excavator_planner/{src/rrt_star_planner.cpp,include/excavator_planner/rrt_star_planner.h,config/planner_params.yaml}.bak.adr029
~/excavator_ws/src/excavator_planner/src/rrt_star_planner.cpp.bak.adr030
~/excavator_ws/tasks/*.md.bak.adr029
```

---

## ADR-029 修复内容（已完成 Windows 备份侧改动）

**根因**：RRT* 用 point inflation 把机器人当作 0 半径质点，但 base_link 6×4m 矩形车体外接圆 3.61m。pure pursuit 让矩形 yaw 摆动 → 角部插入排除圆 (1.11m 几何缺口) → ODE 卡死。

**修复**：规划层升级为"圆盘机器人 (R=robot_radius=3.61m) + 障碍物膨胀 0.5m"，路径中心距障碍物中心 ≥ 4.61m，转弯角部保留 1.0m 富余。

| 文件 | 改动 | 状态 |
|------|------|------|
| `rrt_star_planner.h` | Params 新增 `robot_radius{3.61}` | ✅ Windows |
| `rrt_star_planner.cpp:pointFree()` | 判定加上 `+robot_radius` | ✅ Windows |
| `rrt_star_planner.cpp` 构造函数 | 加载 `robot_radius` ROS 参数 | ✅ Windows |
| `planner_params.yaml` | `obstacle_margin: 2.0→0.5`，新增 `robot_radius: 3.61` | ✅ Windows |

## 待执行（WSL 侧）

- [ ] 同步 3 个源文件到 `~/excavator_ws/src/excavator_planner/`
- [ ] `catkin_make -DCMAKE_BUILD_TYPE=Release` 编译通过
- [ ] T1：G1 烟雾测试（30s，position.x > 5，不退化）
- [ ] T2：G3 端到端（90s，position.x > 19.5 ∧ |y| < 1.0，全程不 EMERGENCY_STOP，最近障碍物 > 0.5m）
- [ ] T3：G2 行人 EMERGENCY_STOP 不退化

## 验证命令
```bash
# WSL 同步（一行）
cp -v /mnt/d/MYSOFTWAREOFtechnology/ClaudeCodeFile/Projects/YoloWithROS/Subbmit_Successful/excavator_savenav_source/excavator_ws/src/excavator_planner/{include/excavator_planner/rrt_star_planner.h,src/rrt_star_planner.cpp,config/planner_params.yaml} ~/excavator_ws/src/excavator_planner/

# 编译
cd ~/excavator_ws && catkin_make -DCMAKE_BUILD_TYPE=Release && source devel/setup.bash

# G3 端到端
roslaunch excavator_gazebo full_simulation.launch headless:=true \
  world_file:=$(rospack find excavator_gazebo)/worlds/test_scenarios/test_static.world
# 监控：rostopic echo /odom | grep "position" && rostopic echo /excavator/system_state
```

## 历史 ADR 关系（本轮）
| ADR | 改动 | 当前是否生效 |
|-----|------|------|
| ADR-023 | URDF 手臂收起 | ✅ 保留 |
| ADR-024 | 5 障碍物 + margin 2.5m | ❌ 已被 ADR-028 回退 |
| ADR-025 | lookahead 1.0m | ✅ 保留 |
| ADR-026 | 圆柱碰撞 | ❌ 已被 ADR-028 回退 |
| ADR-027 | margin 回退 2.0m | ❌ 被 ADR-029 二次回退到 0.5m |
| ADR-028 | 回退 3 障碍布局 | ✅ 保留 |
| **ADR-029** | **robot_radius 引入** | **✅ 本轮新增** |

---

# 已完成：ADR-028（2026-05-20）— G3 回退 3 障碍物布局

详见 `tasks/decisions.md`。当前 G3 场景配置：
- `test_static.world`：3 障碍物 obs_A(5,0)/obs_B(11,5)/obs_C(17,0)（注：与 Subbmit_Successful/ 备份中的 2 障碍物版本不同，以 WSL 当前为准，需核对）
- `planner_params.yaml`：goal_x=20.0，obstacle_margin=0.5（ADR-029 改）, lookahead=1.0, robot_radius=3.61（ADR-029 新增）

---

# 已完成：ADR-023（2026-05-19）— URDF 手臂收起姿态（行走收臂）

## 任务目标
修复 `excavator_simple.urdf.xacro` 铲斗视觉穿透障碍物问题：将手臂从"伸展作业"姿态改为"行走收臂"姿态（动臂上举 60°、斗杆内折垂下、铲斗卷拢），使铲斗收回底盘前端范围内（bucket x ≤ 3.0m）。

## 根因（已确认）
原姿态铲斗在底盘前端延伸约 3.5m，RRT* 安全裕量 2.5m 不足以防止视觉穿透；手臂关节均为 `type="fixed"`，仅需修改 rpy 数值，无需增删关节或添加碰撞体。

## 修复方案（ADR-023）
修改 `src/excavator_description/urdf/excavator_simple.urdf.xacro`：
- `boom_joint` rpy: `0 0 0` → `0 -1.05 0`（动臂上举 60°）
- `arm_joint` rpy: `0 0 0` → `0 2.62 0`（斗杆折回垂下）
- `bucket_joint` rpy: `0 0 0` → `0 -0.52 0`（铲斗卷拢）
- `arm_link` visual rpy: `0 0.35 0` → `0 0 0`（视觉补偿归零）

## Codex 任务文件
`ContactWithCodex/task_adr023_stow_arm.md`

## 验证状态
- [x] 根因分析完成，ADR-023 已写入 decisions.md（Windows）
- [x] Codex 改动完成（Windows 备份路径），XML OK，bucket x=2.94 ≤ 3.0 ✅
- [x] 同步改动到 WSL2 `~/excavator_ws/src/excavator_description/urdf/excavator_simple.urdf.xacro` ✅
- [x] WSL2 `xacro` 展开 + `check_urdf` 通过（连杆树完整，7链接）✅
- [ ] G1/G2/G3 冒烟验证不退化

---

# 已完成：ADR-021（2026-05-13）— 统一所有场景默认 model_variant:=simple

## 任务目标
修复 EC650 高保真模型在 Gazebo 中翻倒（G1/G2/G3 全场景），将两个 launch 文件的 `model_variant` 默认值改为 `simple`。

## 根因（已确认）
EC650 URDF（14连杆+STL mesh）与 `planar_move` 插件在 ODE 物理引擎下接触力冲突，导致车体翻倒。`excavator_simple.urdf.xacro` 已存在且 G3 已验证稳定。

## 修复方案（ADR-021）
- `gazebo_world.launch`：`model_variant` default `ec650` → `simple`
- `full_simulation.launch`：`model_variant` default `ec650` → `simple`

## Codex 任务文件
`ContactWithCodex/task_adr021_simple_default.md`

## 验证状态
- [x] 根因分析完成，ADR-021 已写入 decisions.md（Windows + WSL2）
- [x] `gazebo_world.launch` model_variant default: `ec650` → `simple` ✅
- [x] `full_simulation.launch` model_variant default: `ec650` → `simple` ✅
- [ ] 验证：G1/G2/G3 各场景冒烟测试无翻倒

---

# 已完成：ADR-020（2026-05-13）— G3 FSM PAUSED 阈值修复 + RViz Goal Marker

## 任务目标
修复 G3 场景中机器绕过第一个障碍物后永久卡住（PAUSED）的问题，并使 2D Nav Goal 终点设定功能可正常体验。

## 根因（已确认）
RRT* 路径绕过 obs_A 时最近距离 = 2.5m（=co.radius+obstacle_margin）→ risk_score = 0.625 ≥ 旧 PAUSED 阈值 0.60 → 进入 PAUSED。机器停止，score 卡在 0.625 > 退出阈值 0.45，永远无法恢复。

## 修复方案（ADR-020）
- `fsm_params.yaml`：CAUTION→PAUSED 阈值 0.60 → **0.72**（绕障峰值 0.625 < 0.72，不触发 PAUSED）
- `excavator_monitor.rviz`：添加 `/excavator/goal_marker` Marker 显示

## Codex 任务文件
`ContactWithCodex/task_bug_fix_g3_stuck.md`

## 验证状态
- [x] ADR-019：obs_B(11,5)，obs_C(17,0)，rviz:=true（已完成）
- [x] 根因分析：FSM PAUSED 阈值与绕障距离不匹配（已确认）
- [x] **ADR-020**：fsm_params.yaml 修改 0.60→0.72，RViz Goal Marker（已完成）
- [x] **G3 端到端验证：机器绕过 3 个障碍物成功到达 goal(20,0)，全程无 PAUSED ✅（2026-05-13）**
- [ ] 2D Nav Goal 体验：RViz 设定新目标，红色 Marker 显示，机器重规划（待用户测试）

---

# Phase 7 ✅ 已完成（2026-05-09）

## 项目整体进度：100% — git tag v1.1-real-sim

所有阶段（Phase 1 → Phase 7）已全部完成，系统已通过真实 Gazebo 端到端仿真验证。

---

## Phase 7 完成摘要

**目标**：使真实 Gazebo 感知链路全程运行（无消息注入），端到端验证 G1/G2/G3 三个场景。

### 核心修复（本阶段关键变更）

| 修复项 | 文件 | 变更内容 |
|--------|------|---------|
| sensor_fusion 架构 | `sensor_fusion.py` | 移除 ApproximateTimeSynchronizer，改为独立订阅 + `_last_tracks` 缓存 |
| lidar 自检测过滤 | `perception.launch` | min_range: 0.1m → **2.5m** |
| 远距障碍物检测 | `perception.launch` | min_cluster_points: 2 → **1** |
| 障碍物高度 | 所有 .world 文件 | 围栏 5m / 建材堆 3.5m / 行人碰撞体 4m（ADR-010） |

### 验证结果（G1/G2/G3 全部通过）

| 场景 | 结论 | 关键现象 |
|------|------|---------|
| G1 headless 烟雾测试 | ✅ 通过 | 13 节点在线，lidar 10Hz，detected_obstacles ≥1Hz |
| G2 行人场景 | ✅ 通过 | 行人靠近 → risk_level=2 → EMERGENCY_STOP → cmd_vel=0；resume → NORMAL |
| G3 静态绕障 | ✅ 通过（2026-05-12 simple 模型回归） | odom 坐标统一、planned_path=odom、FSM=CAUTION、risk_level=1；推荐 `~/start_g3_simple.sh`（model_variant:=simple） |

### Git 状态

- **WSL2 master**：commit `2420ea9`，tag `v1.1-real-sim`（21 files, 858 insertions）；G3 坐标系统一 + simple 模型（ADR-016/017）已合入，`catkin_make` 通过
- **Windows master**：commit `c9db65d`（decisions/current 更新）；操作手册、runbook 已同步

---

## 阶段总览

| 阶段 | 名称 | 状态 | 完成日期 |
|------|------|------|---------|
| Phase 1 | 环境搭建与工程骨架 | ✅ 已完成 | 2026-05-08 |
| Phase 2 | 感知模块开发 | ✅ 已完成 | 2026-05-08 |
| Phase 3 | 风险评估模块开发 | ✅ 已完成 | 2026-05-08 |
| Phase 4 | 决策与路径规划模块 | ✅ 已完成 | 2026-05-08 |
| Phase 5 | Gazebo 仿真集成与验证 | ✅ 已完成 | 2026-05-08 |
| Phase 6 | 系统测试、性能优化与文档收尾 | ✅ 已完成 | 2026-05-08 |
| Phase 7 | 真实 Gazebo 端到端仿真验证 | ✅ 已完成 | 2026-05-09 |

---

## 可交付物清单

- `src/` 下全部 8 个 ROS 包，catkin_make [100%] 零错误
- `docs/操作手册-v1.1-real-sim.md` — 一键启动/监控/验证指南
- `tasks/decisions.md` — ADR-001 ～ ADR-017 完整技术决策记录
- `tasks/progress.md` — 全阶段完成状态快照
- `tasks/phase7_runbook.md` — Phase 7 执行 runbook（含调试日志）
- `results/` — 性能测试 CSV 和论文图表（Phase 6）
- `docs/adr/` — 6 条标准格式 ADR
- WSL2 git tag `v1.1-real-sim`

---

## 下一步（如继续开发）

当前项目已达到毕业论文验收标准，无待处理阻塞问题。如需继续扩展，建议方向：

1. 实车部署适配（替换 Gazebo 仿真接口为真实 ROS 驱动）
2. 替换 yolov5s.pt 占位权重为施工场景专项训练权重
3. Phase 8：多机协同 / 更复杂的动态障碍物场景

---


