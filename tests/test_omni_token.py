# Tests for omni_token/omni_token.py - $OMNI token ledger

import pytest

from omni_token.omni_token import (
    OmniTokenLedger,
    DISCOVERY_SHARE,
    NODE_SHARE,
    DEVELOPMENT_SHARE,
)


class TestTokenShares:
    """Validate the royalty split constants."""

    def test_shares_sum_to_one(self):
        total = DISCOVERY_SHARE + NODE_SHARE + DEVELOPMENT_SHARE
        assert abs(total - 1.0) < 1e-9

    def test_share_values(self):
        assert DISCOVERY_SHARE == 0.60
        assert NODE_SHARE == 0.20
        assert DEVELOPMENT_SHARE == 0.20


class TestLedgerCredit:
    """Test credit operations with guard checks."""

    def test_credit_positive(self):
        ledger = OmniTokenLedger()
        ledger.credit("alice", 100.0, "test")
        assert ledger.get_balance("alice") == 100.0

    def test_credit_accumulates(self):
        ledger = OmniTokenLedger()
        ledger.credit("alice", 50.0)
        ledger.credit("alice", 30.0)
        assert ledger.get_balance("alice") == 80.0

    def test_credit_negative_raises(self):
        ledger = OmniTokenLedger()
        with pytest.raises(ValueError, match="must be positive"):
            ledger.credit("alice", -10.0)

    def test_credit_zero_raises(self):
        ledger = OmniTokenLedger()
        with pytest.raises(ValueError, match="must be positive"):
            ledger.credit("alice", 0.0)

    def test_unknown_account_balance_is_zero(self):
        ledger = OmniTokenLedger()
        assert ledger.get_balance("nobody") == 0.0


class TestLedgerDebit:
    """Test debit operations with guard checks."""

    def test_debit_positive(self):
        ledger = OmniTokenLedger()
        ledger.credit("alice", 100.0)
        ledger.debit("alice", 40.0)
        assert ledger.get_balance("alice") == 60.0

    def test_debit_negative_raises(self):
        ledger = OmniTokenLedger()
        with pytest.raises(ValueError, match="must be positive"):
            ledger.debit("alice", -5.0)

    def test_debit_zero_raises(self):
        ledger = OmniTokenLedger()
        with pytest.raises(ValueError, match="must be positive"):
            ledger.debit("alice", 0.0)

    def test_debit_exceeds_balance_raises(self):
        ledger = OmniTokenLedger()
        ledger.credit("alice", 50.0)
        with pytest.raises(ValueError, match="Insufficient balance"):
            ledger.debit("alice", 100.0)

    def test_debit_empty_account_raises(self):
        ledger = OmniTokenLedger()
        with pytest.raises(ValueError, match="Insufficient balance"):
            ledger.debit("nobody", 10.0)


class TestRoyaltyDistribution:
    """Test the 60/20/20 royalty distribution with edge cases."""

    def test_standard_distribution(self):
        ledger = OmniTokenLedger()
        result = ledger.distribute_royalty(
            task="test_task",
            total_amount=1000.0,
            node_id="node_001",
            compute_share=1.0,
        )
        assert result["discovery_reward"] == 600.0
        assert result["node_reward"] == 200.0
        assert result["dev_fund"] == 200.0

    def test_partial_compute_share(self):
        ledger = OmniTokenLedger()
        result = ledger.distribute_royalty(
            task="test_task",
            total_amount=1000.0,
            node_id="node_001",
            compute_share=0.5,
        )
        assert result["node_reward"] == 100.0  # 20% * 50%

    def test_zero_compute_share(self):
        ledger = OmniTokenLedger()
        result = ledger.distribute_royalty(
            task="test_task",
            total_amount=1000.0,
            node_id="node_001",
            compute_share=0.0,
        )
        assert result["node_reward"] == 0.0
        # Discovery and dev fund still credited
        assert result["discovery_reward"] == 600.0
        assert result["dev_fund"] == 200.0

    def test_negative_amount_raises(self):
        ledger = OmniTokenLedger()
        with pytest.raises(ValueError, match="must be positive"):
            ledger.distribute_royalty(
                task="bad", total_amount=-100.0, node_id="node_001"
            )

    def test_zero_amount_raises(self):
        ledger = OmniTokenLedger()
        with pytest.raises(ValueError, match="must be positive"):
            ledger.distribute_royalty(
                task="bad", total_amount=0.0, node_id="node_001"
            )

    def test_rounding_precision(self):
        ledger = OmniTokenLedger()
        result = ledger.distribute_royalty(
            task="precision_test",
            total_amount=333.33,
            node_id="node_001",
            compute_share=0.33,
        )
        # Verify no floating point artifacts beyond 8 decimals
        assert result["discovery_reward"] == round(333.33 * 0.60, 8)
        assert result["node_reward"] == round(333.33 * 0.20 * 0.33, 8)
        assert result["dev_fund"] == round(333.33 * 0.20, 8)


class TestLedgerStats:
    """Test ledger statistics and transaction history."""

    def test_initial_stats(self):
        ledger = OmniTokenLedger()
        stats = ledger.get_stats()
        assert stats["total_accounts"] == 0
        assert stats["total_distributed"] == 0.0

    def test_transactions_logged(self):
        ledger = OmniTokenLedger()
        ledger.credit("alice", 100.0, "grant")
        txs = ledger.get_transactions(account="alice")
        assert len(txs) == 1
        assert txs[0]["type"] == "credit"
        assert txs[0]["amount"] == 100.0

    def test_transactions_filtered_by_account(self):
        ledger = OmniTokenLedger()
        ledger.credit("alice", 100.0)
        ledger.credit("bob", 200.0)
        txs = ledger.get_transactions(account="alice")
        assert len(txs) == 1
        assert all(t["account"] == "alice" for t in txs)
