# Tutorial 7: Performance Tuning

## Overview

ApexGraphSwarm is designed for bounded, predictable performance. This tutorial covers benchmarking tools, performance characteristics of each component, and tuning strategies for different workloads.

## Benchmarking Tools

### Swarm Benchmark

```sh
python3 scripts/benchmark_swarm.py --help
python3 scripts/benchmark_swarm.py --counts 30 100 300 --workers 32 --output /tmp/apex-swarm-benchmark.json
```

This runs the deterministic optimization fixture at different scales and records:
- Classification, environment, source hashes, seed
- Configuration, timing, accounting
- Recovery checks (reopen, recovery completion, stale-lease fencing)

### Optimization Benchmark

```sh
python3 -m scripts.benchmark_optimization
```

Measures local algorithm runtime and gate behavior. Includes source hashes, environment details, timings, and gate outcomes.

### Analytics Benchmark

```sh
python3 -m scripts.benchmark_analytics --rows 50000
```

Creates a reproducible temporary SQLite fixture for analytics performance testing.

## Performance Characteristics

### Control Plane (SQLite)

| Metric | Value |
|--------|-------|
| Default active lease cap | 4 |
| Max logical agents | 300 |
| Max tasks per plan | 10,000 |
| Max plan size | 2 MiB |
| Max result size | 1 MiB |
| Max event size | 64 KiB |
| Lease duration | 1–300 seconds |
| Largest measured fixture | 6,267 ms for 600 tasks, 32 workers |

The control plane uses SQLite WAL mode with `BEGIN IMMEDIATE` transactions. Claims are serialized; rows survive process restart.

### Graph Rendering

| Metric | Value |
|--------|-------|
| Visible nodes | 1,800 |
| Visible edges | 12,000 |
| Import limit | 25,000 nodes / 100,000 edges / 15 MB |
| Force layout budget | 3 seconds |
| Analyzer file limit | 2,000 files |
| Analyzer symbol limit | 10,000 symbols |
| Analyzer per-file limit | 1 MB |

### Analytics Engine

| Metric | Value |
|--------|-------|
| Live scan cap | 200,000 rows |
| Import cap | 10,000 rows |
| SQLite reads | Batched |
| Refresh interval | 30 seconds (opt-in, page visible) |

## Tuning Strategies

### For Large Repositories

1. **Narrow the scope** — Use directory filters to focus on relevant subgraphs before applying force layout.
2. **Increase analyzer limits carefully** — The defaults (2,000 files, 10,000 symbols) balance coverage and speed. Increasing them may slow analysis significantly.
3. **Use grouped layout** for large graphs; force layout is best for smaller, focused subgraphs.
4. **Inspect truncation warnings** — If the graph exceeds visible bounds, some nodes/edges may be omitted.

### For High-Concurrency Swarm Runs

1. **Adjust `max_active`** — The default is 4 concurrent leases. Increase for more parallelism, but ensure your workers can handle the load.
2. **Keep `max_registered_agents` consistent** — All worker processes must use the same value.
3. **Use `fixture` execution class** for deterministic, zero-cost work to maximize throughput.
4. **Monitor recovery** — `recover_expired()` runs before each claim; expired external work blocks the run until reconciled.

### For Analytics Performance

1. **Use the stdlib engine** for live scans up to 200,000 rows.
2. **Batch SQLite reads** — The engine already batches, but avoid unnecessary re-scans.
3. **Limit imports to 10,000 rows** — Larger datasets should use the live scan path.
4. **Enable 30-second refresh** only when the page is visible.

### For Graph Import

1. **Stay within 25,000 nodes / 100,000 edges / 15 MB** — Larger imports may fail or truncate.
2. **Review snapshot contents** before sharing — Graph snapshots contain repository metadata and source-derived summaries.
3. **Use Neo4j for persistent storage** if you need to query the graph repeatedly.

## Recorded Benchmarks

### Swarm Fixture (2026-09-27)

| Measure | Result |
|---------|--------|
| Logical agents | 300 |
| Fixture tasks | 600 |
| Active worker limit / observed peak | 32 / 32 |
| Elapsed time | 6,267.171 ms |
| Duplicate completions | 0 |
| Provider calls / API spend | 0 / $0 |
| Recovery checks | Reopen, recovery completion, stale-lease fencing recorded |

### Analytics Local Benchmark

See `docs/benchmarks/analytics-local.json` for measured evidence on the local fixture.

### Optimization Local Benchmark

See `docs/benchmarks/optimization-local.json` for source hashes, environment details, timings, and gate outcomes.

## Profiling Tips

### Python Control Plane

```python
import time
from apexgraphswarm.control import ControlStore

start = time.perf_counter()
with ControlStore(".apexgraphswarm/control.sqlite3", max_active=4) as store:
    # ... run operations ...
elapsed = time.perf_counter() - start
print(f"Elapsed: {elapsed:.3f}s")
```

### Web Application

1. Use browser DevTools to profile React renders.
2. Monitor WebGL performance in Graph Studio (check for dropped frames).
3. Use the accessible node list as a fallback when WebGL is slow.

### SQLite

```sh
# Check database size
ls -la .apexgraphswarm/control.sqlite3

# Check WAL mode
sqlite3 .apexgraphswarm/control.sqlite3 "PRAGMA journal_mode;"

# Analyze query performance
sqlite3 .apexgraphswarm/control.sqlite3 "EXPLAIN QUERY PLAN SELECT * FROM tasks WHERE run_id = 'xxx';"
```

## Common Bottlenecks

| Bottleneck | Cause | Solution |
|-----------|-------|----------|
| Slow graph rendering | Too many visible nodes/edges | Use filters, narrow scope |
| Force layout doesn't converge | Graph too dense | Use grouped layout, reduce nodes |
| Slow claims | High contention | Increase `max_active`, use `fixture` class |
| Analytics timeout | Too many rows | Limit to 200,000 rows, batch reads |
| Import failure | Graph too large | Stay within 25,000 nodes / 100,000 edges |
| Recovery blocks run | Expired external work | Reconcile promptly, use `fixture` for safe retries |

## Next Steps

- [Tutorial 3: Solver Kernels](03-solver-kernels.md) — Run optimization experiments.
- [Tutorial 8: Deployment](08-deployment.md) — Deploy with performance in mind.
