"""Example 17: Evaluating candidates with held-out promotion gates.

Evaluation compares candidates on train/held-out splits with
conservative statistical bounds.
"""
from apexgraphswarm.evaluation import (
    EvaluationSuite,
    Candidate,
    Attempt,
    evaluate_candidate,
    compare_candidates,
)

# Define an evaluation suite
suite = EvaluationSuite.from_dict({
    "suiteId": "test-suite",
    "suiteVersion": "1",
    "tasksetId": "test-tasks",
    "tasksetVersion": "1",
    "evaluatorId": "exact-evaluator",
    "evaluatorVersion": "1",
    "trainTaskIds": ["t1", "t2", "t3"],
    "heldoutTaskIds": ["h1", "h2", "h3"],
    "sealedTaskIds": ["s1", "s2"],
    "qualityFloor": 0.8,
    "maxLatencyMs": 60000,
    "maxPolicyViolations": 0,
    "confidenceAlpha": 0.05,
    "maxAttemptsPerTask": 3,
})

# Define candidates
baseline = Candidate("baseline", "v1", {"model": "test-small"})
candidate = Candidate("candidate", "v1", {"model": "test-large"})

# Create attempts
attempts = [
    Attempt.from_dict({
        "attemptId": "a1", "candidateId": "baseline", "taskId": "t1",
        "evaluatorId": "exact-evaluator", "evaluatorVersion": "1",
        "status": "succeeded", "elapsedMs": 100, "actualCostMicrousd": 100,
        "qualityScore": 0.9, "accepted": True, "policyViolations": 0,
    }),
    Attempt.from_dict({
        "attemptId": "a2", "candidateId": "candidate", "taskId": "t1",
        "evaluatorId": "exact-evaluator", "evaluatorVersion": "1",
        "status": "succeeded", "elapsedMs": 120, "actualCostMicrousd": 200,
        "qualityScore": 0.95, "accepted": True, "policyViolations": 0,
    }),
]

# Evaluate on training split
report = evaluate_candidate(baseline, suite, attempts, "train")
print(f"Baseline train score: {report['qualityScore']:.3f}")
print(f"Baseline accepted: {report['accepted']}")
print(f"Baseline cost: {report['actualCostMicrousd']}")

# Compare candidates
comparison = compare_candidates(
    evaluate_candidate(baseline, suite, attempts, "heldout"),
    evaluate_candidate(candidate, suite, attempts, "heldout"),
    suite,
)
print(f"\nComparison decision: {comparison['decision']}")
print(f"Mean difference: {comparison['meanDifference']:.4f}")
print(f"Confidence interval: [{comparison['lowerBound']:.4f}, {comparison['upperBound']:.4f}]")
