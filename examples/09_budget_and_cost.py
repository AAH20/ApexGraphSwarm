"""Example 09: Budget management and cost tracking.

Every task must have a known integer reservation. The control
plane tracks reserved vs actual spend and enforces budgets.
"""
from apexgraphswarm.control import ControlStore, BudgetError

store = ControlStore(":memory:")

# This will fail: unknown cost cannot be admitted
try:
    plan = {
        "version": 1,
        "agents": [{"id": "a"}],
        "tasks": [
            {"id": "paid-task", "agentId": "a", "dependencies": [],
             "payload": {"kind": "fixture"}, "reservedCostMicrousd": 1000,
             "maxAttempts": 1, "executionClass": "fixture"},
        ],
    }
    store.create_run(plan, idempotency_key="budget-demo", budget_microusd=None)
except BudgetError as e:
    print(f"Correctly rejected unknown budget: {e}")

# This will fail: reservations exceed budget
try:
    plan = {
        "version": 1,
        "agents": [{"id": "a"}],
        "tasks": [
            {"id": "expensive", "agentId": "a", "dependencies": [],
             "payload": {"kind": "fixture"}, "reservedCostMicrousd": 10000,
             "maxAttempts": 1, "executionClass": "fixture"},
        ],
    }
    store.create_run(plan, idempotency_key="budget-demo-2", budget_microusd=5000)
except BudgetError as e:
    print(f"Correctly rejected over-budget plan: {e}")

# This succeeds: known budget, sufficient funds
plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "task-1", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 1000,
         "maxAttempts": 1, "executionClass": "fixture"},
        {"id": "task-2", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 2000,
         "maxAttempts": 1, "executionClass": "fixture"},
    ],
}
run = store.create_run(plan, idempotency_key="budget-ok", budget_microusd=5000)
print(f"Created run with budget: {run['run']['budgetMicrousd']} micro-USD")
print(f"Total reserved: {sum(t['reservedCostMicrousd'] for t in run['tasks'])}")

store.close()
