"""Deterministic settlement snapshot utilities (P9)."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from omni_token.omni_token import OmniTokenLedger


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def build_settlement_payload(ledger: OmniTokenLedger) -> dict[str, Any]:
    balances = [
        {"account": account, "balance": balance}
        for account, balance in sorted(ledger.balances.items(), key=lambda item: item[0])
    ]
    return {
        "snapshot_version": "v0.2",
        "balances": balances,
        "total_distributed": round(ledger.total_distributed, 8),
        "total_transactions": len(ledger.transactions),
        "total_receipts": len(ledger.receipts),
    }


def generate_settlement_snapshot(
    ledger: OmniTokenLedger,
    output_path: str | Path | None = None,
) -> dict[str, Any]:
    payload = build_settlement_payload(ledger)
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    snapshot = {
        "generated_at": round(time.time(), 6),
        "payload": payload,
        "hash": digest,
    }

    if output_path is not None:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=True), encoding="utf-8")
        snapshot["path"] = str(path)

    return snapshot
