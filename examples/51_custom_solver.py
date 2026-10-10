"""Example 51: Advanced - custom solver integration.

Integrate a custom solver with the evolution framework.
"""
from apexgraphswarm.evaluation import Candidate, Attempt, EvaluationSuite, evaluate_candidate

# Define a custom solver configuration
custom_config = {
    "model": "custom-llm",
    "temperature": 0.7,
    "max_tokens": 2000,
    "top_p": 0.9,
}

candidate = Candidate("custom-solver", "v1", custom_config)

# Define evaluation suite
suite = EvaluationSuite.from_dict({
    "suiteId": "custom-eval",
    "suiteVersion": "1",
    "tasksetId": "custom-tasks",
    "tasksetVersion": "1",
    "evaluatorId": "custom-evaluator",
    "evaluatorVersion": "1",
    "trainTaskIds": ["t1", "t2", "t3", "t4"],
    "heldoutTaskIds": ["h1", "h2", "h3"],
    "sealedTaskIds": ["s1"],
    "qualityFloor": 0.75,
    "maxLatencyMs": 30000,
    "maxPolicyViolations": 0,
})

# Simulate solver outputs
attempts = []
for i, task_id in enumerate(["t1", "t2", "t3", "t4"]):
    attempts.append(Attempt.from_dict({
        "attemptId": f"custom-{i}",
        "candidateId": "custom-solver",
        "taskId": task_id,
        "evaluatorId": "custom-evaluator",
        "evaluatorVersion": "1",
        "status": "succeeded",
        "elapsedMs": 1000 + i * 100,
        "actualCostMicrousd": 500 + i * 50,
        "qualityScore": 0.8 + i * 0.02,
        "accepted": True,
        "policyViolations": 0,
    }))

# Evaluate
report = evaluate_candidate(candidate, suite, attempts, "train")
print(f"Custom solver evaluation:")
print(f"  Quality score: {report['qualityScore']:.3f}")
print(f"  Accepted: {report['accepted']}")
print(f"  Cost: {report['actualCostMicrousd']} micro-USD")
print(f"  Latency: {report['elapsedMs']:.0f}ms")
