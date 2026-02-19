# Reward Dispute Policy (Pilot)

## Scope

Applies to disputes about contribution share, royalty distribution, and claim eligibility in the first-1000 pilot.

## Required Evidence

- Task identifier.
- Settlement snapshot hash.
- Signed receipt identifiers.
- Relevant telemetry excerpts.

## Resolution Flow

1. Verify conservation invariant for the disputed settlement.
2. Validate receipt signatures and replay protection status.
3. Recompute normalized contributions from stored records.
4. Publish decision with reproducible calculation steps.

## Outcomes

- Confirmed correct payout.
- Corrected payout with reconciliation transaction.
- Flagged suspicious behavior for temporary exclusion pending review.
