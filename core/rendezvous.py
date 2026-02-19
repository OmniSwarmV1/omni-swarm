"""Rendezvous registry primitives for NAT-friendly peer bootstrapping (P7)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass
class RendezvousRecord:
    node_id: str
    address: str
    public_key: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    last_seen: float = field(default_factory=time.time)

    def touch(self, address: str | None = None, metadata: dict[str, str] | None = None):
        if address:
            self.address = address
        if metadata:
            self.metadata = dict(metadata)
        self.last_seen = time.time()


class InMemoryRendezvous:
    """Thread-safe in-memory rendezvous for discovery tests and local pilots."""

    def __init__(self, ttl_seconds: float = 30.0):
        self.ttl_seconds = ttl_seconds
        self._records: dict[str, RendezvousRecord] = {}
        self._lock = threading.Lock()

    def register(
        self,
        node_id: str,
        address: str,
        public_key: str | None = None,
        metadata: dict[str, str] | None = None,
    ):
        with self._lock:
            record = self._records.get(node_id)
            if record is None:
                record = RendezvousRecord(
                    node_id=node_id,
                    address=address,
                    public_key=public_key,
                    metadata=dict(metadata or {}),
                )
                self._records[node_id] = record
            else:
                if public_key:
                    record.public_key = public_key
                record.touch(address=address, metadata=metadata)

    def heartbeat(
        self,
        node_id: str,
        address: str,
        metadata: dict[str, str] | None = None,
    ):
        with self._lock:
            record = self._records.get(node_id)
            if record is None:
                self._records[node_id] = RendezvousRecord(
                    node_id=node_id,
                    address=address,
                    metadata=dict(metadata or {}),
                )
            else:
                record.touch(address=address, metadata=metadata)

    def cleanup_stale(self):
        threshold = time.time() - self.ttl_seconds
        with self._lock:
            stale_nodes = [
                node_id
                for node_id, record in self._records.items()
                if record.last_seen < threshold
            ]
            for node_id in stale_nodes:
                del self._records[node_id]

    def get_peers(self, exclude_node_id: str | None = None, limit: int = 50) -> list[dict]:
        self.cleanup_stale()
        with self._lock:
            peers = [
                record
                for record in self._records.values()
                if record.node_id != exclude_node_id
            ]
            peers.sort(key=lambda item: item.last_seen, reverse=True)
            selected = peers[:max(1, limit)]
            return [
                {
                    "node_id": item.node_id,
                    "address": item.address,
                    "public_key": item.public_key,
                    "metadata": dict(item.metadata),
                    "last_seen": item.last_seen,
                }
                for item in selected
            ]

    def size(self) -> int:
        self.cleanup_stale()
        with self._lock:
            return len(self._records)
