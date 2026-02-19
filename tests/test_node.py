# Tests for core/node.py - OmniSwarm Local Core

import asyncio
import pytest
import pytest_asyncio

from core.node import OmniNode


class TestOmniNodeInit:
    """Test node initialization and configuration."""

    def test_default_node_creates_uuid(self):
        node = OmniNode()
        assert node.node_id is not None
        assert len(node.node_id) > 0

    def test_custom_device_id(self):
        node = OmniNode(device_id="test_device_001")
        assert node.node_id == "test_device_001"

    def test_default_compute_share(self):
        node = OmniNode()
        assert node.compute_share == 0.3

    def test_custom_compute_share(self):
        node = OmniNode(compute_share=0.5)
        assert node.compute_share == 0.5

    def test_compute_share_clamped_high(self):
        node = OmniNode(compute_share=1.5)
        assert node.compute_share == 1.0

    def test_compute_share_clamped_low(self):
        node = OmniNode(compute_share=-0.5)
        assert node.compute_share == 0.0

    def test_node_starts_inactive(self):
        node = OmniNode()
        assert node.active is False

    def test_default_mode_is_mock(self):
        node = OmniNode()
        assert node.mode == "mock"


class TestOmniNodeLifecycle:
    """Test node start/stop lifecycle."""

    @pytest.mark.asyncio
    async def test_start_activates_node(self):
        node = OmniNode(device_id="lifecycle_test")
        await node.start()
        assert node.active is True

    @pytest.mark.asyncio
    async def test_stop_deactivates_node(self):
        node = OmniNode(device_id="lifecycle_test")
        await node.start()
        await node.stop()
        assert node.active is False

    @pytest.mark.asyncio
    async def test_start_initializes_evolution_population(self):
        node = OmniNode(device_id="evo_init_test")
        await node.start()
        assert len(node.evolution.population) > 0


class TestOmniNodeSwarm:
    """Test mock swarm creation and execution."""

    @pytest.mark.asyncio
    async def test_create_swarm_returns_result(self):
        node = OmniNode(device_id="swarm_test", compute_share=0.4)
        await node.start()
        result = await node.create_swarm("Test task")
        assert result["status"] == "COMPLETED"
        assert result["task"] == "Test task"

    @pytest.mark.asyncio
    async def test_create_swarm_has_royalty(self):
        node = OmniNode(device_id="swarm_test", compute_share=0.4)
        await node.start()
        result = await node.create_swarm("Test task")
        assert result["royalty_pool"] == 1250.0
        assert result["node_reward"] >= 0

    @pytest.mark.asyncio
    async def test_swarm_requires_active_node(self):
        node = OmniNode(device_id="inactive_test")
        with pytest.raises(RuntimeError, match="not active"):
            await node.create_swarm("Should fail")

    @pytest.mark.asyncio
    async def test_swarm_result_is_deterministic_structure(self):
        node = OmniNode(device_id="deterministic_test", compute_share=0.5)
        await node.start()
        result = await node.create_swarm("Deterministic task")
        # Assert exact keys present (deterministic structure)
        expected_keys = {"task", "swarm_result", "royalty_pool", "node_reward", "status"}
        assert set(result.keys()) == expected_keys

    @pytest.mark.asyncio
    async def test_swarm_advances_evolution_generation(self):
        node = OmniNode(device_id="evo_generation_test", compute_share=0.5)
        await node.start()
        initial_generation = node.evolution.generation
        await node.create_swarm("Generation task")
        assert node.evolution.generation == initial_generation + 1
