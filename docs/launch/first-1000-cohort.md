# First-1000 Node Launch Program

## Objective

Run a controlled rollout from canary to 1000 nodes without Sev-1 safety or accounting incidents.

## Cohort Gates

## Phase 1 - Canary (100 Nodes)

Entry criteria:
- P6-P10 checks complete.
- Full test suite green.

Exit criteria:
- 7 consecutive days with no Sev-1 incident.
- Token conservation invariant stays green.
- Discovery success rate remains stable.

## Phase 2 - Expanded Beta (300 Nodes)

Entry criteria:
- Canary exit criteria met.

Exit criteria:
- Median onboarding time within target.
- Policy-block false positive rate acceptable.
- Signature failure trend stable.

## Phase 3 - Public Pilot (1000 Nodes)

Entry criteria:
- Expanded beta exit criteria met.
- Runbook drill executed.

Exit criteria:
- Operational SLOs hold for 14 days.
- Governance and dispute process validated with real cases.

## Required Launch Artifacts

- Binary artifacts for Windows/macOS/Linux.
- Onboarding checklist for node operators.
- Incident escalation channels.
- Reward and claim documentation.
