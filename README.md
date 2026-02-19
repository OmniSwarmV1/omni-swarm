# OmniSwarm

**The first AI collective super-intelligence.**  
February 18, 2026

Local nodes running on every device -> dynamic swarms -> exploration simulation -> royalty distribution.

Goal: 1 million nodes by the end of 2026, one new discovery per week.

## Quick Start

```bash
pip install -r requirements.txt
python -m core.node
```

When the first node runs, it automatically joins the $OMNI airdrop pool.

## Runtime Modes

- `mock` (default): Fully local simulation.
- `simulated_graph`: LangGraph-based simulation flow.

Note: Real LLM integration is planned for v1.1.

## P2P Note

The IPFS pubsub adapter uses `ipfshttpclient`. This client currently works more stably with older daemon series
(verification test performed with go-ipfs v0.7.x).

## v0.2 Safety Foundations

- Deny-by-default policy engine for task/action gating.
- Per-node sandbox rooted under `.omni_sandbox/<node_id>`.
- Telemetry logging for policy decisions and swarm outcomes.
- Signed token receipts with replay protection.
- Deterministic settlement snapshot support.

## Pilot Operations Docs

- Metrics: `docs/observability/metrics.md`
- Runbooks: `docs/runbooks/`
- Launch plan: `docs/launch/first-1000-cohort.md`
- Governance: `docs/governance/`

## Claim Link for the First 1000 Nodes

- Claim portal (testnet dummy): `https://claim.omniswarm.local/testnet/v0.1`
- Snapshot file: `token/airdrop_snapshot.json`
- Claim flow documentation: `token/claim_flow.md`
