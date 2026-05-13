#!/bin/bash
source ~/excavator_ws/devel/setup.bash
WORLD=$(rospack find excavator_gazebo)/worlds/test_scenarios/test_static.world
tmux new-session -d -s g3_simple -x 220 -y 50 2>/dev/null || true
tmux send-keys -t g3_simple "source ~/excavator_ws/devel/setup.bash && roslaunch excavator_gazebo full_simulation.launch world_file:=$WORLD scenario:=static model_variant:=simple rviz:=true 2>&1 | tee /tmp/g3_launch.log" Enter
echo "G3 static simple-model launch started in tmux g3_simple"
