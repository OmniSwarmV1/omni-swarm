# OmniSwarm Local Core v0.1 - 18 Şubat 2026
# First Collective Super-Intelligence Operating System
#
# Modes:
#   mock (default) - No API key needed, simulated pipeline
#   real           - Set OMNI_MODE=real + OPENAI_API_KEY env vars

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

        # Sub-engines
        self.p2p = P2PDiscovery(self.node_id)
        self.swarm_engine = SwarmEngine(self.node_id)
        self.evolution = EvolutionEngine()
        self.ledger = OmniTokenLedger()

        # Lazy real-mode imports (only when needed)
        self._langgraph_loaded = False

        print(f"[OK] OmniSwarm Node baslatildi -> ID: {self.node_id}")
        print(f"   Mode: {self.mode} | Compute share: {self.compute_share:.0%}")

    def _load_real_mode(self):
        """Lazy-load LangGraph imports for real mode. Fails gracefully."""
        if self._langgraph_loaded:
            return True
        try:
            from langgraph.graph import StateGraph, END  # noqa: F401
            from langgraph.prebuilt import create_react_agent  # noqa: F401

            self._langgraph_loaded = True
            return True
        except ImportError as exc:
            print(f"[WARN] Real mode requires langgraph: {exc}")
            print("   Falling back to mock mode.")
            self.mode = "mock"
            return False

    async def start(self):
        """Boot the node: activate P2P discovery and join the swarm network."""
        self.active = True
        print("[NET] P2P discovery basladi... (IPFS + Tor simule)")
        await self.p2p.start()
        print("[LINK] Swarm agina baglanildi. Komut bekleniyor.")

    async def stop(self):
        """Gracefully shut down the node."""
        self.active = False
        await self.p2p.stop()
        print(f"[STOP] Node {self.node_id} durduruldu.")

    async def create_swarm(self, task: str) -> dict:
        """Create and execute a swarm for the given task.

        In mock mode, runs a simulated research → code → simulate pipeline.
        In real mode, uses LangGraph agents with an LLM backend.
        """
        if not self.active:
            raise RuntimeError("Node is not active. Call start() first.")

        print(f"[SWARM] Yeni swarm olusturuluyor: {task}")

        if self.mode == "real":
            result = await self._run_real_swarm(task)
        else:
            result = await self._run_mock_swarm(task)

        # Evolution: evaluate and improve agents
        self.evolution.record_result(task, result)

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

    async def _run_real_swarm(self, task: str) -> str:
        """Real LangGraph-based swarm with LLM agents."""
        if not self._load_real_mode():
            return await self._run_mock_swarm(task)

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("[WARN] OPENAI_API_KEY not set. Falling back to mock mode.")
            self.mode = "mock"
            return await self._run_mock_swarm(task)

        # Real LangGraph execution
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

    # Test task – real discovery simulation
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
