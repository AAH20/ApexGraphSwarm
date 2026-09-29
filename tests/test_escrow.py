"""Tests for the 3-party escrow system."""
import unittest

from kernels.escrow import (
    AIJudge,
    AssetType,
    DisputeStatus,
    EscrowContract,
    EscrowError,
    EscrowStatus,
    JudgeError,
    MilestoneStatus,
    MockSettlementAdapter,
    SettlementError,
)


class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class EscrowCreationTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)

    def test_create_escrow_with_single_milestone(self):
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Build the thing", "amount": 1000}],
        )
        self.assertEqual(state.status, EscrowStatus.PENDING)
        self.assertEqual(state.total_amount, 1000)
        self.assertEqual(len(state.milestones), 1)
        self.assertEqual(state.milestones[0].status, MilestoneStatus.PENDING)

    def test_create_escrow_with_multiple_milestones(self):
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=3000,
            milestones=[
                {"description": "Phase 1", "amount": 1000},
                {"description": "Phase 2", "amount": 1000},
                {"description": "Phase 3", "amount": 1000},
            ],
        )
        self.assertEqual(len(state.milestones), 3)
        self.assertEqual(state.total_amount, 3000)

    def test_create_escrow_with_erc20(self):
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ERC20,
            token_address="0xToken",
            total_amount=5000,
            milestones=[{"description": "Work", "amount": 5000}],
        )
        self.assertEqual(state.asset_type, AssetType.ERC20)
        self.assertEqual(state.token_address, "0xToken")

    def test_reject_same_requester_and_worker(self):
        with self.assertRaises(EscrowError):
            self.contract.create_escrow(
                requester_address="0xSame",
                worker_address="0xSame",
                judge_address="0xJudge",
                asset_type=AssetType.ETH,
                total_amount=100,
                milestones=[{"description": "Work", "amount": 100}],
            )

    def test_reject_judge_same_as_party(self):
        with self.assertRaises(EscrowError):
            self.contract.create_escrow(
                requester_address="0xRequester",
                worker_address="0xWorker",
                judge_address="0xRequester",
                asset_type=AssetType.ETH,
                total_amount=100,
                milestones=[{"description": "Work", "amount": 100}],
            )

    def test_reject_milestone_sum_mismatch(self):
        with self.assertRaises(EscrowError):
            self.contract.create_escrow(
                requester_address="0xRequester",
                worker_address="0xWorker",
                judge_address="0xJudge",
                asset_type=AssetType.ETH,
                total_amount=1000,
                milestones=[
                    {"description": "Phase 1", "amount": 600},
                    {"description": "Phase 2", "amount": 300},
                ],
            )

    def test_reject_zero_amount(self):
        with self.assertRaises(EscrowError):
            self.contract.create_escrow(
                requester_address="0xRequester",
                worker_address="0xWorker",
                judge_address="0xJudge",
                asset_type=AssetType.ETH,
                total_amount=0,
                milestones=[{"description": "Work", "amount": 0}],
            )

    def test_reject_no_milestones(self):
        with self.assertRaises(EscrowError):
            self.contract.create_escrow(
                requester_address="0xRequester",
                worker_address="0xWorker",
                judge_address="0xJudge",
                asset_type=AssetType.ETH,
                total_amount=100,
                milestones=[],
            )


class EscrowFundingTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)
        self.state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )

    def test_fund_transitions_to_funded(self):
        state = self.contract.fund(self.state.escrow_id, 1000)
        self.assertEqual(state.status, EscrowStatus.FUNDED)
        self.assertIsNotNone(state.funded_at)

    def test_fund_wrong_amount_rejected(self):
        with self.assertRaises(EscrowError):
            self.contract.fund(self.state.escrow_id, 500)

    def test_fund_already_funded_rejected(self):
        self.contract.fund(self.state.escrow_id, 1000)
        with self.assertRaises(EscrowError):
            self.contract.fund(self.state.escrow_id, 1000)


class MilestoneLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)
        self.state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=2000,
            milestones=[
                {"description": "Phase 1", "amount": 1000},
                {"description": "Phase 2", "amount": 1000},
            ],
        )
        self.contract.fund(self.state.escrow_id, 2000)

    def test_start_milestone(self):
        state = self.contract.start_milestone(self.state.escrow_id, 0)
        self.assertEqual(state.status, EscrowStatus.IN_PROGRESS)
        self.assertEqual(state.milestones[0].status, MilestoneStatus.IN_PROGRESS)

    def test_deliver_milestone(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        state = self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")
        self.assertEqual(state.milestones[0].status, MilestoneStatus.DELIVERED)
        self.assertEqual(state.milestones[0].deliverable_hash, "0xabc123")
        # Not all delivered yet
        self.assertEqual(state.status, EscrowStatus.IN_PROGRESS)

    def test_deliver_all_milestones_transitions_to_delivered(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")
        self.contract.start_milestone(self.state.escrow_id, 1)
        state = self.contract.deliver_milestone(self.state.escrow_id, 1, "0xdef456")
        self.assertEqual(state.status, EscrowStatus.DELIVERED)

    def test_approve_milestone(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")
        state = self.contract.approve_milestone(self.state.escrow_id, 0)
        self.assertEqual(state.milestones[0].status, MilestoneStatus.APPROVED)
        self.assertIsNotNone(state.milestones[0].approved_at)

    def test_approve_all_milestones_resolves_escrow(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")
        self.contract.start_milestone(self.state.escrow_id, 1)
        self.contract.deliver_milestone(self.state.escrow_id, 1, "0xdef456")
        self.contract.approve_milestone(self.state.escrow_id, 0)
        state = self.contract.approve_milestone(self.state.escrow_id, 1)
        self.assertEqual(state.status, EscrowStatus.RESOLVED)
        self.assertIsNotNone(state.resolved_at)

    def test_reject_milestone(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")
        state = self.contract.reject_milestone(self.state.escrow_id, 0, "Does not meet spec")
        self.assertEqual(state.milestones[0].status, MilestoneStatus.REJECTED)

    def test_cannot_deliver_without_starting(self):
        with self.assertRaises(EscrowError):
            self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")

    def test_cannot_approve_without_delivery(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        with self.assertRaises(EscrowError):
            self.contract.approve_milestone(self.state.escrow_id, 0)


class DisputeTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)
        self.state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )
        self.contract.fund(self.state.escrow_id, 1000)
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")

    def test_raise_dispute_by_requester(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is unsatisfactory"
        )
        self.assertEqual(dispute.status, DisputeStatus.OPEN)
        state = self.contract.get_escrow(self.state.escrow_id)
        self.assertEqual(state.status, EscrowStatus.DISPUTED)
        self.assertEqual(state.milestones[0].status, MilestoneStatus.DISPUTED)

    def test_raise_dispute_by_worker(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, None, "0xWorker", "Requester won't approve"
        )
        self.assertEqual(dispute.milestone_index, None)

    def test_reject_dispute_by_non_party(self):
        with self.assertRaises(EscrowError):
            self.contract.raise_dispute(
                self.state.escrow_id, 0, "0xStranger", "I don't like it"
            )

    def test_submit_evidence(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        updated = self.contract.submit_evidence(
            dispute.dispute_id,
            "0xWorker",
            {"deliverableHash": "0xabc123", "proofOfWork": "0xproof"},
        )
        self.assertEqual(len(updated.evidence), 1)
        self.assertEqual(updated.evidence[0]["submitter"], "0xWorker")

    def test_start_judging(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xWorker", {"proofOfWork": "0xproof"}
        )
        updated = self.contract.start_judging(dispute.dispute_id, "0xJudge")
        self.assertEqual(updated.status, DisputeStatus.JUDGING)

    def test_resolve_dispute_pay_worker(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xWorker", {"deliverableHash": "0xabc123", "proofOfWork": "0xproof"}
        )
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        state = self.contract.resolve_dispute(
            dispute.dispute_id, "0xJudge", "Worker delivered satisfactory work", True, 0
        )
        self.assertEqual(state.milestones[0].status, MilestoneStatus.APPROVED)
        self.assertEqual(state.status, EscrowStatus.RESOLVED)

    def test_resolve_dispute_reject_worker(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xRequester", {"rejectionReason": "Incomplete", "proofOfDefect": "0xdefect"}
        )
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        state = self.contract.resolve_dispute(
            dispute.dispute_id, "0xJudge", "Worker failed to deliver", False, 0
        )
        self.assertEqual(state.milestones[0].status, MilestoneStatus.REJECTED)
        self.assertEqual(state.status, EscrowStatus.RESOLVED)

    def test_non_judge_cannot_resolve(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        with self.assertRaises(EscrowError):
            self.contract.resolve_dispute(
                dispute.dispute_id, "0xRequester", "I decide", True, 0
            )


class CancellationTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)

    def test_cancel_pending_escrow(self):
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )
        cancelled = self.contract.cancel(state.escrow_id, "0xRequester")
        self.assertEqual(cancelled.status, EscrowStatus.CANCELLED)

    def test_cancel_funded_but_not_started(self):
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )
        self.contract.fund(state.escrow_id, 1000)
        cancelled = self.contract.cancel(state.escrow_id, "0xRequester")
        self.assertEqual(cancelled.status, EscrowStatus.CANCELLED)

    def test_cannot_cancel_after_work_started(self):
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )
        self.contract.fund(state.escrow_id, 1000)
        self.contract.start_milestone(state.escrow_id, 0)
        with self.assertRaises(EscrowError):
            self.contract.cancel(state.escrow_id, "0xRequester")

    def test_non_requester_cannot_cancel(self):
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )
        with self.assertRaises(EscrowError):
            self.contract.cancel(state.escrow_id, "0xWorker")


class AIJudgeTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)
        self.judge = AIJudge()
        self.state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )
        self.contract.fund(self.state.escrow_id, 1000)
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc123")

    def test_judge_evaluates_in_judging_state(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xWorker", {"deliverableHash": "0xabc123", "proofOfWork": "0xproof"}
        )
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        result = self.judge.evaluate(dispute, self.state)
        self.assertIn("pay_worker", result)
        self.assertIn("confidence", result)
        self.assertIn("reasoning", result)
        self.assertIn("scores", result)

    def test_judge_rejects_non_judging_state(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        with self.assertRaises(JudgeError):
            self.judge.evaluate(dispute, self.state)

    def test_judge_renders_decision(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Work is bad"
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xWorker", {"deliverableHash": "0xabc123", "proofOfWork": "0xproof"}
        )
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        pay_worker, resolution = self.judge.render_decision(dispute, self.state)
        self.assertIsInstance(pay_worker, bool)
        self.assertIn("Decision:", resolution)
        self.assertIn("Confidence:", resolution)

    def test_judge_favors_worker_with_strong_evidence(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Bad"
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xWorker",
            {"deliverableHash": "0xabc123", "proofOfWork": "0xproof", "timestamp": 1000},
        )
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        result = self.judge.evaluate(dispute, self.state)
        self.assertTrue(result["pay_worker"])

    def test_judge_favors_requester_with_strong_evidence(self):
        dispute = self.contract.raise_dispute(
            self.state.escrow_id, 0, "0xRequester", "Bad work"
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xRequester",
            {"rejectionReason": "Incomplete", "proofOfDefect": "0xdefect", "timestamp": 1000},
        )
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        result = self.judge.evaluate(dispute, self.state)
        self.assertFalse(result["pay_worker"])


class SettlementTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.adapter = MockSettlementAdapter(clock=self.clock)

    def test_settle_eth(self):
        settlement = self.adapter.settle_eth(
            escrow_id="escrow_1",
            recipient="0xWorker",
            amount=1000,
            milestone_index=0,
        )
        self.assertEqual(settlement.amount, 1000)
        self.assertEqual(settlement.recipient, "0xWorker")
        self.assertEqual(settlement.asset_type, AssetType.ETH)
        self.assertTrue(settlement.tx_hash.startswith("0x"))
        self.assertIsNotNone(settlement.block_number)

    def test_settle_erc20(self):
        settlement = self.adapter.settle_erc20(
            escrow_id="escrow_1",
            token_address="0xToken",
            recipient="0xWorker",
            amount=500,
            milestone_index=1,
        )
        self.assertEqual(settlement.asset_type, AssetType.ERC20)
        self.assertEqual(settlement.token_address, "0xToken")
        self.assertEqual(settlement.amount, 500)

    def test_settle_erc20_requires_token_address(self):
        with self.assertRaises(SettlementError):
            self.adapter.settle_erc20(
                escrow_id="escrow_1",
                token_address=None,
                recipient="0xWorker",
                amount=500,
            )

    def test_settle_zero_amount_rejected(self):
        with self.assertRaises(SettlementError):
            self.adapter.settle_eth(
                escrow_id="escrow_1",
                recipient="0xWorker",
                amount=0,
            )

    def test_balance_updates_after_settlement(self):
        self.adapter.settle_eth(
            escrow_id="escrow_1",
            recipient="0xWorker",
            amount=1000,
        )
        balance = self.adapter.get_balance("0xWorker", AssetType.ETH)
        self.assertEqual(balance, 1000)

    def test_multiple_settlements_accumulate(self):
        self.adapter.settle_eth(
            escrow_id="escrow_1",
            recipient="0xWorker",
            amount=500,
        )
        self.adapter.settle_eth(
            escrow_id="escrow_1",
            recipient="0xWorker",
            amount=300,
        )
        balance = self.adapter.get_balance("0xWorker", AssetType.ETH)
        self.assertEqual(balance, 800)

    def test_get_transaction_receipt(self):
        settlement = self.adapter.settle_eth(
            escrow_id="escrow_1",
            recipient="0xWorker",
            amount=1000,
        )
        receipt = self.adapter.get_transaction_receipt(settlement.tx_hash)
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["to"], "0xWorker")
        self.assertEqual(receipt["amount"], 1000)

    def test_get_nonexistent_receipt_returns_none(self):
        receipt = self.adapter.get_transaction_receipt("0xnonexistent")
        self.assertIsNone(receipt)

    def test_list_settlements(self):
        self.adapter.settle_eth(escrow_id="e1", recipient="0xA", amount=100)
        self.adapter.settle_eth(escrow_id="e2", recipient="0xB", amount=200)
        settlements = self.adapter.list_settlements()
        self.assertEqual(len(settlements), 2)


class QueryTests(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)
        self.state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=2000,
            milestones=[
                {"description": "Phase 1", "amount": 1000},
                {"description": "Phase 2", "amount": 1000},
            ],
        )
        self.contract.fund(self.state.escrow_id, 2000)

    def test_get_pending_milestones(self):
        pending = self.contract.get_pending_milestones(self.state.escrow_id)
        self.assertEqual(len(pending), 2)

    def test_get_approved_milestones(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc")
        self.contract.approve_milestone(self.state.escrow_id, 0)
        approved = self.contract.get_approved_milestones(self.state.escrow_id)
        self.assertEqual(len(approved), 1)
        self.assertEqual(approved[0].index, 0)

    def test_get_total_approved_amount(self):
        self.contract.start_milestone(self.state.escrow_id, 0)
        self.contract.deliver_milestone(self.state.escrow_id, 0, "0xabc")
        self.contract.approve_milestone(self.state.escrow_id, 0)
        total = self.contract.get_total_approved_amount(self.state.escrow_id)
        self.assertEqual(total, 1000)

    def test_to_dict_serialization(self):
        data = self.contract.to_dict(self.state.escrow_id)
        self.assertEqual(data["escrowId"], self.state.escrow_id)
        self.assertEqual(data["status"], "FUNDED")
        self.assertEqual(len(data["milestones"]), 2)
        self.assertEqual(data["totalAmount"], 2000)

    def test_list_escrows(self):
        self.contract.create_escrow(
            requester_address="0xA",
            worker_address="0xB",
            judge_address="0xC",
            asset_type=AssetType.ETH,
            total_amount=100,
            milestones=[{"description": "Work", "amount": 100}],
        )
        escrows = self.contract.list_escrows()
        self.assertEqual(len(escrows), 2)


class FullWorkflowTests(unittest.TestCase):
    """End-to-end workflow tests."""

    def setUp(self):
        self.clock = FakeClock()
        self.contract = EscrowContract(clock=self.clock)
        self.judge = AIJudge()
        self.adapter = MockSettlementAdapter(clock=self.clock)

    def test_full_happy_path_eth(self):
        """Requester creates, funds, worker delivers, requester approves, settlement."""
        # Create
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=2000,
            milestones=[
                {"description": "Phase 1", "amount": 1000},
                {"description": "Phase 2", "amount": 1000},
            ],
        )
        self.assertEqual(state.status, EscrowStatus.PENDING)

        # Fund
        state = self.contract.fund(state.escrow_id, 2000)
        self.assertEqual(state.status, EscrowStatus.FUNDED)

        # Phase 1: start, deliver, approve, settle
        self.contract.start_milestone(state.escrow_id, 0)
        self.contract.deliver_milestone(state.escrow_id, 0, "0xdeliverable1")
        self.contract.approve_milestone(state.escrow_id, 0)
        settlement1 = self.adapter.settle_eth(
            escrow_id=state.escrow_id,
            recipient="0xWorker",
            amount=1000,
            milestone_index=0,
        )
        self.assertEqual(settlement1.amount, 1000)

        # Phase 2: start, deliver, approve, settle
        self.contract.start_milestone(state.escrow_id, 1)
        self.contract.deliver_milestone(state.escrow_id, 1, "0xdeliverable2")
        self.contract.approve_milestone(state.escrow_id, 1)
        settlement2 = self.adapter.settle_eth(
            escrow_id=state.escrow_id,
            recipient="0xWorker",
            amount=1000,
            milestone_index=1,
        )
        self.assertEqual(settlement2.amount, 1000)

        # Verify final state
        state = self.contract.get_escrow(state.escrow_id)
        self.assertEqual(state.status, EscrowStatus.RESOLVED)
        self.assertEqual(self.adapter.get_balance("0xWorker", AssetType.ETH), 2000)

    def test_full_dispute_resolution_path(self):
        """Requester disputes, judge evaluates, worker is paid."""
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ETH,
            total_amount=1000,
            milestones=[{"description": "Work", "amount": 1000}],
        )
        self.contract.fund(state.escrow_id, 1000)
        self.contract.start_milestone(state.escrow_id, 0)
        self.contract.deliver_milestone(state.escrow_id, 0, "0xabc123")

        # Requester disputes
        dispute = self.contract.raise_dispute(
            state.escrow_id, 0, "0xRequester", "Work is unsatisfactory"
        )

        # Both parties submit evidence
        self.contract.submit_evidence(
            dispute.dispute_id, "0xWorker",
            {"deliverableHash": "0xabc123", "proofOfWork": "0xproof", "timestamp": 1000},
        )
        self.contract.submit_evidence(
            dispute.dispute_id, "0xRequester",
            {"rejectionReason": "Minor issues", "timestamp": 1000},
        )

        # Judge evaluates
        self.contract.start_judging(dispute.dispute_id, "0xJudge")
        pay_worker, resolution = self.judge.render_decision(dispute, state)

        # Resolve
        state = self.contract.resolve_dispute(
            dispute.dispute_id, "0xJudge", resolution, pay_worker, 0
        )
        self.assertEqual(state.status, EscrowStatus.RESOLVED)

        # Settle
        if pay_worker:
            settlement = self.adapter.settle_eth(
                escrow_id=state.escrow_id,
                recipient="0xWorker",
                amount=1000,
                milestone_index=0,
            )
            self.assertEqual(settlement.amount, 1000)

    def test_full_erc20_workflow(self):
        """ERC-20 token escrow workflow."""
        state = self.contract.create_escrow(
            requester_address="0xRequester",
            worker_address="0xWorker",
            judge_address="0xJudge",
            asset_type=AssetType.ERC20,
            token_address="0xUSDC",
            total_amount=5000,
            milestones=[
                {"description": "Design", "amount": 2000},
                {"description": "Implementation", "amount": 3000},
            ],
        )
        self.contract.fund(state.escrow_id, 5000)

        # Complete both milestones
        for i in range(2):
            self.contract.start_milestone(state.escrow_id, i)
            self.contract.deliver_milestone(state.escrow_id, i, f"0xhash{i}")
            self.contract.approve_milestone(state.escrow_id, i)

        state = self.contract.get_escrow(state.escrow_id)
        self.assertEqual(state.status, EscrowStatus.RESOLVED)

        # Settle ERC-20
        self.adapter.settle_erc20(
            escrow_id=state.escrow_id,
            token_address="0xUSDC",
            recipient="0xWorker",
            amount=2000,
            milestone_index=0,
        )
        self.adapter.settle_erc20(
            escrow_id=state.escrow_id,
            token_address="0xUSDC",
            recipient="0xWorker",
            amount=3000,
            milestone_index=1,
        )

        balance = self.adapter.get_balance("0xWorker", AssetType.ERC20, "0xUSDC")
        self.assertEqual(balance, 5000)


if __name__ == "__main__":
    unittest.main()
