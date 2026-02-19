# OmniSwarm Local Core v0.1 - 18 Şubat 2026
# First Collective Super-Intelligence Operating System
#
# Modes:
#   mock (default) - No API key needed, simulated pipeline
#   simulated_graph - LangGraph pipeline simulation
#
# Real LLM integration is planned for v1.1 (Opus 4.6 + tool calling).

import asyncio
import os
import uuid
from typing import TypedDict, List, Optional

from core.swarm_engine import SwarmEngine
from core.p2p_discovery import P2PDiscovery
from core.evolution import EvolutionEngine
from omni_token.omni_token import OmniTokenLedger


class SwarmState(TypedDict):
    messages: List[str]
    active_agents: List[str]
    task: str
    result: Optional[str]


class OmniNode:
    """Local node that runs on every device in the OmniSwarm network.

    Each node manages local agents, joins swarms, contributes compute,
    and earns $OMNI token rewards for successful discoveries.
    """

    def __init__(
        self,
        device_id: Optional[str] = None,
        compute_share: float = 0.3,
    ):
        self.node_id = device_id or str(uuid.uuid4())
        self.compute_share = max(0.0, min(1.0, compute_share))
        self.active = False
        self.mode = os.environ.get("OMNI_MODE", "mock").lower()
        if self.mode == "real":
            self.mode = "simulated_graph"

        # Sub-engines
        self.p2p = P2PDiscovery(self.node_id)
        self.swarm_engine = SwarmEngine(self.node_id)
        self.evolution = EvolutionEngine()
        self.ledger = OmniTokenLedger()

        # Lazy simulated-graph imports (only when needed)
        self._langgraph_loaded = False

        print(f"[OK] OmniSwarm Node baslatildi -> ID: {self.node_id}")
        print(f"   Mode: {self.mode} | Compute share: {self.compute_share:.0%}")

    def _load_simulated_graph_mode(self):
        """Lazy-load LangGraph imports for simulated graph mode."""
        if self._langgraph_loaded:
            return True
        try:
            from langgraph.graph import StateGraph, END  # noqa: F401

            self._langgraph_loaded = True
            return True
        except ImportError as exc:
            print(f"[WARN] simulated_graph mode requires langgraph: {exc}")
            print("   Falling back to mock mode.")
            self.mode = "mock"
            return False

    async def start(self):
        """Boot the node: activate P2P discovery and join the swarm network."""
        self.active = True
        print("[NET] P2P discovery basladi... (IPFS + Tor simule)")
        await self.p2p.start()
        if not self.evolution.population:
            self.evolution.initialize_population(
                roles=["researcher", "coder", "simulator"]
            )
        print("[LINK] Swarm agina baglanildi. Komut bekleniyor.")

    async def stop(self):
        """Gracefully shut down the node."""
        self.active = False
        await self.p2p.stop()
        print(f"[STOP] Node {self.node_id} durduruldu.")

    async def create_swarm(self, task: str) -> dict:
        """Create and execute a swarm for the given task.

        In mock mode, runs a simulated research → code → simulate pipeline.
        In simulated_graph mode, runs a LangGraph pipeline simulation.
        """
        if not self.active:
            raise RuntimeError("Node is not active. Call start() first.")

        print(f"[SWARM] Yeni swarm olusturuluyor: {task}")

        if self.mode == "simulated_graph":
            result = await self._run_simulated_graph_swarm(task)
        else:
            result = await self._run_mock_swarm(task)

        # Evolution: evaluate and improve agents
        self.evolution.record_result(task, result)
        self._run_evolution_cycle(task, result)

        # Royalty distribution
        royalty = self.ledger.distribute_royalty(
            task=task,
            total_amount=1250.0,
            node_id=self.node_id,
            compute_share=self.compute_share,
        )

        discovery = {
            "task": task,
            "swarm_result": result,
            "royalty_pool": royalty["total"],
            "node_reward": royalty["node_reward"],
            "status": "COMPLETED",
        }
        print("[DONE] Swarm tamamlandi! Royalty hazir.")
        return discovery

    def _score_swarm_result(self, task: str, result: str) -> float:
        """Derive a bounded fitness score for one completed swarm."""
        result_text = (result or "").lower()
        task_text = (task or "").lower()

        score = 0.40
        if "completed" in result_text:
            score += 0.20
        if "simulated discovery" in result_text:
            score += 0.15
        if any(word in task_text for word in ["optimiz", "kesfet", "patent", "discover"]):
            score += 0.10

        return max(0.0, min(1.0, round(score, 3)))

    def _run_evolution_cycle(self, task: str, result: str):
        """Evaluate current genomes and evolve to next generation."""
        if not self.evolution.population:
            self.evolution.initialize_population(
                roles=["researcher", "coder", "simulator"]
            )

        base_score = self._score_swarm_result(task, result)
        role_bonus = {
            "researcher": 0.05,
            "coder": 0.03,
            "simulator": 0.02,
        }

        for genome in self.evolution.population:
            score = base_score + role_bonus.get(genome.role, 0.0)
            self.evolution.evaluate_fitness(genome, score)

        self.evolution.evolve()
        best = self.evolution.get_best()
        if best is not None:
            print(
                "   [EVO] Generation "
                f"{self.evolution.generation} | "
                f"Best role: {best.role} | "
                f"Fitness: {best.fitness:.3f}"
            )

    async def _run_mock_swarm(self, task: str) -> str:
        """Simulated swarm pipeline – no API key required."""
        agents = ["researcher", "coder", "simulator"]

        for agent_name in agents:
            print(f"   [AGENT] [{agent_name}] calisiyor...")
            await asyncio.sleep(0.3)

        # Create a swarm via the engine
        swarm_id = self.swarm_engine.create_swarm(task, agents)
        self.swarm_engine.complete_swarm(swarm_id)

        return (
            f"[MOCK] Swarm completed for: {task}. "
            f"Agents: {', '.join(agents)}. "
            f"Simulated discovery generated."
        )

    async def _run_simulated_graph_swarm(self, task: str) -> str:
        """LangGraph-based swarm simulation (no real LLM tool-calling yet)."""
        if not self._load_simulated_graph_mode():
            return await self._run_mock_swarm(task)

        # Simulated graph execution (real LLM integration planned for v1.1).
        from langgraph.graph import StateGraph, END

        graph = StateGraph(SwarmState)

        async def research_node(state: SwarmState) -> dict:
            return {
                "messages": state["messages"] + [f"[research] Analyzed: {task}"],
                "active_agents": state["active_agents"] + ["researcher"],
            }

        async def code_node(state: SwarmState) -> dict:
            return {
                "messages": state["messages"] + [f"[code] Generated solution for: {task}"],
                "active_agents": state["active_agents"] + ["coder"],
            }

        async def simulate_node(state: SwarmState) -> dict:
            return {
                "messages": state["messages"] + [f"[simulate] Validated: {task}"],
                "active_agents": state["active_agents"] + ["simulator"],
                "result": f"Discovery for: {task}",
            }

        graph.add_node("research", research_node)
        graph.add_node("code", code_node)
        graph.add_node("simulate", simulate_node)

        graph.set_entry_point("research")
        graph.add_edge("research", "code")
        graph.add_edge("code", "simulate")
        graph.add_edge("simulate", END)

        app = graph.compile()
        result = await app.ainvoke(
            {
                "messages": [task],
                "active_agents": [],
                "task": task,
                "result": None,
            }
        )
        return result.get("result", "No result")


async def main():
    node = OmniNode(device_id="kadir_test_001", compute_share=0.4)
    await node.start()

    # Test task - discovery simulation
    result = await node.create_swarm(
        "Yeni 600Wh/kg batarya kimyası keşfet ve patent öner"
    )
    print()
    print("[RESULT] Sonuc:")
    for key, value in result.items():
        print(f"   {key}: {value}")

    await node.stop()


if __name__ == "__main__":
    asyncio.run(main())
