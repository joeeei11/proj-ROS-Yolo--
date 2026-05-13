#!/bin/bash
source ~/excavator_ws/devel/setup.bash
tmux new-session -d -s g2_sim -x 220 -y 50 2>/dev/null || true
tmux send-keys -t g2_sim "source ~/excavator_ws/devel/setup.bash && roslaunch excavator_gazebo full_simulation.launch scenario:=pedestrian model_variant:=simple rviz:=true 2>&1 | tee /tmp/g2_launch.log" Enter
echo 'G2 pedestrian simple-model launch started in tmux g2_sim'
