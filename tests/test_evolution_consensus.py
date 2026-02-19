import pytest

from core.verification import ConsensusVerifier


class TestConsensusVerifier:
    @pytest.mark.asyncio
    async def test_consensus_passes_for_normal_discovery_output(self):
        verifier = ConsensusVerifier(verifier_count=3, consensus_threshold=0.67)
        result = await verifier.verify(
            task="Yeni batarya kimyasi kesfet",
            result="[MOCK] Swarm completed for chemistry discovery.",
        )
        assert result.passed is True
        assert result.consensus_score >= 0.67

    @pytest.mark.asyncio
    async def test_consensus_fails_for_suspicious_output(self):
        verifier = ConsensusVerifier(verifier_count=3, consensus_threshold=0.67)
        result = await verifier.verify(
            task="Yeni batarya kimyasi kesfet",
            result="No result. Failed with unknown error.",
        )
        assert result.passed is False
        assert result.consensus_score < 0.67
