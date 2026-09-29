# Changelog

All notable changes to ApexGraphSwarm are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.10.0] — 2026-09-29

### Breaking Changes

- **Sigma.js v3 → v4 alpha migration.** Upgraded `sigma` from `3.0.3` to `4.0.0-alpha.7`. The constructor options API was restructured: flat options are now split into `styles` (declarative node/edge styling) and `settings` (imperative renderer settings). The `clickNode` event payload now wraps the original `MouseEvent` under `event.original`. `getCanvases()` was removed in favor of `getStageCanvas()`. Camera animation methods (`animatedZoom`, `animatedUnzoom`, `animatedReset`) now return `Promise<void>`. See `reports/sigma-v4-migration.md` for the full migration report.

#### Files Modified

- `apps/web/package.json` — `sigma` version `3.0.3` → `4.0.0-alpha.7`
- `apps/web/package-lock.json` — updated lockfile
- `apps/web/components/GraphCanvasEnhanced.tsx` — migrated constructor options, event handler, export function
- `apps/web/components/GraphCanvas.tsx` — migrated constructor options
- `reports/sigma-v4-migration.md` — new migration report

#### Performance

- Graphology construction: 28.53 ms → 17.99 ms (−37%)
- ForceAtlas2 layout (1800 nodes, 14400 edges, 30 iterations): 253.06 ms → 221.19 ms (−13%)
- Layout checksum identical across versions, confirming deterministic output

#### Verification

- TypeScript typecheck: clean
- Web tests: 183/183 passed
- No browser rendering benchmark performed; v4 uses WebGL2 and SDF-based label rendering

---

## [0.9.0] — 2026-09-28

#### Added

- **Interactive analytics detail cards.** All 20 supported chart/detail families now expose inspection targets with first-click pinning, keyboard focus, Escape dismissal, category selection, and tooltip placement.
- **Bounded decision workspaces.** New `/decisions` workspace with typed question batches, Laya and AnyJev adapter support, and contextual navigation.
- **AnyJev L0 loopback bridge.** New `integrations/anyjev_bridge.py` — an optional, separately launched process that binds to `127.0.0.1`, requires a bearer token, and accepts only `POST /v1/systemone` from loopback clients. Supports `choice`, `score`, and `noul` question types.
- **Decision runtime and types.** New `apps/web/lib/decision-runtime.ts`, `decision-types.ts`, `decision-fixture.ts`, and `chart-tooltip-details.ts`.
- **Arena studio.** New `/arena` page for shareable Swarm Arena runs with SHA-256 integrity validation.
- **Chart tooltip component.** New `ChartTooltip.tsx` with detailed inspection on hover/focus/click.

#### Changed

- Analytics visual components refactored for shared card implementation (pointer enter/move/leave handlers).
- `AnalyticsVisual.tsx`, `AnalyticsVisualGallery.tsx`, `AnalyticsCharts.tsx` updated for new tooltip system.
- `IntegrationsPanel.tsx` minor updates.

#### Bug Fixes

- Fixed horizontal-bar selection callback in analytics visualizations.
- Fixed fullscreen flex-sizing mismatch in Graph Studio (canvas and outer frame now share non-shrinking height).
- Fixed browser-found numeric JSON roundtrip mismatch in specialist design (protected by Node parse/stringify regression test).

#### Security

- AnyJev bridge: bearer token required, loopback-only, bodies capped at 64 KiB, state to 16,000 characters, requests to 8 questions, total decision options to 32.
- Bridge uses generic upstream errors; never echoes prompts, upstream payloads, or exception text.

#### Verification

- Python: 200 tests passed (14.0–14.7 s)
- Web: 183 tests passed (15.3–15.4 s)
- TypeScript typecheck and production build passed
- Browser: 390 px viewport, no horizontal overflow, no console errors

---

## [0.8.0] — 2026-09-27

#### Added

- **Orchestration controls and analytics visualization studio.** Major expansion adding:
  - `apexgraphswarm/analytics.py` — versioned JSON analytics response builder with KPIs, daily totals, cohorts, heatmaps, graph relationships, latency distribution, correlation, scatter points, anomalies, and spend forecasting.
  - `apexgraphswarm/delegation_plan.py` — constrained schedule-to-durable-delegation-plan compiler.
  - `apexgraphswarm/evaluation.py` — reproducible evaluation and promotion gate with Hoeffding bounds, paired empirical-Bernstein intervals, and field-specific metric profiles.
  - `apexgraphswarm/evolution.py` — bounded algorithm-configuration evolution with exact subset enumeration oracle.
  - `apexgraphswarm/execution_graph.py` — persisted execution/authorization/cost graph projection.
  - `apexgraphswarm/inference_telemetry.py` — bounded read-only Prometheus collector for vLLM metrics.
  - `apexgraphswarm/optimization.py` — pure deterministic planners (DAG schedule, evidence selection, coding waves, capacity recommendation).
  - `apexgraphswarm/provider_receipts.py` — OpenRouter receipt normalization and reconciliation.
  - `apexgraphswarm/receipt_reconciliation.py` — atomic settlement with generation ID ownership.
  - `apexgraphswarm/repository_conflicts.py` — Git commit-based conflict-aware wave planning.
  - `apexgraphswarm/request_registry.py` — credential-scoped hashed idempotency key registry.
  - `apexgraphswarm/specialist_access.py` — local specialist access contracts with approval quorum.
  - `apexgraphswarm/access.py` — access grant and ledger management.
  - `apexgraphswarm/identity.py` — worker identity and credential management.
  - `apexgraphswarm/ledger.py` — execution attempt ledger.
  - `apexgraphswarm/lab.py` — authenticated local optimization dispatcher.
- **Analytics Studio UI.** New `/analytics` page with authenticated read-only ledger queries, validated CSV/JSON imports, opt-in visible-page refresh, operational statistics, cohort economics, graph relationships, and guarded seven-day spending baseline.
- **Optimization Lab UI.** New `/optimization` page with nine experiment templates, hierarchy planner, and execution graph visualization.
- **Durable dispatch.** New `apps/web/lib/durable-dispatch.ts` and `execution-request-client.ts` for planned task execution.
- **Analytics visualization gallery.** 21 implemented chart/detail choices including bar, column, stacked, pie, donut, treemap, waterfall, funnel, line, area, gauge, KPI cards, table, pivot matrix, decomposition, and data narrative.
- **Analytics relationship graph.** Shared `GraphCanvas` WebGL renderer with Sigma, Graphology, ForceAtlas2 worker, and SVG fallback.
- **Execution trace and ledger UI components.**
- **Resource capacity enforcement.** `ControlStore` now supports administrator-configured concurrency ceilings for exact resource identifiers.
- **Worker credential system.** Enrolled workers with opaque 256-bit credentials, SHA-256 hashed storage, and authenticated CLI operations.
- **Specialist contract binding.** `bindSpecialistContract` CLI action for binding plans to active contracts.
- **Planned task worker.** `executePlannedTask` and `withExistingTaskDispatch` for executing compiled durable tasks.

#### Changed

- `apexgraphswarm/control.py` — major expansion: access grants, execution attempts, worker enrollment, checkpoints, resource capacity, specialist contract integration.
- `apps/web/components/GraphCanvas.tsx` — enhanced with new features.
- `apps/web/lib/integration-runtime.ts` — updated for durable dispatch.
- `apps/web/lib/control-client.ts` — extended with new actions.
- `apps/web/package.json` — new dependencies.

#### Security

- Worker credentials are opaque 256-bit values; only SHA-256 hashes stored in SQLite.
- Checkpoints reject secret-bearing fields and worker credentials.
- Request registry stores only SHA-256 digests of keys, tokens, and bodies.
- Registry capped at 100,000 records; refuses new registrations when full.
- Credential rotation creates a new idempotency scope.
- Specialist contracts require authenticated distinct-principal approvals.
- Administrative and physical actuation actions fail closed.

#### Verification

- Python: 214 tests passed (13.8 s)
- Web: 183 tests passed (15.4 s)
- TypeScript typecheck and production build passed
- Browser: 390 px viewport, no horizontal overflow, no console errors

---

## [0.7.0] — 2026-09-27

#### Changed

- **README updated** to present ApexGraphSwarm as a standalone engineering platform. Reframed from an extraction project to a platform for building, understanding, and evaluating agentic graph and swarm systems.

---

## [0.6.0] — 2026-09-27

#### Added

- **Graph screenshots and animated walkthrough.** 17 actual UI captures, 68-second loop walkthrough GIF (1.7 MB), static poster, and capture manifest.
- **Screenshot gallery.** 16 PNG screenshots covering modules, files, symbols, search, force layout, node search, function neighborhood, evidence direction, constraints, directed path, local specialists, integrations, economics, export/storage, scope hierarchy, scope assignment, and scope drilldown.
- **Media documentation.** `docs/media/README.md` with full gallery index and provenance.

---

## [0.5.0] — 2026-09-27

#### Added

- **Comprehensive documentation.** README expanded from 48 lines to 37,108 bytes with full platform documentation including quick start, workspaces, suggested workflow, architecture, graph intelligence, specialist teams, orchestration, models/harnesses, evaluation, optimization, capabilities and boundaries, verification, deployment, and documentation index.

---

## [0.4.0] — 2026-09-27

#### Added

- **Specialist team and scoped authority designer.** New `/teams` page with:
  - `SpecialistDesigner.tsx` — create specialists with precise responsibility/acceptance criteria and model/harness references.
  - `SpecialistEditor.tsx` — edit specialist details.
  - `ScopeTopology.tsx` — zoomable scope hierarchy with up to 40 direct children and searchable directory.
  - `specialist-design.ts` — validated design model with bounded import validation.
  - `identity-evidence.ts` — identity project evidence references.
  - IAM/PAM intent configuration per specialist (provider, subject, owner, tenant, audience, purpose, actions, resources, TTL, delegation limit, approval quorum).
  - Authorization preview with exact request validation.
  - Browser storage persistence and JSON export/import.
- **Design limits:** 300 specialists, 300 scope nodes, 64 teams.

#### Security

- Design stores only design metadata; no credentials minted.
- Approval IDs are unverified simulation input, not authenticated receipts.
- `maxDelegationDepth` is a proposed adapter policy; preview does not mint live delegation chains.
- Administrative and physical actuation requests remain denied.

#### Verification

- Python: 31 tests passed (6.3 s)
- Web: 101 tests passed (0.9 s)
- TypeScript and production build passed
- Browser: 390 px viewport, no console errors

---

## [0.3.0] — 2026-09-27

#### Added

- **Orchestration retrieval and optimization comparison lab.** New `/ecosystem/research` page with:
  - `ArchitectureLab.tsx` — compare orchestration projects, retrieval frameworks, and optimization opportunities.
  - `architecture-benchmark.ts` — benchmark design with baseline, required metrics, and recovery/cost gates.
  - `optimization-evidence.ts` — structured, UI-consumable evidence records.
  - `orchestration-evidence.ts` — orchestration landscape evidence.
  - `retrieval-evidence.ts` — retrieval and graph-store landscape evidence.
  - `ecosystem-catalog.ts` — selectable source catalog.
  - Comparison-candidate selection and workload-specific benchmark design export.
- **New docs:** `architecture-comparison.md`, `optimization-bottlenecks.md`, `orchestration-landscape.md`, `retrieval-landscape.md`.

#### Verification

- Python: 31 tests passed (5.3 s)
- Web: 90 tests passed (0.9 s)
- TypeScript and production build passed
- Browser: 390 px viewport, no console errors

---

## [0.2.0] — 2026-09-27

#### Added

- **AX architecture and MCP skills ecosystem workspace.** New `/ecosystem` page with:
  - `EcosystemWorkspace.tsx` — selectable source catalog with configured endpoint discovery.
  - `mcp-discovery.ts` — bounded read-only MCP protocol discovery with explicit server-owned allowlist.
  - `skill-manifest.ts` — bounded SKILL.md review importer with exact content hashes.
  - `ecosystem-catalog.ts` — source catalog for AX, MCP, and skills.
  - MCP handshake/version/session/pagination/SSE limits.
  - Skill review with exact-content hashing and malformed metadata rejection.
- **New docs:** `ecosystem-interoperability.md`, `google-ax-assessment.md`, `mcp-interoperability.md`, `skills-interoperability.md`.

#### Security

- MCP discovery is read-only; never calls discovered tools.
- Skill review does not fetch, install, or execute skill packages.
- Content hashes are not trust verdicts.

#### Verification

- Python: 31 tests passed (5.4 s)
- Web: 86 tests passed (0.9 s)
- TypeScript and production build passed
- Browser: 390 px viewport, no console errors

---

## [0.1.0] — 2026-09-27

#### Added

- **Initial ApexGraphSwarm engineering workspace.** Extracted from `play-anything` working tree with:
  - **Python control plane** (`apexgraphswarm/control.py`) — SQLite-based durable scheduler with plan admission, lease lifecycle, heartbeat/fencing, cost reservation/settlement in integer micro-USD, execution classes (fixture, local_idempotent, external_idempotent, external), recovery, reconciliation, and JSON-lines CLI.
  - **Repository graph** (`apexgraphswarm/repository_graph.py`) — source-grounded graph extraction with validated snapshots, evidence labels, and graph queries.
  - **Preview** (`apexgraphswarm/preview.py`) — preview generation.
  - **Web application** (`apps/web/`) — Next.js app with:
    - Graph Studio with Sigma WebGL, Graphology, ForceAtlas2 layout, SVG fallback.
    - Delegation planner with cost routing.
    - Execution economics calculator.
    - Model review and model swarm.
    - Integration catalog and runtime.
    - Neo4j export.
    - Evaluation lab.
    - Swarm control.
  - **Integrations** (`integrations/`) — harness runner, kernel sources, harness profiles.
  - **Scripts** (`scripts/`) — benchmark swarm, setup integration kernels.
  - **Tests** — 31 Python tests, 63 web tests.
  - **Docs** — control-plane, extraction, evaluation, cost routing, harness costs, kernel capability matrix, local harness runner, Neo4j setup, verification, agent integrations, integration source audit.

#### Architecture

- Python 3.10+ standard library only (no external runtime dependencies).
- Next.js web application with npm dependencies.
- SQLite WAL mode with `BEGIN IMMEDIATE` for serialized claims.
- Port 3010 for web application.

#### Security

- Private workspace tokens excluded from tracked files.
- Original credentials not copied from source repository.
- No secrets in version control.

#### Verification

- Python: 31 tests passed (5.6 s)
- Web: 63 tests passed
- TypeScript and production build passed
- Browser: source graph identity, active WebGL, fullscreen/Escape, responsive navigation, no horizontal overflow

---

## Summary of Breaking Changes by Version

| Version | Breaking Change |
|---------|-----------------|
| 0.10.0 | Sigma.js v3 → v4 alpha: constructor options restructured, event payload changed, `getCanvases()` removed, camera animations return Promises |

## Summary of Security Patches by Version

| Version | Security Improvement |
|---------|---------------------|
| 0.8.0 | Worker credentials (opaque 256-bit, SHA-256 hashed), checkpoint secret rejection, request registry with hashed keys, credential rotation scope, specialist contract approval quorum |
| 0.9.0 | AnyJev bridge bearer token, loopback-only binding, body/state/question/option limits, generic upstream errors |
| 0.4.0 | Specialist design stores metadata only, no credential minting, actuation actions fail closed |

## Test Suite Growth

| Version | Python Tests | Web Tests |
|---------|-------------|-----------|
| 0.1.0 | 31 | 63 |
| 0.2.0 | 31 | 86 |
| 0.3.0 | 31 | 90 |
| 0.4.0 | 31 | 101 |
| 0.8.0 | 214 | 183 |
| 0.9.0 | 200 | 183 |
| 0.10.0 | — | 183 |

## Key Architectural Decisions

1. **Local-first:** SQLite control plane, no cloud dependency, no external service required for core functionality.
2. **Standard library only:** Python runtime has zero external dependencies.
3. **Explicit boundaries:** Every component documents what it does NOT do. No claims of production IAM, distributed scheduling, or live model execution without explicit configuration.
4. **Cost-aware:** Integer micro-USD accounting throughout; unknown cost is never zero.
5. **Deterministic:** All planners and optimizers are deterministic with bounded search spaces.
6. **Evidence-grounded:** Every result carries snapshot identity, source revision, limits, uncertainty, and partial status.
