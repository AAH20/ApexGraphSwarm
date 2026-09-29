"""Example 04: Claiming and completing tasks.

Workers claim ready tasks, perform work, and complete them.
The control plane enforces dependencies, leases, and fencing.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

plan = {
    "version": 1,
    "agents": [{"id": "agent-1"}],
    "tasks": [
        {"id": "task-1", "agentId": "agent-1", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 2, "executionClass": "fixture"},
        {"id": "task-2", "agentId": "agent-1", "dependencies": ["task-1"],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 2, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="claim-demo", budget_microusd=0)
run_id = run["run"]["id"]

# Claim the first ready task
claim = store.claim(run_id, "worker-1", lease_seconds=30)
print(f"Claimed: {claim['id']} (taskId={claim['taskId']})")
print(f"Lease token: {claim['leaseToken'][:16]}...")

# Complete the task
result = store.complete(
    claim["taskId"],
    claim["leaseToken"],
    {"result": "success", "data": [1, 2, 3]},
    actual_cost_microusd=0,
)
print(f"Run status after completion: {result['run']['status']}")

# Claim the next task (dependency satisfied)
claim2 = store.claim(run_id, "worker-1", lease_seconds=30)
print(f"Claimed: {claim2['id']}")

# Complete it
result2 = store.complete(
    claim2["taskId"],
    claim2["leaseToken"],
    {"result": "done"},
    actual_cost_microusd=0,
)
print(f"Final run status: {result2['run']['status']}")

store.close()
