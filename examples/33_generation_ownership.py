"""Example 33: Provider generation ownership tracking.

Track which provider generation IDs are bound to which task
invocations to prevent duplicate billing.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

# The control plane automatically tracks provider generation ownership
# when tasks are claimed and completed with provider metadata.
# This prevents the same generation ID from being billed twice.

plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {
            "id": "review-1",
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

run = store.create_run(plan, idempotency_key="gen-ownership", budget_microusd=5000)
run_id = run["run"]["id"]

# Grant access for the task
store.grant_access(
    principal_id="worker-1",
    tool_id="integration:openrouter:review",
    resource_id="model-pool-a",
    max_budget_microusd=1000,
    expires_at=9999999999.0,
)

claim = store.claim(run_id, "worker-1", principal_id="worker-1")
print(f"Claimed: {claim['id']}")

# Complete with provider metadata
store.complete(
    claim["taskId"],
    claim["leaseToken"],
    {"generationId": "gen-abc123", "model": "gpt-4"},
    500,
)
print("Completed with generation ID: gen-abc123")

# The generation ID is now bound to this task invocation
# Attempting to use it again will raise ConflictError

store.close()
