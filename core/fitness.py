"""Verification-driven fitness scoring for evolution (P8)."""

from __future__ import annotations


def _clamp_01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class FitnessScorer:
    """Compute bounded fitness scores from verification signals."""

    def __init__(
        self,
        weight_completion: float = 0.35,
        weight_reproducibility: float = 0.30,
        weight_consensus: float = 0.25,
        weight_efficiency: float = 0.10,
    ):
        total = (
            weight_completion
            + weight_reproducibility
            + weight_consensus
            + weight_efficiency
        )
        if total <= 0:
            raise ValueError("Fitness weights must sum to a positive value.")
        self.weight_completion = weight_completion / total
        self.weight_reproducibility = weight_reproducibility / total
        self.weight_consensus = weight_consensus / total
        self.weight_efficiency = weight_efficiency / total

    def score(
        self,
        *,
        completed: bool,
        reproducibility: float,
        consensus: float,
        efficiency: float,
    ) -> float:
        completion_signal = 1.0 if completed else 0.0
        value = (
            completion_signal * self.weight_completion
            + _clamp_01(reproducibility) * self.weight_reproducibility
            + _clamp_01(consensus) * self.weight_consensus
            + _clamp_01(efficiency) * self.weight_efficiency
        )
        return round(_clamp_01(value), 3)

    def score_from_result(self, task: str, result: str, compute_share: float) -> float:
        """Derive a best-effort verification proxy for v0.2 local runtime."""
        result_text = (result or "").lower()
        task_text = (task or "").lower()

        completed = "completed" in result_text or "discovery" in result_text
        reproducibility = 0.8 if "simulated discovery" in result_text else 0.45
        consensus = 0.75 if any(word in task_text for word in ["kesfet", "discover", "patent"]) else 0.55
        efficiency = _clamp_01(1.0 - max(0.0, min(1.0, compute_share)) * 0.5)

        return self.score(
            completed=completed,
            reproducibility=reproducibility,
            consensus=consensus,
            efficiency=efficiency,
        )
