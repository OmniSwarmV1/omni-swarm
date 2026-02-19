from pathlib import Path

import pytest

from omni_token.omni_token import OmniTokenLedger
from omni_token.settlement_snapshot import generate_settlement_snapshot


class TestSignedReceipts:
    def test_signed_receipt_verification_and_apply(self):
        ledger = OmniTokenLedger()
        receipt = ledger.create_signed_receipt(
            account="node_a",
            amount=12.5,
            reason="test-credit",
            task="task_1",
        )
        assert ledger.verify_signed_receipt(receipt) is True
        ledger.apply_signed_receipt(receipt)
        assert ledger.get_balance("node_a") == 12.5
        assert len(ledger.receipts) == 1

    def test_receipt_replay_is_blocked(self):
        ledger = OmniTokenLedger()
        receipt = ledger.create_signed_receipt(
            account="node_a",
            amount=10.0,
            reason="test-credit",
            task="task_2",
        )
        ledger.apply_signed_receipt(receipt)
        with pytest.raises(ValueError, match="replay"):
            ledger.apply_signed_receipt(receipt)

    def test_tampered_receipt_is_rejected(self):
        ledger = OmniTokenLedger()
        receipt = ledger.create_signed_receipt(
            account="node_a",
            amount=5.0,
            reason="test-credit",
            task="task_3",
        )
        receipt["payload"]["amount"] = 5000.0
        assert ledger.verify_signed_receipt(receipt) is False
        with pytest.raises(ValueError, match="Invalid signed receipt"):
            ledger.apply_signed_receipt(receipt)


class TestSettlementSnapshot:
    def test_snapshot_hash_deterministic_for_same_state(self, tmp_path: Path):
        ledger = OmniTokenLedger()
        ledger.distribute_royalty(
            task="snapshot-task",
            total_amount=1000.0,
            node_id="node_1",
            compute_share=0.5,
        )

        first = generate_settlement_snapshot(ledger, tmp_path / "snapshot_a.json")
        second = generate_settlement_snapshot(ledger, tmp_path / "snapshot_b.json")
        assert first["hash"] == second["hash"]
        assert Path(first["path"]).exists()
        assert Path(second["path"]).exists()
