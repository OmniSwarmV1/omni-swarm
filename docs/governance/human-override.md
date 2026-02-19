# Human Override and Safety Veto

## Principle

Automation is bounded by operator authority. High-risk actions are never auto-executed in pilot mode.

## Override Controls

- `OMNI_KILL_SWITCH=1` blocks swarm execution.
- Medium-risk intents remain blocked unless explicitly enabled.
- Operators can stop nodes at any time and review telemetry before restart.

## When to Trigger Override

- Unexpected policy bypass behavior.
- Repeated signature validation anomalies.
- Settlement mismatch or receipt replay anomaly.
- Suspicious task intents from remote peers.

## Post-Override Checklist

1. Capture telemetry and incident context.
2. Run focused regression tests.
3. Apply patch and verify in canary.
4. Resume only after safety owner approval.
