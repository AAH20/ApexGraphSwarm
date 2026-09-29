import copy
import unittest

from apexgraphswarm.evaluation import (
    Attempt, Candidate, EvaluationError, EvaluationSuite, compare_candidates,
    evaluate, evaluate_candidate,
)


def suite_dict(**overrides):
    raw = {
        "suiteId": "suite-x", "suiteVersion": "1", "tasksetId": "tasks",
        "tasksetVersion": "v2", "evaluatorId": "exact-fixture",
        "evaluatorVersion": "3", "trainTaskIds": ["tr1", "tr2"],
        "heldoutTaskIds": ["h1", "h2", "h3"], "sealedTaskIds": ["s1"],
        "qualityFloor": 0.2, "maxLatencyMs": 5000,
        "maxCostMicrousdPerTask": 200, "costCapEnforcementId": "fixture-cap-v1",
    }
    raw.update(overrides)
    return raw


def coding_metric_scores(value=0.9):
    from apexgraphswarm.hierarchy import METRIC_PROFILES
    return {name: value for name in METRIC_PROFILES["coding"]["weights"]}


def candidate(cid, config):
    return {"candidateId": cid, "version": "1", "config": config}


def attempt(aid, cid, task, *, index=1, status="succeeded", cost=10,
            quality=1, accepted=True, elapsed=10, policy=0):
    return {"attemptId": aid, "candidateId": cid, "taskId": task,
            "evaluatorId": "exact-fixture", "evaluatorVersion": "3",
            "attemptIndex": index, "status": status, "elapsedMs": elapsed,
            "actualCostMicrousd": cost, "qualityScore": quality,
            "accepted": accepted, "policyViolations": policy}


def rows_for(cid, tasks, cost):
    return [attempt(cid + "-" + task, cid, task, cost=cost) for task in tasks]


class EvaluationTests(unittest.TestCase):
    def test_field_metric_profile_is_weighted_on_final_tasks_and_compared_paired(self):
        suite = EvaluationSuite.from_dict(suite_dict(metricProfile={
            "profileId": "coding", "profileVersion": "1",
            "minimumWeightedScore": 0.0, "maxScoreRegression": 1.0,
        }))
        base = Candidate.from_dict(candidate("base", {"cap": 1}))
        changed = Candidate.from_dict(candidate("new", {"cap": 2}))
        attempts = []
        for cid, score in (("base", 0.9), ("new", 0.8)):
            for task_id in suite.heldout_task_ids:
                attempts.append(Attempt.from_dict({
                    **attempt(cid + "-" + task_id, cid, task_id, cost=20),
                    "metricScores": coding_metric_scores(score),
                }))
        base_report = evaluate_candidate(base, suite, attempts, "heldout")
        changed_report = evaluate_candidate(changed, suite, attempts, "heldout")
        summary = changed_report["metricProfileEvaluation"]
        self.assertEqual(summary["profileId"], "coding")
        self.assertAlmostEqual(summary["meanWeightedScore"], 0.8)
        self.assertTrue(summary["gateFailures"] == [])
        self.assertEqual(summary["weights"]["correctness"], 30)
        decision = compare_candidates(base_report, changed_report, suite)
        self.assertIsNotNone(decision["pairedWeightedMetricScoreDifference"])
        self.assertAlmostEqual(decision["pairedWeightedMetricScoreDifference"]["mean"], -0.1)

    def test_metric_profile_missing_scores_are_a_gate_and_tampering_is_rejected(self):
        suite = EvaluationSuite.from_dict(suite_dict(metricProfile={
            "profileId": "coding", "minimumWeightedScore": 0.0,
        }))
        c = Candidate.from_dict(candidate("base", {"cap": 1}))
        missing = [Attempt.from_dict(attempt("a-" + task_id, "base", task_id))
                   for task_id in suite.heldout_task_ids]
        report = evaluate_candidate(c, suite, missing, "heldout")
        self.assertIn("metric_profile_scores_incomplete", report["gateFailures"])
        self.assertFalse(report["hardGatesPassed"])
        altered = copy.deepcopy(report)
        altered["metricProfileEvaluation"]["meanWeightedScore"] = 1.0
        with self.assertRaisesRegex(EvaluationError, "summary does not reconcile"):
            compare_candidates(report, altered, suite)

    def test_metric_profile_weights_are_versioned_and_bounded(self):
        with self.assertRaisesRegex(EvaluationError, "version is not registered"):
            EvaluationSuite.from_dict(suite_dict(metricProfile={"profileId": "coding", "profileVersion": "999"}))
        with self.assertRaisesRegex(EvaluationError, "valid range"):
            EvaluationSuite.from_dict(suite_dict(metricProfile={"profileId": "coding", "minimumWeightedScore": 1.1}))
        custom = coding_metric_scores(100)
        weights = {key: 0 for key in custom}
        weights["correctness"] = 100
        with self.assertRaisesRegex(EvaluationError, "require weightSetVersion"):
            EvaluationSuite.from_dict(suite_dict(metricProfile={"profileId": "coding", "weights": weights}))
        configured = EvaluationSuite.from_dict(suite_dict(metricProfile={
            "profileId": "coding", "weights": weights, "weightSetVersion": "team-policy-2",
        }))
        self.assertEqual(configured.to_dict()["metricProfile"]["weights"]["correctness"], 100)
    def test_split_overlap_and_unsafe_candidate_configs_rejected(self):
        with self.assertRaises(EvaluationError):
            EvaluationSuite.from_dict(suite_dict(sealedTaskIds=["h1"]))
        with self.assertRaises(EvaluationError):
            Candidate.from_dict(candidate("bad", {"threshold": float("nan")}))
        with self.assertRaises(EvaluationError):
            Candidate.from_dict(candidate("bad", {"code": "__import__('os').system('true')" * 1000}))

    def test_retries_charge_all_attempts_and_unknown_failed_cost_blocks_hard_gate(self):
        c = Candidate.from_dict(candidate("c", {"capacity": 2}))
        s = EvaluationSuite.from_dict(suite_dict())
        attempts = [
            Attempt.from_dict(attempt("a1", "c", "tr1", status="timed_out", cost=5, accepted=False, quality=None)),
            Attempt.from_dict(attempt("a2", "c", "tr1", index=2, cost=12)),
            Attempt.from_dict(attempt("a3", "c", "tr2", cost=None)),
        ]
        report = evaluate_candidate(c, s, attempts, "train")
        self.assertEqual(report["knownActualCostMicrousd"], 17)
        self.assertEqual(report["unknownCostAttemptCount"], 1)
        self.assertIsNone(report["costPerAcceptedMicrousd"])
        self.assertIn("unknown_actual_cost", report["gateFailures"])
        self.assertEqual(report["attemptCount"], 3)

    def test_evaluator_and_attempt_order_are_versioned_and_bounded(self):
        c = Candidate.from_dict(candidate("c", {"capacity": 2}))
        s = EvaluationSuite.from_dict(suite_dict())
        wrong = Attempt.from_dict({**attempt("a", "c", "tr1"), "evaluatorVersion": "2"})
        with self.assertRaisesRegex(EvaluationError, "evaluator identity"):
            evaluate_candidate(c, s, [wrong], "train")
        out_of_order = [
            Attempt.from_dict(attempt("a2", "c", "tr1", index=2)),
        ]
        with self.assertRaisesRegex(EvaluationError, "contiguous"):
            evaluate_candidate(c, s, out_of_order, "train")

    def test_compare_requires_paired_heldout_reports_and_gates_policy_latency(self):
        suite = EvaluationSuite.from_dict(suite_dict())
        base = Candidate.from_dict(candidate("base", {"cap": 1}))
        changed = Candidate.from_dict(candidate("new", {"cap": 2}))
        base_rows = [Attempt.from_dict(r) for r in rows_for("base", suite.heldout_task_ids, 50)]
        new_rows = [Attempt.from_dict(r) for r in rows_for("new", suite.heldout_task_ids, 20)]
        base_report = evaluate_candidate(base, suite, base_rows, "heldout")
        candidate_report = evaluate_candidate(changed, suite, new_rows, "heldout")
        decision = compare_candidates(base_report, candidate_report, suite)
        self.assertEqual(decision["split"], "heldout")
        self.assertGreater(decision["candidateCostPerAcceptedMicrousdUpperBound"], 0)
        with self.assertRaisesRegex(EvaluationError, "held-out"):
            compare_candidates({**base_report, "split": "sealed"}, candidate_report, suite)
        policy_rows = [Attempt.from_dict({**r, "policyViolations": 1}) for r in rows_for("new", suite.heldout_task_ids, 20)]
        policy_report = evaluate_candidate(changed, suite, policy_rows, "heldout")
        self.assertFalse(policy_report["hardGatesPassed"])
        self.assertIn("policy_violation_limit_exceeded", compare_candidates(base_report, policy_report, suite)["failures"])

    def test_training_selects_candidate_and_sealed_results_do_not_affect_decision(self):
        train = ["tr%03d" % i for i in range(100)]
        held = ["h1", "h2", "h3"]
        s = suite_dict(trainTaskIds=train)
        attempts = rows_for("base", train + held + ["s1"], 50)
        attempts += rows_for("candidate", train + held + ["s1"], 20)
        payload = {"suite": s, "candidates": [candidate("base", {"cap": 1}), candidate("candidate", {"cap": 2})],
                   "attempts": attempts, "baselineCandidateId": "base"}
        result = evaluate(payload)
        self.assertEqual(result["trainingSelection"]["selectedCandidateId"], "candidate")
        self.assertFalse(result["trainingSelection"]["sealedSetUsedForSelection"])
        self.assertFalse(result["promotionDecision"]["sealedSetUsedForSelection"])
        self.assertNotIn("sealed", result["candidateReports"]["candidate"])
        self.assertEqual(result["sealedSet"]["status"], "not_scored_or_returned_by_this_call")
        # Changing only sealed outcomes cannot change selection or held-out decision.
        changed = dict(payload)
        changed["attempts"] = [dict(row, actualCostMicrousd=None, policyViolations=9)
                                if row["taskId"] == "s1" and row["candidateId"] == "candidate" else row
                                for row in attempts]
        again = evaluate(changed)
        self.assertEqual(result["trainingSelection"], again["trainingSelection"])
        self.assertEqual(result["promotionDecision"], again["promotionDecision"])

    def test_failure_cost_and_policy_checks_apply_to_all_retries(self):
        suite = EvaluationSuite.from_dict(suite_dict())
        c = Candidate.from_dict(candidate("c", {"x": 1}))
        records = [
            Attempt.from_dict(attempt("fail", "c", "tr1", status="failed", cost=100, accepted=False,
                                       quality=None, policy=1)),
            Attempt.from_dict(attempt("ok", "c", "tr1", index=2, cost=5)),
        ]
        report = evaluate_candidate(c, suite, records, "train")
        self.assertEqual(report["knownActualCostMicrousd"], 105)
        self.assertEqual(report["policyViolations"], 1)
        self.assertFalse(report["hardGatesPassed"])

    def test_success_status_without_explicit_evaluator_acceptance_is_not_accepted(self):
        suite = EvaluationSuite.from_dict(suite_dict())
        c = Candidate.from_dict(candidate("c", {"x": 1}))
        records = [Attempt.from_dict(attempt("a", "c", "tr1", accepted=None))]
        report = evaluate_candidate(c, suite, records, "train")
        self.assertEqual(report["acceptedCount"], 0)
        self.assertEqual(report["taskOutcomes"]["tr1"], 0)

    def test_incomplete_heldout_coverage_cannot_promote_even_when_missing_rows_would_look_free(self):
        task_ids = ["h%04d" % i for i in range(1_100)]
        suite = EvaluationSuite.from_dict(suite_dict(heldoutTaskIds=task_ids, qualityFloor=0.0))
        base = Candidate.from_dict(candidate("base", {"x": 1}))
        changed = Candidate.from_dict(candidate("new", {"x": 2}))
        base_report = evaluate_candidate(base, suite, [Attempt.from_dict(attempt("b", "base", task_ids[0], cost=100))], "heldout")
        new_report = evaluate_candidate(changed, suite, [Attempt.from_dict(attempt("n", "new", task_ids[0], cost=1))], "heldout")
        self.assertEqual(base_report["missingTaskAttemptCount"], 1_099)
        self.assertFalse(base_report["hardGatesPassed"])
        with self.assertRaisesRegex(EvaluationError, "incomplete attempt coverage"):
            compare_candidates(base_report, new_report, suite)

        train_ids = ["tr%03d" % i for i in range(100)]
        payload_suite = suite_dict(trainTaskIds=train_ids, heldoutTaskIds=task_ids, qualityFloor=0.2)
        attempt_rows = rows_for("base", train_ids, 100) + rows_for("new", train_ids, 50)
        attempt_rows += [attempt("base-held", "base", task_ids[0], cost=100),
                         attempt("new-held", "new", task_ids[0], cost=50)]
        result = evaluate({"suite": payload_suite,
                           "candidates": [candidate("base", {"x": 1}), candidate("new", {"x": 2})],
                           "attempts": attempt_rows, "baselineCandidateId": "base"})
        self.assertFalse(result["promotionDecision"]["promote"])
        self.assertIn("incomplete_heldout_evidence", result["promotionDecision"]["failures"])

    def test_mutated_heldout_summary_is_rejected_before_promotion(self):
        suite = EvaluationSuite.from_dict(suite_dict())
        base = Candidate.from_dict(candidate("base", {"x": 1}))
        changed = Candidate.from_dict(candidate("new", {"x": 2}))
        base_report = evaluate_candidate(base, suite,
            [Attempt.from_dict(r) for r in rows_for("base", suite.heldout_task_ids, 50)], "heldout")
        new_report = evaluate_candidate(changed, suite,
            [Attempt.from_dict(r) for r in rows_for("new", suite.heldout_task_ids, 20)], "heldout")
        forged = dict(new_report)
        forged["taskOutcomes"] = dict(new_report["taskOutcomes"], h1=2)
        forged["hardGatesPassed"] = True
        forged["gateFailures"] = []
        with self.assertRaisesRegex(EvaluationError, "task outcomes do not reconcile"):
            compare_candidates(base_report, forged, suite)

    def test_sufficient_paired_evidence_can_pass_gate_but_unknown_cost_cannot(self):
        count = 2_000
        ids = ["h%04d" % i for i in range(count)]
        suite = EvaluationSuite.from_dict(suite_dict(heldoutTaskIds=ids))
        base = Candidate.from_dict(candidate("base", {"budget": 10}))
        changed = Candidate.from_dict(candidate("new", {"budget": 8}))
        base_rows = [Attempt.from_dict(attempt("b" + task, "base", task, cost=50)) for task in ids]
        new_rows = [Attempt.from_dict(attempt("n" + task, "new", task, cost=20)) for task in ids]
        base_report = evaluate_candidate(base, suite, base_rows, "heldout")
        new_report = evaluate_candidate(changed, suite, new_rows, "heldout")
        decision = compare_candidates(base_report, new_report, suite)
        self.assertTrue(decision["promote"], decision["failures"])
        self.assertGreater(decision["pairedAcceptedRateDifference"]["lower"], -0.02)
        unknown_rows = [Attempt.from_dict(attempt("u" + task, "new", task, cost=None)) for task in ids]
        unknown_report = evaluate_candidate(changed, suite, unknown_rows, "heldout")
        blocked = compare_candidates(base_report, unknown_report, suite)
        self.assertFalse(blocked["promote"])
        self.assertIn("unknown_cost_blocks_promotion", blocked["failures"])


if __name__ == "__main__":
    unittest.main()
