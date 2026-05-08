"""
Unit tests for fsm_controller.py – pure logic tests, no ROS required.
"""
import sys
import math
import pytest

# ── Replicate the pure-logic pieces without importing rospy ──────────────────

NORMAL        = 0
CAUTION       = 1
PAUSED        = 2
EMERGENCY_STOP = 3

STATE_NAMES = {0: "NORMAL", 1: "CAUTION", 2: "PAUSED", 3: "EMERGENCY_STOP"}

_N2C = 0.30
_C2N = 0.20
_C2P = 0.60
_P2C = 0.45
_P2E = 0.85


def quintic_polynomial_velocity(v0, vf, t0, tf, t):
    if tf <= t0:
        return vf
    tau = max(0.0, min(1.0, (t - t0) / (tf - t0)))
    return v0 + (vf - v0) * (10.0 * tau**3 - 15.0 * tau**4 + 6.0 * tau**5)


class SimpleFSM:
    """Stripped FSM for testing without ROS."""

    def __init__(self):
        self.state = NORMAL
        self.transitions = []

    def update(self, score):
        if self.state == EMERGENCY_STOP:
            return
        if self.state == NORMAL and score >= _N2C:
            self._transit(CAUTION, score)
        elif self.state == CAUTION:
            if score >= _C2P:
                self._transit(PAUSED, score)
            elif score < _C2N:
                self._transit(NORMAL, score)
        elif self.state == PAUSED:
            if score >= _P2E:
                self._transit(EMERGENCY_STOP, score)

    def paused_check(self, score):
        if self.state == PAUSED and score < _P2C:
            self._transit(CAUTION, score)

    def _transit(self, new, score):
        self.transitions.append((self.state, new, score))
        self.state = new

    def force_emergency(self):
        self.transitions.append((self.state, EMERGENCY_STOP, -1))
        self.state = EMERGENCY_STOP

    def resume(self):
        if self.state == EMERGENCY_STOP:
            self._transit(NORMAL, -1)
            return True
        return False


# ── Tests ────────────────────────────────────────────────────────────────────

class TestStateTransitions:

    def test_initial_state_is_normal(self):
        fsm = SimpleFSM()
        assert fsm.state == NORMAL

    def test_normal_to_caution_at_threshold(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        assert fsm.state == CAUTION

    def test_normal_below_threshold_stays_normal(self):
        fsm = SimpleFSM()
        fsm.update(0.29)
        assert fsm.state == NORMAL

    def test_caution_to_paused_at_threshold(self):
        fsm = SimpleFSM()
        fsm.update(0.30)   # -> CAUTION
        fsm.update(0.60)   # -> PAUSED
        assert fsm.state == PAUSED

    def test_paused_to_emergency_at_threshold(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.60)
        fsm.update(0.85)
        assert fsm.state == EMERGENCY_STOP

    def test_full_escalation_chain(self):
        fsm = SimpleFSM()
        for score in [0.31, 0.61, 0.86]:
            fsm.update(score)
        assert fsm.state == EMERGENCY_STOP
        states = [t[1] for t in fsm.transitions]
        assert states == [CAUTION, PAUSED, EMERGENCY_STOP]

    def test_hysteresis_caution_no_drop_at_025(self):
        """CAUTION should not drop to NORMAL at 0.25 (need < 0.20)."""
        fsm = SimpleFSM()
        fsm.update(0.30)   # -> CAUTION
        fsm.update(0.25)   # stays CAUTION
        assert fsm.state == CAUTION

    def test_hysteresis_caution_drops_at_019(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.19)
        assert fsm.state == NORMAL

    def test_hysteresis_caution_drops_exactly_below_threshold(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.199)
        assert fsm.state == NORMAL

    def test_caution_below_threshold_does_not_drop_to_paused(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.59)
        assert fsm.state == CAUTION


class TestEmergencyStop:

    def test_emergency_stop_blocks_auto_transitions(self):
        fsm = SimpleFSM()
        fsm.force_emergency()
        fsm.update(0.0)    # should not change state
        assert fsm.state == EMERGENCY_STOP

    def test_emergency_stop_no_auto_recovery(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.60)
        fsm.update(0.85)
        # Even with low score, stays EMERGENCY_STOP
        fsm.update(0.0)
        assert fsm.state == EMERGENCY_STOP

    def test_resume_from_emergency_succeeds(self):
        fsm = SimpleFSM()
        fsm.force_emergency()
        result = fsm.resume()
        assert result is True
        assert fsm.state == NORMAL

    def test_resume_from_non_emergency_fails(self):
        fsm = SimpleFSM()
        result = fsm.resume()
        assert result is False
        assert fsm.state == NORMAL

    def test_resume_from_caution_fails(self):
        fsm = SimpleFSM()
        fsm.update(0.30)   # -> CAUTION
        result = fsm.resume()
        assert result is False
        assert fsm.state == CAUTION

    def test_resume_from_paused_fails(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.60)
        result = fsm.resume()
        assert result is False
        assert fsm.state == PAUSED


class TestPausedAutoResume:

    def test_paused_resumes_to_caution_when_risk_drops(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.60)
        assert fsm.state == PAUSED
        fsm.paused_check(0.44)
        assert fsm.state == CAUTION

    def test_paused_does_not_resume_above_threshold(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.60)
        fsm.paused_check(0.45)  # exactly at threshold, should NOT resume
        assert fsm.state == PAUSED

    def test_paused_does_not_resume_just_above_threshold(self):
        fsm = SimpleFSM()
        fsm.update(0.30)
        fsm.update(0.60)
        fsm.paused_check(0.50)
        assert fsm.state == PAUSED


class TestQuinticPolynomial:

    def test_starts_at_v0(self):
        v = quintic_polynomial_velocity(1.0, 0.0, 0.0, 2.0, 0.0)
        assert abs(v - 1.0) < 1e-9

    def test_ends_at_vf(self):
        v = quintic_polynomial_velocity(1.0, 0.0, 0.0, 2.0, 2.0)
        assert abs(v - 0.0) < 1e-9

    def test_past_end_clamps_to_vf(self):
        v = quintic_polynomial_velocity(1.0, 0.0, 0.0, 2.0, 5.0)
        assert abs(v - 0.0) < 1e-9

    def test_zero_duration_returns_vf(self):
        v = quintic_polynomial_velocity(1.0, 0.5, 1.0, 1.0, 1.0)
        assert abs(v - 0.5) < 1e-9

    def test_midpoint_smooth(self):
        v = quintic_polynomial_velocity(1.0, 0.0, 0.0, 2.0, 1.0)
        assert 0.0 < v < 1.0

    def test_monotone_deceleration(self):
        """Velocity decreasing from 1.0 to 0.0 should be monotone."""
        vals = [quintic_polynomial_velocity(1.0, 0.0, 0.0, 2.0, t * 0.1)
                for t in range(21)]
        for i in range(len(vals) - 1):
            assert vals[i] >= vals[i + 1] - 1e-9

    def test_max_tick_jump_le_01_at_10hz(self):
        """10 Hz ticks: adjacent velocity jump ≤ 0.1 m/s."""
        dt = 0.1
        jumps = [abs(quintic_polynomial_velocity(1.0, 0.0, 0.0, 2.0, t + dt)
                   - quintic_polynomial_velocity(1.0, 0.0, 0.0, 2.0, t))
                 for t in [i * dt for i in range(20)]]
        assert max(jumps) <= 0.1 + 1e-6

    def test_acceleration_from_zero(self):
        vals = [quintic_polynomial_velocity(0.0, 1.0, 0.0, 2.0, t * 0.1)
                for t in range(21)]
        for i in range(len(vals) - 1):
            assert vals[i] <= vals[i + 1] + 1e-9


class TestAllLegalTransitions:

    def test_normal_can_only_go_caution(self):
        for score in [0.30, 0.50, 0.70, 0.90]:
            fsm = SimpleFSM()
            fsm.update(score)
            assert fsm.state == CAUTION, f"score={score} expected CAUTION"

    def test_caution_can_go_paused_or_normal(self):
        fsm1 = SimpleFSM()
        fsm1.update(0.30)
        fsm1.update(0.60)
        assert fsm1.state == PAUSED

        fsm2 = SimpleFSM()
        fsm2.update(0.30)
        fsm2.update(0.19)
        assert fsm2.state == NORMAL

    def test_all_transitions_recorded(self):
        fsm = SimpleFSM()
        fsm.update(0.31)   # NORMAL -> CAUTION
        fsm.update(0.61)   # CAUTION -> PAUSED
        fsm.update(0.86)   # PAUSED -> EMERGENCY_STOP
        assert len(fsm.transitions) == 3
        assert fsm.transitions[0] == (NORMAL, CAUTION, 0.31)
        assert fsm.transitions[1] == (CAUTION, PAUSED, 0.61)
        assert fsm.transitions[2] == (PAUSED, EMERGENCY_STOP, 0.86)
