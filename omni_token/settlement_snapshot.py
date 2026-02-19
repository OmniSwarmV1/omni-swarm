"""Backward-compatible import shim for settlement snapshot helpers."""

from __future__ import annotations

import importlib.util
import pathlib


def _load_moved_module():
    moved_path = pathlib.Path(__file__).resolve().parents[1] / "token" / "settlement_snapshot.py"
    spec = importlib.util.spec_from_file_location("_omniswarm_snapshot_moved", moved_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load moved settlement snapshot module at {moved_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    from token.settlement_snapshot import (  # type: ignore  # noqa: F401
        build_settlement_payload,
        generate_settlement_snapshot,
    )
except Exception:
    _moved = _load_moved_module()
    build_settlement_payload = _moved.build_settlement_payload
    generate_settlement_snapshot = _moved.generate_settlement_snapshot


__all__ = [
    "build_settlement_payload",
    "generate_settlement_snapshot",
]
