import unittest
from unittest.mock import patch

from apexgraphswarm.evolution import (
    ALGORITHM_VERSION,
    EvolutionError,
    _Fixture,
    _Item,
    _exact_oracle,
    _run_greedy,
    run_evolution,
)


class EvolutionTests(unittest.TestCase):
    def test_deterministic_training_and_sealed_split_is_never_scored(self):
        base = {"seed": 81, "trainCount": 3, "heldoutCount": 2,
                "sealedCount": 1, "itemsPerInstance": 6, "claimCount": 5,
                "tokenBudget": 12}
        first = run_evolution(base)
        second = run_evolution({**base, "heldoutCount": 3, "sealedCount": 2})

        self.assertEqual(first["dataset"]["splitSha256"]["train"],
                         second["dataset"]["splitSha256"]["train"])
        self.assertEqual(first["trainingSelection"]["meanObjectiveRatioByCandidate"],
                         second["trainingSelection"]["meanObjectiveRatioByCandidate"])
        self.assertEqual(first["trainingSelection"]["candidateId"],
                         second["trainingSelection"]["candidateId"])
        self.assertEqual(first["sealedSet"]["status"],
                         "generated_not_executed_or_scored_or_selected")
        self.assertFalse(first["sealedSet"]["usedForSelection"])
        evaluated_ids = {
            task_id
            for entry in first["candidates"].values()
            for report in entry["evaluationReports"].values()
            for task_id in report["taskFinalStatus"]
        }
        self.assertFalse(any(task_id.startswith("sealed-") for task_id in evaluated_ids))

    def test_broken_candidate_fails_without_partial_favorable_result(self):
        with patch("apexgraphswarm.evolution._run_greedy", side_effect=RuntimeError("fault")):
            with self.assertRaisesRegex(EvolutionError, "execution failed"):
                run_evolution({"trainCount": 2, "heldoutCount": 2,
                               "sealedCount": 1, "itemsPerInstance": 4,
                               "claimCount": 3})

    def test_missing_real_cost_blocks_heldout_promotion(self):
        result = run_evolution({"trainCount": 2, "heldoutCount": 2,
                                "sealedCount": 1, "itemsPerInstance": 4,
                                "claimCount": 3})
        self.assertFalse(result["heldoutPromotionDecision"]["promote"])
        self.assertIn("unknown_actual_cost", result["heldoutPromotionDecision"]["failures"])
        self.assertIn("missing_enforced_cost_cap", result["heldoutPromotionDecision"]["failures"])
        self.assertIsNone(result["economics"]["actualCostMicrousd"])
        self.assertIsNone(result["economics"]["estimatedMonetaryCostMicrousd"])
        self.assertTrue(result["economics"]["unknownCostBlocksPromotion"])

    def test_exact_oracle_beats_greedy_on_constructed_knapsack_instance(self):
        fixture = _Fixture(
            task_id="counterexample", split="test",
            claim_weights=(10, 10, 10, 10),
            items=(
                _Item("a-large", 6, 0b0111),
                _Item("b-left", 5, 0b0011),
                _Item("c-right", 5, 0b1100),
            ),
        )
        exact = _exact_oracle(fixture, token_budget=10)
        heuristic = _run_greedy(fixture, token_budget=10, cost_exponent=1.0)
        self.assertEqual(exact["objective"], 40)
        self.assertEqual(heuristic["objective"], 30)
        self.assertEqual(heuristic["selectedItemIds"], ["a-large"])

    def test_payload_bounds_and_unknown_fields_are_rejected(self):
        with self.assertRaises(EvolutionError):
            run_evolution({"trainCount": True})
        with self.assertRaises(EvolutionError):
            run_evolution({"costExponents": "0,1"})
        with self.assertRaises(EvolutionError):
            run_evolution({"providerKey": "should-not-be-accepted"})

    def test_computed_loop_work_cap_rejects_before_exact_solver(self):
        payload = {"trainCount": 12, "heldoutCount": 12, "sealedCount": 1,
                   "itemsPerInstance": 14, "claimCount": 3,
                   "tokenBudget": 1000, "costExponents": [1]}
        with patch("apexgraphswarm.evolution._exact_oracle") as exact:
            with self.assertRaisesRegex(EvolutionError, "loop-work estimate"):
                run_evolution(payload)
        exact.assert_not_called()

    def test_candidate_config_is_named_bounded_and_reports_algorithm_version(self):
        result = run_evolution({"trainCount": 2, "heldoutCount": 2,
                                "sealedCount": 1, "itemsPerInstance": 4,
                                "claimCount": 3, "costExponents": [0, 1]})
        self.assertEqual(result["algorithm"]["name"], ALGORITHM_VERSION)
        self.assertEqual(result["candidateGeneration"]["candidates"], 2)
        self.assertEqual(result["dataset"]["generator"], "weighted-max-coverage-fixture-v1")
        self.assertEqual(len(result["sourceHashes"]["evolution"]), 64)


if __name__ == "__main__":
    unittest.main()
