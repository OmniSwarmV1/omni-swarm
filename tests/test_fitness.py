from core.fitness import FitnessScorer


class TestFitnessScorer:
    def test_high_signals_produce_high_score(self):
        scorer = FitnessScorer()
        score = scorer.score(
            completed=True,
            reproducibility=1.0,
            consensus=1.0,
            efficiency=1.0,
        )
        assert score >= 0.99

    def test_incomplete_result_reduces_score(self):
        scorer = FitnessScorer()
        score = scorer.score(
            completed=False,
            reproducibility=0.2,
            consensus=0.2,
            efficiency=0.2,
        )
        assert score < 0.2

    def test_noop_proxy_scores_lower_than_discovery_proxy(self):
        scorer = FitnessScorer()
        noop = scorer.score_from_result(
            task="Generic task",
            result="No result",
            compute_share=0.8,
        )
        discovery = scorer.score_from_result(
            task="Yeni batarya kimyasi kesfet",
            result="[MOCK] Swarm completed. Simulated discovery generated.",
            compute_share=0.4,
        )
        assert noop < discovery
        assert noop < 0.4
