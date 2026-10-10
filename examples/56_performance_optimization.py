"""Example 56: Advanced - performance optimization.

Optimize control plane performance for high-throughput scenarios.
"""
import time
from concurrent.futures import ThreadPoolExecutor
from apexgraphswarm.control import ControlStore

def benchmark_claims(store, run_id, num_workers, claims_per_worker):
    """Benchmark claim throughput."""
    start = time.monotonic()

    def worker(worker_id):
        count = 0
        for _ in range(claims_per_worker):
            claim = store.claim(run_id, f"worker-{worker_id}", lease_seconds=30)
            if claim:
                count += 1
        return count

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(worker, range(num_workers)))

    elapsed = time.monotonic() - start
    total_claims = sum(results)

    return {
        "total_claims": total_claims,
        "elapsed_seconds": elapsed,
        "claims_per_second": total_claims / elapsed if elapsed > 0 else 0,
    }

# Create store with high concurrency
store = ControlStore(":memory:", max_active=64)

# Create a plan with many tasks
plan = {
    "version": 1,
    "agents": [{"id": f"agent-{i}"} for i in range(20)],
    "tasks": [
        {
            "id": f"task-{i}",
            "agentId": f"agent-{i % 20}",
            "dependencies": [],
            "payload": {"kind": "fixture", "index": i},
            "reservedCostMicrousd": 0,
            "maxAttempts": 1,
            "executionClass": "fixture",
        }
        for i in range(100)
    ],
}

run = store.create_run(plan, idempotency_key="perf-test", budget_microusd=0)
run_id = run["run"]["id"]

# Benchmark
print("Performance Benchmark:")
print("=" * 50)

for num_workers in [1, 2, 4, 8]:
    result = benchmark_claims(store, run_id, num_workers, 10)
    print(f"  Workers: {num_workers}")
    print(f"    Claims: {result['total_claims']}")
    print(f"    Time: {result['elapsed_seconds']:.3f}s")
    print(f"    Throughput: {result['claims_per_second']:.1f} claims/s")

store.close()
