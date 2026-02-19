# Runbook: Network Partition / Discovery Failure

## Trigger

- Nodes fail to discover peers within expected SLA.
- `peer_count` remains 0 unexpectedly.

## Diagnostics

1. Check backend mode in logs (`ipfs` vs `local`).
2. Validate rendezvous availability (if configured).
3. Inspect signature failures in node stats.

## Recovery

1. Force fallback path and confirm local operation.
2. Restart affected nodes to re-register heartbeats.
3. Reduce `heartbeat_interval` temporarily for faster convergence.

## Validation

- Start 3 nodes and confirm each reports `peer_count >= 2`.
- Confirm discovery completed in <= 10 seconds for healthy signaling path.
