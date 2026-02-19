# OmniSwarm $OMNI Token Ledger v0.1 - 18 Subat 2026
# Local token accounting and royalty distribution
#
# Royalty split:
#   60% -> Discovery swarm (agents that made the discovery)
#   20% -> Node operators (compute contributors)
#   20% -> Development fund (protocol improvement)
#
# This is a local stub. On-chain integration (Solana / custom L2) planned for v0.3.

from typing import Optional


# Royalty distribution ratios (must sum to 1.0)
DISCOVERY_SHARE = 0.60
NODE_SHARE = 0.20
DEVELOPMENT_SHARE = 0.20
UNCLAIMED_RESERVE_ACCOUNT = "omni_unclaimed_reserve"


class OmniTokenLedger:
    """Local $OMNI token ledger for tracking balances and royalty distribution.

    All amounts use float with rounding guards.
    On-chain settlement is planned for future versions.
    """

    def __init__(self):
        self.balances: dict[str, float] = {}
        self.transactions: list[dict] = []
        self.total_distributed: float = 0.0

    def get_balance(self, account: str) -> float:
        """Get the $OMNI balance for an account."""
        return self.balances.get(account, 0.0)

    def credit(self, account: str, amount: float, reason: str = ""):
        """Credit $OMNI tokens to an account.

        Args:
            account: Account identifier (node_id or address).
            amount: Must be positive.
            reason: Description for the transaction log.

        Raises:
            ValueError: If amount is negative or zero.
        """
        if amount <= 0:
            raise ValueError(f"Credit amount must be positive, got {amount}")

        amount = round(amount, 8)  # Precision guard
        self.balances[account] = round(
            self.balances.get(account, 0.0) + amount, 8
        )
        self.transactions.append({
            "type": "credit",
            "account": account,
            "amount": amount,
            "reason": reason,
        })

    def debit(self, account: str, amount: float, reason: str = ""):
        """Debit $OMNI tokens from an account.

        Args:
            account: Account identifier.
            amount: Must be positive and <= current balance.
            reason: Description for the transaction log.

        Raises:
            ValueError: If amount is negative, zero, or exceeds balance.
        """
        if amount <= 0:
            raise ValueError(f"Debit amount must be positive, got {amount}")

        balance = self.balances.get(account, 0.0)
        if amount > balance:
            raise ValueError(
                f"Insufficient balance for {account}: "
                f"has {balance}, tried to debit {amount}"
            )

        amount = round(amount, 8)
        self.balances[account] = round(balance - amount, 8)
        self.transactions.append({
            "type": "debit",
            "account": account,
            "amount": amount,
            "reason": reason,
        })

    def distribute_royalty(
        self,
        task: str,
        total_amount: float,
        node_id: str,
        compute_share: float = 0.3,
        discovery_account: Optional[str] = None,
        dev_account: str = "omni_dev_fund",
        unclaimed_reserve_account: str = UNCLAIMED_RESERVE_ACCOUNT,
    ) -> dict:
        """Distribute royalty for a completed discovery.

        Splits total_amount according to the 60/20/20 formula and enforces
        token conservation. Any unassigned node share is sent to an
        unclaimed reserve pool.

        Args:
            task: Description of the discovery.
            total_amount: Total royalty pool (must be > 0).
            node_id: The node that contributed compute.
            compute_share: Fraction of compute this node contributed (0.0-1.0).
            discovery_account: Account for the discovery swarm (defaults to node_id).
            dev_account: Development fund account name.
            unclaimed_reserve_account: Account for undistributed node rewards.

        Returns:
            Dictionary with distribution breakdown.

        Raises:
            ValueError: If total_amount <= 0 or compute_share out of range.
        """
        if total_amount <= 0:
            raise ValueError(
                f"Royalty amount must be positive, got {total_amount}"
            )
        compute_share = max(0.0, min(1.0, compute_share))

        # Prevent division issues with zero compute share
        effective_compute = compute_share if compute_share > 0 else 0.0

        # Calculate shares
        discovery_amount = round(total_amount * DISCOVERY_SHARE, 8)
        node_amount = round(total_amount * NODE_SHARE * effective_compute, 8)
        dev_amount = round(total_amount * DEVELOPMENT_SHARE, 8)
        unclaimed_reserve = round(total_amount * NODE_SHARE - node_amount, 8)
        credited_total = round(
            discovery_amount + node_amount + dev_amount + unclaimed_reserve, 8
        )

        # Clamp tiny float artifact into reserve to preserve exact conservation.
        rounding_delta = round(total_amount - credited_total, 8)
        if rounding_delta != 0:
            unclaimed_reserve = round(unclaimed_reserve + rounding_delta, 8)
            credited_total = round(credited_total + rounding_delta, 8)

        # Credit accounts
        discovery_acct = discovery_account or node_id
        self.credit(discovery_acct, discovery_amount, f"Discovery: {task}")
        if node_amount > 0:
            self.credit(node_id, node_amount, f"Compute: {task}")
        self.credit(dev_account, dev_amount, f"Dev fund: {task}")
        if unclaimed_reserve > 0:
            self.credit(
                unclaimed_reserve_account,
                unclaimed_reserve,
                f"Unclaimed reserve: {task}",
            )

        self.total_distributed = round(
            self.total_distributed + credited_total,
            8,
        )

        return {
            "task": task,
            "total": total_amount,
            "credited_total": credited_total,
            "discovery_reward": discovery_amount,
            "node_reward": node_amount,
            "dev_fund": dev_amount,
            "unclaimed_reserve": unclaimed_reserve,
            "node_id": node_id,
            "compute_share": compute_share,
            "conserved": credited_total == round(total_amount, 8),
        }

    def get_stats(self) -> dict:
        """Return ledger statistics."""
        return {
            "total_accounts": len(self.balances),
            "total_distributed": self.total_distributed,
            "total_transactions": len(self.transactions),
        }

    def get_transactions(
        self, account: Optional[str] = None, limit: int = 50
    ) -> list[dict]:
        """Return transaction history, optionally filtered by account."""
        txs = self.transactions
        if account:
            txs = [t for t in txs if t.get("account") == account]
        return txs[-limit:]
