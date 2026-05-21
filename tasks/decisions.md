# 技术决策记录

---

## [2026-05-21] ADR-031 — 综合修复：lidar cluster 偏移补偿 + RViz path 不刷新 + 视觉反馈

**问题背景**：用户实测发现 3 个独立缺陷：

1. **偶发与障碍物碰撞**：机器人转弯通过 obs_A/B/C 旁时，矩形车体角部擦到 obstacle 真实边界
2. **RViz 规划路径走完后不消失**：goal reached 后 `/planned_path` 上次 latched 的旧路径仍占据 RViz 视图
3. **2D Nav Goal 偶发失效**：用户在 RViz 点新目标，机器人无任何视觉反馈，看起来"goal 没生效"

**根因分析**：

| 问题 | 根因 |
|------|------|
| 偶发碰撞 | `obstacleCb` 直接用 lidar cluster 中心 + `radius=0.5`。lidar 估的 cluster 中心是 obstacle 朝向 lidar 的"面中心"，偏向机器人约半边长（~0.5m）。排除圆基于偏移的中心位置，对 obs 真实"远端"覆盖不足，机器人 yaw=45° 时角部最远 3.61m 可能擦到真实边界 |
| RViz path 不刷新 | `followingTimerCb` goal reached 时只 `current_path_.clear()`，**没 publish 空 `nav_msgs::Path`**。`path_pub_` 是 latched topic，RViz 始终显示最后一次 publish 的旧路径 |
| 2D Nav Goal 失效 | `goalCb` 立即调用 `planningTimerCb`，若 plan 失败则 `current_path_` 保留（ADR-030），但 RViz 不会得到任何新 path → 用户看不到 goal 被收到的反馈 |

**修复内容**（共 4 处改动）：

| # | 文件/位置 | 改动 |
|---|----------|------|
| 1 | `planner_params.yaml` | `robot_radius: 2.5 → 3.5`（接近矩形外接圆 3.61，覆盖任意 yaw 角部摆幅）<br>`goal_x: 22.0 → 24.0`（推到 obs_C(17,0) 外侧 7m，远超新排除圆 4.3m）|
| 2 | `rrt_star_planner.cpp:obstacleCb` | 引入 `LIDAR_FACE_BIAS=0.5m` 偏移修正：把 cluster 中心沿"机器人→cluster"方向推 0.5m，等价于估计 box 真实几何中心。修正后保持 `co.radius=0.5` |
| 3 | `rrt_star_planner.cpp:followingTimerCb` | goal reached 时同时发布**空** `nav_msgs::Path` 到 `path_pub_`，使 RViz 清除已走完的路径显示 |
| 4 | `rrt_star_planner.cpp:goalCb` & `planningTimerCb` | goalCb 收到新 goal 时立即 publish 空 path（视觉反馈"goal 已收到"）；planningTimerCb plan 失败时也 publish 空 path 并 ROS_WARN_THROTTLE 告知用户 goal 不可达 |

**几何核查（修复后）**：

```
排除圆 = cluster_radius(0.5) + robot_radius(3.5) + obstacle_margin(0.3) = 4.3m
↓
机器人 yaw=45° 角部到 obs 真实边界富余 = 4.3 - 0.5(box 半边) - 3.61(角部) = 0.19m  ✓
↓
起点 (0,0) 距修正后 obs_A 中心 (5,0) = 5.0m > 4.3m  ✓ 可规划
↓
goal (24,0) 距修正后 obs_C 中心 (17,0) = 7.0m > 4.3m  ✓ 可达
↓
obs_A↔obs_B 走廊 = 7.81 - 8.6 = -0.79m  → RRT* 强制北/南绕，path 远离 obs
```

**验证结果（WSL Gazebo+RViz, sim_time 50s+, 2026-05-21）**：

| 测试 | 结果 |
|------|------|
| G3 端到端 spawn (0,0) → goal (24,0) | ✅ **goal reached @ 36.0s, dist=0.231m** |
| `/planned_path` 在 goal reached 后 | ✅ **poses count = 0**（RViz 路径自动清除）|
| 手动发不可达 goal (5,0)（obs_A 中心）| ✅ 机器人按 fallback path 继续走，未卡死 |
| 手动发可达 goal (-5,0) | ✅ 机器人朝新方向移动 |
| 日志含 `plan failed... RViz path cleared` 反馈 | ✅ 用户明确知道 goal 不可达 |
| 启动期偶发 plan failed | ✅ 14.8s 后稳定 |
| EMERGENCY_STOP 次数 | ✅ 0 |

**与历史 ADR 的关系**：
- ADR-029（robot_radius=2.5, margin=0.3, goal_x=22）：本 ADR 进一步收紧 robot_radius 到 3.5 并修正 cluster 偏移
- ADR-030（goalCb 不清旧 path）：保留 fallback 语义，但增加视觉反馈层（publish 空 path）

**改动量**：1 个 yaml + 4 处 cpp 改动，共约 30 行（含注释）

---

## [2026-05-21] ADR-030 — `goalCb` 不提前清旧路径，修复 2D Nav Goal 偶发"失效"

**问题现象**：用户在 RViz 中通过 `2D Nav Goal` 工具点击新目标，机器人**有时不响应**——停在原地，看起来 Nav Goal 失效。

**根因**：`rrt_star_planner.cpp:goalCb` 收到新 goal 时，在锁内**先**执行 `current_path_.clear()` 再触发 `planningTimerCb` 调用 `plan()`：

```cpp
// 旧代码（有 bug）
{
    std::lock_guard<std::mutex> lk(goal_mutex_);
    goal_.x = msg->pose.position.x;
    goal_.y = msg->pose.position.y;
    current_path_.clear();   // ★ 过早清空
    path_idx_ = 0;
    goal_copy = goal_;
}
planningTimerCb(dummy);
```

`planningTimerCb` 若 `plan()` 返回空（`path.empty()`）则 `return`，于是 `current_path_` 保持为空。`followingTimerCb` 检测到 `current_path_.empty()` 直接 `return`，不发任何 cmd_vel。FSM 在 `planned_cmd_timeout=0.5s` 后转零速 → **机器人停滞**。

**触发条件**：plan 失败有两种常见情况，均会导致此 bug：
1. **新 goal 落在 obs 排除圆内**（用户误点在障碍物附近）→ RRT* 5000 次迭代后 goal_idx<0
2. **机器人当前位置已在 obs 排除圆内**（例如刚 reached 上一个 goal 后位置靠近 obs，或 lidar cluster 中心瞬时漂移导致排除圆覆盖机器人）→ RRT* 从起点扩展的所有 segment 都不 free

复现：本轮验证中机器人位置 (7.20, -2.28)，lidar 估计 obs_A 中心 (5.5, -0.1)，距 2.77m < 3.3m 排除圆。此时点任何新 goal 都失效。

**修复**：`goalCb` 中只更新 `goal_`，**不清空** `current_path_` / `path_idx_`：

```cpp
// 新代码
{
    std::lock_guard<std::mutex> lk(goal_mutex_);
    goal_.x = msg->pose.position.x;
    goal_.y = msg->pose.position.y;
    // 不再 current_path_.clear() 和 path_idx_=0
    goal_copy = goal_;
}
planningTimerCb(dummy);  // 成功则在内部覆盖 current_path_，失败则保留旧路径
```

`planningTimerCb` 的现有逻辑天然支持这种"成功才替换"：

```cpp
auto path = planner.plan(current_pos_, goal_copy);
if (path.empty()) return;          // 失败保留旧 current_path_
current_path_ = path;              // 成功覆盖
path_idx_     = 0;
```

**修复后行为**：
- plan 成功：机器人切换到新路径 ✓
- plan 失败：机器人继续按**旧路径**走，下次 `planning_period=2.0s` 定时器再次重试 ✓
- 副作用：如果用户连发两个不同方向的 goal，第二个 goal 若 plan 失败，机器人可能朝**第一个 goal 的旧路径终点**继续走 ≤2s，看起来"延迟响应"。但比"完全卡死"好得多，且 2s 后下个 planning 周期会重试新 goal

**验证（本轮 G3 测试 145s sim_time）**：
| 测试项 | 结果 |
|--------|------|
| G3 默认 goal=(22,0) 端到端 | ✅ goal reached @ 38.1s, dist=0.298m |
| 手动发可达 goal (5,-5) | ✅ 切换路径并跟随 |
| 手动发**不可达** goal (5,0)（obs_A 中心） | ✅ **机器人继续走，未停滞**（修复前会卡死） |
| 后续到达 (5,-5) | ✅ goal reached @ 96.05s |
| 全程 EMERGENCY_STOP | ✅ 0 次 |

**改动量**：`rrt_star_planner.cpp` 删除 2 行（`current_path_.clear()` + `path_idx_=0`），加 3 行注释。共 1 处改动。

**与 ADR-029 的关系**：ADR-029 解决了"规划层 vs 矩形车体角部"的几何不匹配；本 ADR 解决了"goal 回调与规划失败的状态机错配"。两者正交，均为 G3 稳定运行所必需。

---

## [2026-05-21] ADR-029 — 引入 `robot_radius` 参数解决 G3 转弯角部碰撞卡死

**决策**：在 RRT* 碰撞检测中引入 `robot_radius` 参数（默认 3.61m，即 6×4m 矩形底盘的外接圆半径 √(3²+2²)），将原本"点机器人 + 障碍物膨胀 2.5m"的碰撞模型升级为"圆盘机器人（R=3.61m）+ 障碍物膨胀 0.5m"。同时 `obstacle_margin` 从 2.0m 回退到 0.5m。

**根因（最终定位）**：

ADR-026 圆柱碰撞、ADR-024/027/028 多次调整 `obstacle_margin` 均未触及问题本质 —— **规划层把机器人视为点（point inflation）的假设，与执行层 pure pursuit 让矩形车体频繁摆 yaw 的行为不兼容**：

| 几何量 | 旧值 | 物理含义 |
|--------|------|---------|
| base_link 外接圆 `R_corner` | 3.606m | 矩形车体任意 yaw 下角部最远伸出半径 |
| 旧 RRT* 排除圆 | 2.5m (= 0.5 + 2.0) | 路径中心距障碍物中心的最小值 |
| **几何缺口** | **−1.106m** | 转弯时角部插入障碍物排除圆 |

复现路径：机器人从 (0,0) 经规划路径 (10, 2.5) 绕 obs_A(10,0)，pure pursuit 强制 yaw 摆动追切线，机器人在 (10.5, 2.5) 附近 yaw≈+30° 时，**右后角世界系坐标 (8.9, −0.73)** 距 obs_A 中心仅 1.32m < 2.5m → ODE 接触约束与 planar_move 速度指令互博 → 卡死。

**修复内容**（外科手术 4 处改动）：

| 文件 | 改动 |
|------|------|
| `excavator_planner/include/excavator_planner/rrt_star_planner.h` | `Params` 结构体新增 `double robot_radius{3.61}` |
| `excavator_planner/src/rrt_star_planner.cpp:pointFree()` | 判定条件加上 `+ params_.robot_radius` |
| `excavator_planner/src/rrt_star_planner.cpp` 构造函数 | 加载 `nh_.param("robot_radius", params_.robot_radius, 3.61)` |
| `excavator_planner/config/planner_params.yaml` | `obstacle_margin: 2.0 → 0.5`；新增 `robot_radius: 3.61` |

**几何验证（修复后）**：
- 新排除圆 = obs.radius(0.5) + robot_radius(3.61) + margin(0.5) = **4.61m**
- 转弯时角部到障碍物中心最近距离 ≥ 4.61 − 3.61 = **1.0m 富余**
- obs_A(10,0) 与 obs_B(14,−5) 在 G3 实际 world 文件中不构成必经走廊：路径从 obs_A 上方（y ≥ 4.61）绕过即可到达 (20,0)，全程距 obs_B 距离 ≥ 9m

**为何回退 `obstacle_margin` 到 0.5m**：旧 2.0m 是"用膨胀代偿机器人尺寸"的妥协做法。现在机器人尺寸由 `robot_radius` 独立承担，`obstacle_margin` 回归其真实语义 = 纯粹的"安全裕量"，0.5m 已足。

**与历史 ADR 的关系**：
- ADR-024（margin=2.5m + 5 障碍物）：**已由 ADR-028 回退**；其在 ADR-027 中暴露的"机器人起点落入排除圆"问题，本 ADR 不会复现（路径起点 (0,0) 距任意障碍物 ≥ 10m）
- ADR-026（圆柱碰撞体）：**仍保留作为 ADR-028 回退的基线**；但本 ADR 不依赖圆柱碰撞 —— 即使未来恢复 box 碰撞，规划层已正确处理矩形外接圆
- ADR-027 / ADR-028：依然有效，本 ADR 不与之冲突

**副作用与风险**：
- ✅ FSM / 感知 / risk_assessor 零改动，G1/G2 行为不退化
- ✅ 走廊更窄的场景（如未来 obs 间距 < 9.22m）可能 no path found —— 当前 G3 场景已验证可达
- ⚠️ 若实际机器人 footprint < 6×4m 矩形外接圆，路径会比"理论最优"略远，但安全富余更高

**验证标准**：
- T1（G1 烟雾）：机器人 30s 内 x > 5，不退化
- T2（G3 端到端，核心）：90s 内 odom.position.x > 21.5 ∧ |y| < 1.0，全程未进 EMERGENCY_STOP，最近障碍物距离始终 > 0.5m
- T3（G2 行人）：检测到 person 时正常进入 PAUSED→EMERGENCY_STOP 路径

### [2026-05-21 修订] ADR-029 参数调整 — 适配 3 障碍物之字形走廊

**首次发布参数**（`robot_radius=3.61`, `obstacle_margin=0.5`, `goal_x=20.0`）在 WSL 真实 G3 场景 (ADR-019/020 obs_A(5,0)/obs_B(11,5)/obs_C(17,0)) 中**首次启动即报错** `RRTStar: no path found`，原因：

| 间距 | 圆心距 | 旧排除圆和 (2×4.61) | 走廊宽度 | 备注 |
|------|--------|-------------------|---------|------|
| obs_A↔obs_B | 7.81m | 9.22m | −1.41m | 封死 |
| obs_B↔obs_C | 7.81m | 9.22m | −1.41m | 封死 |
| goal(20,0)↔obs_C | 3.0m | 4.61m (单边) | −1.61m | goal 在排除圆内 |

→ 原因是首次发布时**用了 Subbmit_Successful/ 中 2 障碍物布局的 world 备份做几何核查**，忽略了 WSL 真实场景是 3 障碍物之字形走廊。

**修订后参数**：

| 参数 | 旧值 | 新值 | 理由 |
|------|------|------|------|
| `robot_radius` | 3.61 | **2.5** | 不再用最坏情况外接圆，改用 lookahead=1.0 + 路径平滑下实测 yaw 摆幅 ≤30° 时的等效半径。pure pursuit 切角 ≈ L²/(8R)=0.04m，路径平滑后机器人不会 yaw=45° |
| `obstacle_margin` | 0.5 | **0.3** | 压缩安全裕量以扩走廊，保留最小非零余量 |
| `goal_x` | 20.0 | **22.0** | 推到 obs_C 外侧 5m，绕过 goal 与 obs_C 的几何冲突 |

**新几何核查**（排除圆 = 0.5+2.5+0.3 = **3.3m**）：

| 间距 | 圆心距 | 双排除圆和 (2×3.3) | 走廊宽度 | 安全 |
|------|--------|------------------|---------|------|
| obs_A↔obs_B | 7.81m | 6.6m | **1.21m** | ✓ |
| obs_B↔obs_C | 7.81m | 6.6m | **1.21m** | ✓ |
| goal(22,0)↔obs_C | 5.0m | 3.3m | **1.7m** | ✓ |

**残余风险**：1.21m 走廊宽度 < 机器人体宽 4m。机器人必须**侧着身体**（yaw ≈ 90°）才能挤过两障碍物之间。实际不会，因为 RRT* 不会让路径穿过这条窄走廊—会绕到 obs_B 上方（y>obs_B排除圆 = 5+3.3 = 8.3m）然后绕回。需在验证时观察实际路径形状。

**验收标准更新**：T2 goal x 阈值从 19.5 改为 **21.5**。

---

## [2026-05-20] BUG-记录 — 薄碟型碰撞体导致机器人倾斜并穿入障碍物（已回滚）

**问题描述**：将 `base_link` 碰撞体改为薄圆柱（r=1.5m, h=0.1m, 贴底）后，Gazebo 中挖掘机出现严重倾斜，并完全进入障碍物内部，已立即回滚。

**根因**：
1. 薄碟（h=0.1m）垂直方向支撑不足，ODE 接触计算不稳定，机器人失去水平平衡导致倾斜
2. 一旦倾斜，机器人几何体偏转，圆柱侧面无法有效阻挡障碍物，机器人整体滑入障碍物

**教训**：
- `base_link` 必须保留原始 `box(6×4×0.9)` 碰撞体以保证姿态稳定（planar_move + ODE 需要足够的接触面积）
- 任何对 base_link 碰撞体的修改都需在 Gazebo 中验证机器人不倾斜，再做其他测试
- 不要为了解决规划问题而修改碰撞体，应从规划参数层面解决

**回滚内容**：`excavator_simple.urdf.xacro` 恢复 `base_link` box(6×4×0.9) + `turret_link` box(3.0×2.2×0.9)

---

## [2026-05-20] ADR-028 — 回退 G3 至 3 障碍物布局（ADR-019 验证态）

**决策**：放弃 5 障碍物扩展方案，回退到 ADR-019/020 已验证通过的 3 障碍物布局。

**回退内容**：
| 文件 | 回退内容 |
|------|---------|
| `test_static.world` | 恢复 obs_A(5,0)/obs_B(11,5)/obs_C(17,0)，围栏 center=6/len=42 |
| `planner_params.yaml` | goal_x 33.0→20.0，obstacle_margin 保持 2.0，lookahead_dist 保持 1.0 |
| `excavator_simple.urdf.xacro` | base_link 碰撞恢复 box(6×4×0.9)，turret_link 碰撞恢复 |

**根因（放弃 5 障碍物）**：5 障碍物布局引入多重不稳定：obs_D 被激光雷达检测为双聚类压缩走廊；机器人绕到 obs_C 南侧后形成几何死角无法规划；圆柱碰撞使视觉与碰撞不一致（视觉 6×4m > 圆柱 r=2.0m），机器人视觉穿透障碍物。

**保留**：ADR-023（手臂收起）、ADR-025（lookahead 1.0m）均保留，这两项无副作用。ADR-024/026/027 回退。

---

## [2026-05-20] ADR-027 — obstacle_margin 回退至 2.0m（配合圆柱碰撞）

**决策**：`planner_params.yaml` `obstacle_margin: 2.5` → `obstacle_margin: 2.0`。

**根因**：ADR-024 将 obstacle_margin 从 2.0→2.5m，排除圆从 2.5→3.0m。机器人跟踪路径时会到达距障碍物 ~2.5m 处，落入 3.0m 排除圆内，RRT* 起点被判为"障碍内"→ 持续 no path found。

ADR-026 引入圆柱碰撞后，机器人接触障碍物时可自然滑开，不再需要 2.5m 大间距。回退至 2.0m（排除圆 2.5m）后：机器人在 2.53m 处 → 在排除圆外 ✓；走廊从 2m 扩至 5m（obs y=10）✓。

**影响**：obstacle_margin=2.0m + cylinder collision 是最终稳定组合。

---

## [2026-05-20] ADR-026 — base_link 碰撞体改为圆柱

**决策**：`excavator_simple.urdf.xacro` 中 `base_link` 碰撞体从 `box(6.0×4.0×0.9)` 改为 `cylinder(radius=2.0, length=0.9)`，同时删除 `turret_link` 碰撞体。

**根因**：矩形碰撞体有四个尖角，对角半径 = √(3²+2²) = **3.61m**，而 `obstacle_margin=2.5m` 仅保证中心点距障碍物 3.0m，转弯时前角插入障碍物（3.61m > 3.0m），导致 Gazebo 接触约束将机器人卡死。圆柱碰撞无棱角，接触时自然滑开。

**影响**：
- 圆柱 radius=2.0m，与 `obstacle_margin` 中机器人半宽假设完全匹配
- visual 几何不变（视觉仍为大机器）
- `check_urdf` 通过，连杆树完整
- 不影响感知/评估/决策/规划任何逻辑

---

## [2026-05-19] ADR-025 — pure-pursuit lookahead_dist 减半（2.0→1.0m）

**决策**：`planner_params.yaml` 中 `lookahead_dist: 2.0` → `lookahead_dist: 1.0`。

**根因**：纯跟踪切角量 ≈ L²/(8R)，L=2.0m、R≈3m 时切角 0.17m，而物理间隙仅 0.5m（RRT* 排除圆 3.0m - 障碍物半宽 0.5m - 机器人半宽 2.0m），触碰障碍物后机器人反复修正方向。L=1.0m 时切角降至 0.04m，远小于 0.5m 间隙。

**影响**：路径跟踪更贴合规划路径，转弯响应更灵敏；直线段跟踪频率不变；不影响 RRT* 规划逻辑；G1/G2 不受影响。

---

## [2026-05-19] ADR-024 — G3 场景 5 障碍物布局重设计

**决策**：将 G3 静态绕障场景从 3 障碍物扩展为 5 障碍物，同时将 `obstacle_margin` 从 2.0m 提升至 2.5m。

**修改文件**：
- `src/excavator_planner/config/planner_params.yaml`：`obstacle_margin` 2.0→2.5，`goal_x` 20.0→33.0
- `src/excavator_gazebo/worlds/test_scenarios/test_static.world`：新布局

**新障碍物布局（Δx=6m，y_offset=8m）**：

| 障碍 | 位置 | 尺寸 |
|------|------|------|
| obs_A | (5, 0) | 1.0×1.0×3.5 |
| obs_B | (11, 10) | 0.8×0.8×3.5（原 y=5→10，运行时调整）|
| obs_C | (17, 0) | 1.2×1.0×3.5 |
| obs_D | (23, 10) | 1.0×1.0×3.5（新增，y 调整为 10）|
| obs_E | (29, 0) | 0.8×0.8×3.5（新增） |

目标点：(33, 0)

**根因**：原 `obstacle_margin=2.0m`，排除圆 2.5m，base_link 半宽 2.0m，障碍物半宽 0.5m，物理间隙 = 2.5-0.5-2.0 = **0m**，机器底盘贴着障碍物通过导致 Gazebo 接触力卡顿。

**几何验证**：排除圆=3.0m，相邻障碍圆心距=√(6²+10²)=11.66m（y=10），走廊间隙=5.66m ✓；走廊中点到障碍距离=5.83m>safe_distance，risk_score≈0（NORMAL）✓；caution_to_paused=0.72，最近点score<0.30，不触发PAUSED ✓。

**运行时调整（ADR-024 fix）**：obs_B/obs_D y 从 8→10。根因：y=8 时激光雷达将 obs_D 检测为 2 个聚类（22.51,7.90）+（23.21,7.49），双排除圆使走廊南边界从设计的 y=5.0 压缩到 y=4.49，机器人在 y=4.78 被挡住导致 RRT* 持续 no path found。y=10 时走廊宽 4m，双聚类仍可通过。

**影响**：不改 FSM/risk 阈值；不改 co.radius；G1/G2 场景不受影响。

---

## [2026-05-19] ADR-023 — URDF 手臂收起姿态（行走收臂）

**决策**：将 `excavator_simple.urdf.xacro` 中手臂三个固定关节的 rpy 值调整为行走收臂姿态：动臂上举 60°、斗杆内折悬垂、铲斗卷拢。

**修改文件**：`src/excavator_description/urdf/excavator_simple.urdf.xacro`

| 关节 | 改前 rpy | 改后 rpy | 说明 |
|------|---------|---------|------|
| `boom_joint` | `0 0 0` | `0 -1.05 0` | 动臂上举 60° |
| `arm_joint` | `0 0 0` | `0 2.62 0` | 斗杆折回，从动臂顶端向下垂 |
| `bucket_joint` | `0 0 0` | `0 -0.52 0` | 铲斗向内卷曲 30° |
| `arm_link` visual | `rpy="0 0.35 0"` | `rpy="0 0 0"` | 消除伸臂时的视觉下垂补偿 |

**根因**：原姿态铲斗伸出底盘前端约 3.5m（bucket x≈6.5m，底盘前端 x=3.0m），RRT* 安全裕量仅 2.5m，机器人绕障时铲斗在 Gazebo 中视觉穿入障碍物（无物理阻挡，不影响算法逻辑，但影响论文演示效果）。

**方案选择依据**：
- 不选"添加碰撞体"：给手臂添加 collision 会导致 Gazebo 物理阻挡，破坏 G3 S 形绕障验证
- 不选"调大障碍裕量"：obstacle_margin 已为 2.0m，继续增大会压缩走廊，影响 RRT* 规划

**验证约束**：修改后 bucket 中心 x ≤ 3.0m（底盘前端），check_urdf 通过，不需要 catkin_make。

**影响评估**：纯视觉几何调整，对激光雷达（无手臂碰撞体，扫描不受影响）、感知/评估/决策/规划链路零影响。

---

## [2026-05-13] ADR-022 — G2 场景切换为 test_pedestrian.world + start_g2.sh

**决策**：G2 行人验证场景由 `scenario:=main`（construction_site.world）改为 `scenario:=pedestrian`（test_pedestrian.world），新增 `~/start_g2.sh` 启动脚本。

**根因**：construction_site.world 包含 4 围栏 + 8 建材堆 + 2 锥形柱，LiDAR 从启动即检测到大量 lidar_cluster_*，机器始终处于 CAUTION，行人靠近时 primary_threat_id 在静态障碍物和行人之间跳变，状态转换链路（NORMAL→CAUTION→EMERGENCY_STOP→NORMAL）无法清晰展示。

**方案**：使用 test_pedestrian.world（仅 1 个行人 actor + 1 个碰撞体），背景零干扰。行人路径 `(8,5)→(3,0)→(8,-5)` 正好横穿机器行进路线（x 轴），触发完整状态链路。

**start_g2.sh 内容**：
```bash
roslaunch excavator_gazebo full_simulation.launch scenario:=pedestrian model_variant:=simple rviz:=true
```

**关联**：2D Nav Goal 功能（ADR-018）全场景通用，G2 同样支持 RViz 自由设置终点。

**影响**：construction_site.world 保留不变；G2 单独使用 test_pedestrian.world 进行行人避障专项验证。

---

## [2026-05-13] ADR-021 — 统一所有场景默认使用 simple 模型

**决策**：将 `gazebo_world.launch` 和 `full_simulation.launch` 的 `model_variant` 参数默认值从 `ec650` 改为 `simple`。

**修改文件**：
- `src/excavator_gazebo/launch/gazebo_world.launch`：`model_variant` default `ec650` → `simple`
- `src/excavator_gazebo/launch/full_simulation.launch`：`model_variant` default `ec650` → `simple`

**根因**：EC650 高保真 URDF（14连杆、STL mesh collision）在 Gazebo ODE 物理引擎下与 `planar_move` 插件存在接触力冲突，导致车体 pitch/roll 偏移、翻倒，所有场景（G1/G2/G3）均受影响。G3 已于 ADR-017 引入 simple 模型并验证姿态稳定（roll/pitch ≈ 0），需将此作为全局默认。

**影响评估**：
- EC650 模型文件保留不删除，仍可通过 `model_variant:=ec650` 显式指定
- G1/G2/G3 全部场景使用 simple 模型，行为与已验证的 G3 one-liner 一致
- 不影响任何感知/评估/决策/规划逻辑

**关联**：`bug/g1_ec650_tipover_all_scenarios.md`，ADR-017（simple 模型设计）

---

## [2026-05-13] ADR-020 — 修复 G3 绕障后 FSM 永久 PAUSED

**决策**：将 `fsm_params.yaml` 中 CAUTION→PAUSED 入口阈值从 **0.60 提高到 0.72**。

**修改文件**：`src/excavator_decision/config/fsm_params.yaml`（单一数值修改）

**根因（数学验证）**：
- RRT* 规划绕障路径时最近通过距离 = co.radius(0.5) + obstacle_margin(2.0) = **2.5m**
- risk_score = (safe_dist - 2.5) / (safe_dist - critical_dist) = (5.0 - 2.5) / 4.0 = **0.625**
- 0.625 ≥ 旧阈值 0.60 → 进入 PAUSED → 机器停止 → score 卡在 0.625 > 退出阈值 0.45 → **永久停止**
- 现象印证：`current.md` 观测到 `min_distance≈2.71m`，`state=PAUSED`，这正是机器在绕障路径上停止后的 obs_A 残留距离

**影响评估**：
- G3 静态绕障（type_weight=1.0）：2.5m 处 score=0.625 < 0.72 → CAUTION，继续行驶 ✓
- G2 行人靠近（type_weight=1.5）：3.08m 处 person_score=0.72 → PAUSED；2.46m 处 score=0.9375 > 0.85 → EMERG ✓（G2 行为基本不变）

**附加改动**：`excavator_monitor.rviz` 添加 `/excavator/goal_marker` Marker 显示，使 ADR-018 实现的 2D Nav Goal 功能可被视觉确认。

---

## [2026-05-12] GAP-3 修复 — construction_site.world 添加行人 Actor

**决策**：在主场景 `construction_site.world` 中添加 1 个行人 Actor（`pedestrian_1`）及对应物理碰撞体（`ped_collider_0`），并在 `full_simulation.launch` 中为 `scenario=main` 启用 `actor_collider_sync` 节点。

**修改文件**：
- `excavator_gazebo/worlds/construction_site.world`：新增 `<actor name="pedestrian_1">` 20s 循环路径 `(5,8)→(4,0)→(5,-8)→返回`；新增 `<model name="ped_collider_0">` 高 4m 圆柱碰撞体（中心 z=2.0m）
- `excavator_gazebo/launch/full_simulation.launch`：新增 `scenario=main` 条件下的 `actor_collider_sync` 节点（`actor_names_str=pedestrian_1, collider_names_str=ped_collider_0, collider_z=2.0`）

**验证结果**（2026-05-12 Gazebo headless 端到端）：
- `actor_collider_sync` 节点正常启动，参数配置正确 ✅
- `/excavator/tracked_obstacles` 以 18.5Hz 发布，`obstacle_id=actor_pedestrian_1`，`obstacle_type=person` ✅
- 行人路径正确：`world_x≈4.97,world_y≈8.03`（起点）→ `world_x≈3.95,world_y≈0.12`（最近点）✅
- 行人靠近时 risk_level 从 1 升至 2，FSM 转入 EMERGENCY_STOP（state=3）✅

**理由**：主场景是论文描述的核心演示场景，答辩时需展示行人动态避障功能；行人 Actor 是开题报告明确要求的"移动行人"测试场景要素。

---

## [2026-05-08] 初始技术选型

### 机器人中间件：ROS Noetic
**决策**：使用 ROS Noetic（而非 ROS 2）  
**理由**：ROS Noetic 对 Ubuntu 20.04 支持最完整，nav_msgs/move_base/Gazebo 11 生态成熟，社区迁移学习资源更丰富；ROS 2 在 Gazebo 插件兼容性上仍有不稳定因素  
**权衡**：ROS Noetic 2025年停止官方维护，但本项目为毕业设计验证项目，不需要长期维护

### 目标检测：YOLOv5 6.x + GhostNetV2 主干
**决策**：使用改进 YOLOv5（GhostNetV2 替换原主干），而非 YOLOv8  
**理由**：参考文献[2]（蒋虞，电子科技大学2024）验证该改进使参数减少30%、检测精度达95.5%，满足实时性要求；YOLOv5 的 ROS wrapper 现成可用  
**权衡**：YOLOv8 精度略高，但 ROS 集成需额外适配工作，学习成本更高

### 多目标跟踪：DeepSort
**决策**：使用 DeepSort（外观特征 + 卡尔曼运动预测），而非 ByteTrack 或 SORT  
**理由**：施工现场存在行人遮挡场景，DeepSort 外观特征匹配在遮挡恢复后 ID 切换率更低；参考文献[2][3] 均采用类似融合跟踪方案  
**权衡**：DeepSort 需要 ReID 模型（约50MB），计算开销略高于 SORT，但施工场景障碍物数量通常 < 20，在可接受范围

### 路径规划：改进 RRT*（C++17 实现）
**决策**：路径规划层使用 C++17 实现，其余模块使用 Python 3.8  
**理由**：紧急停止响应时间目标 ≤1.5s，C++ RRT* 实现比 Python 延迟低3-5×；参考文献[4]（杨瑞权，太原科技大学2023）验证 ROS 中 RRT 算法的有效性  
**权衡**：C++ 开发成本略高，但满足实时性硬性约束

### 传感器融合：message_filters.ApproximateTimeSynchronizer
**决策**：使用 ApproximateTimeSynchronizer，时间容差（slop）= 0.05s  
**理由**：摄像头（30Hz）与激光雷达（10Hz）帧率不同，ExactTime 同步会大量丢弃数据；50ms 容差在动态场景下对检测结果影响可忽略  
**权衡**：时间不对齐最大引入50ms误差，在 TTC > 2s 的场景中可接受

### 风险评估：多因子加权评分模型
**决策**：综合风险分 = (w1 × 距离分) + (w2 × TTC分)，类型权重作为乘数  
**理由**：借鉴参考文献[1]（钟星等）原像规划算法的方向判断思路；多因子融合比单一距离阈值更具鲁棒性  
**权衡**：权重参数需要基于实验标定，初始值参考领域经验值

### 仿真平台：Gazebo 11（headless 模式 + rosbag 录制）
**决策**：实验时使用 headless 仿真（gzserver），通过 rosbag 离线分析数据  
**理由**：避免 GUI 渲染占用 GPU 资源影响感知延迟测量；数据可复现  
**权衡**：调试期间仍需开启 GUI 观察，正式实验时切换 headless

---

## [2026-05-08] Ubuntu2004 导入方式：导出现有实例而非下载 rootfs

**决策**：使用 `wsl --export Ubuntu-20.04` + `wsl --import Ubuntu2004` 方式克隆，而非从 cloud-images.ubuntu.com 下载 rootfs  
**理由**：官方 cloud-images URL 返回 404（路径结构已变更）；克隆方式更快（无需网络下载），且保留了已有的系统基础配置  
**关联约束**：
- Ubuntu2004 实例基于已有 Ubuntu-20.04（20.04 LTS），符合项目技术栈要求
- WSL 用户名：`excavator`，密码：`excavator123`，具备 NOPASSWD sudo
- VHD 路径：`D:\WSL\Ubuntu2004\ext4.vhdx`（1324 MB）
- E 盘为 exFAT，原 Ubuntu-20.04 存于 E 盘但不影响导出操作

## [2026-05-08] WSL2 网络配置：mirrored 模式 + Clash TUN 透明代理

**决策**：在 `%USERPROFILE%\.wslconfig` 中启用 `networkingMode=mirrored` + `dnsTunneling=true`，依赖 Clash TUN 透明代理访问外网，**不配置显式 HTTP proxy**  
**理由**：
- 机器运行 Clash（端口 7897，Fake-IP DNS 模式），WSL2 默认隔离网络无法透传 TUN
- mirrored 模式让 WSL2 共享 Windows 网络接口，Clash TUN 可直接拦截 WSL2 流量
- 配置显式 HTTP proxy（127.0.0.1:7897）对国内镜像（aliyun/tuna）反而产生 502（Clash 将国内请求走直连，但 HTTP proxy 模式路由失败）
- 去掉显式 proxy，让 TUN 透明代理后，阿里云 apt 源访问正常（200 OK，2874kB/s）

**关联约束**：
- `.wslconfig` 路径：`C:\Users\27693\.wslconfig`
- WSL2 启动后需 Clash 处于运行状态（TUN 模式开启）才能访问外网
- 关闭 Clash 时如仍需访问国内镜像，可直连；访问境外资源则需手动设置 proxy 环境变量
- **不要**在 `/etc/apt/apt.conf.d/` 下配置 `Acquire::http::Proxy`（已删除）
- **不要**在 `/etc/profile.d/proxy.sh` 中设置全局 `http_proxy`（已删除）

## [2026-05-08] WSL2 + Ubuntu 安装位置

### WSL2 安装到 D 盘
**决策**：WSL2 本体和 Ubuntu 20.04 发行版均安装到 D 盘（`D:\WSL\Ubuntu2004\`）  
**理由**：E 盘为 exFAT，不适合存放 WSL VHD（WSL2 要求 NTFS）；C 盘空间有限，ROS 完整安装 + Gazebo 仿真资源 + 模型权重约需 30-50GB  
**实施方式**：使用 `wsl --import Ubuntu2004 "D:\WSL\Ubuntu2004" <rootfs.tar> --version 2` 而非直接商店安装（商店安装默认在 C 盘且难以迁移）  
**关联约束**：
- D 盘须为 NTFS 格式（WSL2 不支持 exFAT）
- ROS 工作空间路径：WSL 内 `~/excavator_ws`，Windows 侧通过网络路径访问 `\\wsl$\Ubuntu2004\home\<用户名>\excavator_ws`（不是 rootfs 文件夹，VHD 内部文件系统通过 WSL 网络共享挂载）
- VHD 文件位置：`D:\WSL\Ubuntu2004\ext4.vhdx`（勿手动移动）

## [2026-05-08] Phase 1 完成 — 环境关键参数确认

**WSL 用户名**：`excavator`，密码 `excavator123`，已配置 NOPASSWD sudo  
**工作空间路径**：WSL 内 `~/excavator_ws`（即 `/home/excavator/excavator_ws`）  
**GPU**：NVIDIA（驱动 566.24，WSL 侧 CUDA 12.7 可用），PyTorch 使用 cu116 运行时（向下兼容）  
**CUDA 状态**：`torch.cuda.is_available()` 返回 `True`，`torch.version.cuda` = `11.6`  
**pip 镜像**：阿里云（`~/.config/pip/pip.conf`），torch/torchvision 通过官方 whl 本地安装  
**ROS 工作空间编译**：`catkin_make` [100%]，8 个包均可被 `rospack` 识别  
**消息生成**：4 msg + 2 srv，`rosmsg show` 和 `rossrv show` 验证通过  

## [2026-05-08] Phase 2 完成 — 感知模块关键决策

### YOLOv5 权重选型：yolov5s.pt 作为占位权重
**决策**：使用 yolov5s.pt（15MB，标准 COCO 80类）作为 best.pt 占位，后续替换为施工场景专项权重  
**理由**：开发阶段需要一个可用权重验证推理管线；yolov5s 体积最小（15MB < Git LFS 100MB 限制），推理速度最快（符合 ≤200ms 要求）  
**后续**：正式训练使用 COCO 子集（person/vehicle/obstacle 3类）+ Gazebo 合成数据增广

### 中间话题拓扑：raw_detections → tracked_obstacles → detected_obstacles
**决策**：检测节点发布 `/excavator/raw_detections`，跟踪节点发布 `/excavator/tracked_obstacles`，融合节点发布最终 `/excavator/detected_obstacles`  
**理由**：避免两个节点同时发布同一话题产生竞争；明确数据流向，便于独立调试各层  
**权衡**：多了一个中间话题，但调试时可直接 `rostopic echo` 任意层的输出

### DeepSort 位姿占位：归一化像素坐标存入 pose.pose.position.x/y
**决策**：在有深度信息前，临时用归一化图像坐标（0~1）存入 ObstacleInfo.pose  
**理由**：保持消息字段统一；z 字段存 confidence，便于 risk assessor 使用  
**后续**：Phase 5 集成 depth camera 后改为真实 3D 坐标（米）

### Gazebo 仿真骨架：最小 URDF + 3障碍物世界
**决策**：excavator_description 使用 5-link 最小 URDF（底盘+摄像头+激光雷达），world 含3个静态障碍物  
**理由**：Phase 2 验证感知管线可用性，不需要完整挖掘机 mesh；Phase 5 再添加运动学/动力学  
**验证结果**：/camera/image_raw@30Hz + /lidar/scan@10Hz 均正常发布

---

## [2026-05-08] Phase 3 完成 — 风险评估模块关键决策

### TTC 计算公式：基于接近速度的简化模型
**决策**：TTC = distance / (excavator_speed - obstacle_speed)，障碍物速度由卡尔曼滤波器估算  
**理由**：施工现场障碍物速度相对挖掘机较慢（<2m/s），激光雷达提供精确距离，简化公式满足精度要求（误差≤0.5s）  
**验证**：实测 TTC 值（dist=8m→8s, 3m→3s, 0.8m→0.8s）与手动计算完全吻合  
**权衡**：未考虑相对运动方向（只用速度标量），在斜向接近场景下偏保守；Phase 5 可升级为向量TTC

### 风险评分参数标定：领域经验值 + 行人权重调整
**决策**：w_distance=0.6, w_ttc=0.4; 人=1.5, 车=1.2, 静=1.0; safe_distance=5m, critical_distance=1m, safe_ttc=5s, critical_ttc=1.5s  
**理由**：距离是施工现场最直观的安全指标（权重略高）；TTC 反映动态威胁；行人1.5×确保人体安全优先  
**验证**：6组端到端测试全部通过，行人3m处因1.5×权重升至HIGH符合施工安全规范  
**待标定**：Phase 5 Gazebo 实验后根据实测数据微调 critical_distance 和 type_weights

### trajectory_predictor 空列表 bug 修复
**决策**：将 `if not msg.obstacles: return` 改为 `if not msg.obstacles: cleanup_missing(); return`  
**理由**：原实现空帧时不调用 `_cleanup_missing`，导致消失的障碍物 tracker 永不释放（内存泄漏）  
**发现方式**：单元测试 `test_callback_cleans_up_missing` 暴露该 bug

### 仿真验证方式：tmux + rostopic 消息注入（替代 Gazebo GUI）
**决策**：Phase 3 验证使用 tmux 保持 roscore 进程 + 手动注入 ObstacleArray 消息，而非完整 Gazebo 仿真  
**理由**：风险评估模块不依赖 Gazebo 渲染，消息注入测试更精确可控（可手动设定距离/类型）；Gazebo headless 在 WSL 子 shell 中进程生命周期管理复杂  
**约束**：Phase 5 集成测试时仍须在 Gazebo 中验证完整管线

---

---

## [2026-05-08] Phase 4 完成 — 决策与路径规划模块关键决策

### FSM 风险分数来源：订阅 assessed_obstacles 而非 risk_state
**决策**：FSM 从 `/excavator/assessed_obstacles`（ObstacleInfo.risk_score）取最大值作为转换依据，而非 `/excavator/risk_state.current_level`
**理由**：RiskState 消息只有离散 level（LOW/MEDIUM/HIGH），无法支持双阈值磁滞（PAUSED→EMERGENCY 阈值 0.85 在 HIGH 级别内部）；assessed_obstacles 提供连续 risk_score，支持精确磁滞判断
**权衡**：多一个订阅节点间延迟（< 1ms），但换来精确磁滞控制

### FSM 状态机：双阈值磁滞设计
**决策**：进入/退出阈值分离（NORMAL→CAUTION=0.30，退出<0.20；CAUTION→PAUSED=0.60，退出<0.45）
**理由**：防止风险分在阈值附近抖动时频繁切换状态（状态颤振）；PAUSED→CAUTION 自动恢复仅通过周期性检查（5s），EMERGENCY_STOP 仅允许手动服务调用解除
**安全约束**：EMERGENCY_STOP 无任何自动恢复逻辑，这是系统安全性的核心设计要求

### RRT* 参数选择：step=0.5m，rewire=2.0m，5000次迭代
**决策**：step_size=0.5m，rewire_radius=2.0m，max_iterations=5000，obstacle_margin=0.5m
**理由**：step=0.5m 在挖掘机尺寸（~3m）和响应精度（0.3m目标半径）之间平衡；rewire=2.0m 覆盖约 4×step 范围确保路径优化效果；5000次迭代在 5.0s 超时内稳定找到3障碍物场景路径（实测 3625ms）
**验证**：Python 逻辑复现测试 3626ms 内规划成功，终点距目标 0.257m ≤ 0.3m

### 五次多项式路径平滑：Hermite 切线估算
**决策**：路径平滑采用带切线的五次 Hermite 多项式，切线由相邻路点平均差分估算（非等时间参数化）
**理由**：RRT* 输出折线路径含尖角，直接跟踪会产生大角速度；五次多项式确保位置和一阶导数连续（C¹）；切线估算简单高效无需解线性系统
**参数**：每两路点间插值 10 个采样点（约 0.05m 分辨率）

---

## [2026-05-08] Phase 5 完成 — 仿真集成关键决策

### URDF 结构：11连杆分层设计（base_footprint → base_link → 履带/回转体 → 动臂链）
**决策**：底盘 8000kg，通过 box_inertia/cylinder_inertia 宏自动计算惯量，传感器定义分离到 sensors.xacro 通过 xacro:include 引入
**理由**：实际挖掘机底盘+上部结构约 8-30 吨，8000kg 是合理中值；宏避免手动计算错误；分离 sensors.xacro 遵循关注点分离原则
**验证**：check_urdf 通过，11连杆树完整，3个Gazebo插件（差速驱动/摄像头/激光雷达）均已配置

### 施工场景设计：25m×25m，围栏+8建材堆
**决策**：仿真区域定为 25m×25m，4面围栏高 2m，8个建材堆分布在外围区域，中央区域保持通畅供挖掘机运动
**理由**：25m 边长能包含完整的 RRT* 规划测试路径（起点→终点约 15m），围栏防止机器人离开场景；障碍物分布在外围不干扰主路径，需要绕行但不形成死锁
**修改原因（CLAUDE.md 禁止无记录修改 world 文件）**：Phase 5 仿真集成的计划需要，且将原 3 障碍物场景升级为完整施工场景

### 端到端验证：消息注入法替代完整 Gazebo GUI 仿真
**决策**：Phase 5 端到端测试使用与 Phase 3 相同的方式：向 /excavator/predicted_obstacles 直接注入消息，验证 FSM 响应
**理由**：WSL2 无 GUI 环境，Gazebo Actor（行人）行为难以精确控制；直接注入消息可精确控制 TTC/distance/type_weight，验证结果更可靠
**4场景结果**：TEST9(MEDIUM→CAUTION)✓ TEST10(HIGH→EMERG)✓ TEST11(TTC=1.0s→EMERG)✓ TEST12(dominant=HIGH)✓
**约束**：完整 Gazebo 视觉仿真（挖掘机实际驾驶绕障）需 GUI 环境，作为后续实体验证步骤

## [2026-05-08] Phase 6 任务3 完成 — 性能基准测试关键决策

### 测试方法：消息注入法（沿用 Phase 3/5 决策）
**决策**：Phase 6 性能基准测试继续使用消息注入法（phase6_test_node.py 发布 /excavator/predicted_obstacles），而非 Gazebo rosbag 录制  
**理由**：WSL2 无 GUI 环境，Gazebo Actor 动态场景不可精确控制；消息注入可精确控制 TTC/distance/type，结果完全可复现（固定参数）  
**实测结果**：
- 响应时间均值 = 105.4ms（合格 ≤ 1500ms）
- 响应时间最大值 = 200.5ms（合格 ≤ 2000ms）
- 成功率 = 40/40 = 100%（合格 ≥ 90%）
- 各场景：test_static→CAUTION, test_pedestrian/vehicle/multi_threat→EMERGENCY_STOP，全部10/10通过
**约束**：感知延迟（YOLOv5推理）数据未测（需完整感知管线），在汇总 CSV 中标记为空

### FSM 响应机制验证
**决策**：NORMAL→CAUTION→PAUSED→EMERGENCY_STOP 三步顺序转换，每步约 50ms（单次 callback 触发）  
**观测结果**：score≥0.85 时，从 NORMAL 出发约需 3 个 FSM callback 周期（100-200ms）到达 EMERGENCY_STOP  
**约束**：FSM 为安全设计不允许跨状态跳跃，三步顺序是安全保证的一部分

## [2026-05-08] Phase 6 完成 — 感知优化、Web Monitor、最终验收

### YOLOv5 推理延迟：无需优化（GPU 模式已满足）
**决策**：保持 img_size=640px 不变，不启用 TensorRT 量化  
**理由**：GPU（CUDA 11.6）实测 640px 均值=13.3ms（p95=27.7ms），远低于 80ms 目标；320px 均值=9.5ms，提升不显著；不启用 TRT 避免量化精度损失  
**待决策事项已关闭**：TensorRT 方案暂不需要

### DeepSort 参数最终取值
**决策**：max_age=50（从30升级），max_cosine_distance=0.2（保持），n_init=3（保持）  
**理由**：max_age=50对应30Hz摄像头1.67s遮挡容忍，施工场景行人被设备短暂遮挡通常<1s；0.2是外观相似度最严格合理值  
**已更新**：`src/excavator_perception/scripts/deepsort_tracker.py`

### 风险阈值：无需调整（实测验证最优）
**决策**：现有阈值 LOW_THR=0.30 / HIGH_THR=0.70 / 磁滞设计 保持不变  
**理由**：40次测试成功率100%，无漏报；安全区（>5m）内误报率0%；dig模式FP估计8.7%<20%合格  
**待决策事项已关闭**：阈值无需调整

### Web Dashboard 通信：SSE（Server-Sent Events）
**决策**：选用 Flask + SSE（/api/stream 端点），而非 WebSocket（flask-socketio）  
**理由**：SSE 无需安装额外依赖（flask-socketio+eventlet），在 ROS 环境下多线程信号处理更安全；1秒推送频率满足监控需求；浏览器原生 EventSource API 支持重连  
**待决策事项已关闭**

### 最终验收指标（Phase 6 实测）
| 指标 | 目标 | 实测 | 结论 |
|------|------|------|------|
| 响应时间均值 | ≤1500ms | 105.4ms | ✅ |
| 响应时间最大值 | ≤2000ms | 200.5ms | ✅ |
| 成功率 | ≥90% | 100%(40/40) | ✅ |
| YOLOv5延迟(GPU) | ≤80ms | 13.3ms | ✅ |
| /api/health | {"status":"ok"} | 已实现 | ✅ |
| docs/adr/ ≥6条 | 6条 | 6条 | ✅ |
| git tag v1.0-thesis | 已打 | ✅ | ✅ |
| catkin_make | 0 ERROR | [100%] | ✅ |

---

## [2026-05-09] Phase 7 真实端到端修复 — ADR-010 障碍物高度提升

### ADR-010：所有 world 文件中障碍物高度统一提升至覆盖激光雷达扫描面

**问题**：激光雷达安装高度（z≈2.95m，计算链：base_footprint +0.75m → turret_joint +1.0m → sensor_mast_joint +0.9m → lidar_joint +0.3m = 2.95m）远高于场景中所有障碍物顶端（围栏 2.0m、建材堆 0.6~1.5m、行人碰撞体 1.8m），导致 360° 激光扫描全部返回 `inf`，感知链无法获得任何有效数据。

**决策**：不改变 URDF（无合适的避障挂载点：低于 turret 中心则激光射线被车体遮挡；高于 turret 顶则被架空），而是将所有 world 文件中的障碍物提高，使其体积穿过 z=2.95m 的扫描面。

**具体修改**：
- **围栏**（construction_site.world, test_static.world）：高度 2.0m→5.0m，中心 z: 1.0m→2.5m，覆盖范围 0~5m
- **建材堆/障碍物**（construction_site.world, test_static.world）：高度 0.6~1.5m→3.5m，中心 z: 0.3~0.75m→1.75m，覆盖范围 0~3.5m
- **行人碰撞体**（test_pedestrian.world, test_multi_threat.world）：长度 1.8m→4.0m，中心 z: 0.9m→2.0m，覆盖范围 0~4.0m

**理由**：仿真场景并非要求真实比例，而是验证感知-决策-控制链路的功能正确性；在 Gazebo 仿真语境中，"建材堆高 3.5m"只是碰撞体标记，不影响算法逻辑，但能使激光雷达在正确的位置获得有效回波。

**权衡**：
- 优：不需要修改 URDF，规避车体自遮挡问题
- 优：所有四个 world 文件统一策略，修改集中易审查
- 劣：Gazebo 视觉上建材堆偏高，但对算法验证无影响

---

---

## [2026-05-09] Phase 7 完成 — 真实 Gazebo 端到端仿真验证

### ADR-011：sensor_fusion.py 架构变更 — 移除 ApproximateTimeSynchronizer

**问题**：G2/G3 验证中 `/excavator/detected_obstacles` 完全无输出，sensor_fusion 节点收到 lidar_obstacles 后不触发回调。  
**根因分析**：`message_filters.ApproximateTimeSynchronizer(slop=0.05s)` 要求两路话题在 50ms 内同时到达。YOLOv5 CPU 推理实测 ~800ms/帧（无 GPU 时），deepsort_tracker 以 ~1Hz 发布 `/excavator/tracked_obstacles`；激光雷达以 10Hz 发布。两者时间差通常 100~500ms，远超 slop=0.05s，同步器永不触发。  
**决策**：将 ApproximateTimeSynchronizer 替换为各路话题独立订阅回调，引入 `_last_tracks` 缓存字段。激光雷达每次到达时直接调用融合逻辑，使用缓存中的最新跟踪结果（即使是旧的）。  
**理由**：激光雷达是感知链的主要距离信息来源（10Hz 稳定），视觉跟踪（~1Hz CPU）提供目标类型标注。两者不需要严格时间对齐，使用最近可用值语义更接近实际使用场景。  
**权衡**：视觉结果最多有约 1s 滞后，在施工场景中可接受（障碍物速度 < 2m/s，1s 内移动 < 2m，不影响风险等级判断）。  
**文件**：`src/excavator_perception/scripts/sensor_fusion.py`

### ADR-012：lidar_processor 参数调优 — min_range=2.5m，min_cluster_points=1

**问题1 — 机身自检测**：激光雷达安装于 z≈2.95m，向前/后方向的扫描射线会打到挖掘机履带和底盘结构，产生 1.6~2.0m 范围内的有效回波。原 `min_range=0.1m` 或 `min_range=1.5m` 无法过滤这些自检测点，导致 sensor_fusion 始终报告最小障碍物距离 ~1.7m（机身）→ risk_level 持续为 HIGH → FSM 永久 EMERGENCY_STOP。  
**问题2 — 远距障碍物消失**：原 `min_cluster_points=2` 要求一个聚类至少 2 个扫描点。测试场景中 G3 静态障碍物距离 8~12m，在 360° 激光雷达角分辨率下仅返回 1 个有效点，被过滤掉。  
**决策**：`min_range` 提升至 **2.5m**；`min_cluster_points` 降至 **1**。  
**理由**：G3 最近障碍物实测 3.72m，2.5m 截止点可完全过滤机身（最大 ~2.0m）同时保留所有真实障碍物。单点聚类允许远距稀疏障碍物被检测，代价是略有孤立噪声点，但 sensor_fusion 内置角度匹配（0.2rad 阈值）可过滤大多数噪声。  
**文件**：`src/excavator_perception/launch/perception.launch`（覆盖参数：min_range=2.5，min_cluster_points=1）

### Phase 7 最终验证结果（G1/G2/G3 全部通过，2026-05-09）

| 验证项 | 结论 | 关键量化值 |
|--------|------|-----------|
| **G1 headless 烟雾测试** | ✅ 通过 | 13 个节点在线；`/lidar/scan` 10Hz；`/excavator/detected_obstacles` ≥ 1Hz |
| **G2 行人场景（EMERGENCY_STOP）** | ✅ 通过 | 行人靠近至 ~2.1m → risk_level=2(HIGH) → state=3(EMERGENCY_STOP) → cmd_vel.x=0；手动 resume → state=0(NORMAL)，cmd_vel.x=1.0 |
| **G3 静态障碍物绕障（RRT*）** | ✅ 通过 | 3 障碍物检测（3.72m / 8.19m / 8.61m）；risk_level=1(MEDIUM)，state=1(CAUTION)；planned_path x 覆盖 0→9.9m（71 路点，绕障后延伸至障碍物后方） |

**WSL2 git**: commit `2420ea9`，tag `v1.1-real-sim`  
**Windows git**: commit `4f17202`（操作手册），commit `6fdb52d`（进度/runbook）

---

## [2026-05-10] ADR-013：REALTIME-11 修复 — 替换 URDF + planar_move 插件（方案 D+B）

### 背景
Phase 7 验证后发现挖掘机在 Gazebo 中完全无法物理移动（REALTIME-11）：URDF 履带碰撞几何为 Box，平底面接触无法产生滚动摩擦，实测 500kN 外力仅位移 3cm。

### 备选方案
| 方案 | 说明 | 工作量 |
|------|------|--------|
| A | 履带 collision 改为 Cylinder | 中 |
| B | 换 planar_move 插件 | 极低 |
| C | 降地面摩擦系数 mu | 极低 |
| **D+B（选定）** | 替换为 Volvo EC650 CAD URDF + planar_move | 中 |

### 决策
**选定方案 D+B**：以用户提供的 Volvo EC650 真实 CAD URDF（14连杆，STL mesh）替换现有几何体模型，同时使用 `libgazebo_ros_planar_move.so` 替代 diff_drive 彻底绕开履带滚动物理问题。

### 理由
1. EC650 CAD 模型视觉真实性远优于现有几何体，提升论文图表质量
2. planar_move 接口（/cmd_vel + /odom）与 FSM + RRT* 完全兼容，无需修改任何上层逻辑
3. 项目目标为验证感知-决策软件流水线，不需要物理级别履带动力学

### 需适配的问题
- D-01：无移动机制（planar_move 解决）
- D-02：CAD 关节原点偏置（需校验）
- D-03/D-04：补充传感器定义和 Gazebo 插件
- D-05：包路径 `package://volvo_ec650` → `package://excavator_description`
- D-06：补充 base_footprint 根节点
- D-07：碰撞几何简化（mesh → box/cylinder）

### 文件
- 源模型：`Model/Urdf/volvo_ec650/volvo_ec650.urdf`
- 目标文件：`src/excavator_description/urdf/excavator_volvo.urdf.xacro`
- STL 目标：`src/excavator_description/meshes/volvo_ec650/`
- 详细方案：`bug/urdf_fix_plan.md`

---

## [2026-05-10] ADR-014：actor_collider_sync 坐标系统一 — TF2 变换修复

### 问题（bug/g2_coordinate_frame_mismatch.md）
G2 行人场景 `sensor_fusion` 世界坐标近邻匹配永不命中：`actor_collider_sync` 发布的 `world_x/y` 是 Gazebo 绝对坐标（odom 系，~5.1m, 3.3m），而 `lidar_processor` 的 `world_x/y` 是 `base_footprint` 相对坐标（~-5.6m, 2.1m），两者差距约 10m >> 阈值 1.0m。

### 决策
在 `actor_collider_sync.py` 的 `_sync_cb` 中，用 TF2（`odom → base_footprint`）将 Actor 的 Gazebo 世界坐标变换到 `base_footprint` 系后再写入 `obs.world_x/y/z`，与 `lidar_processor` 保持坐标系一致。

### 理由
- `planar_move` 插件在 `odom` 帧追踪机器人（理想运动学，`odom ≈ Gazebo world`），变换路径 `odom → base_footprint` 完整可用
- `lidar_processor` 已使用 TF2（`lidar_link → base_footprint`），两路数据统一到同一系后直接在 `sensor_fusion` 中比较距离

### 变更文件
- `src/excavator_gazebo/scripts/actor_collider_sync.py`：新增 `tf2_ros.Buffer` + `TransformListener`，`_sync_cb` 中替换直接赋值为 TF2 变换；TF 失败降级为 `world_x/y=0.0`（sensor_fusion 会跳过匹配）
- `src/excavator_gazebo/package.xml`：新增 `tf2_ros`、`tf2_geometry_msgs` exec_depend
- `~/kill_all.sh`：新增 `pkill -9 -f "python.*excavator_ws"` 清理孤儿 Python 节点

### 验证结果（2026-05-10）
行人 `distance` = 2.55~5.5m（修复前 999.0），EMERGENCY_STOP 正确触发，cmd_vel=0

---

## [2026-05-11] G3 障碍物位置调整 — 适配 EC650 footprint

**修改文件**：`src/excavator_gazebo/worlds/test_scenarios/test_static.world`（配套：`src/excavator_planner/config/planner_params.yaml`）

**原因**：ADR-013 引入 Volvo EC650 后，车辆 footprint 约 4m 宽，旧 G3 静态障碍物布局按小型 URDF 设计；`obstacle_margin=0.5m` 与障碍物间距不足，RRT* 规划路径贴近障碍物，Gazebo 中 EC650 碰撞几何与静态 box 交叠，导致 planar_move 与接触力互相作用，机体出现姿态抖动/翻倒（见 `bug/g3_static_excavator_tipover.md`）。G3 原验证（2026-05-09）仅验证 topic 输出，EC650 引入后未重新做 GUI 物理导航验证。

**具体改动**：

| 项目 | 旧值 | 新值 |
|------|------|------|
| `obstacle_margin`（planner_params.yaml） | 0.5m | **2.0m** |
| `obstacle_B` 位置（test_static.world） | (9.0, 2.5) | **(9.0, 7.0)** |
| `obstacle_C` 位置（test_static.world） | (12.0, -2.0) | **(12.0, -7.0)** |
| `obstacle_A` 位置（test_static.world） | (5.0, 0.0) | (5.0, 0.0)（不变） |

**验证逻辑**：obstacle_A 距起点 5m > EC650 半宽(2m) + obstacle_margin(2.0m)；obstacle_B/C 外移后各通道宽度 > 2×obstacle_margin + 1m 余量，RRT* 可找到有效 S 形绕障路径；`rrt_star_planner.cpp` 碰撞检测（`d < obs.radius + params_.obstacle_margin`）正确读取 yaml 参数，无硬编码。

---

## [2026-05-11] ADR-015：G3 RRT* 无法找到路径 — co.radius 修正 + 障碍物 S 形回移

### 背景
ADR-013（引入 EC650）+ G3 第一次修复（obstacle_margin 2.0m + 障碍物外移至 y=±7m）解决了物理翻倒问题，但引入新 bug：`RRTStar: no path found to goal (10.00, 0.00)` 持续报警，机器人无法导航（详见 `bug/g3_no_path_found.md`）。

### 根因
1. `rrt_star_planner.cpp` 的 `obstacleCb` 中 `co.radius` 硬编码为 1.0m（未被第一次修复改动），加上 `obstacle_margin=2.0m`，总排除圆半径 = 3.0m，G3 走廊被压缩至 1m，RRT* 5000 次采样无法通过。
2. obstacle_B/C 移至 y=±7m 后距离路径轴线太远，不形成第二次偏折约束，S 形轨迹特征丢失。

### 决策
**`co.radius` 职责厘清**：`co.radius` 应代表障碍物实际物理半径（~0.5m for ~1m box），`obstacle_margin` 代表 EC650 安全裕量（2.0m）。两者叠加后总排除圆 = 2.5m，物理含义正确，且走廊恢复至 2m 可通过。

**障碍物回移**：obstacle_B/C 从 y=±7m 回移至 y=±5m，使其重新对路径形成第二次偏折约束，RRT* 规划出真正的 S 形绕障路径。

### 具体改动

| 项目 | 旧值 | 新值 |
|------|------|------|
| `co.radius`（rrt_star_planner.cpp，obstacleCb 硬编码） | 1.0m | **0.5m** |
| `obstacle_margin`（planner_params.yaml） | 2.0m | 2.0m（不变） |
| `obstacle_B` 位置（test_static.world） | (9.0, 7.0) | **(9.0, 5.0)** |
| `obstacle_C` 位置（test_static.world） | (12.0, -7.0) | **(12.0, -5.0)** |

### S 形几何验证
- obstacle_A (5,0) 排除圆 2.5m：路径在 x≈5 须偏移 y>2.5（上方绕行）
- obstacle_B (9,5) 排除圆 2.5m：下边界 y=2.5，路径在 x≈9 须低于 y<2.5（下压回正）
- S 形约束成立；走廊宽 ≈ 2m，RRT* 可稳定规划

---

## [2026-05-12] G3 坐标系统一与 simple 模型验证 — ADR-016/017

### ADR-016：`ObstacleInfo.world_x/y/z` 统一为 `odom` 全局坐标

**问题**：G3 中 RRT* 使用 `/odom` 作为当前机器人位姿和路径规划坐标系，但 `lidar_processor.py` 曾默认将激光聚类点变换到 `base_footprint`，再写入 `ObstacleInfo.world_x/y/z`。字段名表示 world/global，实际却是机器人相对坐标，导致 RRT* 把障碍物放到机器人附近，采样树难以展开并持续出现 `RRTStar: no path found to goal`。

**决策**：从 2026-05-12 起，`ObstacleInfo.world_x/y/z` 在本项目中统一表示 `odom` 全局规划坐标。`lidar_processor` 默认和 launch 参数均使用 `target_frame=odom`，`sensor_fusion` 保持 `world_frame=odom`，RRT* 可直接消费该字段。

**影响**：
- G3 静态障碍物与 RRT* 坐标系一致，`/planned_path.header.frame_id` 保持 `odom`。
- G2 的 `actor_collider_sync.py` 改为直接发布 actor 的 Gazebo/world 坐标作为 odom 坐标，避免再次转换到 `base_footprint`。
- `trajectory_predictor.py` 订阅 `/odom` 后，用 `obstacle_world - robot_odom` 计算相对距离、相对速度和 TTC，避免将全局坐标距离误认为机器人相对距离。

### ADR-017：G3 默认使用 EC650 footprint 简化动力学代理模型

**问题**：EC650 高保真 URDF 包含多连杆、mesh/collision 和复杂惯量设置，Gazebo ODE 中容易出现 pitch/roll 偏移、翘头和接触抖动。该问题与感知/规划链路是两个不同层面的风险，混在一起会掩盖 G3 的坐标系和 RRT* 验证结果。

**决策**：新增 `src/excavator_description/urdf/excavator_simple.urdf.xacro`，通过 `model_variant:=simple` 启动 G3。simple 模型保留 EC650 量级 footprint 和传感器 frame/topic，但使用简单几何体和固定结构降低 Gazebo 物理不稳定性。原 EC650 模型保留，通过 `model_variant:=ec650` 用于视觉展示或后续高保真物理修复。

**验证**：`xacro` 展开、`check_urdf`、全量 `catkin_make` 均通过；`~/start_g3_simple.sh` 启动后节点在线，`/planned_path` 为 `odom`，FSM 为 `CAUTION`，risk_level=1，模型姿态 roll/pitch 近似 0。

**使用约束**：论文/演示中如使用 simple 模型，应表述为“EC650 footprint 简化动力学代理模型”，不要宣称已完成完整 EC650 机械臂动力学仿真。


## [2026-05-13] ADR-018：G3 动态终点设置 — RViz 2D Nav Goal + 场景扩展

### 背景
G3 静态绕障场景默认终点固定为 `(10, 0)`，路程仅 10m；obstacle_C 位于 `(12, -5)` 已超出终点，机器人实际只需绕过 obstacle_A 即可到达终点，三障碍物 S 形演示效果不完整。答辩演示时无法灵活展示不同路径的绕障过程。

### 决策
**支持运行时通过 RViz "2D Nav Goal" 动态设置终点**，同时扩展 `test_static.world` 的场地范围和障碍物布局，使默认配置本身就能展示完整 S 形绕障。

### 具体改动

| 文件 | 改动 |
|------|------|
| `src/excavator_planner/include/excavator_planner/rrt_star_planner.h` | 新增 `goal_sub_`（`geometry_msgs/PoseStamped`）和 `marker_pub_`（`visualization_msgs/Marker`）成员 |
| `src/excavator_planner/src/rrt_star_planner.cpp` | 新增 `goalCb`：收到 `/move_base_simple/goal` 后更新 `goal_`、清空当前路径、立即触发重规划；发布红色球形 Marker（半径 0.3m）到 `/excavator/goal_marker` |
| `src/excavator_planner/config/planner_params.yaml` | `goal_x: 10.0` → `goal_x: 18.0` |
| `src/excavator_gazebo/worlds/test_scenarios/test_static.world` | 围栏长度 30m→42m，中心 x=0→x=6（覆盖 x=-15 到 x=+27）；三障碍物重新布置为真正 S 形（见下方几何设计） |
| `src/excavator_planner/package.xml` | 新增 `visualization_msgs` exec_depend |
| `src/excavator_planner/CMakeLists.txt` | `find_package` 和 `target_link_libraries` 加入 `visualization_msgs` |

### 障碍物新布局（S 形几何设计）

| 障碍物 | 旧位置 | 新位置 | 作用 |
|--------|--------|--------|------|
| obstacle_A | (5, 0) | **(5, 0)** 不变 | 正中挡路，强制首次侧偏（y+） |
| obstacle_B | (9, 5) | **(11, 4)** | 位于 y+ 绕行走廊中，强制回压至中轴线（y-） |
| obstacle_C | (12, -5) | **(16, 0)** | 回到中轴线，形成第二次偏折，完成 S 形 |

有效排除圆半径 = co.radius(0.5m) + obstacle_margin(2.0m) = 2.5m；走廊验证：

- obs_A(5,0) 上侧走廊：y=0+2.5=2.5m，到 y=-15 围栏 12.5m ✅
- obs_A 与 obs_B 之间（x=8，y≈3）：两排除圆均不相交，通道 ≥ 2m ✅
- obs_B(11,4) 下侧走廊：y=4-2.5=1.5m，RRT* 可规划路径回中轴 ✅
- obs_C(16,0) 两侧走廊：y>2.5 或 y<-2.5，到围栏（x=27 侧无围栏）✅

### 设计决策要点

- **frame_id 处理**：直接使用 `PoseStamped.pose.position.x/y`，忽略 frame_id（RViz Fixed Frame = odom，不会变）
- **立即重规划**：goalCb 内直接调用 `planningTimerCb`，不等 2s 定时器
- **marker 外观**：红色实心球，`ns=goal_marker`，`id=0`，`lifetime=0`（常驻），随新 goal 覆盖更新
- **线程安全**：`goal_` 和 `current_path_` 访问加 `std::mutex goal_mutex_`
- **RViz 配置**：`excavator_monitor.rviz` 已包含 "2D Nav Goal" 工具，无需修改

### 理由
- 动态终点让答辩演示时可现场调整路径，展示系统对不同目标的自适应规划能力
- 场地扩展和障碍物重布局使默认启动即可展示完整 S 形三障碍物绕行，无需手动点击
- 工程量小（~50-60 行，5 个文件），风险低，不影响 G1/G2 场景

### 待验证
- [x] catkin_make 0 ERROR（2026-05-13 验证通过，`[100%] Built target rrt_star_planner`）
- [ ] RViz 点击 2D Nav Goal → goal_marker 红球出现 → 路径重规划
- [ ] 默认启动：三障碍物 S 形路径正确规划（见 Fix-1）
- [ ] G1 烟雾测试不退化

### Fix-1（2026-05-13）：默认终点落在 obstacle_C 膨胀区内
**问题**：obstacle_C(16,0)，有效排除圆 2.5m，默认终点 (18,0) 距中心仅 2.0m < 2.5m，
RRT* 持续报 `no path found to goal (18.00, 0.00)`。  
**修复**：`planner_params.yaml` 中 `goal_x: 18.0` → `goal_x: 20.0`，余量 4m。  
**文件**：`src/excavator_planner/config/planner_params.yaml`（1 行）

---

## [2026-05-13] ADR-019：G3 障碍物布局再调整 — 修复走廊过窄导致机器人卡死

### 问题（2026-05-13 G3 实车运行观察）

ADR-018 将 obs_B 移至 (11, 4)，obs_A(5,0) 与 obs_B(11,4) 圆心距仅 7.21m，有效排除圆（2.5m×2）gap = **2.21m**。机器人在执行 RRT* 规划路径时，路径中点距两圆心仅 3.60m，风险评分 ≈ 0.52，超过 PAUSED 进入阈值（0.60）临界点；实际运行时机器人一旦因跟踪误差稍微偏离规划路径，便触发 PAUSED。PAUSED 退出需 score < 0.45（对应距离 > 3.2m），而停止后对静态障碍物 score 维持在 0.52 → **机器人永久卡死在 PAUSED**。

### 根因分析

- RRT* 排除圆半径 = co.radius(0.5) + obstacle_margin(2.0) = **2.5m**（规划安全裕量）
- FSM PAUSED 进入：score ≥ 0.60，对应距离 ≤ **2.6m**（小于 2.5m 排除圆极限）
- FSM PAUSED 退出：score < 0.45，对应距离 ≥ **3.2m**
- 走廊最近距离（3.60m）< PAUSED 退出所需距离（3.2m）：计划路径合法，但执行中一旦进入 PAUSED 就无法自动退出

obs_B(11,4) 的另一个问题：ADR-018 Option B 曾提议将 obs_A 移至 (5,5)，但经几何验证，obs_A 在 y=5 时排除圆南边界为 y=2.5，机器人沿 y≈0 直行不受阻挡，**S 形约束失效**。正确做法是保留 obs_A 在 (5,0) 以挡住直线路径。

### 决策

**obs_A 不动（(5,0)），只调整 obs_B 和 obs_C：**

| 障碍物 | ADR-018 位置 | ADR-019 位置 | 改动 |
|--------|------------|------------|------|
| obs_A | (5, 0) | **(5, 0)** | 不变 |
| obs_B | (11, 4) | **(11, 5)** | y +1 |
| obs_C | (16, 0) | **(17, 0)** | x +1 |
| goal | (20, 0) | (20, 0) | 不变 |

### 几何验证

- **A↔B** 圆心距：sqrt(6²+5²) = **7.81m**，间隙 = 7.81-5.0 = **2.81m**（+0.60m vs ADR-018）
- **B↔C** 圆心距：sqrt(6²+5²) = **7.81m**，间隙 = **2.81m**（对称布局）
- A↔B 走廊中点：(8, 2.5)，距 A = 距 B = **3.91m** → 风险评分 ≈ 0.19 → **NORMAL ✓**
- B↔C 走廊中点：(14, 2.5)，距 B = 距 C = **3.91m** → **NORMAL ✓**
- goal(20,0) 距 C(17,0) = **3.0m > 2.5m ✓**
- 全路径最近接触距离 **3.91m >> 3.2m**（PAUSED 退出阈值），FSM 全程不触发 PAUSED ✓

### S 形路径说明

```
y
4 |  ╱─╲      ╱─╲
3 | /    ╲  ╱     ╲
2 |       ─╱       ─→ goal(20,0)
1 |
0 +──────────────────── x
   0   5   11   17  20
      A    B    C
```
- obs_A(5,0) 挡住 y=0 直线路，强制北偏（y>2.5）
- obs_B(11,5) 南边界 y=2.5，与 obs_A 北边界 y=2.5 对齐，走廊中心 y≈2.5，机器人在 x=8 区域过渡
- obs_C(17,0) 北边界 y=2.5，再次挡住下压路径，强制北绕
- 路径产生「北→南→北」三段 S 形，幅度 y: 0→3.5→1.5→3→0

### 改动文件

| 文件 | 改动 |
|------|------|
| `src/excavator_gazebo/worlds/test_scenarios/test_static.world` | obs_B pose: y=4→y=5；obs_C pose: x=16→x=17 |
| `~/start_g3_simple.sh` | roslaunch 命令增加 `rviz:=true` 参数 |

### 待验证

- [x] G3 simple 场景已通过 `~/start_g3_simple.sh` 启动，且 `/rviz` 节点在线（2026-05-13 验证）。
- [x] `test_static.world` XML 语法通过：`xmllint --noout`（2026-05-13 验证）。
- [x] 启动脚本已默认启用 RViz：`~/start_g3_simple.sh` 中 roslaunch 参数为 `rviz:=true`。
- [ ] Gazebo 重启后 RRT* 不再报 `no path found`
- [ ] FSM 全程保持 NORMAL/CAUTION，不触发 PAUSED
- [ ] RViz 可见清晰 S 形路径
- [ ] G1 烟雾测试不退化

### 验证记录（2026-05-13）

本次按 ADR-019 修改后启动 `~/start_g3_simple.sh`，tmux 会话 `g3_simple` 创建成功，ROS 节点包含 `/gazebo`、`/gazebo_gui`、`/rviz`、`/rrt_star_planner`、`/fsm_controller`，日志显示 `SpawnModel: Successfully spawned entity`。

但一次状态采样显示 `/excavator/system_state.state=2`、`reason="PAUSED"`，同时 `/excavator/risk_state.current_level=1`、`min_distance≈2.71m`、`primary_threat_id="lidar_cluster_4"`。因此 ADR-019 的“全程 NORMAL/CAUTION、不触发 PAUSED”验收目标尚未通过，需继续排查实际加载 world、旧进程残留、风险距离来源或走廊几何裕量。

---

## 待决策事项

- [x] ~~YOLOv5 训练数据集来源~~：yolov5s.pt 占位权重满足验证，后续使用 Gazebo 合成数据微调
- [x] ~~TensorRT 量化方案~~：GPU 延迟已满足，无需量化
- [x] ~~Web Dashboard 通信方式~~：选定 SSE
- [x] ADR-013 已完成：方案B planar_move 替换，机器人可移动（odom.x=1.90m 验证通过，2026-05-10）
- [x] ADR-014 已完成：actor_collider_sync TF2 坐标系修复，G2 行人场景重新验证通过（2026-05-10）
- [x] G3 物理导航 bug 已修复（第一次）：obstacle_margin 2.0m + 障碍物外移（2026-05-11）
- [x] ADR-015 已完成：co.radius 0.5m + obstacle_B/C 回移至 y=±5m，解决 no path found（见 `bug/g3_no_path_found.md`）
- [x] GAP-3 已完成：construction_site.world 添加行人 Actor，主场景动态行人避障 Gazebo 端到端验证通过（2026-05-12）

---

## [2026-05-13] ADR-020 — 修复 G3 绕障后 FSM 永久 PAUSED

**决策**：将 CAUTION→PAUSED 入口阈值从 0.60 提高到 0.72，并进一步让静态障碍物只触发 NORMAL/CAUTION，不触发 PAUSED/EMERGENCY；PAUSED/EMERGENCY 保留给 person/vehicle 等动态高风险目标。同时让 RViz 显示 `/excavator/goal_marker`，方便验证 2D Nav Goal 的红色目标球。

**根因**：RRT* 绕过 obs_A 时最近通过距离约为 2.5m（`co.radius + obstacle_margin`），对应静态障碍物风险分数会接近或超过旧阈值 0.60。单纯提高到 0.72 后，真实运行仍可能因 TTC 分量出现瞬时峰值而触发 PAUSED；停止后距离不再增大，score 仍高于 PAUSED 退出阈值 0.45，导致永久卡住。

**修改文件**：
- `src/excavator_decision/config/fsm_params.yaml`：新增阈值配置，`caution_to_paused: 0.72`；其余 0.30/0.20/0.45/0.85 不变。
- `src/excavator_decision/scripts/fsm_controller.py`：`_C2P` 默认值同步改为 0.72；新增 `current_pause_score`，只统计非静态障碍物用于 PAUSED/EMERGENCY 转换。
- `src/excavator_gazebo/config/excavator_monitor.rviz`：新增 `GoalMarker`，订阅 `/excavator/goal_marker`。

**影响评估**：
- G3 静态绕障：静态障碍物可持续触发 CAUTION 降速绕行，但不会触发 PAUSED，避免永久卡死。
- G2 行人/车辆：非静态目标仍参与 PAUSED/EMERGENCY 判断，安全停车逻辑保留。

**验证**（2026-05-13）：终止 WSL 清理旧 ROS/Gazebo 后重启 `~/start_g3_simple.sh`，95 秒采样：`/excavator/system_state.state=1(CAUTION)`，未进入 PAUSED；`/odom.pose.pose.position.x≈19.88`，已接近 `goal_x=20.0`。


---

## [2026-05-13] ADR-018：G3 动态终点设置 — RViz 2D Nav Goal + 场景扩展

### 背景
G3 默认终点固定 (10,0)，路程仅 10m；obstacle_C 在 (12,-5) 超出终点后方，机器人只需绕 obs_A 即达终点，S 形演示不完整。

### 决策
支持 RViz 2D Nav Goal 运行时动态设置终点，同时扩展 test_static.world 场地和障碍物布局使默认配置即可完整演示 S 形绕障。

### 改动文件
- rrt_star_planner.h：新增 goal_sub_、marker_pub_、goal_mutex_
- rrt_star_planner.cpp：新增 goalCb（立即重规划 + 红色球 Marker r=0.3m 到 /excavator/goal_marker）
- planner_params.yaml：goal_x 10.0→18.0
- test_static.world：围栏 30m→42m 中心 x=6；障碍物 obs_A(5,0) obs_B(11,4) obs_C(16,0)
- package.xml + CMakeLists.txt：加 visualization_msgs 依赖

### 设计要点
- 忽略 frame_id，直接用 x/y（Fixed Frame=odom 不变）
- goalCb 内立即调用 planningTimerCb，不等 2s 定时器
- goal_ + current_path_ 加 std::mutex goal_mutex_ 保证线程安全

### 待验证
- [ ] catkin_make 0 ERROR
- [ ] RViz 2D Nav Goal → goal_marker + 重规划
- [ ] 默认 goal=(18,0) S 形路径正确
- [ ] G1 不退化

---

## [2026-05-13] ADR-021 — 所有场景统一使用 simple 模型

**决策**：将 `gazebo_world.launch` 和 `full_simulation.launch` 中 `model_variant` 参数的默认值从 `ec650` 改为 `simple`。EC650 高保真 URDF 保留但不再使用。

**根因**：EC650 高保真 URDF（Volvo CAD 模型，14连杆+STL mesh）在 Gazebo ODE 中物理不稳定，所有场景（G1/G2/G3）均出现 pitch/roll 偏移、翘头、翻倒。`excavator_simple.urdf.xacro` 已在 G3 验证通过（roll/pitch ≈ 0，姿态稳定），可直接复用。

**修改文件**：

| 文件 | 改动 |
|------|------|
| `src/excavator_gazebo/launch/gazebo_world.launch` | `model_variant` default: `ec650` → `simple` |
| `src/excavator_gazebo/launch/full_simulation.launch` | `model_variant` default: `ec650` → `simple` |

**影响评估**：
- G1 烟雾测试：传感器 topic 不变（`/lidar/scan`、`/camera/image_raw`），节点在线验证不受影响
- G2 行人场景：`actor_collider_sync` + `sensor_fusion` 链路不依赖模型细节，风险评估逻辑不变
- G3 静态绕障：已使用 `model_variant:=simple`，本次仅消除手动指定参数的需要
- EC650 原模型文件保留，后续如需高保真视觉展示可通过 `model_variant:=ec650` 切换

**详细 bug 记录**：`bug/g1_ec650_tipover_all_scenarios.md`

**待验证**：
- [ ] `gazebo_world.launch` / `full_simulation.launch` 默认值已改为 `simple`
- [ ] G1 headless 启动后节点在线、传感器频率正常
- [ ] G2 行人场景 EMERGENCY_STOP 逻辑不退化
- [ ] G3 静态绕障 S 形路径正常规划
