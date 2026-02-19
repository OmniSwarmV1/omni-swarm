"""TESTNET ONLY - Dummy claimable contract behavior.

This is a local simulation helper, not a real on-chain program.
Use for integration validation of snapshot -> claim flow.
"""

from __future__ import annotations


class TestnetDummyClaimContract:
    """In-memory claim tracker for snapshot-based token claims."""

    def __init__(self, snapshot: dict[str, float]):
        self.snapshot = dict(snapshot)
        self.claimed: set[str] = set()

    def can_claim(self, wallet: str) -> bool:
        return wallet in self.snapshot and wallet not in self.claimed

    def claim(self, wallet: str) -> dict:
        if wallet not in self.snapshot:
            raise ValueError("wallet not in snapshot")
        if wallet in self.claimed:
            raise ValueError("wallet already claimed")

        amount = float(self.snapshot[wallet])
        self.claimed.add(wallet)
        return {
            "wallet": wallet,
            "amount": amount,
            "status": "CLAIMED_TESTNET_DUMMY",
        }
