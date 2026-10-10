"""Example 02: Creating a ControlStore instance.

The ControlStore is the durable, local-first SQLite scheduler.
It manages runs, tasks, workers, leases, and accounting.
"""
from apexgraphswarm.control import ControlStore

# In-memory database (for testing)
store = ControlStore(":memory:")
print(f"Created in-memory ControlStore (max_active={store.max_active})")

# File-based database (for persistence)
# store = ControlStore("/tmp/apex-control.sqlite", max_active=8)

# With custom limits
store_custom = ControlStore(
    ":memory:",
    max_active=16,
    max_registered_agents=100,
    max_run_cost_microusd=10_000_000,  # $10.00
)
print(f"Custom store: max_active={store_custom.max_active}, "
      f"max_agents={store_custom.max_registered_agents}")

# Always close when done
store.close()
store_custom.close()
print("Stores closed.")
