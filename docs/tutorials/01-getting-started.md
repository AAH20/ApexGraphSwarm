# Tutorial 1: Getting Started with ApexGraphSwarm

## Overview

ApexGraphSwarm is a local-first engineering workspace for repository intelligence, specialist teams, bounded swarm orchestration, evaluation, and cost-aware delegation. This tutorial walks you from zero to a running workspace, covering installation, basic concepts, and your first graph analysis.

## Prerequisites

- **Python 3.10+** (standard library only for the control plane)
- **Node.js and npm** compatible with the pinned Next.js release in `apps/web/package.json`
- **Git** (including network access if fetching optional kernel sources)

## Step 1: Clone and Install

```sh
git clone <repository-url>
cd ApexGraphSwarm
```

Install the web application dependencies:

```sh
npm --prefix apps/web ci
```

## Step 2: Start the Development Server

```sh
npm --prefix apps/web run dev
```

Open [http://127.0.0.1:3010](http://127.0.0.1:3010) in your browser.

> **Port note:** Development and production commands use port **3010** by default. Stop any existing server before starting another on that port.

## Step 3: Understand the Workspace Layout

The workspace is organized into these main areas:

| Workspace | Route | Purpose |
|-----------|-------|---------|
| Control room | `/` | Entry point and overview |
| Graph Studio | `/graph` | Search, filter, inspect, trace dependencies |
| Specialist teams | `/teams` | Define specialists, skills, tools, scopes |
| Swarm control | `/swarm` | Create and observe bounded deterministic task runs |
| Delegation & cost | `/delegation` | Compare models, constraints, cost assumptions |
| Data & intelligence | `/analytics` | Event BI, statistics, forecasts |
| Decision intelligence | `/decisions` | Typed question batches with probability inspection |
| Optimization lab | `/optimization` | Scheduling, evidence, conflict experiments |
| Evaluation lab | `/evaluations` | Measured results and held-out evaluations |
| Swarm Arena | `/arena` | Five-case synthetic optimization suite |
| Ecosystem | `/ecosystem` | Architecture comparisons, MCP discovery |

## Step 4: Explore the Prepared Graph

The workspace ships with a prepared repository graph. Navigate to **Graph Studio** (`/graph`) and:

1. **Switch views** between module, file, and symbol levels using the view toggle.
2. **Search** for a known symbol or file path using the search box.
3. **Filter** by relationship type (imports, calls, declarations) and evidence level.
4. **Inspect a node** to see its source location, summary, and incoming/outgoing relationships.
5. **Trace dependencies** using the directed path tool to find routes between two nodes.
6. **Toggle fullscreen** for an immersive exploration experience.

## Step 5: Analyze Another Repository

To analyze a local repository, use the Python CLI:

```sh
python3 -m apexgraphswarm graph /absolute/path/to/repository --output /tmp/repository-graph.json
```

Then in **Graph Studio**, choose **Import graph** and select the generated JSON file.

### Analyzer Limits

The default analyzer processes up to:
- **2,000 files** per scan
- **10,000 symbols** per scan
- **1 MB** per source file

Graph imports support up to **25,000 nodes / 100,000 edges / 15 MB**. The visible graph is bounded at **1,800 nodes / 12,000 edges** for rendering performance.

### Evidence Scope

- **Python:** AST declarations, imports, and lexical calls. Dynamic dispatch may remain unresolved.
- **JavaScript/TypeScript:** lexical hints, not compiler-complete semantic resolution.
- **Rust/Go/C++:** file inventory; compiler-backed semantic modules are planned.
- **Directory relationships:** organizational containment, not proof of runtime dependence.

## Step 6: Set Up Optional Integration Kernels

The four original optimization kernels can be fetched and configured:

```sh
python3 scripts/setup_integration_kernels.py --write-env
python3 scripts/setup_integration_kernels.py --check
```

This downloads the pinned public source repositories and adds missing local configuration. Source pins are recorded in `integrations/kernel-sources.json`; downloaded sources are ignored by Git.

## Step 7: Verify the Installation

Run the test suite from the repository root:

```sh
python3 -m unittest discover tests
npm --prefix apps/web test
npm --prefix apps/web run typecheck
```

The latest recorded verification showed **214 Python tests and 183 web tests passing**, plus typecheck and production build.

## Key Concepts

### Local-First Architecture

ApexGraphSwarm runs entirely on your machine. The Python control plane uses only the standard library. The web application is a Next.js frontend backed by a SQLite control plane. No cloud service is required for core functionality.

### Bounded Everything

Every component has explicit bounds:
- **300 logical agents** by default
- **4 concurrent active leases** (configurable)
- **300 specialists, 64 teams, 300 scope nodes** in the designer
- **1,800 visible nodes / 12,000 visible edges** in the graph
- **200,000 rows** for live analytics scans
- **10,000 rows** for analytics imports

These are operating limits, not latency guarantees.

### Design vs. Execution

ApexGraphSwarm separates **design** from **execution**. You can design specialist teams, assign scopes, and preview authorization without dispatching any agents. Execution requires explicit adapter configuration and authenticated workers.

## Next Steps

- Continue to [Tutorial 2: Graph Visualization](02-graph-visualization.md) for a deep dive into Graph Studio.
- Jump to [Tutorial 4: Agent Orchestration](04-agent-orchestration.md) to understand the control plane.
- Explore [Tutorial 5: Governance](05-governance.md) to design specialist teams with proper authority boundaries.
