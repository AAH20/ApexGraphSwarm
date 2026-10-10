"""Example 32: Ledger and attempt receipts.

Read stable attempt receipts with explicit coverage and
bounded rows. The ledger provides full cost attribution.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

# Create and execute a run
plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 1000,
         "maxAttempts": 2, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="ledger-demo", budget_microusd=5000)
run_id = run["run"]["id"]

claim = store.claim(run_id, "worker-1")
store.complete(claim["taskId"], claim["leaseToken"], {"ok": True}, 750)

# Read the ledger
ledger = store.ledger(run_id)
print(f"Total attempts: {ledger['totalAttempts']}")
print(f"Returned attempts: {ledger['returnedAttempts']}")
print(f"Known actual: {ledger['knownActualMicrousd']} micro-USD")
print(f"Unresolved count: {ledger['unresolvedCostCount']}")
print(f"Coverage complete: {ledger['coverageComplete']}")
print(f"All costs resolved: {ledger['allCostsResolved']}")

print("\nAttempt details:")
for attempt in ledger["attempts"]:
    print(f"  {attempt['attemptId'][:16]}...")
    print(f"    Task: {attempt['taskId']}")
    print(f"    Outcome: {attempt['outcome']}")
    print(f"    Actual cost: {attempt['actualCostMicrousd']} micro-USD")
    print(f"    Reserved: {attempt['reservedMicrousd']} micro-USD")

store.close()
