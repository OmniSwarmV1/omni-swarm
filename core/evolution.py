# OmniSwarm Evolution Engine v0.1 - 18 Şubat 2026
# Genetic algorithm-based agent self-improvement
#
# Each agent has a "genome" (prompt template + config).
# After a swarm completes, the engine:
#   1. Evaluates fitness of each agent's contribution
#   2. Selects top performers
#   3. Mutates their genomes (prompt variations)
#   4. Creates next generation

import random
import time
import uuid
from typing import Optional


class AgentGenome:
    """Represents the evolvable 'DNA' of an agent.

    Contains the prompt template, temperature, max_tokens,
    and a set of skills that define agent behavior.
    """

    def __init__(
        self,
        role: str,
        prompt_template: str = "",
        temperature: float = 0.7,
        skills: Optional[list[str]] = None,
        parent_id: Optional[str] = None,
    ):
        self.genome_id = f"genome_{uuid.uuid4().hex[:8]}"
        self.role = role
        self.prompt_template = prompt_template or f"You are a {role} agent."
        self.temperature = max(0.0, min(2.0, temperature))
        self.skills = list(skills) if skills else []
        self.parent_id = parent_id
        self.generation = 0
        self.fitness: float = 0.0
        self.created_at = time.time()

    def mutate(self, mutation_rate: float = 0.1) -> "AgentGenome":
        """Create a mutated copy of this genome.

        Args:
            mutation_rate: Probability of each parameter being mutated (0.0-1.0).

        Returns:
            A new AgentGenome with mutations applied.
        """
        mutation_rate = max(0.0, min(1.0, mutation_rate))

        child = AgentGenome(
            role=self.role,
            prompt_template=self.prompt_template,
            temperature=self.temperature,
            skills=list(self.skills),
            parent_id=self.genome_id,
        )
        child.generation = self.generation + 1

        # Mutate temperature
        if random.random() < mutation_rate:
            delta = random.uniform(-0.2, 0.2)
            child.temperature = max(0.0, min(2.0, self.temperature + delta))

        # Mutate prompt (append variation suffix)
        if random.random() < mutation_rate:
            suffixes = [
                " Focus on accuracy.",
                " Prioritize speed.",
                " Be creative and exploratory.",
                " Use systematic analysis.",
                " Consider edge cases.",
            ]
            child.prompt_template = self.prompt_template + random.choice(suffixes)

        # Mutate skills (add or remove one)
        if random.random() < mutation_rate and child.skills:
            if random.random() < 0.5:
                # Remove a random skill
                idx = random.randint(0, len(child.skills) - 1)
                child.skills.pop(idx)
            else:
                # Add a new skill
                new_skills = [
                    "deep_search", "code_review", "hypothesis_test",
                    "data_analysis", "patent_search", "summarize",
                ]
                child.skills.append(random.choice(new_skills))

        return child

    def to_dict(self) -> dict:
        return {
            "genome_id": self.genome_id,
            "role": self.role,
            "generation": self.generation,
            "temperature": self.temperature,
            "fitness": self.fitness,
            "skills": self.skills,
            "parent_id": self.parent_id,
        }


class EvolutionEngine:
    """Genetic evolution engine for agent self-improvement.

    Maintains a population of agent genomes, evaluates fitness,
    selects top performers, and breeds the next generation.
    """

    def __init__(
        self,
        population_size: int = 10,
        mutation_rate: float = 0.1,
        elite_ratio: float = 0.3,
    ):
        self.population_size = max(2, population_size)
        self.mutation_rate = max(0.0, min(1.0, mutation_rate))
        self.elite_ratio = max(0.1, min(0.9, elite_ratio))
        self.generation = 0
        self.population: list[AgentGenome] = []
        self.history: list[dict] = []

    def initialize_population(self, roles: Optional[list[str]] = None):
        """Create the initial population of agent genomes."""
        roles = roles or ["researcher", "coder", "simulator"]
        self.population = []
        for i in range(self.population_size):
            role = roles[i % len(roles)]
            genome = AgentGenome(role=role)
            genome.generation = 0
            self.population.append(genome)
        print(f"   [GEN] Population initialized: {self.population_size} genomes")

    def evaluate_fitness(self, genome: AgentGenome, score: float):
        """Set the fitness score for a genome.

        Args:
            genome: The genome to evaluate.
            score: Fitness score (0.0 to 1.0).
        """
        genome.fitness = max(0.0, min(1.0, score))

    def record_result(self, task: str, result: str):
        """Record a swarm result for evolutionary tracking."""
        self.history.append({
            "task": task,
            "result": result,
            "generation": self.generation,
            "timestamp": time.time(),
            "population_size": len(self.population),
        })

    def select_elite(self) -> list[AgentGenome]:
        """Select top-performing genomes based on fitness."""
        if not self.population:
            return []
        sorted_pop = sorted(
            self.population, key=lambda g: g.fitness, reverse=True
        )
        elite_count = max(1, int(len(sorted_pop) * self.elite_ratio))
        return sorted_pop[:elite_count]

    def evolve(self) -> list[AgentGenome]:
        """Run one generation of evolution.

        1. Select elite (top fitness)
        2. Mutate elite to fill population
        3. Increment generation counter

        Returns:
            The new generation population.
        """
        if not self.population:
            print("   [WARN] No population to evolve. Call initialize_population() first.")
            return []

        elite = self.select_elite()
        new_population: list[AgentGenome] = list(elite)  # Keep elites

        # Fill remaining slots with mutated offspring
        while len(new_population) < self.population_size:
            parent = random.choice(elite)
            child = parent.mutate(self.mutation_rate)
            new_population.append(child)

        self.population = new_population
        self.generation += 1

        avg_fitness = (
            sum(g.fitness for g in self.population) / len(self.population)
            if self.population
            else 0.0
        )
        print(
            f"   [GEN] Generation {self.generation} | "
            f"Pop: {len(self.population)} | "
            f"Avg fitness: {avg_fitness:.3f}"
        )
        return self.population

    def get_best(self) -> Optional[AgentGenome]:
        """Return the genome with highest fitness."""
        if not self.population:
            return None
        return max(self.population, key=lambda g: g.fitness)

    def get_stats(self) -> dict:
        """Return evolution statistics."""
        fitnesses = [g.fitness for g in self.population] if self.population else [0.0]
        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "best_fitness": max(fitnesses),
            "worst_fitness": min(fitnesses),
            "total_tasks": len(self.history),
        }
