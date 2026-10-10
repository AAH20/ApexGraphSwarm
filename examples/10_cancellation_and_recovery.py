"""Example 10: Run cancellation and expired lease recovery.

Runs can be cancelled. Expired leases are recovered automatically
during claim, moving tasks to needs_reconciliation.
"""
import time
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "task-1", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 2, "executionClass": "fixture"},
        {"id": "task-2", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 2, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="cancel-demo", budget_microusd=0)
run_id = run["run"]["id"]

# Claim a task
claim = store.claim(run_id, "worker-1", lease_seconds=1)
print(f"Claimed: {claim['id']}")

# Cancel the run
store.cancel(run_id)
status = store.status(run_id)
print(f"Run status after cancel: {status['run']['status']}")
print(f"Cancel requested: {status['run']['cancelRequested']}")

# Recover expired leases
store.recover_expired()
status2 = store.status(run_id)
print(f"After recovery: {status2['run']['status']}")

store.close()
