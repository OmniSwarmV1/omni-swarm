from pathlib import Path

import pytest

from core.sandbox import OmniSandbox, SandboxViolationError


class TestOmniSandbox:
    def test_write_and_read_inside_sandbox(self, tmp_path: Path):
        sandbox = OmniSandbox(node_id="node_1", base_dir=tmp_path)
        sandbox.write_text("tasks/task.txt", "hello")
        content = sandbox.read_text("tasks/task.txt")
        assert content == "hello"

    def test_path_escape_blocked(self, tmp_path: Path):
        sandbox = OmniSandbox(node_id="node_1", base_dir=tmp_path)
        with pytest.raises(SandboxViolationError):
            sandbox.write_text("../outside.txt", "nope")

    def test_absolute_path_blocked(self, tmp_path: Path):
        sandbox = OmniSandbox(node_id="node_1", base_dir=tmp_path)
        with pytest.raises(SandboxViolationError):
            sandbox.read_text(Path(tmp_path).resolve())

    def test_list_files_returns_only_sandbox_files(self, tmp_path: Path):
        sandbox = OmniSandbox(node_id="node_1", base_dir=tmp_path)
        sandbox.write_text("a.txt", "a")
        sandbox.write_text("nested/b.txt", "b")
        files = sandbox.list_files(".")
        names = [f.name for f in files]
        assert "a.txt" in names
        assert "b.txt" in names

    def test_allowed_host_check(self, tmp_path: Path):
        sandbox = OmniSandbox(node_id="node_1", base_dir=tmp_path, allowed_hosts={"localhost"})
        assert sandbox.is_host_allowed("localhost") is True
        assert sandbox.is_host_allowed("example.com") is False
