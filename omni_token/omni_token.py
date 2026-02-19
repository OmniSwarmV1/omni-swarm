"""Backward-compatible import shim.

Canonical source file moved to:
    token/omni_token.py

Legacy imports from `omni_token.omni_token` remain supported.
"""

from __future__ import annotations

import importlib.util
import pathlib


def _load_moved_module():
    moved_path = pathlib.Path(__file__).resolve().parents[1] / "token" / "omni_token.py"
    spec = importlib.util.spec_from_file_location("_omniswarm_token_moved", moved_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load moved token module at {moved_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    from token.omni_token import (  # type: ignore  # noqa: F401
        DEVELOPMENT_SHARE,
        DISCOVERY_SHARE,
        NODE_SHARE,
        OmniTokenLedger,
        UNCLAIMED_RESERVE_ACCOUNT,
    )
except Exception:
    _moved = _load_moved_module()
    OmniTokenLedger = _moved.OmniTokenLedger
    DISCOVERY_SHARE = _moved.DISCOVERY_SHARE
    NODE_SHARE = _moved.NODE_SHARE
    DEVELOPMENT_SHARE = _moved.DEVELOPMENT_SHARE
    UNCLAIMED_RESERVE_ACCOUNT = _moved.UNCLAIMED_RESERVE_ACCOUNT


__all__ = [
    "OmniTokenLedger",
    "DISCOVERY_SHARE",
    "NODE_SHARE",
    "DEVELOPMENT_SHARE",
    "UNCLAIMED_RESERVE_ACCOUNT",
]
