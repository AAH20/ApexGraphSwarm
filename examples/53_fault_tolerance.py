"""Example 53: Advanced - fault tolerance and retry logic.

Implement fault-tolerant task execution with automatic retries
and exponential backoff.
"""
import time
import random
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "flaky-task", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 5, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="retry-demo", budget_microusd=0)
run_id = run["run"]["id"]

max_retries = 5
base_delay = 0.1

for attempt in range(max_retries):
    claim = store.claim(run_id, "worker-1", lease_seconds=30)
    if claim is None:
        print(f"Attempt {attempt+1}: No task available (run may be complete)")
        break

    try:
        # Simulate flaky work
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Simulated failure")

        store.complete(claim["taskId"], claim["leaseToken"], {"ok": True}, 0)
        print(f"Attempt {attempt+1}: SUCCESS")
        break

    except Exception as e:
        print(f"Attempt {attempt+1}: FAILED - {e}")

        # Check if we can retry
        status = store.status(run_id)
        task = next(t for t in status["tasks"] if t["taskId"] == claim["taskId"])

        if task["attempts"] < task["maxAttempts"]:
            # Exponential backoff
            delay = base_delay * (2 ** attempt)
            print(f"  Retrying in {delay:.1f}s...")
            time.sleep(delay)

            # Mark as retryable failure
            store.fail(claim["taskId"], claim["leaseToken"], str(e), retryable=True)
        else:
            print(f"  Max retries exceeded, marking as failed")
            store.fail(claim["taskId"], claim["leaseToken"], str(e), retryable=False)
            break

status = store.status(run_id)
print(f"\nFinal status: {status['run']['status']}")
task = status["tasks"][0]
print(f"Task attempts: {task['attempts']}/{task['maxAttempts']}")

store.close()
