"""Health monitoring helpers for P2P transport backends."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class P2PHealthMonitor:
    latency_warn_ms: float = 1500.0
    failure_threshold: int = 2
    total_checks: int = 0
    total_failures: int = 0
    consecutive_failures: int = 0
    latency_warn_count: int = 0
    last_latency_ms: float | None = None
    last_error: str | None = None
    last_check_ts: float | None = None
    degraded: bool = False

    def record_success(self, latency_ms: float):
        self.total_checks += 1
        self.consecutive_failures = 0
        self.last_error = None
        self.last_latency_ms = round(latency_ms, 3)
        self.last_check_ts = time.time()
        if latency_ms > self.latency_warn_ms:
            self.latency_warn_count += 1
        self.degraded = False

    def record_failure(self, error: Exception | str):
        self.total_checks += 1
        self.total_failures += 1
        self.consecutive_failures += 1
        self.last_error = str(error)
        self.last_check_ts = time.time()
        if self.consecutive_failures >= self.failure_threshold:
            self.degraded = True

    def to_dict(self) -> dict:
        return {
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
            "consecutive_failures": self.consecutive_failures,
            "latency_warn_count": self.latency_warn_count,
            "last_latency_ms": self.last_latency_ms,
            "last_error": self.last_error,
            "last_check_ts": self.last_check_ts,
            "degraded": self.degraded,
            "latency_warn_ms": self.latency_warn_ms,
            "failure_threshold": self.failure_threshold,
        }
