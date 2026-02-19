# Tests for core/swarm_engine.py - Swarm lifecycle management

import pytest

from core.swarm_engine import SwarmEngine, SwarmStatus


class TestSwarmCreation:
    """Test swarm creation and agent assignment."""

    def test_create_swarm_returns_id(self):
        engine = SwarmEngine(node_id="test_node")
        swarm_id = engine.create_swarm("Test task")
        assert swarm_id.startswith("swarm_")

    def test_create_swarm_with_custom_agents(self):
        engine = SwarmEngine(node_id="test_node")
        agents = ["agent_a", "agent_b"]
        swarm_id = engine.create_swarm("Task", agents=agents)
        swarm = engine.get_swarm(swarm_id)
        assert swarm["agents"] == ["agent_a", "agent_b"]

    def test_create_swarm_default_agents(self):
        engine = SwarmEngine(node_id="test_node")
        swarm_id = engine.create_swarm("Task")
        swarm = engine.get_swarm(swarm_id)
        assert len(swarm["agents"]) == len(SwarmEngine.DEFAULT_AGENT_POOL)

    def test_swarm_starts_active(self):
        engine = SwarmEngine(node_id="test_node")
        swarm_id = engine.create_swarm("Task")
        swarm = engine.get_swarm(swarm_id)
        assert swarm["status"] == "active"


class TestSwarmLifecycle:
    """Test swarm state transitions."""

    def test_complete_swarm(self):
        engine = SwarmEngine(node_id="test_node")
        swarm_id = engine.create_swarm("Task")
        engine.complete_swarm(swarm_id, result="Done")
        swarm = engine.get_swarm(swarm_id)
        assert swarm["status"] == "completed"
        assert swarm["result"] == "Done"

    def test_fail_swarm(self):
        engine = SwarmEngine(node_id="test_node")
        swarm_id = engine.create_swarm("Task")
        engine.fail_swarm(swarm_id, reason="Out of memory")
        swarm = engine.get_swarm(swarm_id)
        assert swarm["status"] == "failed"
        assert "Out of memory" in swarm["result"]

    def test_dissolve_swarm(self):
        engine = SwarmEngine(node_id="test_node")
        swarm_id = engine.create_swarm("Task")
        engine.dissolve_swarm(swarm_id)
        swarm = engine.get_swarm(swarm_id)
        assert swarm["status"] == "dissolved"
        assert swarm["agents"] == []

    def test_unknown_swarm_raises_keyerror(self):
        engine = SwarmEngine(node_id="test_node")
        with pytest.raises(KeyError, match="Swarm not found"):
            engine.complete_swarm("nonexistent_swarm")

    def test_completed_swarm_has_duration(self):
        engine = SwarmEngine(node_id="test_node")
        swarm_id = engine.create_swarm("Task")
        engine.complete_swarm(swarm_id)
        swarm = engine.get_swarm(swarm_id)
        assert swarm["duration"] is not None
        assert swarm["duration"] >= 0


class TestSwarmStats:
    """Test engine-level statistics."""

    def test_stats_initial(self):
        engine = SwarmEngine(node_id="test_node")
        stats = engine.get_stats()
        assert stats["total_swarms"] == 0
        assert stats["completed"] == 0
        assert stats["failed"] == 0

    def test_stats_after_operations(self):
        engine = SwarmEngine(node_id="test_node")
        s1 = engine.create_swarm("Task 1")
        s2 = engine.create_swarm("Task 2")
        engine.complete_swarm(s1)
        engine.fail_swarm(s2, "error")
        stats = engine.get_stats()
        assert stats["total_swarms"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1

    def test_get_active_swarms(self):
        engine = SwarmEngine(node_id="test_node")
        engine.create_swarm("Task 1")
        s2 = engine.create_swarm("Task 2")
        engine.complete_swarm(s2)
        active = engine.get_active_swarms()
        assert len(active) == 1
        assert active[0]["status"] == "active"
