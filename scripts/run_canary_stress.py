"""Run a local multi-node canary stress simulation and emit JSON report."""

from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing as mp
import os
import sys
import statistics
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from core.node import OmniNode


def _node_worker(
    node_id: str,
    compute_share: float,
    tasks_per_node: int,
    out_queue: mp.Queue,
):
    os.environ["OMNI_P2P_BACKEND"] = "local"

    async def _run():
        node = OmniNode(device_id=node_id, compute_share=compute_share)
        await node.start()
        successes = 0
        failures = 0
        task_latencies: list[float] = []

        for index in range(tasks_per_node):
            task = f"Canary task {index} for {node_id}: Yeni batarya kimyasi kesfet"
            started = time.perf_counter()
            try:
                await node.create_swarm(task)
                await node.wait_for_verifications(timeout=5.0)
                successes += 1
            except Exception:
                failures += 1
            finally:
                task_latencies.append(time.perf_counter() - started)

        health = node.get_health()
        verification = node.verification_report()
        diagnostics_path = node.export_diagnostics(f"canary/{node_id}_diagnostics.json")
        await node.stop()

        out_queue.put(
            {
                "node_id": node_id,
                "successes": successes,
                "failures": failures,
                "task_latencies_sec": [round(value, 4) for value in task_latencies],
                "health": health,
                "verification": verification,
                "diagnostics_path": diagnostics_path,
            }
        )

    asyncio.run(_run())


def _build_report(results: list[dict], started_at: float) -> dict:
    total_tasks = sum(item["successes"] + item["failures"] for item in results)
    total_successes = sum(item["successes"] for item in results)
    total_failures = sum(item["failures"] for item in results)
    all_latencies = [lat for item in results for lat in item["task_latencies_sec"]]
    success_rate = (total_successes / total_tasks) if total_tasks else 0.0

    verification_totals = sum(item["verification"]["total"] for item in results)
    verification_failures = sum(item["verification"]["failed"] for item in results)
    verification_failure_rate = (
        verification_failures / verification_totals if verification_totals else 0.0
    )

    return {
        "started_at": round(started_at, 3),
        "finished_at": round(time.time(), 3),
        "duration_sec": round(time.time() - started_at, 3),
        "node_count": len(results),
        "total_tasks": total_tasks,
        "total_successes": total_successes,
        "total_failures": total_failures,
        "success_rate": round(success_rate, 4),
        "verification_total": verification_totals,
        "verification_failures": verification_failures,
        "verification_failure_rate": round(verification_failure_rate, 4),
        "latency_avg_sec": round(statistics.mean(all_latencies), 4) if all_latencies else 0.0,
        "latency_p95_sec": round(
            sorted(all_latencies)[max(0, int(len(all_latencies) * 0.95) - 1)],
            4,
        )
        if all_latencies
        else 0.0,
        "nodes": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run local OmniSwarm canary stress test.")
    parser.add_argument("--nodes", type=int, default=10, help="Number of parallel nodes.")
    parser.add_argument("--tasks-per-node", type=int, default=3, help="Tasks per node.")
    parser.add_argument(
        "--output",
        type=str,
        default="canary_report.json",
        help="Output JSON report path.",
    )
    args = parser.parse_args()

    started_at = time.time()
    out_queue: mp.Queue = mp.Queue()
    processes: list[mp.Process] = []

    for index in range(max(1, args.nodes)):
        node_id = f"canary_node_{index:03d}"
        share = round(0.2 + ((index % 5) * 0.15), 2)
        process = mp.Process(
            target=_node_worker,
            args=(node_id, min(1.0, share), max(1, args.tasks_per_node), out_queue),
        )
        process.start()
        processes.append(process)

    for process in processes:
        process.join(timeout=120)
        if process.exitcode != 0:
            out_queue.put(
                {
                    "node_id": f"pid_{process.pid}",
                    "successes": 0,
                    "failures": max(1, args.tasks_per_node),
                    "task_latencies_sec": [],
                    "health": {"status": "degraded", "process_exit": process.exitcode},
                    "verification": {"total": 0, "failed": 0},
                    "diagnostics_path": "",
                }
            )

    results = [out_queue.get(timeout=5) for _ in range(len(processes))]
    report = _build_report(results, started_at=started_at)

    output_path = Path(args.output)
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(
        "[CANARY] "
        f"nodes={report['node_count']} tasks={report['total_tasks']} "
        f"success_rate={report['success_rate']:.2%} "
        f"verification_failure_rate={report['verification_failure_rate']:.2%}"
    )
    print(f"[CANARY] report={output_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
