# Runbook: Node Bootstrap Failure

## Trigger

- Node cannot start or exits during `python -m core.node`.

## Quick Checks

1. Verify Python version and dependencies:
   - `python --version`
   - `pip install -r requirements.txt`
2. Confirm local write permissions for `.omni_sandbox/`.
3. Check telemetry log:
   - `.omni_sandbox/<node_id>/telemetry.jsonl`

## Recovery

1. Restart with local backend only:
   - `set OMNI_P2P_BACKEND=local` (Windows)
   - `export OMNI_P2P_BACKEND=local` (Unix)
2. Disable medium-risk actions:
   - ensure `OMNI_ALLOW_MEDIUM_RISK` is unset or `0`.
3. Retry node startup.

## Escalation

- If startup repeatedly fails across 3 retries, collect logs and open `incident/bootstrap-failure`.
