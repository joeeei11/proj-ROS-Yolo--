#!/usr/bin/env python3
"""
run_phase6_tests.py
Phase 6 性能基准测试执行器（消息注入法）

用法（已 source devel/setup.bash）：
    python3 run_phase6_tests.py [--auto-start] [--scenario test_static] [--runs 10]

--auto-start : 自动启动 roscore + risk_assessor + fsm_controller 子进程
默认发布频率: 20Hz，每次测试超时: 5s
"""

import argparse
import csv
import os
import subprocess
import sys
import time
from datetime import datetime

import rospy
from excavator_msgs.msg import ObstacleArray, ObstacleInfo, SystemState, RiskState
from geometry_msgs.msg import PoseStamped, Vector3
from std_msgs.msg import Header
from std_srvs.srv import Trigger

# ──────────────────────────── 场景定义 ────────────────────────────── #
# type_weights 映射：risk_assessor 默认: person=1.5, vehicle=1.2, obstacle=1.0
# 根据 Phase 3 决策的评分公式验证场景触发的风险等级

SCENARIOS = {
    "test_static": {
        "description": "静态障碍物（预期 CAUTION）",
        "obstacles": [
            {"id": "static_1", "type": "obstacle", "distance": 3.0, "ttc": 3.0, "vel": 0.0},
        ],
        "target_state": 1,   # CAUTION
        "expect_emerg": False,
    },
    "test_pedestrian": {
        "description": "行人接近（预期 EMERGENCY_STOP）",
        "obstacles": [
            {"id": "ped_1",    "type": "person",   "distance": 2.5, "ttc": 1.0, "vel": 0.5},
        ],
        "target_state": 3,   # EMERGENCY_STOP
        "expect_emerg": True,
    },
    "test_vehicle": {
        "description": "高速车辆（预期 EMERGENCY_STOP）",
        "obstacles": [
            {"id": "veh_1",    "type": "vehicle",  "distance": 1.5, "ttc": 0.9, "vel": 2.0},
        ],
        "target_state": 3,
        "expect_emerg": True,
    },
    "test_multi_threat": {
        "description": "多威胁（预期 EMERGENCY_STOP）",
        "obstacles": [
            {"id": "ped_1",    "type": "person",   "distance": 2.0, "ttc": 1.2, "vel": 0.5},
            {"id": "veh_1",    "type": "vehicle",  "distance": 3.0, "ttc": 2.0, "vel": 1.5},
            {"id": "static_1", "type": "obstacle", "distance": 6.0, "ttc": 6.0, "vel": 0.0},
        ],
        "target_state": 3,
        "expect_emerg": True,
    },
}

SAFE_OBSTACLES = [
    {"id": "far_1", "type": "obstacle", "distance": 10.0, "ttc": 999.0, "vel": 0.0}
]

CSV_FIELDS = [
    "run_id", "timestamp", "scenario", "event_type",
    "response_time_ms", "perception_latency_ms_p95",
    "risk_level", "obstacle_type", "min_distance_m", "success",
]

WS = os.path.expanduser("~/excavator_ws")
RESULTS_DIR = os.path.join(WS, "results")


# ──────────────────────────── 消息构建 ────────────────────────────── #

def make_obstacle_array(obstacles_cfg):
    now = rospy.Time.now()
    arr = ObstacleArray()
    arr.header.stamp = now
    arr.header.frame_id = "base_link"
    for cfg in obstacles_cfg:
        obs = ObstacleInfo()
        obs.header.stamp = now
        obs.header.frame_id = "base_link"
        obs.obstacle_id   = cfg["id"]
        obs.obstacle_type = cfg["type"]
        obs.distance      = float(cfg["distance"])
        obs.ttc           = float(cfg["ttc"])
        obs.relative_velocity = float(cfg["vel"])
        obs.risk_score    = 0.0
        obs.risk_level    = 0
        ps = PoseStamped()
        ps.header = obs.header
        ps.pose.position.x = float(cfg["distance"])
        obs.pose = ps
        obs.velocity_vec = Vector3(x=float(cfg["vel"]))
        arr.obstacles.append(obs)
    return arr


# ──────────────────────────── 测试执行器 ────────────────────────────── #

class Phase6TestRunner:

    def __init__(self, pub_rate=20.0, timeout_sec=5.0, reset_sec=1.5):
        self.pub_rate    = pub_rate
        self.timeout_sec = timeout_sec
        self.reset_sec   = reset_sec
        self._procs      = []

        # ROS 状态
        self._current_state   = None
        self._current_risk_lv = None
        self._current_min_dist = None
        self._state_change_time = None

    # ── 子进程管理 ── #

    def start_infrastructure(self):
        print("[runner] 启动 roscore...")
        p = subprocess.Popen(["roscore"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._procs.append(p)
        time.sleep(2.5)

        src = "source {}/devel/setup.bash".format(WS)

        print("[runner] 启动 risk_assessor...")
        p2 = subprocess.Popen(
            ["bash", "-c",
             "{} && rosrun excavator_risk risk_assessor.py".format(src)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._procs.append(p2)
        time.sleep(1.5)

        print("[runner] 启动 fsm_controller...")
        p3 = subprocess.Popen(
            ["bash", "-c",
             "{} && rosrun excavator_decision fsm_controller.py".format(src)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._procs.append(p3)
        time.sleep(2.0)
        print("[runner] 基础设施启动完毕")

    def stop_infrastructure(self):
        for p in reversed(self._procs):
            try:
                p.terminate()
                p.wait(timeout=3)
            except Exception:
                try:
                    p.kill()
                except Exception:
                    pass
        self._procs.clear()

    # ── ROS 回调 ── #

    def _state_cb(self, msg):
        self._current_state = msg.state
        self._state_change_time = rospy.Time.now().to_sec()

    def _risk_cb(self, msg):
        self._current_risk_lv  = msg.current_level
        self._current_min_dist = msg.min_distance

    # ── 单次测试 ── #

    def run_single(self, scenario_name, run_id, pub):
        cfg = SCENARIOS[scenario_name]

        # 重置：先确保到 NORMAL 状态（先发安全消息）
        t_reset_start = time.time()
        safe_arr = make_obstacle_array(SAFE_OBSTACLES)
        rate = rospy.Rate(self.pub_rate)
        while not rospy.is_shutdown():
            pub.publish(safe_arr)
            if self._current_state == 0:   # NORMAL
                break
            if time.time() - t_reset_start > 3.0:
                # 如果 EMERGENCY_STOP 状态，尝试 resume 服务
                try:
                    resume = rospy.ServiceProxy("/excavator/resume", Trigger)
                    resume()
                except Exception:
                    pass
            if time.time() - t_reset_start > 5.0:
                break
            rate.sleep()
        time.sleep(0.3)  # 等待稳定

        # 注入危险障碍物，记录注入时刻
        danger_arr = make_obstacle_array(cfg["obstacles"])
        t_inject = rospy.Time.now().to_sec()
        t_inject_wall = time.time()
        target_state  = cfg["target_state"]
        t_response    = None

        # 连续发布危险障碍物，直到达到目标状态或超时
        while not rospy.is_shutdown():
            pub.publish(danger_arr)
            if self._current_state is not None and self._current_state >= target_state:
                t_response = rospy.Time.now().to_sec()
                break
            if time.time() - t_inject_wall > self.timeout_sec:
                break
            rate.sleep()

        # 组装结果
        rt_ms = None
        if t_response is not None:
            rt_ms = round((t_response - t_inject) * 1000.0, 1)
            if rt_ms < 0:
                rt_ms = round((time.time() - t_inject_wall) * 1000.0, 1)

        success = (t_response is not None)
        if scenario_name == "test_static":
            success = (self._current_state is not None and self._current_state >= 1)

        risk_names = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
        primary_type = cfg["obstacles"][0]["type"]
        primary_dist = cfg["obstacles"][0]["distance"]

        row = {
            "run_id":                    run_id,
            "timestamp":                 datetime.now().strftime("%Y%m%d_%H%M%S"),
            "scenario":                  scenario_name,
            "event_type":                ("EMERGENCY_STOP" if self._current_state == 3
                                          else ("CAUTION" if self._current_state == 1
                                                else "NO_TRIGGER")),
            "response_time_ms":          rt_ms if rt_ms is not None else "",
            "perception_latency_ms_p95": "",   # 感知管线未在测试中运行
            "risk_level":                risk_names.get(self._current_risk_lv, "UNKNOWN"),
            "obstacle_type":             primary_type,
            "min_distance_m":            (round(self._current_min_dist, 3)
                                          if self._current_min_dist is not None
                                          else primary_dist),
            "success":                   success,
        }
        return row

    # ── 主入口 ── #

    def run_all(self, scenarios, n_runs=10):
        rospy.init_node("phase6_test_runner", anonymous=True)

        pub = rospy.Publisher("/excavator/predicted_obstacles",
                              ObstacleArray, queue_size=10)
        rospy.Subscriber("/excavator/system_state",  SystemState, self._state_cb)
        rospy.Subscriber("/excavator/risk_state",    RiskState,   self._risk_cb)

        rospy.sleep(1.0)   # 等待订阅就绪

        all_results = {}
        for scene in scenarios:
            rows = []
            cfg = SCENARIOS[scene]
            print(f"\n[runner] === 场景: {scene} ({cfg['description']}) ===")
            csv_path = os.path.join(RESULTS_DIR, f"metrics_{scene}.csv")
            os.makedirs(RESULTS_DIR, exist_ok=True)

            for run_id in range(1, n_runs + 1):
                print(f"[runner]  run {run_id:02d}/{n_runs} ...", end=" ", flush=True)
                row = self.run_single(scene, run_id, pub)
                rows.append(row)
                status = "✓" if row["success"] else "✗"
                rt_str = f"{row['response_time_ms']}ms" if row["response_time_ms"] else "N/A"
                print(f"{status} state={row['event_type']}  rt={rt_str}")
                time.sleep(0.5)   # 两次测试之间短暂间隔

            # 写 CSV
            write_hdr = not os.path.exists(csv_path)
            with open(csv_path, "a", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
                if write_hdr:
                    writer.writeheader()
                writer.writerows(rows)
            print(f"[runner]  写入 {csv_path} ({len(rows)} 行)")

            # 场景小结
            ok = sum(1 for r in rows if r["success"])
            rts = [float(r["response_time_ms"]) for r in rows if r["response_time_ms"]]
            print(f"[runner]  成功率: {ok}/{n_runs} = {ok/n_runs*100:.0f}%")
            if rts:
                print(f"[runner]  响应时间: 均值={sum(rts)/len(rts):.1f}ms  "
                      f"最大={max(rts):.1f}ms  最小={min(rts):.1f}ms")
            all_results[scene] = rows

        return all_results


# ──────────────────────────── 入口点 ────────────────────────────── #

def main():
    parser = argparse.ArgumentParser(description="Phase 6 测试执行器")
    parser.add_argument("--auto-start", action="store_true",
                        help="自动启动 roscore + risk_assessor + fsm_controller")
    parser.add_argument("--scenario",   default="all",
                        help="要运行的场景名，或 'all'（默认）")
    parser.add_argument("--runs",       type=int, default=10,
                        help="每个场景的重复次数（默认10）")
    args = parser.parse_args()

    runner = Phase6TestRunner(pub_rate=20.0, timeout_sec=5.0, reset_sec=1.5)

    if args.auto_start:
        runner.start_infrastructure()

    if args.scenario == "all":
        scenes = list(SCENARIOS.keys())
    else:
        scenes = [args.scenario]

    try:
        results = runner.run_all(scenes, n_runs=args.runs)

        # 最终汇总
        total = sum(len(v) for v in results.values())
        ok    = sum(sum(1 for r in v if r["success"]) for v in results.values())
        print(f"\n[runner] ====== 全部测试完成 ======")
        print(f"[runner] 总计: {total} 次, 成功: {ok} 次 ({ok/total*100:.1f}%)")
        print(f"[runner] 结果已保存到 {RESULTS_DIR}/")
        print(f"[runner] 汇总统计: python3 data_logger.py --summarize {RESULTS_DIR}/")

    except rospy.ROSInterruptException:
        pass
    finally:
        if args.auto_start:
            runner.stop_infrastructure()


if __name__ == "__main__":
    main()
