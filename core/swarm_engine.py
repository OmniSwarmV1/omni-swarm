# OmniSwarm Swarm Engine v0.1 - 18 Şubat 2026
# Dynamic swarm creation, lifecycle management, and task distribution

import uuid
import time
from typing import Optional
from enum import Enum


class SwarmStatus(Enum):
    """Lifecycle states for a swarm."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    DISSOLVED = "dissolved"


class Swarm:
    """Represents a single swarm instance with its agents and task."""

    def __init__(self, swarm_id: str, task: str, agents: list[str]):
        self.swarm_id = swarm_id
        self.task = task
        self.agents = list(agents)
        self.status = SwarmStatus.PENDING
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.result: Optional[str] = None

    def activate(self):
        self.status = SwarmStatus.ACTIVE

    def complete(self, result: Optional[str] = None):
        self.status = SwarmStatus.COMPLETED
        self.completed_at = time.time()
        self.result = result or f"Swarm {self.swarm_id} completed task: {self.task}"

    def fail(self, reason: str = "Unknown error"):
        self.status = SwarmStatus.FAILED
        self.completed_at = time.time()
        self.result = f"FAILED: {reason}"

    def dissolve(self):
        self.status = SwarmStatus.DISSOLVED
        self.agents.clear()

    @property
    def duration(self) -> Optional[float]:
        if self.completed_at and self.created_at:
            return self.completed_at - self.created_at
        return None

    def to_dict(self) -> dict:
        return {
            "swarm_id": self.swarm_id,
            "task": self.task,
            "agents": self.agents,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration": self.duration,
            "result": self.result,
        }


class SwarmEngine:
    """Manages swarm lifecycle: creation, execution, evolution hooks, dissolution.

    Each node runs one SwarmEngine instance. The engine tracks all swarms
    created by this node and provides hooks for the EvolutionEngine.
    """

    # Default specialist agent roles for auto-assignment
    DEFAULT_AGENT_POOL = [
        "researcher",
        "coder",
        "simulator",
        "reviewer",
        "patent_drafter",
    ]

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.swarms: dict[str, Swarm] = {}
        self.completed_count = 0
        self.failed_count = 0

    def create_swarm(
        self,
        task: str,
        agents: Optional[list[str]] = None,
    ) -> str:
        """Create a new swarm for the given task.

        Args:
            task: The task description for the swarm.
            agents: List of agent role names. Defaults to DEFAULT_AGENT_POOL.

        Returns:
            The swarm_id of the newly created swarm.
        """
        swarm_id = f"swarm_{uuid.uuid4().hex[:12]}"
        agent_list = agents if agents is not None else list(self.DEFAULT_AGENT_POOL)

        swarm = Swarm(swarm_id=swarm_id, task=task, agents=agent_list)
        swarm.activate()
        self.swarms[swarm_id] = swarm

        print(f"   [NEW] Swarm {swarm_id} olusturuldu | Agents: {len(agent_list)}")
        return swarm_id

    def complete_swarm(self, swarm_id: str, result: Optional[str] = None):
        """Mark a swarm as completed."""
        swarm = self._get_swarm(swarm_id)
        swarm.complete(result)
        self.completed_count += 1
        print(f"   [OK] Swarm {swarm_id} tamamlandi ({swarm.duration:.2f}s)")

    def fail_swarm(self, swarm_id: str, reason: str = "Unknown error"):
        """Mark a swarm as failed."""
        swarm = self._get_swarm(swarm_id)
        swarm.fail(reason)
        self.failed_count += 1
        print(f"   [FAIL] Swarm {swarm_id} basarisiz: {reason}")

    def dissolve_swarm(self, swarm_id: str):
        """Dissolve a swarm and release its agents."""
        swarm = self._get_swarm(swarm_id)
        swarm.dissolve()
        print(f"   [DISSOLVED] Swarm {swarm_id} dagitildi")

    def get_swarm(self, swarm_id: str) -> dict:
        """Return swarm info as a dictionary."""
        return self._get_swarm(swarm_id).to_dict()

    def get_active_swarms(self) -> list[dict]:
        """Return all active swarms."""
        return [
            s.to_dict()
            for s in self.swarms.values()
            if s.status == SwarmStatus.ACTIVE
        ]

    def get_stats(self) -> dict:
        """Return aggregate statistics for this engine."""
        return {
            "node_id": self.node_id,
            "total_swarms": len(self.swarms),
            "active": sum(
                1 for s in self.swarms.values() if s.status == SwarmStatus.ACTIVE
            ),
            "completed": self.completed_count,
            "failed": self.failed_count,
        }

    def _get_swarm(self, swarm_id: str) -> Swarm:
        """Internal helper – raises KeyError if swarm not found."""
        if swarm_id not in self.swarms:
            raise KeyError(f"Swarm not found: {swarm_id}")
        return self.swarms[swarm_id]
