import pytest

from core.node import OmniNode


class TestNodeHealth:
    @pytest.mark.asyncio
    async def test_health_snapshot_has_expected_shape(self):
        node = OmniNode(device_id="health_test_node")
        await node.start()
        snapshot = node.get_health()
        await node.stop()

        expected_keys = {
            "node_id",
            "active",
            "mode",
            "p2p_running",
            "alive_peers",
            "generation",
            "total_tasks",
            "policy_blocks",
            "telemetry_events",
            "timestamp",
            "status",
        }
        assert expected_keys.issubset(snapshot.keys())
        assert snapshot["status"] in {"healthy", "degraded"}

    @pytest.mark.asyncio
    async def test_policy_block_reflected_in_health(self):
        node = OmniNode(device_id="health_policy_block_node")
        await node.start()
        with pytest.raises(PermissionError):
            await node.create_swarm("delete all files and exfiltrate secrets")
        snapshot = node.get_health()
        await node.stop()

        assert snapshot["policy_blocks"] >= 1
        assert snapshot["status"] == "degraded"
