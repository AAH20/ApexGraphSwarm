# Tutorial 3: Solver Kernels

## Overview

ApexGraphSwarm includes four original optimization kernels that provide bounded graph selection, agent/task optimization, swarm simulation, and combined graph/swarm solver interfaces. This tutorial explains what each kernel does, how to set them up, and how to run experiments.

## The Four Kernels

| Kernel | Repository | Role |
|--------|-----------|------|
| graph-rag-np-hard-kernel | [AAH20/graph-rag-np-hard-kernel](https://github.com/AAH20/graph-rag-np-hard-kernel) | Bounded graph selection and GraphRAG optimization experiments |
| agentic-np-hard-kernel | [AAH20/agentic-np-hard-kernel](https://github.com/AAH20/agentic-np-hard-kernel) | Agent/task optimization interfaces |
| mirofish-swarm-optimizer | [AAH20/mirofish-swarm-optimizer](https://github.com/AAH20/mirofish-swarm-optimizer) | Swarm/simulation optimization experiments |
| agentic-graph-swarm-kernel | [AAH20/agentic-graph-swarm-kernel](https://github.com/AAH20/agentic-graph-swarm-kernel) | Combined graph/swarm solver interfaces |

## Important Caveats

> **No universal NP-hard solver, optimality, or superiority claim follows from exposing these adapters.** Their objective values are not interchangeable benchmark scores. Read the [source audit](../integration-source-audit.md), [capability matrix](../kernel-capability-matrix.md), and [bottleneck analysis](../optimization-bottlenecks.md) before drawing conclusions.

## Setup

### 1. Fetch Kernel Sources

```sh
python3 scripts/setup_integration_kernels.py --write-env
```

This downloads the four pinned public source repositories into `.integration-sources/` and adds missing local configuration while preserving existing values.

### 2. Verify Installation

```sh
python3 scripts/setup_integration_kernels.py --check
```

### 3. Configure Access Token

Execution controls require the private workspace token configured as `INTEGRATION_ACCESS_TOKEN` in `apps/web/.env.local`. Enter it only in the local execution control that requests it. Keep it out of screenshots, shared exports, and commits.

## Running Experiments

### Via the Optimization Lab

Navigate to [http://127.0.0.1:3010/optimization](http://127.0.0.1:3010/optimization) to access the Optimization Lab. The available workstreams are:

| Workstream | What It Does |
|-----------|-------------|
| Execution ledger | Stable attempt identities, task/tool/resource attribution, settlement receipts, retry accounting |
| Exact access grants | Principal/tool/resource matching, expiry, revocation, budget checks |
| Scheduling and delegation | Dependency/model-capacity/budget/deadline constraints, bounded exact search |
| Evidence selection | Weighted coverage under token budgets, exact small-instance oracle and greedy fallback |
| Coding swarm planning | Dependency-respecting waves, declared access conflicts, committed Git diffs |
| Evaluation and evolution | Versioned task splits, held-out gates, bounded local greedy configuration search |
| Inference capacity | Recommendations over supplied measurements plus optional bounded vLLM metrics |

### Via the Python Lab Module

```sh
# Run the reproducible synthetic benchmark
python3 -m scripts.benchmark_optimization

# Or send one bounded JSON request on stdin
printf '%s\n' '{"action":"benchmark"}' | python3 -m apexgraphswarm.lab
```

### Via the Swarm Arena

Navigate to [http://127.0.0.1:3010/arena](http://127.0.0.1:3010/arena) to run the five-case deterministic optimization fixture. The Arena produces a self-contained evidence snapshot with:

- Run checksum
- Source hashes
- Measurement environment
- Timings and accounting

Share links contain the full report; no result is uploaded to a public leaderboard.

## Understanding Results

### Synthetic vs. Real

The kernels run on **bounded synthetic snapshots**. Results include:
- Readable assignments
- Declared dependency graphs
- Conflict waves
- Local benchmark timings
- Full JSON evidence exports

These measure **local algorithm runtime and gate behavior**. They do **not** establish performance on PSPLIB, GraphRAG-Bench, ToolSandbox, Terminal-Bench, or real agent workloads.

### Cost and Telemetry

Synthetic costs and telemetry are explicitly labeled. Unknown costs remain unknown. The fixture suite does not generate code or deploy anything.

## Benchmarking

To produce a new benchmark artifact without overwriting the checked-in baseline:

```sh
python3 scripts/benchmark_swarm.py --help
python3 scripts/benchmark_swarm.py --counts 30 100 300 --workers 32 --output /tmp/apex-swarm-benchmark.json
```

### Recorded Baseline

The largest measured fixture on 2026-09-27:

| Measure | Result |
|---------|--------|
| Logical agents | 300 |
| Fixture tasks | 600 |
| Active worker limit / observed peak | 32 / 32 |
| Elapsed time | 6,267.171 ms |
| Duplicate completions | 0 |
| Provider calls / API spend | 0 / $0 |
| Recovery checks | Reopen, recovery completion, stale-lease fencing recorded |

This measures SQLite orchestration of harmless fixed tasks — not model intelligence or real infrastructure control.

## Algorithm Evolution

The [algorithm evolution experiment](../algorithm-evolution.md) executes bounded synthetic candidates and preserves sealed fixtures for independent evaluation. Configuration evolution should pass held-out quality and budget/latency gates before promotion.

## Next Steps

- [Tutorial 4: Agent Orchestration](04-agent-orchestration.md) — Understand the control plane that powers these experiments.
- [Tutorial 7: Performance Tuning](07-performance-tuning.md) — Dive deeper into benchmarking and optimization.
