# 挖掘机作业智能避障系统 (ExcavatorSafeNav)

基于 YOLOv5 + DeepSort + ROS Noetic 的挖掘机智能避障系统，集成 Gazebo 仿真验证。

## 系统要求

- Ubuntu 20.04 LTS（推荐通过 WSL2 在 Windows 上运行）
- ROS Noetic
- Python 3.8
- PyTorch 1.12.1（可选 CUDA 11.6）

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/joeeei11/proj-ROS-Yolo--.git excavator_ws
cd excavator_ws
```

### 2. 安装 ROS Noetic

```bash
sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu focal main" > /etc/apt/sources.list.d/ros-latest.list'
curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
sudo apt update
sudo apt install -y ros-noetic-desktop-full python3-catkin-tools
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### 3. 安装 Python 依赖

```bash
pip3 install torch==1.12.1+cu116 torchvision==0.13.1+cu116 -f https://download.pytorch.org/whl/torch_stable.html
pip3 install opencv-python==4.5.5.64 filterpy==1.4.5 flask==2.3.3 scipy numpy
```

### 4. 安装 ROS 依赖包

```bash
sudo apt install -y ros-noetic-gazebo-ros-pkgs ros-noetic-gazebo-ros-control   ros-noetic-robot-state-publisher ros-noetic-joint-state-publisher   ros-noetic-diff-drive-controller ros-noetic-cv-bridge ros-noetic-vision-opencv
```

### 5. 编译工作空间

```bash
catkin_make -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash
```

### 6. 启动仿真系统

```bash
# 完整系统（含 Gazebo GUI）
roslaunch excavator_gazebo full_simulation.launch

# 无头模式（服务器/无显示器）
roslaunch excavator_gazebo full_simulation.launch headless:=true

# 切换测试场景
roslaunch excavator_gazebo full_simulation.launch world_file:=$(rospack find excavator_gazebo)/worlds/test_scenarios/test_pedestrian.world
```

### 7. 查看 Web 监控面板

```bash
python3 src/excavator_monitor/scripts/monitor_server.py
# 浏览器访问 http://localhost:8080
```

## 目录结构

```
src/
├── excavator_msgs/        # 自定义 ROS 消息/服务定义
├── excavator_description/ # URDF 机器人模型（11连杆）
├── excavator_perception/  # YOLOv5 目标检测 + DeepSort 跟踪 + 激光雷达融合
├── excavator_risk/        # 多因子风险评估（LOW/MEDIUM/HIGH）
├── excavator_decision/    # 有限状态机决策控制器
├── excavator_planner/     # RRT* 路径规划（C++17）
├── excavator_gazebo/      # Gazebo 仿真世界与场景
└── excavator_monitor/     # Web 监控面板 + 数据记录
```

## 测试

```bash
# 单元测试
pytest src/excavator_risk/test/ -v
pytest src/excavator_perception/test/ -v
pytest src/excavator_decision/test/ -v

# ROS 集成测试
catkin_make run_tests
```

## 技术栈

| 组件 | 版本 |
|------|------|
| ROS | Noetic 1.16.x |
| Gazebo | 11 |
| PyTorch | 1.12.1 + CUDA 11.6 |
| YOLOv5 | v6.x |
| Python | 3.8 |
| C++ | 17 |
