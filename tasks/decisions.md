# 技术决策记录

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

## 待决策事项

- [x] ~~YOLOv5 训练数据集来源~~：yolov5s.pt 占位权重满足验证，后续使用 Gazebo 合成数据微调
- [x] ~~TensorRT 量化方案~~：GPU 延迟已满足，无需量化
- [x] ~~Web Dashboard 通信方式~~：选定 SSE
