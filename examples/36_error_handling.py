"""Example 36: Error handling and validation.

The control plane validates all inputs and raises specific
exceptions for different error conditions.
"""
from apexgraphswarm.control import (
    ControlStore,
    ControlError,
    ConflictError,
    LeaseError,
    BudgetError,
)

store = ControlStore(":memory:")

# Test various error conditions
print("Testing error handling:")

# 1. Missing dependencies
try:
    plan = {
        "version": 1,
        "agents": [{"id": "a"}],
        "tasks": [
            {"id": "t1", "agentId": "a", "dependencies": ["nonexistent"],
             "payload": {}, "reservedCostMicrousd": 0, "maxAttempts": 1},
        ],
    }
    store.create_run(plan, idempotency_key="err-1", budget_microusd=0)
except ControlError as e:
    print(f"  Missing deps: {e}")

# 2. Cycle detection
try:
    plan = {
        "version": 1,
        "agents": [{"id": "a"}],
        "tasks": [
            {"id": "x", "agentId": "a", "dependencies": ["y"],
             "payload": {}, "reservedCostMicrousd": 0, "maxAttempts": 1},
            {"id": "y", "agentId": "a", "dependencies": ["x"],
             "payload": {}, "reservedCostMicrousd": 0, "maxAttempts": 1},
        ],
    }
    store.create_run(plan, idempotency_key="err-2", budget_microusd=0)
except ControlError as e:
    print(f"  Cycle: {e}")

# 3. Secret fields in payload
try:
    plan = {
        "version": 1,
        "agents": [{"id": "a"}],
        "tasks": [
            {"id": "t1", "agentId": "a", "dependencies": [],
             "payload": {"api_key": "secret123"}, "reservedCostMicrousd": 0,
             "maxAttempts": 1},
        ],
    }
    store.create_run(plan, idempotency_key="err-3", budget_microusd=0)
except ControlError as e:
    print(f"  Secret field: {e}")

# 4. Budget exceeded
try:
    plan = {
        "version": 1,
        "agents": [{"id": "a"}],
        "tasks": [
            {"id": "t1", "agentId": "a", "dependencies": [],
             "payload": {}, "reservedCostMicrousd": 10000,
             "maxAttempts": 1},
        ],
    }
    store.create_run(plan, idempotency_key="err-4", budget_microusd=5000)
except BudgetError as e:
    print(f"  Budget: {e}")

# 5. Idempotency conflict
plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": [],
         "payload": {}, "reservedCostMicrousd": 0, "maxAttempts": 1},
    ],
}
store.create_run(plan, idempotency_key="unique-key", budget_microusd=0)
try:
    store.create_run(plan, idempotency_key="unique-key", budget_microusd=100)
except ConflictError as e:
    print(f"  Idempotency: {e}")

print("\nAll error conditions handled correctly.")
store.close()
