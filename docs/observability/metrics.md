# OmniSwarm v0.2 Observability Metrics

## Core Health Metrics

- `node_active`: 1 when node runtime is active, 0 otherwise.
- `p2p_alive_peers`: number of currently alive peers.
- `policy_block_count`: number of policy-denied task attempts.
- `telemetry_event_count`: total emitted telemetry events.

## Discovery and Evolution Metrics

- `swarm_completion_count`: completed swarm tasks.
- `swarm_failure_count`: failed swarm tasks.
- `evolution_generation`: current generation number.
- `evolution_total_tasks`: number of recorded swarm outcomes.
- `fitness_avg`: average fitness in current population.

## Security and Integrity Metrics

- `signature_failure_count`: invalid heartbeat/signature envelopes.
- `receipt_replay_rejections`: rejected replay attempts on token receipts.
- `token_conservation_pass`: boolean invariant check per settlement.
- `rendezvous_sync_failures`: failed rendezvous synchronization attempts.

## Operational SLO Targets (First-1000 Pilot)

- P2P peer discovery within 10 seconds for healthy nodes.
- Zero unhandled high-risk action execution.
- 100% token conservation invariant pass rate.
- Mean incident detection under 5 minutes.
