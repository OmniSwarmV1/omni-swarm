"""Node health snapshot helpers for operations readiness (P10)."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class HealthSnapshot:
    node_id: str
    active: bool
    mode: str
    p2p_running: bool
    alive_peers: int
    generation: int
    total_tasks: int
    policy_blocks: int
    telemetry_events: int
    timestamp: float
    status: str

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "active": self.active,
            "mode": self.mode,
            "p2p_running": self.p2p_running,
            "alive_peers": self.alive_peers,
            "generation": self.generation,
            "total_tasks": self.total_tasks,
            "policy_blocks": self.policy_blocks,
            "telemetry_events": self.telemetry_events,
            "timestamp": self.timestamp,
            "status": self.status,
        }


def build_health_snapshot(
    *,
    node_id: str,
    active: bool,
    mode: str,
    p2p_running: bool,
    alive_peers: int,
    generation: int,
    total_tasks: int,
    policy_blocks: int,
    telemetry_events: int,
) -> HealthSnapshot:
    degraded = (not active) or (policy_blocks > 0 and total_tasks == 0)
    status = "degraded" if degraded else "healthy"
    return HealthSnapshot(
        node_id=node_id,
        active=active,
        mode=mode,
        p2p_running=p2p_running,
        alive_peers=alive_peers,
        generation=generation,
        total_tasks=total_tasks,
        policy_blocks=policy_blocks,
        telemetry_events=telemetry_events,
        timestamp=time.time(),
        status=status,
    )
