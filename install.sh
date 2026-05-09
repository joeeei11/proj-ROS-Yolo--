#!/bin/bash
# ExcavatorSafeNav 一键安装脚本
# 适用于 Ubuntu 20.04 LTS（原生或 WSL2）
# 用法：bash install.sh [--cpu]
#   --cpu  强制使用 CPU 推理（无 NVIDIA GPU 时使用）

set -e
WORKSPACE_DIR="$(cd "$(dirname "$0")" && pwd)"
USE_CPU=false
[[ "$1" == "--cpu" ]] && USE_CPU=true

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ── 系统检查 ──────────────────────────────────────────────
info "检查系统环境..."
if ! grep -q "Ubuntu 20.04" /etc/os-release 2>/dev/null; then
    warn "本系统非 Ubuntu 20.04，可能出现兼容性问题。继续? (y/N)"
    read -r ans; [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

# ── ROS Noetic ────────────────────────────────────────────
if ! command -v rosversion &>/dev/null; then
    info "安装 ROS Noetic..."
    sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu focal main" > /etc/apt/sources.list.d/ros-latest.list'
    curl -s https://raw.githubusercontent.com/ros/rosdistro/master/ros.asc | sudo apt-key add -
    sudo apt-get update -q
    sudo apt-get install -y ros-noetic-desktop-full
    echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
    info "ROS Noetic 安装完成"
else
    info "ROS Noetic 已安装 ($(rosversion -d))"
fi

source /opt/ros/noetic/setup.bash

# ── ROS 额外依赖包 ─────────────────────────────────────────
info "安装 ROS 依赖包..."
sudo apt-get install -y \
    python3-catkin-tools \
    ros-noetic-gazebo-ros-pkgs \
    ros-noetic-gazebo-ros-control \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher \
    ros-noetic-joint-state-publisher-gui \
    ros-noetic-diff-drive-controller \
    ros-noetic-cv-bridge \
    ros-noetic-vision-opencv \
    ros-noetic-nav-msgs \
    ros-noetic-tf2-ros \
    ros-noetic-tf \
    tmux \
    python3-pip

# ── Python 依赖 ───────────────────────────────────────────
info "安装 Python 依赖..."

# 检测 GPU
HAS_GPU=false
if command -v nvidia-smi &>/dev/null && nvidia-smi &>/dev/null 2>&1; then
    HAS_GPU=true
fi

if [[ "$USE_CPU" == "true" ]]; then
    HAS_GPU=false
    info "强制 CPU 模式"
fi

if [[ "$HAS_GPU" == "true" ]]; then
    info "检测到 NVIDIA GPU，安装 CUDA 版本 PyTorch..."
    pip3 install torch==1.12.1+cu116 torchvision==0.13.1+cu116 \
        --extra-index-url https://download.pytorch.org/whl/cu116 || \
    pip3 install torch==1.12.1+cu116 torchvision==0.13.1+cu116 \
        -f https://download.pytorch.org/whl/torch_stable.html
else
    info "CPU 模式，安装 CPU 版 PyTorch（视觉推理 ~1Hz，不影响激光雷达路径）..."
    pip3 install torch==1.12.1+cpu torchvision==0.13.1+cpu \
        -f https://download.pytorch.org/whl/torch_stable.html
fi

pip3 install \
    "opencv-python==4.5.5.64" \
    "filterpy==1.4.5" \
    "flask==2.3.3" \
    "deep-sort-realtime==1.3.2" \
    scipy numpy matplotlib seaborn Pillow PyYAML requests

# ── 编译工作空间 ──────────────────────────────────────────
info "编译 ROS 工作空间..."
cd "$WORKSPACE_DIR"
catkin_make -DCMAKE_BUILD_TYPE=Release
source devel/setup.bash

# ── 创建辅助脚本 ──────────────────────────────────────────
info "创建 ~/kill_all.sh ~/start_g2.sh ~/start_g3.sh ~/monitor_g2.sh ..."

cat > ~/kill_all.sh << 'SCRIPT_EOF'
#!/bin/bash
pkill -9 -f "roslaunch"  2>/dev/null
pkill -9 -f "gzserver"   2>/dev/null
pkill -9 -f "gzclient"   2>/dev/null
pkill -9 -f "rosmaster"  2>/dev/null
pkill -9 -f "roscore"    2>/dev/null
sleep 3
pgrep -f gzserver > /dev/null 2>&1 && echo "STILL_RUNNING" || echo "ALL_STOPPED"
SCRIPT_EOF

cat > ~/start_g2.sh << SCRIPT_EOF
#!/bin/bash
source ~/excavator_ws/devel/setup.bash
WORLD=\$(rospack find excavator_gazebo)/worlds/test_scenarios/test_pedestrian.world
tmux new-session -d -s g2_ped -x 220 -y 50 2>/dev/null || true
tmux send-keys -t g2_ped "source ~/excavator_ws/devel/setup.bash && roslaunch excavator_gazebo full_simulation.launch world_file:=\$WORLD scenario:=pedestrian rviz:=false 2>&1 | tee /tmp/g2_launch.log" Enter
echo "G2 pedestrian launch started in tmux g2_ped"
SCRIPT_EOF

cat > ~/start_g3.sh << SCRIPT_EOF
#!/bin/bash
source ~/excavator_ws/devel/setup.bash
WORLD=\$(rospack find excavator_gazebo)/worlds/test_scenarios/test_static.world
tmux new-session -d -s g3_static -x 220 -y 50 2>/dev/null || true
tmux send-keys -t g3_static "source ~/excavator_ws/devel/setup.bash && roslaunch excavator_gazebo full_simulation.launch world_file:=\$WORLD scenario:=static rviz:=false 2>&1 | tee /tmp/g3_launch.log" Enter
echo "G3 static launch started in tmux g3_static"
SCRIPT_EOF

cat > ~/monitor_g2.sh << 'SCRIPT_EOF'
#!/bin/bash
source /opt/ros/noetic/setup.bash
source ~/excavator_ws/devel/setup.bash
for i in $(seq 1 15); do
    RISK=$(timeout 2 rostopic echo /excavator/risk_state -n 1 2>/dev/null | grep -E 'current_level|min_distance' | tr '\n' ' ')
    SYS=$(timeout 2 rostopic echo /excavator/system_state -n 1 2>/dev/null | grep 'state:' | head -1)
    CMD=$(timeout 1 rostopic echo /cmd_vel -n 1 2>/dev/null | grep 'x:' | head -1)
    echo "[$i] $RISK | $SYS | cmd_vel $CMD"
    sleep 2
done
SCRIPT_EOF

chmod +x ~/kill_all.sh ~/start_g2.sh ~/start_g3.sh ~/monitor_g2.sh

# ── 配置 bashrc ───────────────────────────────────────────
SETUP_LINE="source $WORKSPACE_DIR/devel/setup.bash"
if ! grep -qF "$SETUP_LINE" ~/.bashrc; then
    echo "$SETUP_LINE" >> ~/.bashrc
    info "已将工作空间 setup.bash 加入 ~/.bashrc"
fi

# ── 完成 ─────────────────────────────────────────────────
echo ""
echo "=================================================="
info "安装完成！"
echo ""
echo "  下一步 — 快速验证 G3 场景（静态障碍物绕行）："
echo ""
echo "    source ~/.bashrc"
echo "    ~/kill_all.sh && ~/start_g3.sh"
echo "    sleep 45 && rosnode list | wc -l   # 期望：13"
echo ""
echo "  完整使用说明：docs/操作手册-v1.1-real-sim.md"
echo "=================================================="
