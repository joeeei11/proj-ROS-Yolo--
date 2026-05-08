#!/usr/bin/env python3
"""
phase6_test_node.py
Phase 6 测试节点（纯 pub/sub，不启动子进程）

调用方：phase6_run_all.sh 负责启动 roscore + 节点
本脚本仅作为 ROS 节点连接到已有 roscore，执行消息注入测试并写 CSV。
"""

import csv
import os
import sys
import time
from datetime import datetime

import rospy
from excavator_msgs.msg import ObstacleArray, ObstacleInfo, SystemState, RiskState
from geometry_msgs.msg import PoseStamped, Vector3
from std_msgs.msg import Header
from std_srvs.srv import Trigger, TriggerResponse

# ─── 场景配置 ─── #
SCENARIOS = {
    "test_static": {
        "description": "静态障碍物（CAUTION）",
        "obstacles": [
            {"id": "s1", "type": "obstacle", "distance": 3.0, "ttc": 3.0, "vel": 0.0},
        ],
        "target_state": 1,   # CAUTION
    },
    "test_pedestrian": {
        "description": "行人接近（EMERGENCY_STOP）",
        "obstacles": [
            {"id": "p1", "type": "person",   "distance": 2.0, "ttc": 1.0, "vel": 0.5},
        ],
        "target_state": 3,
    },
    "test_vehicle": {
        "description": "高速车辆（EMERGENCY_STOP）",
        "obstacles": [
            {"id": "v1", "type": "vehicle",  "distance": 1.5, "ttc": 0.9, "vel": 2.0},
        ],
        "target_state": 3,
    },
    "test_multi_threat": {
        "description": "多威胁（EMERGENCY_STOP）",
        "obstacles": [
            {"id": "p1", "type": "person",   "distance": 2.0, "ttc": 1.0, "vel": 0.5},
            {"id": "v1", "type": "vehicle",  "distance": 3.0, "ttc": 2.0, "vel": 1.5},
            {"id": "s1", "type": "obstacle", "distance": 6.0, "ttc": 6.0, "vel": 0.0},
        ],
        "target_state": 3,
    },
}

SAFE_CFG = [{"id": "far", "type": "obstacle", "distance": 12.0, "ttc": 999.0, "vel": 0.0}]

CSV_FIELDS = [
    "run_id", "timestamp", "scenario", "event_type",
    "response_time_ms", "perception_latency_ms_p95",
    "risk_level", "obstacle_type", "min_distance_m", "success",
]

WS = os.path.expanduser("~/excavator_ws")
RESULTS_DIR = os.path.join(WS, "results")
RISK_LV_NAMES = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
STATE_NAMES   = {0: "NORMAL", 1: "CAUTION", 2: "PAUSED", 3: "EMERGENCY_STOP"}

# ─── 全局状态 ─── #
g_state      = None
g_risk_lv    = None
g_min_dist   = None


def state_cb(msg):
    global g_state
    g_state = msg.state


def risk_cb(msg):
    global g_risk_lv, g_min_dist
    g_risk_lv   = msg.current_level
    g_min_dist  = msg.min_distance


def make_array(cfgs):
    now = rospy.Time.now()
    arr = ObstacleArray()
    arr.header.stamp    = now
    arr.header.frame_id = "base_link"
    for c in cfgs:
        o = ObstacleInfo()
        o.header            = arr.header
        o.obstacle_id       = c["id"]
        o.obstacle_type     = c["type"]
        o.distance          = float(c["distance"])
        o.ttc               = float(c["ttc"])
        o.relative_velocity = float(c["vel"])
        ps = PoseStamped()
        ps.header = arr.header
        ps.pose.position.x = float(c["distance"])
        o.pose = ps
        o.velocity_vec = Vector3(x=float(c["vel"]))
        arr.obstacles.append(o)
    return arr


def try_resume():
    try:
        rospy.wait_for_service("/excavator/resume", timeout=0.5)
        svc = rospy.ServiceProxy("/excavator/resume", Trigger)
        svc()
    except Exception:
        pass


def run_single(pub, scene_name, run_id, n_runs, timeout=5.0, pub_hz=20.0):
    global g_state, g_risk_lv, g_min_dist
    cfg = SCENARIOS[scene_name]
    rate = rospy.Rate(pub_hz)
    safe_arr   = make_array(SAFE_CFG)
    danger_arr = make_array(cfg["obstacles"])

    # ── 阶段1：重置到 NORMAL ──
    reset_start = time.time()
    while not rospy.is_shutdown():
        pub.publish(safe_arr)
        if g_state == 0:
            break
        if g_state == 3:       # EMERGENCY_STOP → 调用 resume
            try_resume()
        if time.time() - reset_start > 6.0:
            rospy.logwarn(f"[test] 重置超时 state={g_state}")
            break
        rate.sleep()
    rospy.sleep(0.3)

    # ── 阶段2：注入危险障碍物，计时 ──
    t_inject  = rospy.Time.now().to_sec()
    t_wall    = time.time()
    t_resp    = None
    target    = cfg["target_state"]

    while not rospy.is_shutdown():
        pub.publish(danger_arr)
        if g_state is not None and g_state >= target:
            t_resp = rospy.Time.now().to_sec()
            break
        if time.time() - t_wall > timeout:
            break
        rate.sleep()

    # ── 构造结果行 ──
    rt_ms = None
    if t_resp is not None:
        rt_ms = round((t_resp - t_inject) * 1000.0, 1)
        if rt_ms < 0:
            rt_ms = round((time.time() - t_wall) * 1000.0, 1)

    success = t_resp is not None
    if scene_name == "test_static":
        success = (g_state is not None and g_state >= 1)

    return {
        "run_id":                    run_id,
        "timestamp":                 datetime.now().strftime("%Y%m%d_%H%M%S"),
        "scenario":                  scene_name,
        "event_type":                STATE_NAMES.get(g_state, "NO_TRIGGER"),
        "response_time_ms":          rt_ms if rt_ms is not None else "",
        "perception_latency_ms_p95": "",
        "risk_level":                RISK_LV_NAMES.get(g_risk_lv, "UNKNOWN"),
        "obstacle_type":             cfg["obstacles"][0]["type"],
        "min_distance_m":            round(g_min_dist, 3) if g_min_dist is not None else cfg["obstacles"][0]["distance"],
        "success":                   success,
    }


def main():
    rospy.init_node("phase6_test_node", anonymous=False)

    n_runs = int(rospy.get_param("~runs",     10))
    scenes = rospy.get_param("~scenarios",   "all")
    if scenes == "all":
        scenes = list(SCENARIOS.keys())
    else:
        scenes = [s.strip() for s in scenes.split(",")]

    pub = rospy.Publisher("/excavator/predicted_obstacles",
                          ObstacleArray, queue_size=10)
    rospy.Subscriber("/excavator/system_state", SystemState, state_cb)
    rospy.Subscriber("/excavator/risk_state",   RiskState,   risk_cb)

    rospy.loginfo("[test] 等待订阅建立...")
    rospy.sleep(2.0)

    # 验证节点连接：先等 system_state 到来
    wait_start = time.time()
    while g_state is None and not rospy.is_shutdown():
        if time.time() - wait_start > 8.0:
            rospy.logerr("[test] 超时：未收到 /excavator/system_state，请确认 fsm_controller 已启动")
            sys.exit(1)
        rospy.sleep(0.2)
    rospy.loginfo(f"[test] 初始状态: {STATE_NAMES.get(g_state, '?')}")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    total_ok = 0
    total_all = 0

    for scene in scenes:
        rospy.loginfo(f"\n[test] === {scene}: {SCENARIOS[scene]['description']} ===")
        csv_path   = os.path.join(RESULTS_DIR, f"metrics_{scene}.csv")
        write_hdr  = not os.path.exists(csv_path)
        rows       = []

        for run_id in range(1, n_runs + 1):
            rospy.loginfo(f"[test]  run {run_id:02d}/{n_runs}...")
            row  = run_single(pub, scene, run_id, n_runs)
            rows.append(row)
            ok_c = "✓" if row["success"] else "✗"
            rt_s = f"{row['response_time_ms']}ms" if row["response_time_ms"] else "N/A"
            rospy.loginfo(f"[test]   {ok_c} event={row['event_type']}  rt={rt_s}")
            rospy.sleep(0.3)

        # CSV 追加写入
        with open(csv_path, "a", newline="") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            if write_hdr:
                w.writeheader()
            w.writerows(rows)

        ok  = sum(1 for r in rows if r["success"])
        rts = [float(r["response_time_ms"]) for r in rows if r["response_time_ms"]]
        rospy.loginfo(f"[test]  成功率: {ok}/{n_runs} = {ok/n_runs*100:.0f}%")
        if rts:
            rospy.loginfo(f"[test]  响应时间: 均值={sum(rts)/len(rts):.1f}ms  "
                          f"max={max(rts):.1f}ms  min={min(rts):.1f}ms")
        total_ok  += ok
        total_all += n_runs

    rospy.loginfo(f"\n[test] ===== 全部完成 =====")
    rospy.loginfo(f"[test] 总计: {total_all} 次, 成功: {total_ok} 次 "
                  f"({total_ok/total_all*100:.1f}%)")
    rospy.loginfo(f"[test] 结果目录: {RESULTS_DIR}")


if __name__ == "__main__":
    main()
