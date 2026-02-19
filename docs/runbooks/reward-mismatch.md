# Runbook: Reward Mismatch / Settlement Integrity

## Trigger

- Royalty distribution appears inconsistent.
- Conservation check fails in tests or runtime assertion.

## Diagnostics

1. Recompute expected split (60/20/20).
2. Check `unclaimed_reserve` handling and rounding deltas.
3. Verify signed receipts and replay rejections.
4. Generate deterministic settlement snapshot and compare hash.

## Recovery

1. Halt new payouts (enable emergency kill switch for payout path).
2. Regenerate settlement snapshot from ledger state.
3. Reconcile balances against receipt log.
4. Resume payouts only after invariant passes.

## Validation Command

- `pytest -q tests/test_omni_token.py tests/test_settlement_integrity.py`
