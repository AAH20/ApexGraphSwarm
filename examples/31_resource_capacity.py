"""Example 31: Resource capacity management.

Configure exact resource caps for concurrency control.
Capacity cannot be lowered below currently occupied work.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

# Configure resource capacity
result = store.configure_resource_capacity("model-pool-a", max_concurrency=5)
print(f"Resource: {result['resourceId']}")
print(f"Max concurrency: {result['maxConcurrency']}")
print(f"Occupied: {result['occupiedCount']}")
print(f"Changed: {result['changed']}")

# Check capacity status
status = store.resource_capacity_status()
print(f"\nConfigured resources: {status['totalConfiguredResources']}")
for res in status["resources"]:
    print(f"  {res['resourceId']}: {res['occupiedCount']}/{res['maxConcurrency']} "
          f"(available: {res['availableCount']}, overcommitted: {res['overcommitted']})")

# Try to lower below occupied (will fail if occupied > new limit)
try:
    store.configure_resource_capacity("model-pool-a", max_concurrency=0)
except Exception as e:
    print(f"\nCorrectly rejected invalid capacity: {e}")

store.close()
