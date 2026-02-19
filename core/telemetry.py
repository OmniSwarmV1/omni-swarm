"""Structured telemetry collector for OmniSwarm nodes."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class TelemetryEvent:
    timestamp: float
    node_id: str
    name: str
    level: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "node_id": self.node_id,
            "name": self.name,
            "level": self.level,
            "payload": self.payload,
        }


class TelemetryCollector:
    """Local JSONL telemetry sink with in-memory query support."""

    def __init__(self, node_id: str, base_dir: str | Path):
        self.node_id = node_id
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.base_dir / "telemetry.jsonl"
        self._events: list[TelemetryEvent] = []

    def emit(self, name: str, payload: dict[str, Any] | None = None, level: str = "INFO"):
        event = TelemetryEvent(
            timestamp=time.time(),
            node_id=self.node_id,
            name=name,
            level=level,
            payload=dict(payload or {}),
        )
        self._events.append(event)
        with self.log_path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event.to_dict(), ensure_ascii=True) + "\n")

    def events(self, name: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        records = self._events
        if name is not None:
            records = [event for event in records if event.name == name]
        return [event.to_dict() for event in records[-limit:]]

    @property
    def count(self) -> int:
        return len(self._events)
