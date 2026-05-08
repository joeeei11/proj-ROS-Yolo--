# ADR-004：路径规划实现语言 — RRT* C++17

**状态**：已接受  
**日期**：2026-05-08  
**作者**：ExcavatorSafeNav 开发团队

## 背景

系统在 CAUTION 状态下需要实时计算绕行路径，规划节点须在 200ms 内完成单次 RRT* 求解（max_iter=5000，地图尺寸 50m×50m）。感知/评估/决策层已用 Python 实现，但 Python 的 GIL 和循环性能难以满足规划层实时性要求。

## 决策

路径规划模块（excavator_planner）使用 **C++17** 实现，通过 catkin CMakeLists.txt 编译为 ROS 节点，与 Python 层通过标准 ROS 话题通信。

## 理由

1. **性能优势**：C++ RRT* 单次规划（5000 次迭代）耗时约 15–30ms，Python 等效实现约 120–200ms
2. **内存控制**：树节点使用 std::vector 预分配，避免 Python GC 停顿导致的延迟抖动
3. **ROS 兼容**：roscpp 与 rospy 共享同一 Master，话题/服务接口透明互通
4. **路径平滑**：五次 Hermite 多项式平滑直接在 C++ 中计算，避免 Python ↔ C++ 数据跨语言拷贝

## 权衡

- C++ 开发调试周期比 Python 长；通过充分的 GTest 单元测试和 RViz 可视化弥补
- 编译依赖 catkin_make，增量编译时间约 8s；接受该代价

## 结果

rrt_star_planner 节点编译通过，静态障碍物绕行测试（test_static.world）规划延迟均值 22ms，满足实时性要求。
