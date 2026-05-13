#!/bin/bash
pkill -9 -f "roslaunch" 2>/dev/null
pkill -9 -f "gzserver" 2>/dev/null
pkill -9 -f "gzclient" 2>/dev/null
pkill -9 -f "rosmaster" 2>/dev/null
pkill -9 -f "roscore" 2>/dev/null
pkill -9 -f "python.*excavator_ws" 2>/dev/null
sleep 3
if pgrep -f gzserver > /dev/null 2>&1; then
  echo "STILL_RUNNING"
else
  echo "ALL_STOPPED"
fi
