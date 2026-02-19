"""Asynchronous consensus verification for swarm outputs (M3)."""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationResult:
    verification_id: str
    task: str
    approvals: int
    rejections: int
    verifier_count: int
    consensus_score: float
    passed: bool
    reason: str
    timestamp: float

    def to_dict(self) -> dict:
        return {
            "verification_id": self.verification_id,
            "task": self.task,
            "approvals": self.approvals,
            "rejections": self.rejections,
            "verifier_count": self.verifier_count,
            "consensus_score": self.consensus_score,
            "passed": self.passed,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class ConsensusVerifier:
    """Run verifier swarm simulation asynchronously and compute consensus."""

    def __init__(
        self,
        verifier_count: int = 3,
        consensus_threshold: float = 0.67,
        verifier_latency_ms: float = 30.0,
    ):
        self.verifier_count = max(1, verifier_count)
        self.consensus_threshold = max(0.0, min(1.0, consensus_threshold))
        self.verifier_latency_ms = max(0.0, verifier_latency_ms)
        self.history: list[VerificationResult] = []

    @staticmethod
    def _is_result_suspicious(task: str, result: str) -> bool:
        task_text = (task or "").lower()
        result_text = (result or "").lower()
        suspicious_markers = [
            "no result",
            "failed",
            "error",
            "empty",
            "unknown",
        ]
        if any(marker in result_text for marker in suspicious_markers):
            return True
        if "discovery" not in result_text and any(
            keyword in task_text for keyword in ("discover", "kesfet", "patent", "chemistry", "kimyasi")
        ):
            return True
        return False

    async def _simulate_verifier_vote(self, task: str, result: str, verifier_idx: int) -> bool:
        await asyncio.sleep(self.verifier_latency_ms / 1000.0)
        suspicious = self._is_result_suspicious(task, result)
        if suspicious:
            # Fail-leaning majority for suspicious outcomes.
            return verifier_idx == 0
        return True

    async def verify(self, task: str, result: str) -> VerificationResult:
        verification_id = f"verif_{uuid.uuid4().hex[:10]}"
        votes = await asyncio.gather(
            *(
                self._simulate_verifier_vote(task, result, idx)
                for idx in range(self.verifier_count)
            )
        )
        approvals = sum(1 for vote in votes if vote)
        rejections = self.verifier_count - approvals
        consensus_score = round(approvals / self.verifier_count, 3)
        passed = consensus_score >= self.consensus_threshold
        reason = "consensus_pass" if passed else "consensus_fail"

        verification = VerificationResult(
            verification_id=verification_id,
            task=task,
            approvals=approvals,
            rejections=rejections,
            verifier_count=self.verifier_count,
            consensus_score=consensus_score,
            passed=passed,
            reason=reason,
            timestamp=time.time(),
        )
        self.history.append(verification)
        return verification
