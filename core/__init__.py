# OmniSwarm Core Package
# v0.1 - 18 Şubat 2026

__version__ = "0.1.0"
__author__ = "OmniSwarm Contributors"


def __getattr__(name):
    """Lazy import to avoid circular issues with python -m execution."""
    if name == "OmniNode":
        from core.node import OmniNode
        return OmniNode
    raise AttributeError(f"module 'core' has no attribute {name!r}")
