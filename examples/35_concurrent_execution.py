"""Example 35: Concurrent task execution with thread safety.

ControlStore is thread-safe. Multiple workers can claim and
complete tasks concurrently.
"""
import threading
import time
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:", max_active=8)

# Create a plan with many independent tasks
plan = {
    "version": 1,
    "agents": [{"id": f"agent-{i}"} for i in range(10)],
    "tasks": [
        {
            "id": f"task-{i}",
            "agentId": f"agent-{i}",
            "dependencies": [],
            "payload": {"kind": "fixture", "index": i},
            "reservedCostMicrousd": 0,
            "maxAttempts": 2,
            "executionClass": "fixture",
        }
        for i in range(20)
    ],
}

run = store.create_run(plan, idempotency_key="concurrent-demo", budget_microusd=0)
run_id = run["run"]["id"]

completed = []
errors = []

def worker(worker_id):
    try:
        for _ in range(5):
            claim = store.claim(run_id, f"worker-{worker_id}", lease_seconds=30)
            if claim is None:
                break
            time.sleep(0.01)  # Simulate work
            store.complete(claim["taskId"], claim["leaseToken"], {"worker": worker_id}, 0)
            completed.append(claim["id"])
    except Exception as e:
        errors.append(str(e))

# Launch concurrent workers
threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(f"Completed: {len(completed)} tasks")
print(f"Errors: {len(errors)}")
if errors:
    for e in errors:
        print(f"  Error: {e}")

status = store.status(run_id)
print(f"Final status: {status['run']['status']}")

store.close()
