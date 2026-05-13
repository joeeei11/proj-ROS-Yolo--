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
