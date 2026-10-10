"""Example 03: Creating a simple DAG run.

A run is a versioned plan with agents, tasks, and dependencies.
All work must specify a known integer budget.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

plan = {
    "version": 1,
    "agents": [
        {"id": "planner", "name": "Planner Agent"},
        {"id": "worker-a", "name": "Worker A"},
        {"id": "worker-b", "name": "Worker B"},
    ],
    "tasks": [
        {
            "id": "inspect",
            "agentId": "planner",
            "dependencies": [],
            "payload": {"kind": "fixture", "action": "inspect"},
            "reservedCostMicrousd": 0,
            "maxAttempts": 2,
            "executionClass": "fixture",
        },
        {
            "id": "analyze-a",
            "agentId": "worker-a",
            "dependencies": ["inspect"],
            "payload": {"kind": "fixture", "action": "analyze"},
            "reservedCostMicrousd": 0,
            "maxAttempts": 2,
            "executionClass": "fixture",
        },
        {
            "id": "analyze-b",
            "agentId": "worker-b",
            "dependencies": ["inspect"],
            "payload": {"kind": "fixture", "action": "analyze"},
            "reservedCostMicrousd": 0,
            "maxAttempts": 2,
            "executionClass": "fixture",
        },
        {
            "id": "synthesize",
            "agentId": "planner",
            "dependencies": ["analyze-a", "analyze-b"],
            "payload": {"kind": "fixture", "action": "synthesize"},
            "reservedCostMicrousd": 0,
            "maxAttempts": 1,
            "executionClass": "fixture",
        },
    ],
}

result = store.create_run(plan, idempotency_key="run-001", budget_microusd=0)
run_id = result["run"]["id"]
print(f"Created run: {run_id}")
print(f"Status: {result['run']['status']}")
print(f"Tasks: {len(result['tasks'])}")

# Idempotency: same key + same plan returns the original
same = store.create_run(plan, idempotency_key="run-001", budget_microusd=0)
assert same["run"]["id"] == run_id
print("Idempotency verified: same key returns same run.")

store.close()
