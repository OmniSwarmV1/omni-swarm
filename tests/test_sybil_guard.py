import time

import pytest

from core.sybil_guard import NodeSybilGuard


class TestNodeSybilGuard:
    def test_fingerprint_is_stable(self):
        guard = NodeSybilGuard(node_id="node_a")
        assert guard.fingerprint == guard.fingerprint
        assert len(guard.fingerprint) == 64

    def test_duplicate_task_blocked_inside_window(self):
        guard = NodeSybilGuard(node_id="node_a", duplicate_window_sec=5.0)
        first = guard.evaluate("same task", compute_share=0.5)
        second = guard.evaluate("same task", compute_share=0.5)
        assert first.allowed is True
        assert second.allowed is False
        assert "Duplicate task" in second.reason

    def test_rate_limit_blocks_fast_replays(self):
        guard = NodeSybilGuard(node_id="node_a", min_task_interval_sec=0.5, duplicate_window_sec=0.0)
        first = guard.evaluate("task_1", compute_share=0.5)
        second = guard.evaluate("task_2", compute_share=0.5)
        assert first.allowed is True
        assert second.allowed is False
        assert "Rate limited" in second.reason

    def test_rate_limit_allows_after_wait(self):
        guard = NodeSybilGuard(node_id="node_a", min_task_interval_sec=0.01, duplicate_window_sec=0.0)
        first = guard.evaluate("task_1", compute_share=0.5)
        time.sleep(0.02)
        second = guard.evaluate("task_2", compute_share=0.5)
        assert first.allowed is True
        assert second.allowed is True

    def test_compute_share_floor_blocks_low_share(self):
        guard = NodeSybilGuard(node_id="node_a", min_compute_share=0.4)
        decision = guard.evaluate("task_1", compute_share=0.2)
        assert decision.allowed is False
