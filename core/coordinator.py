"""Distributed swarm coordination primitives.

P3 scope:
- Normalize node contribution weights
- Merge per-node swarm outputs into a single result
- Distribute royalty pool across discovery, nodes, and development fund
"""

from __future__ import annotations

from typing import Any

from omni_token.omni_token import (
    DEVELOPMENT_SHARE,
    DISCOVERY_SHARE,
    NODE_SHARE,
    OmniTokenLedger,
    UNCLAIMED_RESERVE_ACCOUNT,
)


class WeightedMergeCoordinator:
    """Coordinator for weighted multi-node swarm execution."""

    def normalize_contributions(
        self,
        contributions: dict[str, float],
    ) -> dict[str, float]:
        """Normalize arbitrary non-negative contributions to sum exactly to 1.0."""
        positive = {node_id: max(0.0, value) for node_id, value in contributions.items()}
        total = sum(positive.values())
        if total <= 0:
            raise ValueError("At least one contribution must be > 0")

        normalized = {
            node_id: round(value / total, 8)
            for node_id, value in positive.items()
        }
        delta = round(1.0 - sum(normalized.values()), 8)
        if delta != 0:
            # Apply tiny rounding delta to the highest-contribution node.
            top_node = max(normalized, key=normalized.get)
            normalized[top_node] = round(normalized[top_node] + delta, 8)

        return normalized

    def merge_results(
        self,
        task: str,
        node_results: list[dict[str, Any]],
        normalized_contributions: dict[str, float],
    ) -> dict[str, Any]:
        """Create a single merged swarm result from node outputs."""
        summaries: list[str] = []
        weighted_confidence = 0.0

        for result in node_results:
            node_id = str(result["node_id"])
            node_weight = normalized_contributions.get(node_id, 0.0)
            swarm_result = str(result["discovery"]["swarm_result"])
            summaries.append(f"{node_id} ({node_weight:.2%}): {swarm_result}")
            weighted_confidence += node_weight

        contributed_nodes = len(normalized_contributions)
        total_nodes = len(node_results)
        status = self.completion_log(total_nodes, contributed_nodes)

        return {
            "task": task,
            "status": status,
            "weighted_confidence": round(weighted_confidence, 8),
            "contributions": normalized_contributions,
            "merged_result": " | ".join(summaries),
        }

    def distribute_royalty(
        self,
        task: str,
        total_amount: float,
        normalized_contributions: dict[str, float],
        ledger: OmniTokenLedger,
        discovery_account: str = "distributed_swarm",
        dev_account: str = "omni_dev_fund",
        reserve_account: str = UNCLAIMED_RESERVE_ACCOUNT,
    ) -> dict[str, Any]:
        """Distribute one royalty pool for a distributed swarm run."""
        if total_amount <= 0:
            raise ValueError("total_amount must be > 0")
        if not normalized_contributions:
            raise ValueError("normalized_contributions cannot be empty")

        discovery_reward = round(total_amount * DISCOVERY_SHARE, 8)
        node_pool = round(total_amount * NODE_SHARE, 8)
        dev_reward = round(total_amount * DEVELOPMENT_SHARE, 8)

        node_rewards: dict[str, float] = {}
        assigned_node_rewards = 0.0
        for node_id, weight in normalized_contributions.items():
            reward = round(node_pool * max(0.0, weight), 8)
            node_rewards[node_id] = reward
            assigned_node_rewards = round(assigned_node_rewards + reward, 8)
            if reward > 0:
                ledger.credit(node_id, reward, f"Distributed compute: {task}")

        unclaimed_reserve = round(node_pool - assigned_node_rewards, 8)
        if unclaimed_reserve > 0:
            ledger.credit(
                reserve_account,
                unclaimed_reserve,
                f"Distributed reserve: {task}",
            )

        ledger.credit(discovery_account, discovery_reward, f"Distributed discovery: {task}")
        ledger.credit(dev_account, dev_reward, f"Distributed dev fund: {task}")

        credited_total = round(
            discovery_reward + assigned_node_rewards + unclaimed_reserve + dev_reward,
            8,
        )
        delta = round(total_amount - credited_total, 8)
        if delta > 0:
            ledger.credit(reserve_account, delta, f"Distributed rounding delta: {task}")
            unclaimed_reserve = round(unclaimed_reserve + delta, 8)
            credited_total = round(credited_total + delta, 8)

        return {
            "task": task,
            "total": total_amount,
            "discovery_reward": discovery_reward,
            "node_pool": node_pool,
            "node_rewards": node_rewards,
            "dev_fund": dev_reward,
            "unclaimed_reserve": unclaimed_reserve,
            "credited_total": credited_total,
            "conserved": credited_total == round(total_amount, 8),
        }

    def completion_log(self, total_nodes: int, contributed_nodes: int) -> str:
        return (
            "Distributed swarm completed - "
            f"{contributed_nodes}/{total_nodes} nodes contributed"
        )
