"""Example 07: Heartbeats and lease management.

Workers must heartbeat before their lease expires. The control
plane enforces lease expiry and fenced completion.
"""
import time
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "long-task", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 2, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="heartbeat-demo", budget_microusd=0)
run_id = run["run"]["id"]

# Claim with a short lease
claim = store.claim(run_id, "worker-1", lease_seconds=5)
print(f"Claimed with 5s lease: {claim['id']}")

# Heartbeat to extend
hb = store.heartbeat(claim["taskId"], claim["leaseToken"], lease_seconds=30)
print(f"Heartbeat extended lease: {hb['leaseExpiresAt']}")

# Complete within the extended lease
result = store.complete(
    claim["taskId"], claim["leaseToken"], {"done": True}, 0
)
print(f"Completed: {result['run']['status']}")

store.close()
