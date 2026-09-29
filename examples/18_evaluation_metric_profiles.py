"""Example 18: Evaluation with metric profiles and hard gates.

Metric profiles define weighted scoring across multiple dimensions.
Hard gates are non-compensating — a failed gate blocks promotion
regardless of weighted score.
"""
from apexgraphswarm.evaluation import EvaluationSuite

# Suite with metric profile
suite = EvaluationSuite.from_dict({
    "suiteId": "profile-suite",
    "suiteVersion": "1",
    "tasksetId": "test-tasks",
    "tasksetVersion": "1",
    "evaluatorId": "exact-evaluator",
    "evaluatorVersion": "1",
    "trainTaskIds": ["t1", "t2"],
    "heldoutTaskIds": ["h1", "h2"],
    "sealedTaskIds": ["s1"],
    "qualityFloor": 0.75,
    "maxLatencyMs": 30000,
    "maxPolicyViolations": 0,
    "confidenceAlpha": 0.05,
    "maxAttemptsPerTask": 3,
    "metricProfile": {
        "profileId": "coding",
        "weights": {
            "correctness": 40,
            "test_coverage": 25,
            "regression_control": 15,
            "evidence_provenance": 10,
            "reliability": 5,
            "latency": 3,
            "cost_efficiency": 1,
            "coordination_efficiency": 1,
        },
        "weightSetVersion": "custom-v1",
        "minimumWeightedScore": 0.8,
        "maxScoreRegression": 0.02,
    },
})

print(f"Suite: {suite.suite_id}")
print(f"Quality floor: {suite.quality_floor}")
print(f"Max latency: {suite.max_latency_ms}ms")
print(f"Max policy violations: {suite.max_policy_violations}")
print(f"Confidence alpha: {suite.confidence_alpha}")
if suite.metric_profile:
    print(f"Metric profile: {suite.metric_profile['profileId']}")
    print(f"Weight version: {suite.metric_profile['weightSetVersion']}")
    print(f"Weights: {suite.metric_profile['weights']}")
    print(f"Min weighted score: {suite.metric_profile['minimumWeightedScore']}")
