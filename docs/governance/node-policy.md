# Node Policy (v0.2 Pilot)

## Allowed by Default

- Local swarm simulation tasks.
- Signed heartbeat exchange.
- Local telemetry write under node sandbox.
- Royalty accounting with signed receipts.

## Explicitly Blocked

- Arbitrary host command execution.
- Access outside `.omni_sandbox/<node_id>/`.
- High-risk tasks flagged by policy engine.
- Unallowlisted tool/action invocation.

## Medium-Risk Actions

- Disabled by default.
- Require explicit operator opt-in (`OMNI_ALLOW_MEDIUM_RISK=1`).

## Enforcement Model

- Deny-by-default policy gate.
- Audit trail through telemetry and receipt logs.
- Emergency kill switch can block swarm creation.
