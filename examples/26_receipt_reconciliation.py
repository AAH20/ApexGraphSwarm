"""Example 26: Receipt reconciliation for unresolved tasks.

Bind supplied provider metadata to generation/model identities
that were persisted before and after each invocation.
"""
from apexgraphswarm.receipt_reconciliation import reconcile_openrouter_task
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

# Create a task that needs reconciliation
plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {
            "id": "review-task",
            "agentId": "a",
            "dependencies": [],
            "payload": {"kind": "fixture"},
            "reservedCostMicrousd": 1000,
            "maxAttempts": 1,
            "executionClass": "external",
            "tool": "integration:openrouter:review",
            "resource": "model-pool-a",
        },
    ],
}

# This is a simplified example. In practice, you would:
# 1. Create the run with the task
# 2. Claim and start the task
# 3. Save provider checkpoints
# 4. Mark the task as needs_reconciliation
# 5. Call reconcile_openrouter_task with the saved entries

print("Receipt reconciliation workflow:")
print("1. Create run with OpenRouter task")
print("2. Claim task and save :started checkpoint")
print("3. Call OpenRouter API")
print("4. Save :receipt checkpoint with generation ID")
print("5. Mark task as needs_reconciliation")
print("6. Call reconcile_openrouter_task with entries")
print("7. System normalizes receipts and settles costs")

store.close()
