"""Integration test for distributed 3-node swarm coordination (P3)."""

from __future__ import annotations

import asyncio
import multiprocessing as mp
import os

import pytest

from core.coordinator import WeightedMergeCoordinator
from core.node import OmniNode
from omni_token.omni_token import OmniTokenLedger


def _node_worker(
    node_id: str,
    compute_share: float,
    task: str,
    out_queue: mp.Queue,
):
    """Run one OmniNode lifecycle in a child process and return result."""
    os.environ["OMNI_P2P_BACKEND"] = "local"

    async def _run():
        node = OmniNode(device_id=node_id, compute_share=compute_share)
        await node.start()
        discovery = await node.create_swarm(task)
        generation = node.evolution.generation
        history_size = len(node.evolution.history)
        await node.stop()
        out_queue.put(
            {
                "node_id": node_id,
                "compute_share": compute_share,
                "discovery": discovery,
                "generation": generation,
                "history_size": history_size,
            }
        )

    asyncio.run(_run())


@pytest.mark.integration
def test_distributed_swarm_three_nodes_contribute_and_merge(capsys):
    task = "Yeni 650Wh/kg batarya kimyasi kesfet"
    node_specs = [
        ("node_a", 0.5),
        ("node_b", 0.3),
        ("node_c", 0.2),
    ]

    out_queue: mp.Queue = mp.Queue()
    processes: list[mp.Process] = []
    for node_id, share in node_specs:
        proc = mp.Process(
            target=_node_worker,
            args=(node_id, share, task, out_queue),
        )
        proc.start()
        processes.append(proc)

    for proc in processes:
        proc.join(timeout=45)
        assert proc.exitcode == 0, f"Child process failed: pid={proc.pid}, exit={proc.exitcode}"

    node_results = [out_queue.get(timeout=5) for _ in node_specs]
    assert len(node_results) == 3

    contributions = {
        entry["node_id"]: float(entry["compute_share"])
        for entry in node_results
    }

    coordinator = WeightedMergeCoordinator()
    normalized = coordinator.normalize_contributions(contributions)
    assert pytest.approx(sum(normalized.values()), rel=0, abs=1e-8) == 1.0

    merged = coordinator.merge_results(task, node_results, normalized)
    assert merged["task"] == task
    assert merged["status"] == "Distributed swarm completed - 3/3 nodes contributed"
    assert "node_a" in merged["merged_result"]
    assert "node_b" in merged["merged_result"]
    assert "node_c" in merged["merged_result"]

    ledger = OmniTokenLedger()
    royalty = coordinator.distribute_royalty(
        task=task,
        total_amount=1250.0,
        normalized_contributions=normalized,
        ledger=ledger,
    )
    assert royalty["conserved"] is True
    assert royalty["credited_total"] == 1250.0
    assert set(royalty["node_rewards"].keys()) == {"node_a", "node_b", "node_c"}

    for entry in node_results:
        assert entry["generation"] >= 1
        assert entry["history_size"] >= 1

    completion = coordinator.completion_log(total_nodes=3, contributed_nodes=3)
    print(completion)
    captured = capsys.readouterr()
    assert "Distributed swarm completed - 3/3 nodes contributed" in captured.out
