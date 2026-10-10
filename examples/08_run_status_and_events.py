"""Example 08: Reading run status and event history.

The control plane maintains a full event log for each run,
providing an audit trail of all state transitions.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

plan = {
    "version": 1,
    "agents": [{"id": "a"}, {"id": "b"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 1, "executionClass": "fixture"},
        {"id": "t2", "agentId": "b", "dependencies": ["t1"],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 1, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="status-demo", budget_microusd=0)
run_id = run["run"]["id"]

# Get full status
status = store.status(run_id)
print(f"Run: {status['run']['id']}")
print(f"Status: {status['run']['status']}")
print(f"Tasks: {len(status['tasks'])}")
print(f"Events: {len(status['events'])}")

# Execute tasks
claim1 = store.claim(run_id, "worker-1")
store.complete(claim1["taskId"], claim1["leaseToken"], {"ok": True}, 0)

claim2 = store.claim(run_id, "worker-2")
store.complete(claim2["taskId"], claim2["leaseToken"], {"ok": True}, 0)

# Get final status with events
final = store.status(run_id)
print(f"\nFinal status: {final['run']['status']}")
print("Event history:")
for event in final["events"]:
    print(f"  [{event['sequence']}] {event['type']}: {event['data']}")

store.close()
