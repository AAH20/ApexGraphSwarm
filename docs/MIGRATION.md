# ApexGraphSwarm Migration Guide

This document provides comprehensive migration guidance for upgrading ApexGraphSwarm across its major dependency and API changes. It covers v0.x → v1.0, Sigma v3 → v4, Graphology upgrades, API contract changes, and configuration migrations.

**Last updated:** 2026-09-29  
**Current version:** v1.0 (package.json `0.1.0`)

---

## Table of Contents

- [Overview](#overview)
- [v0.x → v1.0 Migration](#v0x--v10-migration)
- [Sigma v3 → v4 Migration](#sigma-v3--v4-migration)
- [Graphology Upgrades](#graphology-upgrades)
- [API Changes](#api-changes)
- [Configuration Changes](#configuration-changes)
- [Python Control Plane Changes](#python-control-plane-changes)
- [Testing Changes](#testing-changes)
- [Verification Checklist](#verification-checklist)

---

## Overview

ApexGraphSwarm has undergone significant evolution from its initial prototype to its current v1.0 state. The major migration areas are:

| Area | Before | After | Breaking? |
|------|--------|-------|-----------|
| Sigma.js | 3.0.3 | 4.0.0-alpha.7 | Yes |
| Graphology | 0.26.0 (single package) | 0.26.0 + 4 companion packages | Additive |
| Next.js | 16.3.6 | 16.3.6 | No |
| React | 19.3.0 | 19.3.0 | No |
| Python control plane | Basic fixture runner | Full SQLite scheduler with auth | Yes |
| API routes | Minimal | 10 route handlers | Yes |
| Environment config | 5 variables | 30+ variables | Additive |

---

## v0.x → v1.0 Migration

### Architecture Changes

The project transitioned from a simple graph viewer to a full engineering workspace:

**Before (v0.x):**
- Single `GraphCanvas` component with basic Sigma rendering
- No enhanced graph features (minimap, communities, centrality)
- Simple fixture-based control plane
- No specialist team designer
- No analytics or decision workspaces
- No optimization lab

**After (v1.0):**
- Dual canvas system: `GraphCanvas` (basic) + `GraphCanvasEnhanced` (full-featured)
- SQLite-backed `ControlStore` with worker identity, capability grants, and specialist contracts
- Full specialist team designer with scope hierarchies
- Analytics workspace with import/visualization
- Decision intelligence with Laya/AnyJev integration
- Optimization lab with scheduling, evidence, and evolution experiments
- Swarm Arena with five-case synthetic benchmark suite

### File System Changes

```
v0.x structure:
  apexgraphswarm/
    __init__.py
    __main__.py
    repository_graph.py
    control.py          # Basic fixture runner
    preview.py

v1.0 structure:
  apexgraphswarm/
    __init__.py
    __main__.py
    repository_graph.py
    control.py          # Full SQLite scheduler (1400+ lines)
    preview.py
    execution_graph.py  # NEW: Read-only projection
    analytics.py        # NEW: Bounded analytics
    optimization.py     # NEW: Scheduling/evidence/waves
    evolution.py        # NEW: Evolution gates
    evaluation.py       # NEW: Held-out evaluation
    hierarchy.py        # NEW: Hierarchical planning
    delegation_plan.py  # NEW: Cost-aware delegation
    identity.py         # NEW: Worker credentials
    access.py           # NEW: Capability grants
    ledger.py           # NEW: Attempt receipts
    specialist_access.py # NEW: Contract lifecycle
    provider_receipts.py # NEW: Receipt normalization
    receipt_reconciliation.py # NEW: Reconciliation
    repository_conflicts.py  # NEW: Conflict planning
    inference_telemetry.py   # NEW: vLLM telemetry
    lab.py              # NEW: Optimization lab interface
```

### Python Module Entry Points

All Python modules now accept JSON via stdin and output JSON to stdout:

```python
# v0.x - direct function calls
from apexgraphswarm.control import ControlStore
store = ControlStore(":memory:")

# v1.0 - JSON stdin/stdout interface
# echo '{"action":"createFixture","agents":10,"idempotencyKey":"test"}' | python3 -m apexgraphswarm.preview
```

### Database Schema Changes

The SQLite control plane now includes these tables (created automatically):

| Table | Purpose |
|-------|---------|
| `runs` | DAG run metadata, budget, status |
| `agents` | Logical agent identities per run |
| `tasks` | Task DAG with execution class, cost, lease |
| `dependencies` | Task dependency edges |
| `events` | Ordered event log |
| `control_meta` | Key-value configuration |
| `resource_capacities` | Exact resource concurrency caps |
| `worker_checkpoints` | Bounded per-attempt output |
| `provider_receipt_reconciliations` | Operator-asserted receipt evidence |
| `provider_generation_ownership` | Provider call deduplication |
| `execution_attempts` | Settled attempt receipts |
| `workers` | Enrolled worker identities |
| `access_grants` | Capability grants with budget |

**Migration note:** The `_initialize()` method includes additive migrations for databases created by earlier prototypes. New columns are added via `ALTER TABLE` if missing.

---

## Sigma v3 → v4 Migration

### Dependency Change

```json
// Before
"sigma": "3.0.3"

// After
"sigma": "^4.0.0-alpha.7"
```

### Constructor Options Restructured

Sigma v4 splits the flat v3 options object into `styles` (declarative) and `settings` (imperative):

```typescript
// v3 — flat options
new Sigma(graph, container, {
  defaultNodeColor: "#8493ff",
  defaultEdgeColor: "rgba(151, 167, 194, 0.22)",
  defaultEdgeType: "arrow",
  labelFont: "Inter, sans-serif",
  labelSize: 12,
  labelWeight: "bold",
  labelColor: { color: "#e5ebf6" },
  labelRenderedSizeThreshold: 7,
  labelDensity: 0.08,
  stagePadding: 28,
  minCameraRatio: 0.08,
  maxCameraRatio: 8,
  hideEdgesOnMove: true,
  renderEdgeLabels: false,
});

// v4 — split styles + settings
new Sigma(graph, container, {
  styles: {
    nodes: {
      x: { attribute: "x" },
      y: { attribute: "y" },
      size: { attribute: "size", defaultValue: 4 },
      color: { attribute: "color", defaultValue: "#8493ff" },
      label: { attribute: "label" },
      labelColor: "#e5ebf6",
      labelFont: "Inter, sans-serif",
      labelSize: 12,
    },
    edges: {
      size: { attribute: "size", defaultValue: 1 },
      color: { attribute: "color", defaultValue: "rgba(151, 167, 194, 0.22)" },
      label: { attribute: "label" },
      head: "arrow",
    },
  },
  settings: {
    labelRenderedSizeThreshold: 7,
    labelDensity: 0.08,
    stagePadding: 28,
    minCameraRatio: 0.08,
    maxCameraRatio: 8,
    hideEdgesOnMove: true,
    renderEdgeLabels: false,
  },
});
```

### Option Mapping Table

| v3 Option | v4 Equivalent | Notes |
|-----------|---------------|-------|
| `defaultNodeColor` | `styles.nodes.color` with `attribute: "color"` + `defaultValue` | |
| `defaultEdgeColor` | `styles.edges.color` with `attribute: "color"` + `defaultValue` | |
| `defaultEdgeType: "arrow"` | `styles.edges.head: "arrow"` | |
| `labelFont` | `styles.nodes.labelFont` | |
| `labelSize` | `styles.nodes.labelSize` | |
| `labelWeight` | **Removed** | No v4 equivalent |
| `labelColor: { color: "..." }` | `styles.nodes.labelColor: "..."` | Plain string, not object |
| `labelRenderedSizeThreshold` | `settings.labelRenderedSizeThreshold` | |
| `labelDensity` | `settings.labelDensity` | |
| `stagePadding` | `settings.stagePadding` | |
| `minCameraRatio` / `maxCameraRatio` | `settings.minCameraRatio` / `settings.maxCameraRatio` | Now `null \| number` |
| `hideEdgesOnMove` | `settings.hideEdgesOnMove` | |
| `renderEdgeLabels` | `settings.renderEdgeLabels` | |

### Event Payload Changes

```typescript
// v3 — direct MouseEvent access
renderer.on("clickNode", ({ node, event }) => {
  handleNodeClick(node, event?.shiftKey ?? false);
});

// v4 — event wrapped in MouseCoords
renderer.on("clickNode", ({ node, event }) => {
  const original = event.original as MouseEvent | undefined;
  handleNodeClick(node, original?.shiftKey ?? false);
});
```

### `getCanvases()` Removed

```typescript
// v3
const canvases = sigma.getCanvases();

// v4
const canvas = sigma.getStageCanvas();
```

### Camera Animation Returns Promise

```typescript
// v3 — void return
camera.animatedZoom({ duration: 200 });

// v4 — Promise<void> return
void camera.animatedZoom({ duration: 200 }); // void prefix still works
```

### Files Modified in v4 Migration

- `apps/web/components/GraphCanvas.tsx` — constructor options migrated
- `apps/web/components/GraphCanvasEnhanced.tsx` — constructor options, event handler, export function migrated
- `apps/web/package.json` — sigma version updated
- `apps/web/package-lock.json` — lockfile updated

### Performance Impact

Benchmark results (1800 nodes, 14400 edges, 30 ForceAtlas2 iterations):

| Metric | v3 | v4 | Delta |
|--------|----|----|-------|
| Build time | 28.53 ms | 17.99 ms | −37% |
| Layout time | 253.06 ms | 221.19 ms | −13% |
| Checksum | −126934.9236 | −126934.9236 | identical |

---

## Graphology Upgrades

### New Companion Packages

The project now uses four additional Graphology packages:

```json
{
  "graphology": "0.26.0",
  "graphology-communities-louvain": "^2.0.2",
  "graphology-layout": "^0.6.1",
  "graphology-layout-forceatlas2": "0.10.1",
  "graphology-metrics": "^2.4.2"
}
```

### Package Responsibilities

| Package | Purpose | Used In |
|---------|---------|---------|
| `graphology` | Core graph data structure | All components |
| `graphology-layout` | Layout algorithms (circular) | `GraphCanvasEnhanced.tsx` |
| `graphology-layout-forceatlas2` | Force-directed layout | Both canvas components |
| `graphology-communities-louvain` | Community detection | `GraphCanvasEnhanced.tsx` (dynamic import) |
| `graphology-metrics` | Centrality metrics (PageRank) | `GraphCanvasEnhanced.tsx` (dynamic import) |

### Dynamic Imports

Community detection and centrality are loaded via dynamic imports to keep the initial bundle small:

```typescript
// GraphCanvasEnhanced.tsx
useEffect(() => {
  if (!showCommunities || nodes.length < 3) {
    setCommunities(null);
    return;
  }
  let cancelled = false;
  import("graphology-communities-louvain").then((mod: { default: Louvain }) => {
    if (cancelled) return;
    try {
      const g = new Graph();
      nodes.forEach((n) => g.addNode(n.id, { kind: n.kind }));
      edges.forEach((e) => {
        if (g.hasNode(e.source) && g.hasNode(e.target)) {
          g.addEdge(e.source, e.target);
        }
      });
      setCommunities(mod.default(g));
    } catch {
      setCommunities(null);
    }
  });
  return () => { cancelled = true; };
}, [showCommunities, nodes, edges]);
```

### Graph Construction Pattern

Both canvas components now use the same graph construction pattern:

```typescript
const graph = new Graph({ multi: true, type: "directed" });

// Add nodes with attributes
graph.addNode(node.id, {
  x: point.x,
  y: point.y,
  label: node.name,
  color: nodeColor,
  size: nodeSize,
  kind: node.kind,
});

// Add edges with keys
graph.addDirectedEdgeWithKey(
  `relationship-${index}`,
  edge.source,
  edge.target,
  {
    color: "rgba(151, 167, 194, 0.22)",
    size: Math.min(2, 0.6 + Math.log2((edge.count ?? 1) + 1) * 0.25),
    relation: edge.relation,
  }
);
```

### ForceAtlas2 Layout

The ForceAtlas2 layout worker is shared between both canvas components:

```typescript
const worker = new ForceAtlas2Layout(graph, {
  settings: {
    gravity: 0.12,
    scalingRatio: 6,
    slowDown: 2,
    barnesHutOptimize: graph.order > 200,
    outboundAttractionDistribution: true,
  },
});
worker.start();
// ... 3-second timeout ...
worker.stop();
worker.kill();
```

---

## API Changes

### API Route Overview

| Route | Method | Purpose | Auth |
|-------|--------|---------|------|
| `/api/control` | POST | Fixture create/status/advance/cancel/executionGraph | `INTEGRATION_ACCESS_TOKEN` |
| `/api/swarm` | POST | Model swarm review/delegate | `GRAPH_REVIEW_ACCESS_TOKEN` |
| `/api/optimization` | POST | Lab experiments | `INTEGRATION_ACCESS_TOKEN` |
| `/api/analytics` | POST | Analytics queries | None (read-only) |
| `/api/graph-store` | GET/POST | Neo4j graph load/save | `GRAPH_STORE_ACCESS_TOKEN` |
| `/api/integrations` | GET/POST | Integration catalog/start | `INTEGRATION_ACCESS_TOKEN` |
| `/api/planned-tasks` | POST | Planned task execution | `INTEGRATION_ACCESS_TOKEN` |
| `/api/review` | POST | Model review | `GRAPH_REVIEW_ACCESS_TOKEN` |
| `/api/decisions` | POST | Decision provider queries | Varies |
| `/api/ecosystem` | GET | Ecosystem catalog | None |

### Request/Response Format

All API routes accept JSON via POST and return JSON:

```typescript
// Request
POST /api/control
Content-Type: application/json
Authorization: Bearer <token>

{
  "action": "createFixture",
  "agents": 10,
  "idempotencyKey": "my-run-key"
}

// Response
{
  "state": {
    "run": { "id": "...", "status": "queued", ... },
    "tasks": [...],
    "agents": [...]
  }
}
```

### Authentication Patterns

Three authentication mechanisms are used:

1. **Integration token** (`INTEGRATION_ACCESS_TOKEN`): Used by control, optimization, and integration routes
2. **Graph store token** (`GRAPH_STORE_ACCESS_TOKEN`): Used by graph-store route
3. **Review access token** (`GRAPH_REVIEW_ACCESS_TOKEN`): Used by swarm and review routes

All use Bearer token authentication with timing-safe comparison:

```typescript
function isAuthorized(request: Request, token: string | undefined): boolean {
  if (!token) return false;
  const value = request.headers.get("authorization") || "";
  if (!value.startsWith("Bearer ") || value.length !== token.length + 7) return false;
  const received = Buffer.from(value.slice(7));
  const expected = Buffer.from(token);
  return received.length === expected.length && timingSafeEqual(received, expected);
}
```

### Origin Validation

All state-changing routes validate the request origin:

```typescript
function hasSafeOrigin(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true; // No origin header = same-origin
  try {
    const parsed = new URL(origin);
    const host = request.headers.get("x-forwarded-host") || request.headers.get("host");
    const proto = request.headers.get("x-forwarded-proto") || new URL(request.request.url).protocol.slice(0, -1);
    return Boolean(host && parsed.host === host && parsed.protocol === `${proto}:`);
  } catch { return false; }
}
```

### Error Handling

All routes follow a consistent error pattern:

```typescript
try {
  // ... process request ...
  return Response.json({ data: result }, { headers: { "Cache-Control": "no-store" } });
} catch (error) {
  const message = error instanceof Error ? error.message : "Operation failed.";
  // Sanitize paths from error messages
  const sanitized = message.replace(/\/(?:Users|private|tmp)\/[^\s]+/g, "[local path]").slice(0, 300);
  return Response.json({ error: sanitized }, { status: 400, headers: { "Cache-Control": "no-store" } });
}
```

### Body Size Limits

| Route | Limit |
|-------|-------|
| `/api/control` | 4 KB |
| `/api/optimization` | 128 KiB |
| `/api/graph-store` | 2 MB |
| `/api/swarm` | `REVIEW_MAX_BYTES` |
| `/api/integrations` | 2 MB |

### Control Plane Actions

The `/api/control` route supports these actions:

| Action | Parameters | Description |
|--------|------------|-------------|
| `createFixture` | `agents`, `idempotencyKey` | Create a fixture run (1, 10, 30, 100, or 300 agents) |
| `status` | `runId` | Get run status |
| `advanceFixture` | `runId` | Execute fixture tasks (10 rounds of 4 workers) |
| `cancel` | `runId` | Cancel a run |
| `executionGraph` | `runId` | Get execution graph projection |

### Optimization Lab Actions

The `/api/optimization` route supports these actions:

| Action | Description |
|--------|-------------|
| `hierarchy` | Build plan-only hierarchy |
| `schedule` | Run scheduling experiment |
| `evidence` | Run evidence experiment |
| `waves` | Run wave experiment |
| `capacity` | Run capacity experiment |
| `evaluate` | Run evaluation |
| `telemetry` | Collect vLLM telemetry |
| `benchmark` | Run benchmark suite |
| `evolve` | Run evolution gate |
| `compileDelegation` | Compile delegation plan |
| `repositoryConflicts` | Plan repository conflicts |
| `verifyRepositoryConflicts` | Verify conflict plan |

---

## Configuration Changes

### Environment Variables

The `.env.example` file defines all supported variables. Key additions from v0.x:

#### Model Review (Required for `/api/review` and `/api/swarm`)

```bash
AI_GATEWAY_API_KEY=              # Private AI Gateway key
GRAPH_REVIEW_MODEL=              # Gateway model ID
GRAPH_REVIEW_ACCESS_TOKEN=       # Bearer token for review requests
```

#### Neo4j Graph Store (Optional)

```bash
NEO4J_URI=                       # HTTP origin (not Bolt URI)
NEO4J_USERNAME=
NEO4J_PASSWORD=
NEO4J_DATABASE=neo4j
GRAPH_STORE_NAMESPACE=apexgraphswarm
GRAPH_STORE_ACCESS_TOKEN=
```

#### Direct Model Providers (Optional)

```bash
OPENROUTER_API_KEY=
OPENROUTER_MODEL=
VLLM_BASE_URL=
VLLM_MODEL=
VLLM_API_KEY=
```

#### Kernel Sources (Optional)

```bash
GRAPH_RAG_KERNEL_PATH=
AGENTIC_KERNEL_PATH=
MIROFISH_KERNEL_PATH=
GRAPH_SWARM_KERNEL_PATH=
```

#### Framework Integrations (Optional)

```bash
COGNEE_BASE_URL=
COGNEE_DATASET=
COGNEE_API_KEY=
MIROFISH_BASE_URL=
LANGGRAPH_BASE_URL=
LANGGRAPH_ASSISTANT_ID=
LANGGRAPH_API_KEY=
CREWAI_BASE_URL=
CREWAI_TOKEN=
HERMES_BASE_URL=
HERMES_API_KEY=
HERMES_MODEL=
```

#### Local Harness Bridge (Optional)

```bash
LOCAL_RUNNER_URL=http://127.0.0.1:8765
LOCAL_RUNNER_ACCESS_TOKEN=
```

#### MCP Discovery (Optional)

```bash
MCP_SERVERS_JSON=[]
MCP_SERVER_TEAM_GATEWAY_TOKEN=
```

#### Durable Adapter Dispatch (Optional)

```bash
APEX_WORKER_ID=
APEX_WORKER_CREDENTIAL=
APEX_CONTROL_DB_PATH=            # Default: .runtime/control.sqlite
APEX_INTEGRATION_POLICIES_JSON=[]
```

#### vLLM Telemetry (Optional)

```bash
VLLM_METRICS_URL=
VLLM_METRICS_TOKEN=
```

#### Repository Conflicts (Optional)

```bash
APEX_REPOSITORY_PATH=            # Default: ApexGraphSwarm checkout
```

#### Decision Providers (Optional)

```bash
LAYA_PREDICT_URL=
LAYA_API_KEY=
LAYA_COST_MICROUSD_PER_QUESTION=
ANYJEV_PREDICT_URL=
ANYJEV_API_KEY=
ANYJEV_COST_MICROUSD_PER_QUESTION=
```

### Environment Variable Security Rules

1. **Never prefix with `NEXT_PUBLIC_`** — all credentials are server-side only
2. **Never commit `.env.local`** — it is in `.gitignore`
3. **Never expose in browser** — the integration catalog only exposes non-secret metadata
4. **Never log or return in error messages** — all routes sanitize paths and redact secrets

### Integration Limits

Defined in `integration-runtime.ts`:

```typescript
export const INTEGRATION_LIMITS = {
  requestBytes: 2 * 1024 * 1024,      // 2 MB
  outputBytes: 1024 * 1024,            // 1 MB
  concurrency: 2,
  queued: 12,
  timeoutMs: 45_000,
  jobTtlMs: 60 * 60_000,              // 1 hour
  maxJobs: 100,
  modelInputNodes: 300,
  modelInputEdges: 900,
  kernelNodes: 500,
  kernelEdges: 5000,
} as const;
```

### Graph Store Limits

Defined in `neo4j-store.ts`:

```typescript
export const GRAPH_STORE_MAX_BYTES = 2 * 1024 * 1024;  // 2 MB
export const GRAPH_STORE_TIMEOUT_MS = 20_000;           // 20 seconds
export const GRAPH_STORE_MAX_NODES = 20_000;
export const GRAPH_STORE_MAX_EDGES = 80_000;
```

### Graph Import Limits

Defined in `graph.ts`:

```typescript
export const LIMITS = {
  nodes: 25000,
  edges: 100000,
  bytes: 15000000,      // 15 MB
  visible: 1800,
  visibleEdges: 12000,
  findings: 24,
};
```

---

## Python Control Plane Changes

### ControlStore API

The `ControlStore` class in `control.py` is the primary interface:

```python
from apexgraphswarm.control import ControlStore

with ControlStore(".runtime/control.sqlite", max_active=4) as store:
    # Create a run
    result = store.create_run(
        plan={
            "version": 1,
            "agents": [{"id": "agent-1", "name": "Worker"}],
            "tasks": [{
                "id": "task-1",
                "agentId": "agent-1",
                "dependencies": [],
                "executionClass": "fixture",
                "payload": {"kind": "deterministic-fixture"},
                "reservedCostMicrousd": 0,
                "maxAttempts": 2,
            }],
        },
        idempotency_key="my-run-key",
        budget_microusd=0,
    )

    # Claim a task
    task = store.claim(run_id, worker_id="worker-1", lease_seconds=30)

    # Complete a task
    store.complete(task["taskId"], task["leaseToken"], {"result": "ok"}, 0)

    # Get status
    status = store.status(run_id)
```

### Worker Identity

Workers must be enrolled before they can claim tasks:

```python
# Enroll a worker (returns credential exactly once)
worker = store.enroll_worker(
    worker_id="worker-1",
    principal_id="principal-1",
    expires_at=1700000000.0,
)
# Returns: {"workerId": "worker-1", "principalId": "principal-1", "expiresAt": ..., "credential": "..."}

# Revoke a worker
store.revoke_worker("worker-1")
```

### Capability Grants

Non-fixture tasks require exact capability grants:

```python
# Create a grant
grant = store.grant_access(
    principal_id="principal-1",
    tool_id="integration:openrouter:review",
    resource_id="resource-1",
    max_budget_microusd=100000,
    expires_at=1700000000.0,
)

# Revoke a grant
store.revoke_access(grant["grantId"])
```

### Specialist Contracts

Specialist-bound tasks require a validated contract:

```python
# Configure approvers
store.configure_specialist_approvers(["approver-1", "approver-2"])

# Create a contract
contract = store.create_specialist_contract(
    idempotency_key="contract-key",
    design={...},
    assignment={...},
)

# Approve the contract
store.approve_specialist_contract(contract_id, worker_id, credential)

# Activate the contract
store.activate_specialist_contract(contract_id)

# Bind to a plan
store.bind_specialist_contract(contract_id=contract_id, plan=plan, task_id=task_id)

# Revoke
store.revoke_specialist_contract(contract_id)
```

### Resource Capacity

Resources must be configured before tasks can use them:

```python
# Configure capacity
store.configure_resource_capacity("resource-1", max_concurrency=5)

# Check status
status = store.resource_capacity_status()
```

### Execution Classes

| Class | Description | Auto-retry |
|-------|-------------|------------|
| `fixture` | Deterministic local fixture | Yes |
| `local_idempotent` | Local idempotent operation | Yes |
| `external_idempotent` | External idempotent operation | Yes |
| `external` | External non-idempotent | No |

### Budget Enforcement

- All tasks must have a known integer `reservedCostMicrousd`
- Unknown cost cannot be represented as zero
- Run budget must cover all task reservations
- Attempt reservations are settled on completion
- Unknown-cost completions move to `needs_reconciliation`

---

## Testing Changes

### Python Tests

```bash
# Run all Python tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_control.py -v
```

Test files in `tests/`:

| File | Coverage |
|------|----------|
| `test_control.py` | ControlStore, fixtures, leases, budget |
| `test_repository_graph.py` | Graph building, imports, calls |
| `test_repository_conflicts.py` | Conflict planning |
| `test_specialist_access.py` | Contract lifecycle |
| `test_access.py` | Capability grants |
| `test_ledger.py` | Attempt receipts |
| `test_analytics.py` | Analytics aggregation |
| `test_analytics_adversarial.py` | Adversarial analytics inputs |
| `test_optimization.py` | Scheduling, evidence, waves |
| `test_optimization_lab.py` | Lab interface |
| `test_evaluation.py` | Evaluation gates |
| `test_evolution.py` | Evolution experiments |
| `test_hierarchy.py` | Hierarchical planning |
| `test_delegation_plan.py` | Delegation compilation |
| `test_execution_graph.py` | Execution graph projection |
| `test_preview.py` | Fixture operations |
| `test_request_registry.py` | Request registry |
| `test_worker_identity.py` | Worker enrollment |
| `test_provider_receipts.py` | Receipt normalization |
| `test_receipt_reconciliation.py` | Reconciliation |
| `test_inference_telemetry.py` | vLLM telemetry |
| `test_resource_capacity.py` | Resource capacity |
| `test_benchmarks.py` | Benchmark suite |
| `test_harness_runner.py` | Harness runner |
| `test_anyjev_bridge.py` | AnyJev bridge |

### Web Tests

```bash
# Run all web tests
npm test

# Run with typecheck
npm run typecheck
```

Test files in `apps/web/tests/`:

| File | Coverage |
|------|----------|
| `analytics-route.test.ts` | Analytics API route |
| `analytics-import.test.ts` | Analytics import |
| `analytics-graph.test.ts` | Analytics graph |
| `analytics-visuals.test.ts` | Analytics visuals |
| `analytics-visual-tooltip-math.test.ts` | Tooltip math |
| `architecture-benchmark.test.ts` | Architecture benchmark |
| `decision-fixture.test.ts` | Decision fixtures |
| `decision-runtime.test.ts` | Decision runtime |
| `ecosystem-catalog.test.ts` | Ecosystem catalog |
| `execution-request-client.test.ts` | Execution request client |
| `framework-adapters.test.ts` | Framework adapters |
| `hermes-adapter.test.ts` | Hermes adapter |
| `integration-catalog.test.ts` | Integration catalog |
| `mcp-discovery.test.ts` | MCP discovery |
| `model-swarm.test.ts` | Model swarm |
| `neo4j-store.test.ts` | Neo4j store |
| `optimization-route.test.ts` | Optimization route |
| `planned-task.test.ts` | Planned tasks |
| `specialist-design.test.ts` | Specialist design |
| `specialist-python-contract.test.ts` | Specialist Python contract |

---

## Verification Checklist

After completing migration, verify:

### Build & Typecheck

```bash
# Install dependencies
npm --prefix apps/web ci

# Typecheck
npm --prefix apps/web run typecheck

# Build
npm --prefix apps/web run build
```

### Tests

```bash
# Python tests
python3 -m pytest tests/ -v

# Web tests
npm --prefix apps/web test
```

### Runtime

```bash
# Start development server
npm --prefix apps/web run dev

# Open http://127.0.0.1:3010
```

### Smoke Tests

1. **Graph import**: Import a repository graph snapshot
2. **Graph rendering**: Verify Sigma v4 canvas renders without errors
3. **Fixture run**: Create and advance a fixture run via `/api/control`
4. **Analytics**: Query analytics via `/api/analytics`
5. **Optimization**: Run a scheduling experiment via `/api/optimization`
6. **Specialist design**: Create and validate a specialist design
7. **Graph store**: If Neo4j is configured, test save/load

### Common Issues

| Issue | Solution |
|-------|----------|
| `sigma` import errors | Ensure `sigma@^4.0.0-alpha.7` is installed |
| `graphology-communities-louvain` not found | Run `npm --prefix apps/web ci` |
| `ControlStore` migration errors | Delete `.runtime/control.sqlite` and restart |
| `INTEGRATION_ACCESS_TOKEN` not set | Add to `apps/web/.env.local` |
| Neo4j connection fails | Verify `NEO4J_URI` is HTTP origin, not Bolt |
| Worker credential lost | Re-enroll worker; credentials are shown once |
| `executionClass` not recognized | Use one of: `fixture`, `local_idempotent`, `external_idempotent`, `external` |

---

## Support

For issues not covered by this guide:

1. Check the [README](../README.md) for general documentation
2. Review [docs/verification.md](verification.md) for testing guidance
3. Examine the [reports/](../reports/) directory for migration reports
4. Run the test suite to identify specific failures
