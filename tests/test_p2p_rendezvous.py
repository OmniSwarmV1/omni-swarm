import asyncio

import pytest

from core.p2p_discovery import P2PDiscovery
from core.rendezvous import InMemoryRendezvous


@pytest.mark.asyncio
async def test_rendezvous_bootstrap_discovers_three_nodes():
    rendezvous = InMemoryRendezvous(ttl_seconds=5.0)
    node_a = P2PDiscovery(
        node_id="node_a",
        enable_ipfs=False,
        rendezvous=rendezvous,
        heartbeat_interval=0.1,
    )
    node_b = P2PDiscovery(
        node_id="node_b",
        enable_ipfs=False,
        rendezvous=rendezvous,
        heartbeat_interval=0.1,
    )
    node_c = P2PDiscovery(
        node_id="node_c",
        enable_ipfs=False,
        rendezvous=rendezvous,
        heartbeat_interval=0.1,
    )

    await node_a.start()
    await node_b.start()
    await node_c.start()

    await asyncio.sleep(0.35)
    assert node_a.peer_count >= 2
    assert node_b.peer_count >= 2
    assert node_c.peer_count >= 2
    assert rendezvous.size() == 3

    await node_a.stop()
    await node_b.stop()
    await node_c.stop()


def test_rendezvous_cleans_stale_entries():
    rendezvous = InMemoryRendezvous(ttl_seconds=0.01)
    rendezvous.register("node_a", "local")
    rendezvous.register("node_b", "local")
    peers_initial = rendezvous.get_peers()
    assert len(peers_initial) == 2

    import time

    time.sleep(0.02)
    peers_after = rendezvous.get_peers()
    assert peers_after == []
