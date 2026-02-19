# OmniSwarm P2P Discovery v0.1 - 18 Şubat 2026
# Peer-to-peer node discovery and messaging
#
# v0.1: Simulation mode (local peer registry)
# v0.2+: Live IPFS pubsub integration

import asyncio
import time
from typing import Optional, Callable


class Peer:
    """Represents a discovered peer node in the network."""

    def __init__(self, node_id: str, address: str = "local"):
        self.node_id = node_id
        self.address = address
        self.last_seen = time.time()
        self.latency_ms: Optional[float] = None

    def ping(self):
        """Update last_seen timestamp."""
        self.last_seen = time.time()

    def is_alive(self, timeout: float = 60.0) -> bool:
        """Check if peer was seen within timeout seconds."""
        return (time.time() - self.last_seen) < timeout

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "address": self.address,
            "last_seen": self.last_seen,
            "alive": self.is_alive(),
        }


class P2PDiscovery:
    """Manages peer-to-peer discovery and messaging for a node.

    v0.1 operates in simulation mode with a local peer registry.
    Future versions will integrate IPFS pubsub, Bluetooth, WiFi Direct, and Tor.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.peers: dict[str, Peer] = {}
        self.running = False
        self._message_handlers: list[Callable] = []
        self._message_log: list[dict] = []

    async def start(self):
        """Start the P2P discovery service."""
        self.running = True
        # Register self as a peer (bootstrap)
        self.peers[self.node_id] = Peer(self.node_id, address="127.0.0.1")
        await asyncio.sleep(0.1)  # Simulate discovery delay
        print(f"   [P2P] Discovery active | Node: {self.node_id}")

    async def stop(self):
        """Stop the P2P discovery service."""
        self.running = False
        print(f"   [P2P] Discovery stopped | Node: {self.node_id}")

    def register_peer(self, node_id: str, address: str = "local") -> Peer:
        """Register a new peer or update existing one."""
        if node_id in self.peers:
            self.peers[node_id].ping()
        else:
            self.peers[node_id] = Peer(node_id, address)
            print(f"   [PEER] New peer discovered: {node_id}")
        return self.peers[node_id]

    def remove_peer(self, node_id: str):
        """Remove a peer from the registry."""
        if node_id in self.peers and node_id != self.node_id:
            del self.peers[node_id]

    def get_peers(self, alive_only: bool = True) -> list[dict]:
        """Return list of known peers."""
        peers = self.peers.values()
        if alive_only:
            peers = [p for p in peers if p.is_alive()]
        return [p.to_dict() for p in peers]

    @property
    def peer_count(self) -> int:
        """Number of known alive peers (excluding self)."""
        return sum(
            1 for p in self.peers.values()
            if p.node_id != self.node_id and p.is_alive()
        )

    async def broadcast(self, message: dict):
        """Broadcast a message to all known peers (simulated).

        In simulation mode, messages are logged locally.
        In live mode, this will use IPFS pubsub.
        """
        entry = {
            "from": self.node_id,
            "message": message,
            "timestamp": time.time(),
            "recipients": [
                p.node_id for p in self.peers.values()
                if p.node_id != self.node_id
            ],
        }
        self._message_log.append(entry)

        # Notify local handlers
        for handler in self._message_handlers:
            try:
                handler(entry)
            except Exception as exc:
                print(f"   [WARN] Handler error: {exc}")

    def on_message(self, handler: Callable):
        """Register a message handler callback."""
        self._message_handlers.append(handler)

    def get_message_log(self) -> list[dict]:
        """Return the message log (simulation mode only)."""
        return list(self._message_log)

    def get_stats(self) -> dict:
        """Return P2P network statistics."""
        return {
            "node_id": self.node_id,
            "running": self.running,
            "total_peers": len(self.peers),
            "alive_peers": self.peer_count,
            "messages_sent": len(self._message_log),
        }
