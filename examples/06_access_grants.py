"""Example 06: Access grants and capability-based authorization.

Grants provide exact (principal, tool, resource) capability scoping
with budget limits and expiry. They are checked transactionally
at claim time.
"""
import time
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

# Create a capability grant
expires_at = time.time() + 3600
grant = store.grant_access(
    principal_id="agent-1",
    tool_id="integration:openrouter:review",
    resource_id="model-pool-a",
    max_budget_microusd=500_000,  # $0.50
    expires_at=expires_at,
)
print(f"Grant ID: {grant['grantId']}")
print(f"Tool: {grant['tool']}")
print(f"Resource: {grant['resource']}")
print(f"Max budget: {grant['maxBudgetMicrousd']} micro-USD")

# Revoke the grant
revoked = store.revoke_access(grant["grantId"])
print(f"Grant revoked: {revoked}")

# After revocation, claims requiring this grant will be denied
store.close()
