"""Lightweight anti-sybil guardrails for pilot cohorts (M4)."""

from __future__ import annotations

import hashlib
import platform
import time
from dataclasses import dataclass


@dataclass(frozen=True)
class SybilDecision:
    allowed: bool
    reason: str


class NodeSybilGuard:
    """Simple local anti-abuse guard (rate + duplicate task suppression)."""

    def __init__(
        self,
        node_id: str,
        min_task_interval_sec: float = 0.0,
        duplicate_window_sec: float = 15.0,
        min_compute_share: float = 0.0,
    ):
        self.node_id = node_id
        self.min_task_interval_sec = max(0.0, float(min_task_interval_sec))
        self.duplicate_window_sec = max(0.0, float(duplicate_window_sec))
        self.min_compute_share = max(0.0, min(1.0, float(min_compute_share)))
        self.last_task_ts: float | None = None
        self._task_hash_last_seen: dict[str, float] = {}

    @property
    def fingerprint(self) -> str:
        payload = (
            f"{self.node_id}|{platform.system()}|{platform.release()}|"
            f"{platform.machine()}|{platform.python_version()}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _task_hash(task: str) -> str:
        normalized = (task or "").strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def evaluate(self, task: str, compute_share: float) -> SybilDecision:
        now = time.time()
        if compute_share < self.min_compute_share:
            return SybilDecision(False, "Compute share below anti-sybil minimum.")

        if self.last_task_ts is not None and self.min_task_interval_sec > 0:
            elapsed = now - self.last_task_ts
            if elapsed < self.min_task_interval_sec:
                return SybilDecision(
                    False,
                    f"Rate limited by anti-sybil guard ({elapsed:.2f}s < {self.min_task_interval_sec:.2f}s).",
                )

        task_hash = self._task_hash(task)
        previous_ts = self._task_hash_last_seen.get(task_hash)
        if previous_ts is not None and self.duplicate_window_sec > 0:
            if (now - previous_ts) < self.duplicate_window_sec:
                return SybilDecision(False, "Duplicate task detected inside anti-sybil window.")

        self.last_task_ts = now
        self._task_hash_last_seen[task_hash] = now
        return SybilDecision(True, "Allowed by anti-sybil guard.")
