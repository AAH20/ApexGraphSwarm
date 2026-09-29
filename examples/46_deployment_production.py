"""Example 46: Deployment - production ControlStore setup.

Configure a production-ready ControlStore with appropriate
limits and monitoring.
"""
from apexgraphswarm.control import ControlStore
import os

# Production configuration
db_path = os.environ.get("APEX_CONTROL_DB", "/var/lib/apexgraphswarm/control.sqlite")

# Ensure directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Create production store with appropriate limits
store = ControlStore(
    db_path,
    max_active=int(os.environ.get("APEX_MAX_ACTIVE", "16")),
    max_registered_agents=int(os.environ.get("APEX_MAX_AGENTS", "100")),
    max_run_cost_microusd=int(os.environ.get("APEX_MAX_RUN_COST", "100_000_000")),  # $100
)

print(f"Production ControlStore initialized:")
print(f"  Database: {db_path}")
print(f"  Max active: {store.max_active}")
print(f"  Max agents: {store.max_registered_agents}")
print(f"  Max run cost: ${store.max_run_cost_microusd / 1_000_000:.2f}")

# Health check
try:
    status = store.status("non-existent-run")
    print(f"  Health check: OK (returned {status})")
except Exception as e:
    print(f"  Health check: FAILED - {e}")

# Resource capacity status
capacity = store.resource_capacity_status()
print(f"  Configured resources: {capacity['totalConfiguredResources']}")

store.close()
print("Store closed.")
