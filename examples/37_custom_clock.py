"""Example 37: Custom clock for testing.

ControlStore accepts a custom clock function for deterministic
testing of time-dependent behavior.
"""
from apexgraphswarm.control import ControlStore

class FakeClock:
    def __init__(self, value=1000.0):
        self.value = value

    def __call__(self):
        return self.value

# Create store with fake clock
clock = FakeClock(1000.0)
store = ControlStore(":memory:", clock=clock)

plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "t1", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 2, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="clock-demo", budget_microusd=0)
run_id = run["run"]["id"]

# Claim with 30-second lease
claim = store.claim(run_id, "worker-1", lease_seconds=30)
print(f"Claimed at t={clock.value}")
print(f"Lease expires at: {claim['leaseExpiresAt']}")

# Advance time by 20 seconds (lease still valid)
clock.value = 1020.0
hb = store.heartbeat(claim["taskId"], claim["leaseToken"], lease_seconds=30)
print(f"Heartbeat at t={clock.value}, new expiry: {hb['leaseExpiresAt']}")

# Advance time past lease expiry
clock.value = 1051.0
store.recover_expired()
status = store.status(run_id)
task = status["tasks"][0]
print(f"After expiry at t={clock.value}: task status = {task['status']}")

store.close()
