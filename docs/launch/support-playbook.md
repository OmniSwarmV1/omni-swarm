# First-1000 Support Playbook

## Triage Priorities

1. `sev1-security`: policy bypass, unauthorized action, credential leakage.
2. `sev1-integrity`: token conservation failure, replay acceptance.
3. `sev2-network`: widespread peer discovery or heartbeat degradation.
4. `sev3-ux`: install/startup friction, non-critical runtime issues.

## Incident Flow

1. Acknowledge within 15 minutes.
2. Attach diagnostics bundle from affected node (`export_diagnostics` output).
3. Reproduce on canary sandbox.
4. Apply patch behind safety gate and rerun go/no-go checks.
5. Publish post-incident summary in runbook format.

## Operator Checklist

- Confirm `OMNI_KILL_SWITCH` state.
- Confirm `OMNI_ALLOW_MEDIUM_RISK` not unintentionally enabled.
- Review `telemetry.jsonl` for `policy_blocked`, `sybil_blocked`, `verification_penalty_applied`.
- Verify settlement hash for impacted time window.
