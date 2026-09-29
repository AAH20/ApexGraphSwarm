"""Example 34: Worker checkpoints and recovery.

Workers can save checkpoints during task execution for
crash recovery and progress tracking.
"""
from apexgraphswarm.control import ControlStore

store = ControlStore(":memory:")

plan = {
    "version": 1,
    "agents": [{"id": "a"}],
    "tasks": [
        {"id": "long-task", "agentId": "a", "dependencies": [],
         "payload": {"kind": "fixture"}, "reservedCostMicrousd": 0,
         "maxAttempts": 3, "executionClass": "fixture"},
    ],
}

run = store.create_run(plan, idempotency_key="checkpoint-demo", budget_microusd=0)
run_id = run["run"]["id"]

claim = store.claim(run_id, "worker-1")
task_id = claim["taskId"]
token = claim["leaseToken"]

# Save checkpoints during execution
store.save_checkpoint(task_id, token, "progress", {"percent": 25})
store.save_checkpoint(task_id, token, "progress", {"percent": 50})
store.save_checkpoint(task_id, token, "progress", {"percent": 75})

# Complete the task
store.complete(task_id, token, {"result": "done"}, 0)

# Read checkpoints from ledger
ledger = store.ledger(run_id)
for attempt in ledger["attempts"]:
    print(f"Attempt {attempt['attempt']}:")
    for cp in attempt.get("checkpoints", []):
        print(f"  Checkpoint: {cp['checkpointId']}")
        print(f"    SHA256: {cp['sha256'][:16]}...")
        print(f"    Size: {cp['byteLength']} bytes")

store.close()
