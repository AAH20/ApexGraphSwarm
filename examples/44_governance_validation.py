"""Example 44: Governance - plan validation and compliance.

Validate plans against governance policies before execution.
"""
from apexgraphswarm.control import ControlStore, ControlError

store = ControlStore(":memory:")

# Governance policy: all tasks must have known budgets
def validate_governance(plan):
    """Validate plan against governance policies."""
    errors = []

    # Policy 1: All tasks must have known integer budgets
    for task in plan.get("tasks", []):
        cost = task.get("reservedCostMicrousd")
        if cost is None:
            errors.append(f"Task {task['id']}: missing budget")
        elif not isinstance(cost, int) or cost < 0:
            errors.append(f"Task {task['id']}: invalid budget {cost}")

    # Policy 2: No secret fields in payloads
    for task in plan.get("tasks", []):
        payload = task.get("payload", {})
        if isinstance(payload, dict):
            for key in payload:
                if any(s in key.lower() for s in ["api_key", "password", "secret", "token"]):
                    errors.append(f"Task {task['id']}: secret field '{key}' in payload")

    # Policy 3: Dependencies must exist
    task_ids = {t["id"] for t in plan.get("tasks", [])}
    for task in plan.get("tasks", []):
        for dep in task.get("dependencies", []):
            if dep not in task_ids:
                errors.append(f"Task {task['id']}: unknown dependency '{dep}'")

    return errors

# Valid plan
valid_plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": [],
         "payload": {"data": "value"}, "reservedCostMicrousd": 1000,
         "maxAttempts": 2, "executionClass": "fixture"},
    ],
}

errors = validate_governance(valid_plan)
print(f"Valid plan errors: {errors}")

# Invalid plan
invalid_plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": ["nonexistent"],
         "payload": {"api_key": "secret"}, "reservedCostMicrousd": -100,
         "maxAttempts": 2},
    ],
}

errors = validate_governance(invalid_plan)
print(f"Invalid plan errors: {errors}")

store.close()
