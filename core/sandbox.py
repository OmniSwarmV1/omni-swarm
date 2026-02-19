"""Filesystem and network safety boundaries for OmniSwarm nodes (P6)."""

from __future__ import annotations

from pathlib import Path


class SandboxViolationError(PermissionError):
    """Raised when an operation escapes sandbox boundaries."""


class OmniSandbox:
    """Per-node sandbox rooted under .omni_sandbox/<node_id>."""

    def __init__(
        self,
        node_id: str,
        base_dir: str | Path = ".omni_sandbox",
        allowed_hosts: set[str] | None = None,
    ):
        self.node_id = node_id
        self.base_dir = Path(base_dir).resolve()
        self.root_path = (self.base_dir / node_id).resolve()
        self.allowed_hosts = set(allowed_hosts or {"127.0.0.1", "localhost"})
        self.root_path.mkdir(parents=True, exist_ok=True)

    def resolve_path(self, relative_path: str | Path) -> Path:
        rel = Path(relative_path)
        if rel.is_absolute():
            raise SandboxViolationError("Absolute paths are not allowed in sandbox operations.")

        candidate = (self.root_path / rel).resolve()
        if not candidate.is_relative_to(self.root_path):
            raise SandboxViolationError("Path escapes sandbox root.")
        return candidate

    def ensure_dir(self, relative_path: str | Path) -> Path:
        path = self.resolve_path(relative_path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def write_text(self, relative_path: str | Path, content: str) -> Path:
        path = self.resolve_path(relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def read_text(self, relative_path: str | Path) -> str:
        path = self.resolve_path(relative_path)
        return path.read_text(encoding="utf-8")

    def delete_file(self, relative_path: str | Path):
        path = self.resolve_path(relative_path)
        if path.exists():
            path.unlink()

    def list_files(self, relative_dir: str | Path = ".") -> list[Path]:
        directory = self.resolve_path(relative_dir)
        if not directory.exists():
            return []
        return sorted(p for p in directory.rglob("*") if p.is_file())

    def is_host_allowed(self, host: str) -> bool:
        return host in self.allowed_hosts
