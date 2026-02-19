"""Node attestation and diagnostics export helpers (M5/M6)."""

from __future__ import annotations

import json
import platform
import time
from pathlib import Path
from typing import Any


def build_attestation_payload(
    *,
    node_id: str,
    fingerprint: str,
    mode: str,
    version: str = "v0.2-alpha",
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "fingerprint": fingerprint,
        "mode": mode,
        "version": version,
        "generated_at": round(time.time(), 6),
        "runtime": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
    }


def write_json_document(path: str | Path, payload: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
    return out
