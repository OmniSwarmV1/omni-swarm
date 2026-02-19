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

    @pytest.mark.asyncio
    async def test_diagnostics_and_attestation_export(self):
        node = OmniNode(device_id="health_diag_node")
        await node.start()
        await node.create_swarm("Yeni batarya kimyasi kesfet")
        await node.wait_for_verifications(timeout=2.0)

        attestation_path = node.export_attestation()
        diagnostics_path = node.export_diagnostics()
        await node.stop()

        import json
        from pathlib import Path

        attestation = json.loads(Path(attestation_path).read_text(encoding="utf-8"))
        diagnostics = json.loads(Path(diagnostics_path).read_text(encoding="utf-8"))

        assert attestation["node_id"] == "health_diag_node"
        assert "fingerprint" in attestation
        assert "health" in diagnostics
        assert "verification" in diagnostics
