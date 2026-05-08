#!/usr/bin/env python3
"""
monitor_server.py - 挖掘机避障系统 Web 监控服务器
Flask REST API + Server-Sent Events 实时推送
端口: 8080  访问: http://localhost:8080
"""

import json
import os
import sys
import threading
import time
from datetime import datetime

from flask import Flask, Response, jsonify, send_from_directory

WEB_DIR = os.path.join(os.path.dirname(__file__), "..", "web")
app = Flask(__name__, static_folder=WEB_DIR)

# ─── 线程安全状态容器 ─── #
_lock = threading.Lock()
_state = {
    "system_state": {
        "state": 0,
        "state_name": "NORMAL",
        "reason": "initializing",
        "state_duration": 0.0,
        "timestamp": "",
    },
    "risk": {
        "current_level": 0,
        "level_name": "LOW",
        "min_distance": 99.0,
        "min_ttc": 99.0,
        "primary_threat_id": "",
    },
    "obstacles": [],
    "metrics": {
        "perception_fps": 0.0,
        "risk_latency_ms": 0.0,
        "fsm_latency_ms": 0.0,
        "total_obstacles": 0,
        "uptime_sec": 0,
    },
}
_start_time = time.time()
_msg_counts = {"perception": 0, "risk": 0, "fsm": 0}
_last_perception_time = [time.time()]

STATE_NAMES = {0: "NORMAL", 1: "CAUTION", 2: "PAUSED", 3: "EMERGENCY_STOP"}
LEVEL_NAMES = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}

# ─── ROS 集成（可选，无 ROS 时退化为静态 demo 数据）─── #
_ros_active = False


def _start_ros():
    global _ros_active
    try:
        import rospy
        from excavator_msgs.msg import ObstacleArray, RiskState, SystemState

        rospy.init_node("monitor_server", anonymous=True, disable_signals=True)

        def on_state(msg):
            with _lock:
                _state["system_state"].update(
                    {
                        "state": int(msg.state),
                        "state_name": STATE_NAMES.get(msg.state, "UNKNOWN"),
                        "reason": msg.reason,
                        "state_duration": round(float(msg.state_duration), 2),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                _msg_counts["fsm"] += 1

        def on_risk(msg):
            with _lock:
                _state["risk"].update(
                    {
                        "current_level": int(msg.current_level),
                        "level_name": LEVEL_NAMES.get(msg.current_level, "UNKNOWN"),
                        "min_distance": round(float(msg.min_distance), 3),
                        "min_ttc": round(float(msg.min_ttc), 3),
                        "primary_threat_id": msg.primary_threat_id,
                    }
                )
                _msg_counts["risk"] += 1

        def on_obstacles(msg):
            now = time.time()
            dt = now - _last_perception_time[0]
            _last_perception_time[0] = now
            fps = round(1.0 / dt, 1) if dt > 0 else 0.0
            obs_list = []
            for o in msg.obstacles:
                obs_list.append(
                    {
                        "id": o.obstacle_id,
                        "type": o.obstacle_type,
                        "distance": round(float(o.distance), 2),
                        "ttc": round(float(o.ttc), 2),
                        "risk_score": round(float(o.risk_score), 3),
                        "risk_level": LEVEL_NAMES.get(int(o.risk_level), "LOW"),
                    }
                )
            obs_list.sort(key=lambda x: x["distance"])
            with _lock:
                _state["obstacles"] = obs_list
                _state["metrics"]["perception_fps"] = fps
                _state["metrics"]["total_obstacles"] = len(obs_list)
                _msg_counts["perception"] += 1

        rospy.Subscriber("/excavator/system_state", SystemState, on_state)
        rospy.Subscriber("/excavator/risk_state", RiskState, on_risk)
        rospy.Subscriber("/excavator/assessed_obstacles", ObstacleArray, on_obstacles)
        _ros_active = True
        rospy.loginfo("[monitor_server] ROS 订阅已建立")
        rospy.spin()
    except Exception as e:
        print(f"[monitor_server] ROS 不可用 ({e})，使用 demo 模式", flush=True)
        _demo_mode()


def _demo_mode():
    """ROS 不可用时生成演示数据。"""
    import math, random

    t = 0
    while True:
        t += 0.1
        dist = 3.0 + 2.0 * math.sin(t * 0.5)
        state = 1 if dist < 3.5 else 0
        with _lock:
            _state["system_state"].update(
                {
                    "state": state,
                    "state_name": STATE_NAMES[state],
                    "reason": "demo",
                    "state_duration": round(t % 30, 1),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            _state["risk"].update(
                {
                    "current_level": 1 if state else 0,
                    "level_name": "MEDIUM" if state else "LOW",
                    "min_distance": round(dist, 2),
                    "min_ttc": round(dist / 0.5, 1),
                    "primary_threat_id": "demo_obs_1",
                }
            )
            _state["obstacles"] = [
                {
                    "id": "demo_obs_1",
                    "type": "person",
                    "distance": round(dist, 2),
                    "ttc": round(dist / 0.5, 1),
                    "risk_score": round(max(0, (5 - dist) / 4), 3),
                    "risk_level": "MEDIUM" if dist < 3.5 else "LOW",
                }
            ]
            _state["metrics"].update(
                {
                    "perception_fps": round(28.0 + random.uniform(-2, 2), 1),
                    "risk_latency_ms": round(15.0 + random.uniform(-5, 5), 1),
                    "fsm_latency_ms": round(105.0 + random.uniform(-20, 20), 1),
                    "total_obstacles": 1,
                    "uptime_sec": int(time.time() - _start_time),
                }
            )
        time.sleep(0.1)


def _update_metrics():
    """后台线程：每秒更新性能指标。"""
    while True:
        with _lock:
            _state["metrics"]["uptime_sec"] = int(time.time() - _start_time)
        time.sleep(1.0)


# ─── REST API ─── #


@app.route("/api/health")
def api_health():
    return jsonify({"status": "ok", "uptime_sec": int(time.time() - _start_time)})


@app.route("/api/system/state")
def api_system_state():
    with _lock:
        return jsonify(_state["system_state"])


@app.route("/api/obstacles")
def api_obstacles():
    with _lock:
        return jsonify({"obstacles": _state["obstacles"], "count": len(_state["obstacles"])})


@app.route("/api/risk")
def api_risk():
    with _lock:
        return jsonify(_state["risk"])


@app.route("/api/metrics")
def api_metrics():
    with _lock:
        return jsonify(_state["metrics"])


# ─── Server-Sent Events（实时推送）─── #


@app.route("/api/stream")
def api_stream():
    def generate():
        while True:
            with _lock:
                payload = json.dumps(
                    {
                        "system_state": _state["system_state"],
                        "risk": _state["risk"],
                        "obstacles": _state["obstacles"],
                        "metrics": _state["metrics"],
                    }
                )
            yield f"data: {payload}\n\n"
            time.sleep(1.0)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ─── 静态文件 ─── #


@app.route("/")
def index():
    return send_from_directory(WEB_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(WEB_DIR, filename)


# ─── 入口 ─── #


if __name__ == "__main__":
    threading.Thread(target=_start_ros, daemon=True).start()
    threading.Thread(target=_update_metrics, daemon=True).start()
    time.sleep(1.0)
    port = int(os.environ.get("MONITOR_PORT", 8080))
    print(f"[monitor_server] 启动于 http://localhost:{port}", flush=True)
    app.run(host="0.0.0.0", port=port, threaded=True, debug=False)