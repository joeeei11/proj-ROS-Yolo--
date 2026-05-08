#!/usr/bin/env python3
"""
data_logger.py — 自动化指标记录节点

在线模式（ROS节点）：
    rosrun excavator_monitor data_logger.py \
        _scenario:=test_static _run_id:=1 \
        _output:=/home/excavator/excavator_ws/results/metrics_test_static.csv

离线模式（rosbag分析）：
    python3 data_logger.py --bag path.bag --scenario test_static --run-id 1 \
        --output results/metrics_test_static.csv

汇总统计：
    python3 data_logger.py --summarize results/
"""

import argparse
import csv
import os
import sys
import time
from collections import deque
from datetime import datetime

# ─────────────────────────────── 常量 ──────────────────────────────── #

CRITICAL_DISTANCE = 1.0   # m，触发响应时间计时的距离阈值
CRITICAL_TTC      = 1.5   # s，触发响应时间计时的 TTC 阈值
SAFE_DISTANCE     = 5.0   # m，误报率判定的安全距离阈值

CSV_FIELDS = [
    "run_id", "timestamp", "scenario", "event_type",
    "response_time_ms", "perception_latency_ms_p95",
    "risk_level", "obstacle_type", "min_distance_m", "success",
]

RISK_LEVEL_NAMES = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
STATE_NAMES      = {0: "NORMAL", 1: "CAUTION", 2: "PAUSED", 3: "EMERGENCY_STOP"}


# ─────────────────────────────── 指标分析器 ──────────────────────────── #

class MetricsAnalyzer:
    """从消息序列中计算性能指标，与 ROS 或 rosbag 均可配合使用。"""

    def __init__(self):
        self.reset()

    def reset(self):
        self._trigger_time   = None   # 危险区进入时刻（ROS时间，秒）
        self._emerg_time     = None   # EMERGENCY_STOP 切换时刻（秒）
        self._prev_state     = None   # 上一帧 FSM 状态

        self._image_stamps   = deque(maxlen=200)   # 图像时间戳队列
        self._detect_stamps  = deque(maxlen=200)   # 检测输出时间戳队列
        self._latencies_ms   = []                  # 感知延迟样本（ms）

        self._total_frames   = 0   # 判定帧总数
        self._fp_frames      = 0   # 误报帧数

        self._last_risk      = None   # 最近一条 RiskState
        self._last_obstacles = None   # 最近一条 ObstacleArray
        self._scenario       = "unknown"

    def set_scenario(self, scenario: str):
        self._scenario = scenario

    # ── 消息回调（在线 / 离线均调用） ── #

    def on_image(self, stamp_sec: float):
        """每收到一帧图像时调用，stamp_sec 为 header.stamp 换算后的秒数。"""
        self._image_stamps.append(stamp_sec)

    def on_detected_obstacles(self, stamp_sec: float, obstacles):
        """每收到 /excavator/detected_obstacles 时调用。"""
        self._detect_stamps.append(stamp_sec)
        # 找最近的图像时间戳，计算延迟
        if self._image_stamps:
            closest = min(self._image_stamps, key=lambda t: abs(t - stamp_sec))
            latency_ms = (stamp_sec - closest) * 1000.0
            if 0 <= latency_ms < 2000:   # 过滤异常值
                self._latencies_ms.append(latency_ms)
        self._last_obstacles = obstacles

    def on_risk_state(self, stamp_sec: float, risk_state):
        """每收到 /excavator/risk_state 时调用。"""
        self._last_risk = risk_state
        in_danger = (risk_state.min_distance < CRITICAL_DISTANCE or
                     (0 < risk_state.min_ttc < CRITICAL_TTC))
        if in_danger and self._trigger_time is None and self._emerg_time is None:
            self._trigger_time = stamp_sec

    def on_system_state(self, stamp_sec: float, system_state):
        """每收到 /excavator/system_state 时调用。"""
        state = system_state.state
        STATE_EMERG = 3   # SystemState.EMERGENCY_STOP

        if (self._prev_state is not None and
                self._prev_state != STATE_EMERG and
                state == STATE_EMERG and
                self._trigger_time is not None and
                self._emerg_time is None):
            self._emerg_time = stamp_sec

        # 误报帧统计：所有障碍物在安全距离外但状态非 NORMAL
        self._total_frames += 1
        all_safe = True
        if self._last_obstacles is not None:
            for obs in self._last_obstacles.obstacles:
                if obs.distance < SAFE_DISTANCE:
                    all_safe = False
                    break
        if all_safe and state != 0:   # 0 = NORMAL
            self._fp_frames += 1

        self._prev_state = state

    # ── 汇总计算 ── #

    def compute_response_time_ms(self):
        if self._trigger_time is None or self._emerg_time is None:
            return None
        dt = (self._emerg_time - self._trigger_time) * 1000.0
        return round(dt, 1) if dt >= 0 else None

    def compute_perception_latency_p95_ms(self):
        if len(self._latencies_ms) < 5:
            return None
        sorted_lat = sorted(self._latencies_ms)
        idx = int(len(sorted_lat) * 0.95)
        return round(sorted_lat[min(idx, len(sorted_lat) - 1)], 1)

    def compute_false_positive_rate(self):
        if self._total_frames == 0:
            return 0.0
        return round(self._fp_frames / self._total_frames * 100.0, 2)

    def is_success(self) -> bool:
        """根据场景判断本次测试是否成功。"""
        if "static" in self._scenario:
            # 静态场景：触发 CAUTION 或 EMERGENCY_STOP 均算感知到，只要未发生碰撞
            return self._prev_state is not None
        # 其余场景：必须触发 EMERGENCY_STOP
        return self._emerg_time is not None

    def primary_obstacle_type(self) -> str:
        if self._last_obstacles is None or not self._last_obstacles.obstacles:
            return "unknown"
        obs_sorted = sorted(self._last_obstacles.obstacles, key=lambda o: o.distance)
        return obs_sorted[0].obstacle_type if obs_sorted else "unknown"

    def min_distance(self) -> float:
        if self._last_risk is None:
            return float("nan")
        return round(self._last_risk.min_distance, 3)

    def risk_level_str(self) -> str:
        if self._last_risk is None:
            return "UNKNOWN"
        return RISK_LEVEL_NAMES.get(self._last_risk.current_level, "UNKNOWN")


# ─────────────────────────────── 离线 rosbag 分析 ──────────────────────── #

def analyze_bag(bag_path: str, scenario: str, run_id: int, output_csv: str):
    """从 rosbag 文件中提取指标并追加到 CSV。"""
    try:
        import rosbag
    except ImportError:
        print("[ERROR] rosbag 模块不可用，请在 ROS 环境中运行（source devel/setup.bash）")
        sys.exit(1)

    from excavator_msgs.msg import SystemState, RiskState, ObstacleArray
    from sensor_msgs.msg import Image

    analyzer = MetricsAnalyzer()
    analyzer.set_scenario(scenario)

    print(f"[data_logger] 分析 bag: {bag_path}")
    with rosbag.Bag(bag_path, "r") as bag:
        for topic, msg, t in bag.read_messages():
            stamp = t.to_sec()

            if topic == "/camera/image_raw":
                analyzer.on_image(msg.header.stamp.to_sec())

            elif topic == "/excavator/detected_obstacles":
                analyzer.on_detected_obstacles(msg.header.stamp.to_sec(), msg)

            elif topic == "/excavator/risk_state":
                analyzer.on_risk_state(stamp, msg)

            elif topic == "/excavator/system_state":
                analyzer.on_system_state(stamp, msg)

    row = _build_csv_row(analyzer, run_id, scenario)
    _append_csv_row(output_csv, row)
    print(f"[data_logger] 写入 CSV: {output_csv} (run_id={run_id})")
    _print_row_summary(row)


def _build_csv_row(analyzer: MetricsAnalyzer, run_id: int, scenario: str) -> dict:
    rt = analyzer.compute_response_time_ms()
    return {
        "run_id":                      run_id,
        "timestamp":                   datetime.now().strftime("%Y%m%d_%H%M%S"),
        "scenario":                    scenario,
        "event_type":                  "EMERGENCY_STOP" if analyzer._emerg_time else "NO_TRIGGER",
        "response_time_ms":            rt if rt is not None else "",
        "perception_latency_ms_p95":   analyzer.compute_perception_latency_p95_ms() or "",
        "risk_level":                  analyzer.risk_level_str(),
        "obstacle_type":               analyzer.primary_obstacle_type(),
        "min_distance_m":              analyzer.min_distance(),
        "success":                     analyzer.is_success(),
    }


def _append_csv_row(csv_path: str, row: dict):
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    write_header = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)


def _print_row_summary(row: dict):
    print(f"  response_time_ms      = {row['response_time_ms']}")
    print(f"  perception_latency_p95= {row['perception_latency_ms_p95']}")
    print(f"  risk_level            = {row['risk_level']}")
    print(f"  min_distance_m        = {row['min_distance_m']}")
    print(f"  success               = {row['success']}")


# ─────────────────────────────── 汇总统计 ──────────────────────────────── #

def summarize_results(results_dir: str):
    """读取 results_dir 下所有 metrics_*.csv，生成汇总统计表。"""
    import glob

    csv_files = sorted(glob.glob(os.path.join(results_dir, "metrics_*.csv")))
    if not csv_files:
        print(f"[ERROR] 未找到 CSV 文件：{results_dir}/metrics_*.csv")
        sys.exit(1)

    all_rows = []
    for csv_path in csv_files:
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_rows.append(row)

    if not all_rows:
        print("[ERROR] CSV 文件为空")
        sys.exit(1)

    # 响应时间统计
    rt_values = []
    for r in all_rows:
        try:
            rt_values.append(float(r["response_time_ms"]))
        except (ValueError, KeyError):
            pass

    # 成功率统计
    success_count = sum(1 for r in all_rows if r.get("success", "").lower() in ("true", "1"))
    total_count = len(all_rows)

    # 感知延迟 p95
    lat_values = []
    for r in all_rows:
        try:
            lat_values.append(float(r["perception_latency_ms_p95"]))
        except (ValueError, KeyError):
            pass

    print("\n" + "=" * 50)
    print("Phase 6 系统测试汇总统计")
    print("=" * 50)
    print(f"测试总数: {total_count}")
    print()

    if rt_values:
        sorted_rt = sorted(rt_values)
        p95_idx = int(len(sorted_rt) * 0.95)
        print(f"响应时间（ms）:")
        print(f"  均值  = {sum(rt_values)/len(rt_values):.1f}  (合格: ≤ 1500)")
        print(f"  最大值= {max(rt_values):.1f}  (合格: ≤ 2000)")
        print(f"  最小值= {min(rt_values):.1f}")
        print(f"  p95   = {sorted_rt[min(p95_idx, len(sorted_rt)-1)]:.1f}")
    else:
        print("响应时间: 无数据")

    print()
    print(f"成功率: {success_count}/{total_count} = {success_count/total_count*100:.1f}%  (合格: ≥ 90%)")

    print()
    if lat_values:
        print(f"感知延迟 p95 均值: {sum(lat_values)/len(lat_values):.1f} ms  (合格: ≤ 150)")
    else:
        print("感知延迟: 无数据")

    # 按场景分组
    scenarios = {}
    for r in all_rows:
        s = r.get("scenario", "unknown")
        scenarios.setdefault(s, []).append(r)

    print()
    print("各场景成功率:")
    for s, rows in sorted(scenarios.items()):
        ok = sum(1 for r in rows if r.get("success", "").lower() in ("true", "1"))
        print(f"  {s}: {ok}/{len(rows)} = {ok/len(rows)*100:.0f}%")

    print("=" * 50)

    # 保存汇总 CSV
    summary_path = os.path.join(results_dir, "summary.csv")
    if rt_values:
        with open(summary_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value", "threshold", "pass"])
            writer.writerow(["response_time_mean_ms",
                              f"{sum(rt_values)/len(rt_values):.1f}", "1500", str(sum(rt_values)/len(rt_values) <= 1500)])
            writer.writerow(["response_time_max_ms",
                              f"{max(rt_values):.1f}", "2000", str(max(rt_values) <= 2000)])
            writer.writerow(["success_rate_pct",
                              f"{success_count/total_count*100:.1f}", "90", str(success_count/total_count >= 0.9)])
            if lat_values:
                writer.writerow(["perception_latency_p95_ms",
                                  f"{sum(lat_values)/len(lat_values):.1f}", "150",
                                  str(sum(lat_values)/len(lat_values) <= 150)])
        print(f"\n汇总已保存: {summary_path}")


# ─────────────────────────────── 在线 ROS 节点 ─────────────────────────── #

def run_as_node():
    """作为 ROS 节点在线运行，实时订阅话题并记录指标。"""
    import rospy
    from excavator_msgs.msg import SystemState, RiskState, ObstacleArray
    from sensor_msgs.msg import Image

    rospy.init_node("data_logger")

    scenario  = rospy.get_param("~scenario",  "unknown")
    run_id    = rospy.get_param("~run_id",    1)
    output    = rospy.get_param("~output",    "results/metrics.csv")
    duration  = rospy.get_param("~duration",  90.0)   # 记录持续秒数

    analyzer = MetricsAnalyzer()
    analyzer.set_scenario(scenario)

    rospy.Subscriber("/camera/image_raw", Image,
                     lambda msg: analyzer.on_image(msg.header.stamp.to_sec()))

    rospy.Subscriber("/excavator/detected_obstacles", ObstacleArray,
                     lambda msg: analyzer.on_detected_obstacles(
                         msg.header.stamp.to_sec(), msg))

    rospy.Subscriber("/excavator/risk_state", RiskState,
                     lambda msg: analyzer.on_risk_state(
                         msg.header.stamp.to_sec(), msg))

    rospy.Subscriber("/excavator/system_state", SystemState,
                     lambda msg: analyzer.on_system_state(
                         msg.header.stamp.to_sec(), msg))

    rospy.loginfo(f"[data_logger] 开始记录：场景={scenario}, run_id={run_id}, 持续={duration}s")

    start = rospy.get_time()
    rate = rospy.Rate(10)
    while not rospy.is_shutdown():
        if rospy.get_time() - start >= duration:
            break
        rate.sleep()

    row = _build_csv_row(analyzer, run_id, scenario)
    _append_csv_row(output, row)
    rospy.loginfo(f"[data_logger] 记录完成，写入 {output}")
    _print_row_summary(row)


# ─────────────────────────────── 入口点 ──────────────────────────────── #

def main():
    parser = argparse.ArgumentParser(description="data_logger: 指标记录与分析")
    parser.add_argument("--bag",       help="rosbag 文件路径（离线模式）")
    parser.add_argument("--scenario",  default="unknown", help="场景名")
    parser.add_argument("--run-id",    type=int, default=1, help="测试编号")
    parser.add_argument("--output",    default="results/metrics.csv", help="CSV 输出路径")
    parser.add_argument("--summarize", metavar="RESULTS_DIR",
                        help="汇总 results/ 目录下所有 CSV（不需要 ROS 环境）")

    # 如果无参数且有 ROS 环境，尝试在线模式
    if len(sys.argv) == 1:
        try:
            import rospy  # noqa: F401
            run_as_node()
            return
        except ImportError:
            parser.print_help()
            sys.exit(1)

    args = parser.parse_args()

    if args.summarize:
        summarize_results(args.summarize)
    elif args.bag:
        analyze_bag(args.bag, args.scenario, args.run_id, args.output)
    else:
        run_as_node()


if __name__ == "__main__":
    main()
