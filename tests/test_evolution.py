# Tests for core/evolution.py - Genetic evolution engine

import pytest

from core.evolution import EvolutionEngine, AgentGenome


class TestAgentGenome:
    """Test individual genome creation and mutation."""

    def test_genome_creation(self):
        genome = AgentGenome(role="researcher")
        assert genome.role == "researcher"
        assert genome.generation == 0
        assert genome.fitness == 0.0

    def test_genome_default_prompt(self):
        genome = AgentGenome(role="coder")
        assert "coder" in genome.prompt_template

    def test_genome_custom_prompt(self):
        genome = AgentGenome(role="coder", prompt_template="Custom prompt")
        assert genome.prompt_template == "Custom prompt"

    def test_temperature_clamped(self):
        genome = AgentGenome(role="test", temperature=5.0)
        assert genome.temperature == 2.0
        genome2 = AgentGenome(role="test", temperature=-1.0)
        assert genome2.temperature == 0.0

    def test_mutate_returns_new_genome(self):
        parent = AgentGenome(role="researcher")
        child = parent.mutate(mutation_rate=1.0)  # Force mutation
        assert child.genome_id != parent.genome_id
        assert child.parent_id == parent.genome_id
        assert child.generation == parent.generation + 1

    def test_mutate_preserves_role(self):
        parent = AgentGenome(role="simulator")
        child = parent.mutate(mutation_rate=1.0)
        assert child.role == "simulator"

    def test_to_dict(self):
        genome = AgentGenome(role="researcher", skills=["search"])
        data = genome.to_dict()
        assert data["role"] == "researcher"
        assert data["skills"] == ["search"]
        assert "genome_id" in data


class TestEvolutionEngine:
    """Test population management and evolution."""

    def test_initialize_population(self):
        engine = EvolutionEngine(population_size=6)
        engine.initialize_population(roles=["a", "b", "c"])
        assert len(engine.population) == 6

    def test_evaluate_fitness(self):
        engine = EvolutionEngine()
        genome = AgentGenome(role="test")
        engine.evaluate_fitness(genome, 0.85)
        assert genome.fitness == 0.85

    def test_fitness_clamped(self):
        engine = EvolutionEngine()
        genome = AgentGenome(role="test")
        engine.evaluate_fitness(genome, 2.0)
        assert genome.fitness == 1.0
        engine.evaluate_fitness(genome, -0.5)
        assert genome.fitness == 0.0

    def test_select_elite(self):
        engine = EvolutionEngine(population_size=4, elite_ratio=0.5)
        engine.initialize_population(roles=["a"])
        for i, g in enumerate(engine.population):
            g.fitness = i * 0.25  # 0.0, 0.25, 0.50, 0.75
        elite = engine.select_elite()
        assert len(elite) == 2
        # Elite should have highest fitness
        assert elite[0].fitness >= elite[1].fitness

    def test_evolve_increments_generation(self):
        engine = EvolutionEngine(population_size=4)
        engine.initialize_population()
        for g in engine.population:
            g.fitness = 0.5
        engine.evolve()
        assert engine.generation == 1

    def test_evolve_maintains_population_size(self):
        engine = EvolutionEngine(population_size=6)
        engine.initialize_population()
        for g in engine.population:
            g.fitness = 0.5
        new_pop = engine.evolve()
        assert len(new_pop) == 6

    def test_evolve_empty_population(self):
        engine = EvolutionEngine()
        result = engine.evolve()
        assert result == []

    def test_get_best(self):
        engine = EvolutionEngine(population_size=3)
        engine.initialize_population(roles=["a"])
        engine.population[0].fitness = 0.3
        engine.population[1].fitness = 0.9
        engine.population[2].fitness = 0.6
        best = engine.get_best()
        assert best.fitness == 0.9

    def test_record_result(self):
        engine = EvolutionEngine()
        engine.record_result("task_1", "result_1")
        assert len(engine.history) == 1
        assert engine.history[0]["task"] == "task_1"

    def test_get_stats(self):
        engine = EvolutionEngine(population_size=3)
        engine.initialize_population()
        engine.population[0].fitness = 0.2
        engine.population[1].fitness = 0.8
        engine.population[2].fitness = 0.5
        stats = engine.get_stats()
        assert stats["population_size"] == 3
        assert stats["best_fitness"] == 0.8
        assert stats["worst_fitness"] == 0.2
        assert abs(stats["avg_fitness"] - 0.5) < 0.01

    def test_rollback_generation_restores_previous_snapshot(self):
        engine = EvolutionEngine(population_size=4)
        engine.initialize_population()
        for genome in engine.population:
            genome.fitness = 0.6
        engine.evolve()
        for genome in engine.population:
            genome.fitness = 0.7
        engine.evolve()
        assert engine.generation == 2

        rolled_back = engine.rollback_generation(1)
        assert rolled_back is True
        assert engine.generation == 1
        assert len(engine.population) == 4
