#!/usr/bin/env python3
import math, sys, types
import pytest

# ── stub rospy ────────────────────────────────────────────────────────────────
rospy_stub = types.ModuleType("rospy")
rospy_stub.get_param      = lambda key, default=None: default
rospy_stub.Subscriber     = lambda *a, **kw: None
rospy_stub.Publisher      = lambda *a, **kw: None
rospy_stub.on_shutdown    = lambda *a: None
rospy_stub.loginfo        = lambda *a, **kw: None
rospy_stub.init_node      = lambda *a, **kw: None
rospy_stub.spin           = lambda: None
rospy_stub.ROSInterruptException = Exception
sys.modules["rospy"] = rospy_stub

# ── stub excavator_msgs ───────────────────────────────────────────────────────
def _make_msg_module():
    mod = types.ModuleType("excavator_msgs.msg")

    class Header: pass

    class _Point:
        def __init__(self): self.x = 0.0; self.y = 0.0; self.z = 0.0

    class _Vec3:
        def __init__(self): self.x = 0.0; self.y = 0.0; self.z = 0.0

    class _Pose:
        def __init__(self): self.position = _Point()

    class _PoseStamped:
        def __init__(self): self.pose = _Pose()

    class ObstacleInfo:
        def __init__(self):
            self.obstacle_id = ""; self.obstacle_type = "obstacle"
            self.distance = 0.0;   self.relative_velocity = 0.0
            self.ttc = 0.0;        self.risk_score = 0.0; self.risk_level = 0
            self.pose = _PoseStamped(); self.velocity_vec = _Vec3()

    class ObstacleArray:
        def __init__(self):
            self.header = Header(); self.obstacles = []; self.dominant_risk_level = 0

    class RiskState:
        LEVEL_LOW = 0; LEVEL_MEDIUM = 1; LEVEL_HIGH = 2
        def __init__(self):
            self.header = Header(); self.current_level = 0
            self.min_distance = 0.0; self.min_ttc = 0.0; self.primary_threat_id = ""

    mod.ObstacleInfo  = ObstacleInfo
    mod.ObstacleArray = ObstacleArray
    mod.RiskState     = RiskState
    return mod

msg_mod = _make_msg_module()
sys.modules["excavator_msgs"]       = types.ModuleType("excavator_msgs")
sys.modules["excavator_msgs.msg"]   = msg_mod

# ── import modules under test ─────────────────────────────────────────────────
sys.path.insert(0, "/home/excavator/excavator_ws/src/excavator_risk/scripts")
import risk_assessor      as ra_mod
import trajectory_predictor as tp_mod


# ── helpers ───────────────────────────────────────────────────────────────────
def make_assessor(**kw):
    a = object.__new__(ra_mod.RiskAssessor)
    a.w_distance          = kw.get("w_distance",          0.6)
    a.w_ttc               = kw.get("w_ttc",               0.4)
    a.type_weights        = kw.get("type_weights",         {"person": 1.5, "vehicle": 1.2, "obstacle": 1.0})
    a.risk_low_threshold  = kw.get("risk_low_threshold",   0.3)
    a.risk_high_threshold = kw.get("risk_high_threshold",  0.7)
    a.safe_distance       = kw.get("safe_distance",        5.0)
    a.critical_distance   = kw.get("critical_distance",    1.0)
    a.safe_ttc            = kw.get("safe_ttc",             5.0)
    a.critical_ttc        = kw.get("critical_ttc",         1.5)
    a.risk_pub            = types.SimpleNamespace(publish=lambda m: None)
    a.assessed_pub        = types.SimpleNamespace(publish=lambda m: None)
    return a


def make_obs(obstacle_id="o1", obstacle_type="obstacle", distance=3.0, ttc=3.0):
    obs = msg_mod.ObstacleInfo()
    obs.obstacle_id   = obstacle_id
    obs.obstacle_type = obstacle_type
    obs.distance      = distance
    obs.ttc           = ttc
    return obs


# ── TestDistanceScore ─────────────────────────────────────────────────────────
class TestDistanceScore:
    def setup_method(self): self.a = make_assessor()

    def test_at_critical(self):
        assert self.a._distance_score(1.0) == pytest.approx(1.0)

    def test_below_critical(self):
        assert self.a._distance_score(0.5) == pytest.approx(1.0)

    def test_at_safe(self):
        assert self.a._distance_score(5.0) == pytest.approx(0.0)

    def test_above_safe(self):
        assert self.a._distance_score(10.0) == pytest.approx(0.0)

    def test_midpoint(self):
        # (5-3)/(5-1) = 0.5
        assert self.a._distance_score(3.0) == pytest.approx(0.5)

    def test_zero_distance(self):
        assert self.a._distance_score(0.0) == pytest.approx(1.0)


# ── TestTTCScore ──────────────────────────────────────────────────────────────
class TestTTCScore:
    def setup_method(self): self.a = make_assessor()

    def test_negative_ttc(self):
        assert self.a._ttc_score(-1.0) == pytest.approx(0.0)

    def test_at_critical(self):
        assert self.a._ttc_score(1.5) == pytest.approx(1.0)

    def test_below_critical(self):
        assert self.a._ttc_score(0.5) == pytest.approx(1.0)

    def test_at_safe(self):
        assert self.a._ttc_score(5.0) == pytest.approx(0.0)

    def test_above_safe(self):
        assert self.a._ttc_score(10.0) == pytest.approx(0.0)

    def test_midpoint(self):
        # (5-3.25)/(5-1.5) = 0.5
        assert self.a._ttc_score(3.25) == pytest.approx(0.5)


# ── TestComputeRisk ───────────────────────────────────────────────────────────
class TestComputeRisk:
    def setup_method(self): self.a = make_assessor()

    def test_low_risk_far_obstacle(self):
        obs = make_obs(obstacle_type="obstacle", distance=6.0, ttc=10.0)
        score, level = self.a._compute_risk(obs)
        assert score == pytest.approx(0.0)
        assert level == ra_mod.LEVEL_LOW

    def test_high_risk_close_person(self):
        obs = make_obs(obstacle_type="person", distance=0.5, ttc=0.5)
        score, level = self.a._compute_risk(obs)
        assert score == pytest.approx(1.0)
        assert level == ra_mod.LEVEL_HIGH

    def test_person_higher_than_obstacle(self):
        p = make_obs(obstacle_type="person",   distance=2.0, ttc=3.0)
        o = make_obs(obstacle_type="obstacle", distance=2.0, ttc=3.0)
        sp, _ = self.a._compute_risk(p)
        so, _ = self.a._compute_risk(o)
        assert sp > so

    def test_vehicle_higher_than_obstacle(self):
        v = make_obs(obstacle_type="vehicle",  distance=2.0, ttc=3.0)
        o = make_obs(obstacle_type="obstacle", distance=2.0, ttc=3.0)
        sv, _ = self.a._compute_risk(v)
        so, _ = self.a._compute_risk(o)
        assert sv > so

    def test_score_capped_at_1(self):
        obs = make_obs(obstacle_type="person", distance=0.0, ttc=0.0)
        score, _ = self.a._compute_risk(obs)
        assert score <= 1.0

    def test_medium_boundary(self):
        a = make_assessor(risk_low_threshold=0.3, risk_high_threshold=0.7,
                          w_distance=1.0, w_ttc=0.0)
        # distance=3m -> d_score=0.5 -> raw=0.5*1.0(obstacle) -> MEDIUM
        obs = make_obs(obstacle_type="obstacle", distance=3.0, ttc=10.0)
        _, level = a._compute_risk(obs)
        assert level == ra_mod.LEVEL_MEDIUM


# ── TestCallback ──────────────────────────────────────────────────────────────
class TestCallback:
    def setup_method(self):
        self.a = make_assessor()
        self.states = []; self.arrays = []
        self.a.risk_pub     = types.SimpleNamespace(publish=self.states.append)
        self.a.assessed_pub = types.SimpleNamespace(publish=self.arrays.append)

    def _arr(self, obs=None):
        arr = msg_mod.ObstacleArray()
        arr.obstacles = obs or []
        return arr

    def test_empty_list_publishes_low(self):
        self.a._callback(self._arr([]))
        assert self.states[0].current_level == ra_mod.LEVEL_LOW

    def test_high_risk_propagates(self):
        self.a._callback(self._arr([make_obs("x", "person", 0.5, 0.5)]))
        assert self.states[0].current_level == ra_mod.LEVEL_HIGH

    def test_primary_threat_id(self):
        self.a._callback(self._arr([make_obs("x", "person", 0.5, 0.5)]))
        assert self.states[0].primary_threat_id == "x"

    def test_primary_is_highest_score(self):
        lo = make_obs("lo", "obstacle", 6.0, 10.0)
        hi = make_obs("hi", "person",   0.5,  0.5)
        self.a._callback(self._arr([lo, hi]))
        assert self.states[0].primary_threat_id == "hi"

    def test_min_distance_updated(self):
        a = make_obs("a", distance=3.0, ttc=3.0)
        b = make_obs("b", distance=1.5, ttc=3.0)
        self.a._callback(self._arr([a, b]))
        assert self.states[0].min_distance == pytest.approx(1.5)

    def test_assessed_array_has_risk_score(self):
        self.a._callback(self._arr([make_obs(distance=3.0, ttc=3.0)]))
        assert self.arrays[0].obstacles[0].risk_score > 0.0


# ── TestTTPComputeTTC ─────────────────────────────────────────────────────────
class TestTTPComputeTTC:
    def setup_method(self):
        self.tp = object.__new__(tp_mod.TrajectoryPredictor)
        self.tp.excavator_speed = 1.0

    def test_static_obstacle(self):
        # obstacle still -> approach_speed=1.0 -> ttc=4.0
        assert self.tp._compute_ttc(4.0, 0.0, 0.0) == pytest.approx(4.0)

    def test_obstacle_moving_away(self):
        assert self.tp._compute_ttc(4.0, 2.0, 0.0) == pytest.approx(-1.0)

    def test_zero_distance(self):
        assert self.tp._compute_ttc(0.0, 0.0, 0.0) == pytest.approx(0.0)

    def test_ttc_capped_at_999(self):
        assert self.tp._compute_ttc(500.0, 0.999, 0.0) == pytest.approx(999.0)

    def test_same_speed_as_excavator(self):
        # approach_speed=0 -> ttc=-1
        assert self.tp._compute_ttc(3.0, 1.0, 0.0) == pytest.approx(-1.0)


# ── TestMakeKF ────────────────────────────────────────────────────────────────
class TestMakeKF:
    def test_dimensions(self):
        kf = tp_mod._make_kf(dt=0.1)
        assert kf.F.shape == (4, 4)
        assert kf.H.shape == (2, 4)
        assert kf.R.shape == (2, 2)
        assert kf.Q.shape == (4, 4)

    def test_predict_updates_state(self):
        import numpy as np
        kf = tp_mod._make_kf(dt=0.1)
        kf.x = np.array([[0.0], [0.0], [1.0], [0.0]])
        kf.predict()
        assert float(kf.x[0]) == pytest.approx(0.1, abs=1e-6)

    def test_update_reduces_uncertainty(self):
        import numpy as np
        kf = tp_mod._make_kf(dt=0.1)
        p_before = float(kf.P[0, 0])
        kf.predict()
        kf.update(np.array([[0.1], [0.0]]))
        p_after = float(kf.P[0, 0])
        assert p_after < p_before


# ── TestTrackerManagement ─────────────────────────────────────────────────────
class TestTrackerManagement:
    def _make_tp(self):
        tp = object.__new__(tp_mod.TrajectoryPredictor)
        tp.dt = 0.1; tp.proc_noise = 0.1; tp.meas_noise = 0.5
        tp.max_missing_frames = 3; tp.excavator_speed = 1.0
        tp._trackers = {}
        return tp

    def test_create_new_tracker(self):
        tp = self._make_tp()
        kf = tp._get_or_create_tracker("obj1", 1.0, 2.0)
        assert "obj1" in tp._trackers
        assert kf is not None

    def test_reuse_existing_tracker(self):
        tp = self._make_tp()
        kf1 = tp._get_or_create_tracker("obj1", 1.0, 2.0)
        kf2 = tp._get_or_create_tracker("obj1", 1.5, 2.5)
        assert kf1 is kf2

    def test_cleanup_removes_old_trackers(self):
        tp = self._make_tp()
        tp._get_or_create_tracker("obj1", 0.0, 0.0)
        tp._get_or_create_tracker("obj2", 1.0, 1.0)
        # simulate obj1 missing for max_missing_frames iterations
        for _ in range(tp.max_missing_frames):
            tp._cleanup_missing(seen_ids={"obj2"})
        assert "obj1" not in tp._trackers
        assert "obj2" in tp._trackers

    def test_cleanup_increments_missing_count(self):
        tp = self._make_tp()
        tp._get_or_create_tracker("obj1", 0.0, 0.0)
        tp._cleanup_missing(seen_ids=set())
        assert tp._trackers["obj1"]["missing"] == 1


# ── TestTPCallback ────────────────────────────────────────────────────────────
class TestTPCallback:
    def _make_tp(self):
        import numpy as np
        tp = object.__new__(tp_mod.TrajectoryPredictor)
        tp.dt = 0.1; tp.proc_noise = 0.1; tp.meas_noise = 0.5
        tp.max_missing_frames = 10; tp.excavator_speed = 1.0
        tp._trackers = {}
        tp._published = []
        tp.pub = types.SimpleNamespace(publish=tp._published.append)
        return tp

    def _arr(self, obstacles=None):
        arr = msg_mod.ObstacleArray()
        arr.obstacles = obstacles or []
        return arr

    def test_empty_callback_publishes(self):
        tp = self._make_tp()
        tp._callback(self._arr([]))
        assert len(tp._published) == 1
        assert len(tp._published[0].obstacles) == 0

    def test_callback_updates_velocity(self):
        tp = self._make_tp()
        obs = msg_mod.ObstacleInfo()
        obs.obstacle_id = "a"; obs.distance = 3.0; obs.ttc = 0.0
        obs.pose.pose.position.x = 0.1; obs.pose.pose.position.y = 0.0
        tp._callback(self._arr([obs]))
        out_obs = tp._published[0].obstacles[0]
        # after one step the velocity estimate might be small but velocity_vec is set
        assert hasattr(out_obs, "velocity_vec")

    def test_callback_sets_ttc(self):
        tp = self._make_tp()
        obs = msg_mod.ObstacleInfo()
        obs.obstacle_id = "b"; obs.distance = 4.0; obs.ttc = 0.0
        obs.pose.pose.position.x = 0.0; obs.pose.pose.position.y = 0.0
        tp._callback(self._arr([obs]))
        out_obs = tp._published[0].obstacles[0]
        # static obstacle, excavator_speed=1.0 -> ttc=4.0
        assert out_obs.ttc == pytest.approx(4.0)

    def test_callback_cleans_up_missing(self):
        tp = self._make_tp()
        tp.max_missing_frames = 1
        # first call creates tracker for "x"
        obs = msg_mod.ObstacleInfo()
        obs.obstacle_id = "x"; obs.distance = 3.0; obs.ttc = 0.0
        obs.pose.pose.position.x = 0.0; obs.pose.pose.position.y = 0.0
        tp._callback(self._arr([obs]))
        # second call without "x" -> missing count increases -> cleaned up after 1 miss
        tp._callback(self._arr([]))
        assert "x" not in tp._trackers


# ── TestTypeWeight ────────────────────────────────────────────────────────────
class TestTypeWeight:
    def test_unknown_type_defaults_to_1(self):
        a = make_assessor()
        assert a._type_weight("unknown_type") == pytest.approx(1.0)

    def test_known_types(self):
        a = make_assessor()
        assert a._type_weight("person")   == pytest.approx(1.5)
        assert a._type_weight("vehicle")  == pytest.approx(1.2)
        assert a._type_weight("obstacle") == pytest.approx(1.0)


# ── TestShutdown ──────────────────────────────────────────────────────────────
class TestShutdown:
    def test_assessor_shutdown_does_not_raise(self):
        a = make_assessor()
        a._shutdown()  # should not raise

    def test_tp_shutdown_does_not_raise(self):
        tp = object.__new__(tp_mod.TrajectoryPredictor)
        tp._trackers = {}
        tp._shutdown()  # should not raise


# ── TestMinTTC ────────────────────────────────────────────────────────────────
class TestMinTTC:
    def test_min_ttc_only_positive_ttc_counts(self):
        """min_ttc 应只记录 ttc > 0 的障碍物"""
        a = make_assessor()
        states = []
        a.risk_pub     = types.SimpleNamespace(publish=states.append)
        a.assessed_pub = types.SimpleNamespace(publish=lambda m: None)

        # obs1: ttc = -1 (远离), obs2: ttc = 3.0
        o1 = make_obs("a", distance=3.0, ttc=-1.0)
        o2 = make_obs("b", distance=4.0, ttc=3.0)
        arr = msg_mod.ObstacleArray(); arr.obstacles = [o1, o2]
        a._callback(arr)
        # min_ttc 应为 3.0（忽略负值）
        assert states[0].min_ttc == pytest.approx(3.0)

    def test_min_ttc_all_negative_stays_inf(self):
        """所有障碍物 ttc < 0 时，min_ttc 应保持 INF_FLOAT32=999"""
        a = make_assessor()
        states = []
        a.risk_pub     = types.SimpleNamespace(publish=states.append)
        a.assessed_pub = types.SimpleNamespace(publish=lambda m: None)

        o1 = make_obs("a", distance=3.0, ttc=-1.0)
        arr = msg_mod.ObstacleArray(); arr.obstacles = [o1]
        a._callback(arr)
        assert states[0].min_ttc == pytest.approx(999.0)
