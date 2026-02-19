"""Go/No-Go gate for OmniSwarm release readiness."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path


CRITICAL_TEST_TARGETS = [
    "tests/test_policy_engine.py",
    "tests/test_sandbox.py",
    "tests/test_p2p_discovery.py",
    "tests/test_p2p_rendezvous.py",
    "tests/test_fitness.py",
    "tests/test_evolution.py",
    "tests/test_omni_token.py",
    "tests/test_settlement_integrity.py",
    "tests/test_health.py",
    "tests/test_node.py",
    "tests/test_multi_node_integration.py",
]


def run_command(command: list[str]) -> tuple[int, float]:
    started = time.perf_counter()
    completed = subprocess.run(command, check=False)
    elapsed = time.perf_counter() - started
    return completed.returncode, elapsed


def main() -> int:
    report: dict[str, object] = {
        "timestamp": round(time.time(), 3),
        "critical_targets": CRITICAL_TEST_TARGETS,
        "steps": [],
        "status": "NO_GO",
    }

    test_cmd = [sys.executable, "-m", "pytest", "-q", *CRITICAL_TEST_TARGETS]
    code, duration = run_command(test_cmd)
    report["steps"].append({
        "name": "critical_tests",
        "command": " ".join(test_cmd),
        "exit_code": code,
        "duration_sec": round(duration, 3),
    })

    if code != 0:
        report["status"] = "NO_GO"
    else:
        report["status"] = "GO"

    out_path = Path("go_no_go_report.json")
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"[GATE] status={report['status']}")
    print(f"[GATE] report={out_path.resolve()}")
    return 0 if report["status"] == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
