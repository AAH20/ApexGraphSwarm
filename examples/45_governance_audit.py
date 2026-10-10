"""Example 45: Governance - audit trail and compliance reporting.

Generate compliance reports from the control plane event log.
"""
from apexgraphswarm.control import ControlStore
import json

store = ControlStore(":memory:")

# Create and execute a run
plan = {
    "version": 1,
    "agents": [{"id": "a"}, {"id": "b"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 1000,
         "maxAttempts": 2, "executionClass": "fixture"},
        {"id": "t2", "agentId": "b", "dependencies": ["t1"],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 2000,
         "maxAttempts": 2, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="audit-demo", budget_microusd=5000)
run_id = run["run"]["id"]

claim1 = store.claim(run_id, "worker-1")
store.complete(claim1["taskId"], claim1["leaseToken"], {"ok": True}, 800)

claim2 = store.claim(run_id, "worker-2")
store.complete(claim2["taskId"], claim2["leaseToken"], {"ok": True}, 1500)

# Generate audit report
status = store.status(run_id)
ledger = store.ledger(run_id)

audit_report = {
    "run_id": run_id,
    "status": status["run"]["status"],
    "budget": {
        "allocated": status["run"]["budgetMicrousd"],
        "spent": status["run"]["spentMicrousd"],
        "remaining": status["run"]["remainingMicrousd"],
    },
    "tasks": [
        {
            "id": t["id"],
            "status": t["status"],
            "agent": t["agentId"],
            "attempts": t["attempts"],
            "reserved": t["reservedCostMicrousd"],
        }
        for t in status["tasks"]
    ],
    "events": [
        {
            "sequence": e["sequence"],
            "type": e["type"],
            "timestamp": e["createdAt"],
        }
        for e in status["events"]
    ],
    "cost_attribution": [
        {
            "attempt": a["attemptId"][:16],
            "task": a["taskId"],
            "actual_cost": a["actualCostMicrousd"],
            "worker": a["workerId"],
        }
        for a in ledger["attempts"]
    ],
}

print("Audit Report:")
print(json.dumps(audit_report, indent=2))

store.close()
