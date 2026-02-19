# Tests for core/p2p_discovery.py - Peer discovery and messaging

import pytest
import pytest_asyncio

from core.p2p_discovery import P2PDiscovery, Peer


class TestPeer:
    """Test individual Peer objects."""

    def test_peer_creation(self):
        peer = Peer(node_id="peer_001", address="192.168.1.1")
        assert peer.node_id == "peer_001"
        assert peer.address == "192.168.1.1"

    def test_peer_is_alive_initially(self):
        peer = Peer(node_id="peer_001")
        assert peer.is_alive() is True

    def test_peer_ping_updates_last_seen(self):
        peer = Peer(node_id="peer_001")
        first_seen = peer.last_seen
        peer.ping()
        assert peer.last_seen >= first_seen

    def test_peer_to_dict(self):
        peer = Peer(node_id="peer_001", address="local")
        data = peer.to_dict()
        assert data["node_id"] == "peer_001"
        assert data["address"] == "local"
        assert "alive" in data


class TestP2PDiscovery:
    """Test P2P discovery service."""

    def test_keypair_generated(self):
        p2p = P2PDiscovery(node_id="node_001")
        assert isinstance(p2p.public_key_b64, str)
        assert len(p2p.public_key_b64) > 0

    def test_signed_heartbeat_verifies(self):
        p2p = P2PDiscovery(node_id="node_001")
        envelope = p2p.build_signed_heartbeat()
        assert p2p._verify_envelope(envelope) is True

    def test_tampered_heartbeat_fails(self):
        p2p = P2PDiscovery(node_id="node_001")
        envelope = p2p.build_signed_heartbeat()
        envelope["payload"]["node_id"] = "node_x_tampered"
        assert p2p._verify_envelope(envelope) is False

    @pytest.mark.asyncio
    async def test_start_registers_self(self):
        p2p = P2PDiscovery(node_id="node_001")
        await p2p.start()
        assert p2p.running is True
        assert "node_001" in p2p.peers

    @pytest.mark.asyncio
    async def test_stop(self):
        p2p = P2PDiscovery(node_id="node_001")
        await p2p.start()
        await p2p.stop()
        assert p2p.running is False

    def test_register_peer(self):
        p2p = P2PDiscovery(node_id="node_001")
        peer = p2p.register_peer("peer_002", "192.168.1.2")
        assert peer.node_id == "peer_002"
        assert "peer_002" in p2p.peers

    def test_register_existing_peer_pings(self):
        p2p = P2PDiscovery(node_id="node_001")
        p2p.register_peer("peer_002")
        first_seen = p2p.peers["peer_002"].last_seen
        p2p.register_peer("peer_002")
        assert p2p.peers["peer_002"].last_seen >= first_seen

    def test_remove_peer(self):
        p2p = P2PDiscovery(node_id="node_001")
        p2p.register_peer("peer_002")
        p2p.remove_peer("peer_002")
        assert "peer_002" not in p2p.peers

    def test_cannot_remove_self(self):
        p2p = P2PDiscovery(node_id="node_001")
        p2p.peers["node_001"] = Peer("node_001")
        p2p.remove_peer("node_001")
        assert "node_001" in p2p.peers

    def test_peer_count_excludes_self(self):
        p2p = P2PDiscovery(node_id="node_001")
        p2p.peers["node_001"] = Peer("node_001")
        p2p.register_peer("peer_002")
        p2p.register_peer("peer_003")
        assert p2p.peer_count == 2


class TestP2PMessaging:
    """Test message broadcast and handler system."""

    @pytest.mark.asyncio
    async def test_broadcast_logs_message(self):
        p2p = P2PDiscovery(node_id="node_001")
        await p2p.start()
        await p2p.broadcast({"type": "hello"})
        log = p2p.get_message_log()
        assert len(log) == 1
        assert log[0]["from"] == "node_001"

    @pytest.mark.asyncio
    async def test_message_handler_called(self):
        p2p = P2PDiscovery(node_id="node_001")
        received = []
        p2p.on_message(lambda msg: received.append(msg))
        await p2p.start()
        await p2p.broadcast({"type": "test"})
        assert len(received) == 1

    def test_get_stats(self):
        p2p = P2PDiscovery(node_id="node_001")
        stats = p2p.get_stats()
        assert stats["node_id"] == "node_001"
        assert stats["running"] is False
        assert stats["messages_sent"] == 0


class _FakeIPFSAdapter:
    def __init__(self, latency_ms: float = 10.0, fail: bool = False):
        self.latency_ms = latency_ms
        self.fail = fail

    def health_check(self):
        if self.fail:
            raise RuntimeError("ipfs daemon unreachable")
        return self.latency_ms

    def close(self):
        return None

    def connect(self):
        return None

    def publish(self, payload):
        if self.fail:
            raise RuntimeError("publish failed")
        return None

    def subscribe(self):
        return []


class TestP2PHealth:
    @pytest.mark.asyncio
    async def test_health_check_records_latency_warning(self):
        p2p = P2PDiscovery(
            node_id="node_health_warn",
            enable_ipfs=True,
            ipfs_latency_warn_ms=50.0,
        )
        p2p._ipfs_connected = True
        p2p._ipfs = _FakeIPFSAdapter(latency_ms=120.0, fail=False)

        ok = await p2p.check_ipfs_health_once()
        stats = p2p.get_stats()

        assert ok is True
        assert stats["ipfs_health"]["latency_warn_count"] >= 1
        assert stats["ipfs_health"]["degraded"] is False

    @pytest.mark.asyncio
    async def test_health_check_degrades_after_consecutive_failures(self):
        p2p = P2PDiscovery(
            node_id="node_health_degrade",
            enable_ipfs=True,
            ipfs_failure_threshold=2,
        )
        p2p._ipfs_connected = True
        p2p._ipfs = _FakeIPFSAdapter(fail=True)

        first = await p2p.check_ipfs_health_once()
        second = await p2p.check_ipfs_health_once()
        stats = p2p.get_stats()

        assert first is False
        assert second is False
        assert stats["ipfs_health"]["degraded"] is True
        assert p2p._ipfs_connected is False
