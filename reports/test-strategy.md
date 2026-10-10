# ApexGraphSwarm — Comprehensive Test Strategy

**Project:** ApexGraphSwarm  
**Date:** 2026-09-29  
**Scope:** All Python modules, integrations, web frontend, and cross-cutting concerns

---

## Executive Summary

This document defines a multi-layered test strategy covering eight testing dimensions: unit, integration, end-to-end, performance, security, fuzzing, property-based, and visual regression. The strategy is tailored to ApexGraphSwarm's architecture — a local-first, dependency-free Python control plane with SQLite persistence, a Next.js web frontend, and opt-in integration bridges.

**Current state:** 28 Python test files and 30+ TypeScript test files already exist. This strategy identifies coverage gaps, formalizes the testing pyramid, and provides a roadmap for achieving production-grade confidence.

---

## 1. Architecture & Module Inventory

### 1.1 Python Control Plane (`apexgraphswarm/`)

| Module | Lines | Responsibility | Risk |
|--------|-------|---------------|------|
| `control.py` | 2010 | SQLite scheduler, DAG execution, leases, budgets, access grants | **Critical** |
| `analytics.py` | 523 | Read-only attempt analytics, forecasting, cohorts | High |
| `execution_graph.py` | 493 | Bounded projection of control history to explanation graph | High |
| `evaluation.py` | 762 | Paired evaluation, promotion gates, metric profiles | High |
| `evolution.py` | 568 | Bounded config evolution on synthetic fixtures | Medium |
| `hierarchy.py` | 421 | Hierarchical swarm assignment, metric profiles | Medium |
| `optimization.py` | 712 | DAG scheduling, wave planning, capacity recommendation | High |
| `delegation_plan.py` | 405 | Compile verified schedules into control-plane plans | Medium |
| `specialist_access.py` | 568 | Specialist contract lifecycle, approvals, task binding | High |
| `provider_receipts.py` | 386 | OpenRouter receipt normalization, vLLM cost estimation | Medium |
| `receipt_reconciliation.py` | 159 | Operator-assisted reconciliation for OpenRouter tasks | High |
| `inference_telemetry.py` | 690 | Prometheus telemetry parsing, snapshot comparison | Medium |
| `repository_graph.py` | 284 | AST-based repository graph (Python + JS/TS hints) | Medium |
| `repository_conflicts.py` | 610 | Git-based conflict planning, bounded subprocess calls | High |
| `request_registry.py` | 145 | Crash-safe idempotency registry | Medium |
| `access.py` | 52 | Exact capability checks for scheduler boundary | High |
| `identity.py` | 51 | Worker enrollment, token verification | High |
| `ledger.py` | 36 | Attempt ID stability, settlement receipts | Medium |
| `preview.py` | 68 | Bounded fixture operations for engineering UI | Low |
| `lab.py` | 93 | JSON interface to optimization experiments | Medium |

### 1.2 Integrations (`integrations/`)

| Module | Lines | Responsibility |
|--------|-------|---------------|
| `harness_runner.py` | 537 | Localhost bridge for trusted harness profiles |
| `anyjev_bridge.py` | 460 | Loopback HTTP adapter for AnyJev L0 decisions |

### 1.3 Web Frontend (`apps/web/`)

- Next.js application with 52 component directories
- 30+ existing TypeScript test files
- Sigma.js v4 graph visualization
- Analytics dashboards, delegation planner, specialist designer

### 1.4 Scripts (`scripts/`)

| Script | Responsibility |
|--------|---------------|
| `benchmark_swarm.py` | Deterministic local queue benchmark |
| `benchmark_analytics.py` | Analytics performance benchmark |
| `benchmark_optimization.py` | Optimization kernel benchmark |
| `setup_integration_kernels.py` | Kernel source setup |

---

## 2. Testing Pyramid

```
                    ┌─────────────┐
                    │   Visual    │  ~5%  (Playwright + pixel diff)
                    │  Regression │
                   ┌┴─────────────┴┐
                   │     E2E       │  ~10% (API + browser flows)
                  ┌┴───────────────┴┐
                  │  Integration    │  ~20% (module interactions)
                 ┌┴─────────────────┴┐
                 │       Unit        │  ~50% (isolated functions)
                ┌┴───────────────────┴┐
                │  Fuzz / Property   │  ~15% (generative + invariants)
                └─────────────────────┘
```

---

## 3. Unit Test Strategy

### 3.1 Principles

- **Isolation:** Each test exercises one function/class with all dependencies mocked or injected.
- **Determinism:** No wall-clock dependence; inject `clock` callables (already the pattern in `control.py`).
- **Bounded inputs:** Every `MAX_*` constant must have a boundary test.
- **Error paths:** Every `raise` statement needs a negative test.

### 3.2 Module-by-Module Unit Test Plan

#### 3.2.1 `control.py` (Critical — 2010 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Plan validation | Missing fields, oversized plans, invalid DAG (cycles, unknown deps), >MAX_TASKS, >MAX_AGENTS | P0 |
| Idempotency | Same key returns same run; different payload with same key → `ConflictError` | P0 |
| Budget enforcement | Unknown cost rejected; reserved > budget → `BudgetError`; exact boundary values | P0 |
| Lease lifecycle | Claim → complete; claim → fail (retryable); claim → fail (non-retryable); lease expiry; fenced completion | P0 |
| Access integration | Grant → claim; expired grant; revoked grant; wrong tool/resource; budget exhaustion | P0 |
| Resource capacity | Opt-in enforcement; head-of-line saturation; per-run limit vs global cap | P1 |
| Recovery | `recover_expired()` reclaims stale leases; idempotent replay | P1 |
| Concurrency | Thread-safe claim (barrier-synchronized); no double-claim under contention | P1 |
| Secret redaction | `_SECRET_FIELD` pattern matches all credential-like keys; no secrets in status/ledger output | P0 |
| Event log | Event ordering; event types; event size limits | P2 |

**Gap analysis:** Existing `test_control.py` covers DAG, idempotency, fenced completion, budget, and basic access. Missing: secret redaction tests, concurrency stress, event log verification, resource capacity edge cases at boundaries.

#### 3.2.2 `analytics.py` (High — 523 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Row validation | All 7 `EVENT_KEYS` required; extra keys rejected; type coercion (bool vs int) | P0 |
| Timezone handling | UTC daily heatmap; DST boundary; `now` as epoch/datetime/None | P0 |
| Forecast | Disjoint train/holdout; blocked on incomplete coverage; deterministic demo | P0 |
| Live source | Missing DB path (no creation); read-only open; legacy schema gap detection | P1 |
| Cohort limits | >MAX_COHORTS truncation; >MAX_SCATTER truncation; >MAX_GRAPH_NODES truncation | P1 |
| Import limits | >MAX_IMPORT_ROWS; >MAX_LIVE_ROWS; >MAX_METRIC_SAMPLE | P1 |
| Unknown cost | `actualCostMicrousd=None` with outcome≠running → liability tracking | P0 |

**Gap analysis:** Existing tests cover basic import, timezone, demo determinism, live missing path, and legacy gap. Missing: boundary tests for all MAX_* constants, cohort/scatter truncation, metric sample limits.

#### 3.2.3 `execution_graph.py` (High — 493 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Projection | Node kinds (run/task/attempt/agent/worker); edge kinds (dependency/assigned/attempt_of/executed) | P0 |
| Redaction | No payloads, results, errors, receipts, checkpoints, lease tokens in output | P0 |
| Bounded output | >MAX_NODES, >MAX_EDGES, >MAX_SOURCE_ROWS truncation | P1 |
| Ledger integration | Attempt coverage complete/missing; cost resolved/unresolved | P1 |
| Unknown attempts | `outcome='unknown'` → `needs_reconciliation` status | P1 |

**Gap analysis:** Existing tests cover projection, redaction, dependency edges, capacity saturation. Missing: truncation boundaries, ledger view integration, unknown attempt handling.

#### 3.2.4 `evaluation.py` (High — 762 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Suite validation | All required fields; version strings; task ID uniqueness; split overlap | P0 |
| Candidate comparison | Paired comparison; quality floor; latency bound; policy violations; cost cap | P0 |
| Metric profiles | Weighted scoring; missing metrics not renormalized; hard gate override | P0 |
| Promotion gate | Unknown spend blocks; accept rate regression; sealed split never scored | P1 |
| Attempt validation | Status values; cost bounds; quality score range | P1 |

**Gap analysis:** Existing tests cover weighted scoring, paired comparison, unknown cost blocking, exact oracle. Missing: suite validation edge cases, promotion gate boundary conditions, metric profile completeness.

#### 3.2.5 `evolution.py` (Medium — 568 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Determinism | Same seed → same splits, same selection, same sealed hash | P0 |
| Sealed split | Generated but never scored/selected | P0 |
| Candidate grid | All 4 exponents; work bound enforcement; broken candidate fails | P0 |
| Heldout gate | Unknown cost blocks promotion; missing cost cap blocks | P1 |
| Fixture bounds | >MAX_ITEMS, >MAX_CLAIMS, >MAX_TRAIN, >MAX_HELDOUT, >MAX_SEALED | P1 |

**Gap analysis:** Existing tests cover determinism, sealed split, broken candidate, unknown cost, exact oracle. Missing: work bound boundaries, candidate grid completeness, fixture generation limits.

#### 3.2.6 `hierarchy.py` (Medium — 421 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Metric profiles | All 5 profiles; weights sum to 100; hard gates separate | P0 |
| Weighted score | Complete vs partial metrics; explicit missing list | P0 |
| Plan validation | Task/agent capability matching; dependency ordering; budget/deadline | P1 |
| Assignment | Capability coverage; action authorization; resource scope; data boundary | P1 |

**Gap analysis:** Existing tests cover weight sums, weighted score, missing metrics, plan hierarchy. Missing: assignment edge cases, capability mismatch scenarios, boundary validation.

#### 3.2.7 `optimization.py` (High — 712 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| DAG scheduling | Dependency ordering; budget feasibility; deadline enforcement; capacity limits | P0 |
| Infeasibility | Budget exceeded; deadline missed; capacity zero; cycle detection | P0 |
| Unknown cost | `None` cost → status "unknown", never treated as free | P0 |
| Wave planning | Conflict detection (shared writes); wave count minimization | P1 |
| Evidence selection | Bounded items; relevance scoring; deduplication | P1 |
| Capacity recommendation | Utilization target; telemetry sample bounds | P1 |
| Overflow | Aggregate duration overflow rejection | P1 |

**Gap analysis:** Existing tests cover scheduling, infeasibility, unknown cost, overflow, cycles. Missing: wave planning edge cases, evidence selection bounds, capacity recommendation boundaries.

#### 3.2.8 `delegation_plan.py` (Medium — 405 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Compilation | Schedule recomputation; control-compatible dependency emission | P0 |
| Validation | Problem field validation; binding field validation; adapter mapping | P0 |
| Review graph | Node/edge limits; confidence levels; byte size limit | P1 |
| Task inputs | Goal bounds; graph embedding; parameter validation | P1 |

**Gap analysis:** Existing tests cover compilation, schedule recomputation, review graph. Missing: binding validation edge cases, task input bounds, compiled plan size limit.

#### 3.2.9 `specialist_access.py` (High — 568 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Contract lifecycle | Create → approve → activate → bind → revoke; invalid transitions | P0 |
| Approval quorum | Single approver; multi approver; unlisted approver rejected | P0 |
| Secret rejection | `_SECRET` pattern; unsafe keys (`__proto__`, `constructor`, `prototype`) | P0 |
| Task binding | Field validation; action matching; expiry; execution input bounds | P1 |
| Design validation | Agent/team/node field sets; policy field validation | P1 |

**Gap analysis:** Existing tests cover contract lifecycle, approval quorum, secret rejection, task binding. Missing: design validation edge cases, policy field boundaries, delegation depth limits.

#### 3.2.10 `provider_receipts.py` (Medium — 386 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Normalization | Completion vs generation metadata; token usage extraction; cost ceiling | P0 |
| Reconciliation | Generation ID match; model match; cost agreement; currency validation | P0 |
| vLLM estimation | GPU count bounds; allocation seconds; rate limits | P1 |
| Validation | Missing fields; mismatched IDs; negative cost; oversized payload | P1 |

**Gap analysis:** Existing tests cover normalization, reconciliation, ID/model mismatch, currency. Missing: vLLM estimation bounds, token count limits, payload size limits.

#### 3.2.11 `receipt_reconciliation.py` (High — 159 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Checkpoint matching | `:started` / `:receipt` suffix matching; duplicate call IDs rejected | P0 |
| Coverage | Exact match with saved checkpoints; missing entries rejected | P0 |
| Settlement | Atomic settlement request; operator ID validation | P1 |
| Bounds | Entry count limit; input byte limit; JSON finiteness | P1 |

**Gap analysis:** Existing tests cover checkpoint matching, coverage, settlement. Missing: bounds testing, operator ID validation edge cases.

#### 3.2.12 `inference_telemetry.py` (Medium — 690 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Prometheus parsing | Gauge/counter/histogram families; label extraction; type validation | P0 |
| Snapshot comparison | Delta calculation; window bounds; rate computation | P0 |
| Endpoint safety | URL validation; localhost enforcement; redirect rejection | P0 |
| Bounds | Body size; metric lines; label count; label value length; token length | P1 |

**Gap analysis:** Existing tests cover parsing, labels, duplicates, malformed labels, byte limits. Missing: snapshot comparison edge cases, endpoint safety validation, histogram bucket handling.

#### 3.2.13 `repository_graph.py` (Medium — 284 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Python AST | Imports, calls, inheritance, recursion, nested functions, shadowed params | P0 |
| JS/TS hints | Import detection; export detection; inferred confidence | P1 |
| Privacy | `.env` exclusion; generated directory exclusion; symlink skip | P0 |
| Limits | `max_files`, `max_symbols` boundaries; truncation flag | P1 |
| Determinism | Same input → same output | P1 |

**Gap analysis:** Existing tests cover calls/imports/inheritance, shadowed params, self-calls, JS hints, limits, privacy. Missing: determinism verification, symlink handling, `.env.example` inclusion.

#### 3.2.14 `repository_conflicts.py` (High — 610 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Git session | Subprocess count limit; total time limit; per-call timeout | P0 |
| Conflict planning | Read overlap detection; change overlap detection; wave assignment | P0 |
| Verification | Plan digest stability; base revision validation; task ID validation | P1 |
| Bounds | >MAX_TASKS, >MAX_DEPENDENCIES, >MAX_READS, >MAX_CHANGES | P1 |
| Environment | Safe git environment; hooks disabled; fsmonitor disabled | P1 |

**Gap analysis:** Existing tests cover conflict planning, verification, git session. Missing: bounds testing, environment safety verification, subprocess failure handling.

#### 3.2.15 `request_registry.py` (Medium — 145 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Registration | Atomic create-or-lookup; durable across reopen; no raw data persisted | P0 |
| Conflict | Same scoped key + different payload → `RequestConflictError` | P0 |
| Concurrency | Concurrent contenders converge on one job ID | P1 |
| Validation | SHA-256 format; UUID canonical form; path creation with mode 0o700 | P1 |

**Gap analysis:** Existing tests cover registration, conflict, concurrency, validation. Missing: path permission verification, database corruption recovery.

#### 3.2.16 `access.py` (High — 52 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Authorization | Exact tuple match; missing principal; expired grant; revoked grant | P0 |
| Budget | Spent + reserved + new ≤ max; boundary equality | P0 |
| Grant ID | UUID format; uniqueness | P2 |

**Gap analysis:** Existing tests cover fail-closed, expiry, revocation. Missing: budget boundary equality, concurrent grant exhaustion.

#### 3.2.17 `identity.py` (High — 51 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Enrollment | Hash-only persistence; credential length bounds | P0 |
| Verification | Constant-time comparison; revoked worker; expired worker | P0 |
| Timing safety | Absent identity still performs comparison (no timing leak) | P1 |

**Gap analysis:** Existing tests cover enrollment, verification, persistence. Missing: timing safety verification, credential length boundaries.

#### 3.2.18 `ledger.py` (Medium — 36 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Attempt ID | Deterministic across retries; different task/attempt → different ID | P0 |
| Settlement | Idempotent replay; different settlement rejected; unknown attempt ignored | P0 |

**Gap analysis:** Existing tests cover stability, cost attribution, expiry. Missing: concurrent settlement race conditions.

#### 3.2.19 `preview.py` (Low — 68 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Fixture creation | Agent count bounds (1/10/30/100/300); idempotency | P1 |
| Fixture execution | Advance completes all tasks; non-fixture payload rejected | P1 |
| Status | Run status reporting; spent cost = 0 | P2 |

**Gap analysis:** Existing tests cover fixture creation, completion, bounds. Missing: non-fixture rejection, status after partial completion.

#### 3.2.20 `lab.py` (Medium — 93 lines)

| Area | Test Cases | Priority |
|------|-----------|----------|
| Action dispatch | All actions routed; unknown action rejected | P0 |
| Input bounds | Non-finite JSON rejected; oversized input rejected | P0 |
| CLI | Exit codes; error JSON format; no traceback leak | P1 |

**Gap analysis:** Existing tests cover action rejection, CLI bounds, inspectable output. Missing: all action routing tests, telemetry action, evolve action.

### 3.3 Integration Test Strategy

#### 3.3.1 Module Interaction Matrix

| Source | Target | Interaction | Test Scenario |
|--------|--------|-------------|---------------|
| `control.py` | `access.py` | Grant → claim | Full dispatch flow with access enforcement |
| `control.py` | `identity.py` | Enroll → claim_authenticated | Worker authentication end-to-end |
| `control.py` | `ledger.py` | Attempt → settle | Cost attribution across retries |
| `control.py` | `specialist_access.py` | Contract → bind → claim | Specialist dispatch with contract enforcement |
| `control.py` | `execution_graph.py` | Status → projection | Graph projection from live control state |
| `control.py` | `analytics.py` | Ledger → analytics | Analytics from persisted control history |
| `control.py` | `receipt_reconciliation.py` | Checkpoint → reconcile | OpenRouter reconciliation flow |
| `optimization.py` | `delegation_plan.py` | Schedule → compile | Plan compilation from optimization output |
| `evaluation.py` | `evolution.py` | Evaluate → gate | Evolution with evaluation gating |
| `hierarchy.py` | `control.py` | Plan → create_run | Hierarchical assignment to control plane |
| `repository_graph.py` | `delegation_plan.py` | Graph → review | Repository graph embedded in delegation |
| `repository_conflicts.py` | `optimization.py` | Waves → plan | Conflict-aware wave planning |
| `inference_telemetry.py` | `optimization.py` | Telemetry → capacity | Capacity recommendation from telemetry |
| `provider_receipts.py` | `receipt_reconciliation.py` | Receipt → reconcile | Full reconciliation pipeline |
| `request_registry.py` | `control.py` | Register → dispatch | Idempotent dispatch with registry |

#### 3.3.2 Integration Test Scenarios

**Scenario 1: Full Dispatch Lifecycle**
```
create_run → grant_access → enroll_worker → claim_authenticated →
checkpoint_authenticated → complete → ledger → analytics
```
Verify: cost attribution, attempt IDs, ledger consistency, analytics accuracy.

**Scenario 2: Specialist Contract Dispatch**
```
create_contract → approve_contract → activate_contract → bind_plan →
create_run → claim_authenticated (with contract) → complete
```
Verify: contract enforcement, approval quorum, task binding validation.

**Scenario 3: OpenRouter Reconciliation**
```
create_run → claim → checkpoint(:started) → checkpoint(:receipt) →
reconcile_openrouter_task → verify settlement
```
Verify: checkpoint matching, coverage validation, atomic settlement.

**Scenario 4: Evolution with Evaluation**
```
run_evolution → evaluate_candidate → compare_candidates →
verify sealed split not scored → verify unknown cost blocks promotion
```
Verify: deterministic splits, conservative gate, sealed split isolation.

**Scenario 5: Repository Graph → Delegation**
```
build_repository_graph → compile_delegation_plan (with review graph) →
verify graph embedding → verify node/edge limits
```
Verify: AST parsing, graph projection, plan compilation.

**Scenario 6: Conflict-Aware Wave Planning**
```
plan_repository_conflicts → verify plan → plan_waves →
verify wave count → verify conflict detection
```
Verify: Git analysis, read overlap detection, wave minimization.

**Scenario 7: Idempotent Dispatch with Registry**
```
register_hashed_request → dispatch → register_hashed_request (same key) →
verify same job ID → register_hashed_request (different payload) →
verify conflict
```
Verify: crash-safe deduplication, scope isolation, conflict detection.

**Scenario 8: Telemetry-Driven Capacity**
```
collect_configured_telemetry → compare_snapshots → recommend_capacity →
verify capacity bounds
```
Verify: Prometheus parsing, snapshot comparison, capacity recommendation.

### 3.4 End-to-End Test Strategy

#### 3.4.1 Python CLI E2E

| Flow | Command | Verification |
|------|---------|-------------|
| Repository graph | `python -m apexgraphswarm graph /path/to/repo` | Valid JSON output; node/edge structure |
| Lab dispatch | `echo '{"action":"waves",...}' \| python -m apexgraphswarm.lab` | Correct wave plan JSON |
| Lab benchmark | `echo '{"action":"benchmark"}' \| python -m apexgraphswarm.lab` | Deterministic benchmark report |
| Lab evaluate | `echo '{"action":"evaluate",...}' \| python -m apexgraphswarm.lab` | Evaluation report |
| Lab evolve | `echo '{"action":"evolve",...}' \| python -m apexgraphswarm.lab` | Evolution result with sealed split |
| Lab compile | `echo '{"action":"compileDelegation",...}' \| python -m apexgraphswarm.lab` | Compiled plan |
| Lab hierarchy | `echo '{"action":"hierarchy",...}' \| python -m apexgraphswarm.lab` | Hierarchy assignment |
| Lab telemetry | `echo '{"action":"telemetry","windowSeconds":1}' \| python -m apexgraphswarm.lab` | Telemetry comparison |

#### 3.4.2 Integration Bridge E2E

| Flow | Setup | Verification |
|------|-------|-------------|
| Harness runner | Start `HarnessRunner` with test profile; HTTP POST | Process spawn, output capture, timeout |
| AnyJev bridge | Start `BridgeService`; HTTP POST with decision | Question normalization, decision payload |
| Preview fixture | `operate({'action':'createFixture',...})` | Fixture creation, advance, completion |

#### 3.4.3 Web Frontend E2E

| Flow | Tool | Verification |
|------|------|-------------|
| Repository graph rendering | Playwright | Graph canvas renders nodes/edges |
| Analytics dashboard | Playwright | Charts render with data |
| Delegation planner | Playwright | Plan compilation flow |
| Specialist designer | Playwright | Contract creation and assignment |
| Execution graph view | Playwright | Graph projection rendering |
| Lab dispatch | Playwright | JSON input → result display |

---

## 4. Performance Test Strategy

### 4.1 Benchmarks

| Benchmark | Module | Metric | Target |
|-----------|--------|--------|--------|
| Queue benchmark | `benchmark_swarm.py` | Tasks/sec at 300 agents | ≥ 1000 tasks/sec |
| Analytics import | `benchmark_analytics.py` | Rows/sec at 10K rows | ≥ 5000 rows/sec |
| Optimization | `benchmark_optimization.py` | Schedules/sec at 500 tasks | ≥ 100 schedules/sec |
| Repository graph | `repository_graph.py` | Files/sec at 2000 files | ≥ 200 files/sec |
| Control claim | `control.py` | Claims/sec (single worker) | ≥ 500 claims/sec |
| Control claim (concurrent) | `control.py` | Claims/sec (64 workers) | ≥ 2000 claims/sec |
| Analytics forecast | `analytics.py` | Forecast latency at 200K rows | ≤ 500ms |
| Evolution | `evolution.py` | Evolution latency at max bounds | ≤ 2s |
| Telemetry parse | `inference_telemetry.py` | Parse latency at 100K lines | ≤ 200ms |

### 4.2 Stress Tests

| Scenario | Load | Duration | Success Criteria |
|----------|------|----------|-----------------|
| Control claim storm | 64 threads × 1000 claims | 60s | No deadlocks; no double-claims |
| Analytics import | 10K rows × 100 batches | 120s | Memory stable; no OOM |
| Repository graph | 10K files × 10 runs | 300s | Consistent timing; no fd leak |
| Git conflict analysis | 32 tasks × 64 reads | 120s | Subprocess limits enforced |
| Request registry | 100K registrations | 300s | No corruption; durable across restart |

### 4.3 Profiling Targets

| Module | Function | Profile Focus |
|--------|----------|--------------|
| `control.py` | `claim()` | Lock contention, SQLite wait time |
| `analytics.py` | `build_analytics()` | Memory allocation, sort complexity |
| `optimization.py` | `schedule_dag()` | Exact solver branching factor |
| `repository_graph.py` | `build_repository_graph()` | AST parse time, memory per file |
| `inference_telemetry.py` | `parse_prometheus()` | Regex matching, line processing |
| `repository_conflicts.py` | `plan_repository_conflicts()` | Subprocess spawn time, I/O |

---

## 5. Security Test Strategy

### 5.1 Input Validation Fuzzing

| Target | Attack Vector | Expected Behavior |
|--------|--------------|-------------------|
| `control.py` plan | Deeply nested JSON (recursion) | `ControlError` with size limit |
| `control.py` plan | Non-finite numbers (NaN, Infinity) | `ControlError` |
| `control.py` plan | Oversized payload (>2MB) | `ControlError` |
| `analytics.py` rows | Extra keys in event | `AnalyticsError` |
| `analytics.py` rows | Boolean instead of int for cost | `AnalyticsError` |
| `specialist_access.py` | `__proto__` key in contract | `SpecialistContractError` |
| `specialist_access.py` | `constructor` key in contract | `SpecialistContractError` |
| `specialist_access.py` | Secret-like field names | `SpecialistContractError` |
| `provider_receipts.py` | Negative cost | `ReceiptError` |
| `provider_receipts.py` | Non-numeric cost string | `ReceiptError` |
| `inference_telemetry.py` | Oversized exposition (>2MB) | `TelemetryError` |
| `inference_telemetry.py` | Malformed label syntax | `TelemetryError` |
| `repository_conflicts.py` | Command injection in task ID | `RepositoryConflictError` |
| `request_registry.py` | Non-SHA-256 digest | `RequestRegistryError` |
| `request_registry.py` | Non-canonical UUID | `RequestRegistryError` |

### 5.2 Access Control Tests

| Scenario | Setup | Expected |
|----------|-------|----------|
| Missing principal | `claim()` without `principal_id` | `AccessDenied` |
| Wrong tool | Grant for tool A, claim with tool B | `AccessDenied` |
| Wrong resource | Grant for resource A, claim with resource B | `AccessDenied` |
| Expired grant | Grant expired at T, claim at T+1 | `AccessDenied` |
| Revoked grant | Grant revoked, claim attempted | `AccessDenied` |
| Budget exhaustion | Spent + reserved = max, claim with cost | `AccessDenied` |
| Worker not enrolled | `claim_authenticated` with unknown worker | `WorkerIdentityError` |
| Worker expired | Enrollment expired, claim attempted | `WorkerIdentityError` |
| Worker revoked | Enrollment revoked, claim attempted | `WorkerIdentityError` |
| Contract not activated | Bind task with inactive contract | `SpecialistContractError` |
| Contract expired | Bind task with expired contract | `SpecialistContractError` |
| Approval not satisfied | Quorum=2, only 1 approval | `SpecialistContractError` |

### 5.3 Secret Handling Tests

| Scenario | Verification |
|----------|-------------|
| Worker credential | Only SHA-256 hash persisted; raw credential never in DB |
| Access token | Not in status/ledger/graph output |
| API key patterns | `_SECRET_FIELD` regex matches all credential-like keys |
| Contract secrets | `_SECRET` pattern rejects credential fields in contract JSON |
| Receipt payload | Provider payload text never copied into receipts |
| Error messages | No secrets in exception messages |

### 5.4 Subprocess Safety Tests

| Scenario | Verification |
|----------|-------------|
| Git command injection | Task IDs with `;`, `|`, `$()` rejected |
| Git environment | `core.hooksPath=/dev/null`; `core.fsmonitor=false` |
| Git timeout | Per-call timeout enforced; total time limit enforced |
| Git stdout limit | Output truncated at `MAX_STDOUT_BYTES` |
| Harness argv | Fixed argv from profile; no shell injection |
| Harness timeout | Process killed at `PROCESS_TIMEOUT_SECONDS` |
| Harness output | Output capped at `MAX_OUTPUT_BYTES` |

### 5.5 Network Safety Tests

| Scenario | Verification |
|----------|-------------|
| Telemetry endpoint | Only `VLLM_METRICS_URL` env var; no URL from payload |
| Telemetry redirects | `HTTPRedirectHandler` not used (no redirect following) |
| Telemetry proxy | `ProxyHandler` not used (no proxy) |
| Harness runner | Loopback-only (`127.0.0.1`); token required |
| AnyJev bridge | Loopback-only; token required; IP validation |

---

## 6. Fuzzing Strategy

### 6.1 Python Fuzzing (Atheris / Hypothesis)

| Target | Generator | Invariant |
|--------|-----------|-----------|
| `control.py` `create_run()` | Random plan dicts (valid + invalid) | No unhandled exceptions; valid plans succeed |
| `control.py` `claim()` | Random worker IDs, lease seconds | No double-claim; lease always fenced |
| `analytics.py` `build_analytics()` | Random event rows | No unhandled exceptions; output always valid JSON |
| `evaluation.py` `evaluate_candidate()` | Random attempt lists | Score in [0,1]; no division by zero |
| `optimization.py` `schedule_dag()` | Random DAGs | Feasible schedule respects all constraints |
| `hierarchy.py` `plan_hierarchy()` | Random task/agent configs | All tasks assigned or explicitly unassigned |
| `provider_receipts.py` `normalize_openrouter_receipt()` | Random receipt dicts | Cost always non-negative integer micro-USD |
| `inference_telemetry.py` `parse_prometheus()` | Random exposition text | No unhandled exceptions; series always valid |
| `repository_graph.py` `build_repository_graph()` | Random Python source files | No unhandled exceptions; graph always valid |
| `specialist_access.py` `create_contract()` | Random contract dicts | No secrets in canonical form |

### 6.2 Integration Fuzzing

| Target | Generator | Invariant |
|--------|-----------|-----------|
| `harness_runner.py` | Random HTTP payloads | No process spawn without valid profile |
| `anyjev_bridge.py` | Random HTTP payloads | No unhandled exceptions; error JSON returned |
| `request_registry.py` | Random digests/UUIDs | No corruption; conflict detected |

### 6.3 Web Frontend Fuzzing

| Target | Generator | Invariant |
|--------|-----------|-----------|
| Analytics import | Random CSV/JSON | Graceful error; no crash |
| Lab dispatch | Random JSON payloads | Error JSON returned; no crash |
| Repository graph | Random file trees | Graph renders or error shown |

---

## 7. Property-Based Testing Strategy

### 7.1 Python (Hypothesis)

| Property | Module | Statement |
|----------|--------|-----------|
| `attempt_id` determinism | `ledger.py` | `attempt_id(t, a) == attempt_id(t, a)` for all valid t, a |
| `attempt_id` injectivity | `ledger.py` | `attempt_id(t1, a1) != attempt_id(t2, a2)` when (t1,a1) ≠ (t2,a2) |
| `token_digest` determinism | `identity.py` | `token_digest(c) == token_digest(c)` for all strings |
| `token_digest` preimage resistance | `identity.py` | `token_digest(c1) != token_digest(c2)` for c1 ≠ c2 (probabilistic) |
| `weighted_score` bounds | `hierarchy.py` | `0 ≤ score ≤ 1` for all valid metric inputs |
| `weighted_score` completeness | `hierarchy.py` | `complete=True` iff all metrics present |
| `schedule_dag` feasibility | `optimization.py` | If status=feasible, all constraints satisfied |
| `schedule_dag` dependency | `optimization.py` | If status=feasible, start[dep] ≤ start[task] for all deps |
| `schedule_dag` budget | `optimization.py` | If status=feasible, total_cost ≤ budget |
| `normalize_openrouter_receipt` cost | `provider_receipts.py` | `costMicrousd ≥ 0` and `costMicrousd ≤ MAX_MICRO_USD` |
| `parse_prometheus` round-trip | `inference_telemetry.py` | `parse(format(series)) == series` for valid series |
| `build_repository_graph` determinism | `repository_graph.py` | Same input → same output |
| `build_repository_graph` bounds | `repository_graph.py` | `len(nodes) ≤ max_files + max_symbols` |
| `plan_repository_conflicts` digest | `repository_conflicts.py` | Same input → same digest |
| `register_hashed_request` idempotency | `request_registry.py` | Same args → same job_id; different payload → conflict |
| `compare_candidates` symmetry | `evaluation.py` | `compare(a, b) == -compare(b, a)` (for comparable candidates) |

### 7.2 TypeScript (fast-check)

| Property | Module | Statement |
|----------|--------|-----------|
| Analytics visualization | `analytics-graph.test.ts` | Node count ≤ data point count |
| Graph rendering | `graph.test.ts` | All nodes have valid x,y coordinates |
| Delegation planner | `delegation-planner.test.ts` | Compiled plan has valid dependency graph |
| Specialist activation | `specialist-activation.test.ts` | Contract state transitions are valid |

---

## 8. Visual Regression Strategy

### 8.1 Web Frontend Screenshots

| Page | Viewport | Capture Points |
|------|----------|---------------|
| Repository graph | 1280×900, 1920×1080 | Initial load, after layout, after filter |
| Analytics dashboard | 1280×900, 1920×1080 | Charts rendered, tooltip visible |
| Delegation planner | 1280×900 | Plan compiled, graph embedded |
| Specialist designer | 1280×900 | Contract created, assignment view |
| Execution graph | 1280×900 | Graph projection, node selection |
| Lab dispatch | 1280×900 | Result display, error state |

### 8.2 Visual Regression Tools

| Tool | Purpose | Threshold |
|------|---------|-----------|
| Playwright | Screenshot capture | Pixel-perfect |
| `pixelmatch` | Image diff | ≤ 0.1% pixel difference |
| `odiff` | Image diff with reporting | ≤ 0.5% pixel difference |

### 8.3 Visual Test Scenarios

| Scenario | Setup | Verification |
|----------|-------|-------------|
| Graph layout stability | Same repo, same seed | Identical node positions |
| Theme consistency | Light/dark mode | Colors match design system |
| Responsive layout | 1280×900, 1920×1080, 375×667 | No overflow, readable text |
| Loading states | Slow network | Skeleton screens shown |
| Error states | Invalid input | Error message displayed |
| Empty states | No data | Empty state message shown |

---

## 9. Test Infrastructure

### 9.1 Python Test Stack

| Tool | Purpose |
|------|---------|
| `pytest` | Test runner |
| `pytest-cov` | Coverage reporting |
| `pytest-xdist` | Parallel execution |
| `hypothesis` | Property-based testing |
| `atheris` | Fuzzing (optional) |
| `freezegun` | Time mocking (alternative to injectable clock) |
| `responses` | HTTP mocking |

### 9.2 TypeScript Test Stack

| Tool | Purpose |
|------|---------|
| `vitest` | Unit test runner |
| `@playwright/test` | E2E and visual regression |
| `fast-check` | Property-based testing |

### 9.3 CI Pipeline

```yaml
stages:
  - lint
  - unit
  - integration
  - performance
  - security
  - e2e
  - visual

unit:
  script: pytest tests/ -x -q --cov=apexgraphswarm --cov-report=xml
  coverage: '/^TOTAL.*\s+(\d+%)$/'

integration:
  script: pytest tests/ -k "integration" -x -q

performance:
  script: python scripts/benchmark_swarm.py && python scripts/benchmark_analytics.py

security:
  script: pytest tests/ -k "security or adversarial" -x -q

e2e:
  script: npx playwright test

visual:
  script: npx playwright test --project=visual-regression
```

### 9.4 Coverage Targets

| Module | Line Coverage | Branch Coverage |
|--------|--------------|-----------------|
| `control.py` | ≥ 90% | ≥ 85% |
| `analytics.py` | ≥ 90% | ≥ 85% |
| `execution_graph.py` | ≥ 90% | ≥ 85% |
| `evaluation.py` | ≥ 85% | ≥ 80% |
| `evolution.py` | ≥ 85% | ≥ 80% |
| `hierarchy.py` | ≥ 85% | ≥ 80% |
| `optimization.py` | ≥ 85% | ≥ 80% |
| `delegation_plan.py` | ≥ 85% | ≥ 80% |
| `specialist_access.py` | ≥ 90% | ≥ 85% |
| `provider_receipts.py` | ≥ 85% | ≥ 80% |
| `receipt_reconciliation.py` | ≥ 90% | ≥ 85% |
| `inference_telemetry.py` | ≥ 85% | ≥ 80% |
| `repository_graph.py` | ≥ 85% | ≥ 80% |
| `repository_conflicts.py` | ≥ 85% | ≥ 80% |
| `request_registry.py` | ≥ 90% | ≥ 85% |
| `access.py` | ≥ 95% | ≥ 90% |
| `identity.py` | ≥ 95% | ≥ 90% |
| `ledger.py` | ≥ 95% | ≥ 90% |
| `preview.py` | ≥ 80% | ≥ 75% |
| `lab.py` | ≥ 85% | ≥ 80% |

---

## 10. Test Data Management

### 10.1 Fixtures

| Fixture | Location | Purpose |
|---------|----------|---------|
| Simple plan | `tests/fixtures/simple_plan.json` | Basic 2-task DAG |
| Paid plan | `tests/fixtures/paid_plan.json` | External dispatch with cost |
| Specialist design | `tests/fixtures/specialist_design.json` | Contract with agents/teams/nodes |
| Evaluation suite | `tests/fixtures/evaluation_suite.json` | Suite with splits |
| Repository fixture | `tests/fixtures/repo/` | Git repo with Python + JS files |
| Prometheus exposition | `tests/fixtures/metrics.txt` | vLLM metrics sample |
| OpenRouter receipt | `tests/fixtures/receipt.json` | Provider receipt sample |

### 10.2 Factories

| Factory | Module | Generates |
|---------|--------|-----------|
| `make_plan()` | `control.py` | Valid plan dicts with configurable tasks/agents |
| `make_event()` | `analytics.py` | Valid event rows with configurable fields |
| `make_attempt()` | `evaluation.py` | Valid attempt records |
| `make_contract()` | `specialist_access.py` | Valid contract dicts |
| `make_receipt()` | `provider_receipts.py` | Valid receipt dicts |
| `make_dag()` | `optimization.py` | Valid DAG task lists |

---

## 11. Risk-Based Test Prioritization

### 11.1 P0 — Critical (Must pass before any release)

- `control.py`: Plan validation, idempotency, budget enforcement, lease lifecycle, access integration
- `access.py`: All authorization paths
- `identity.py`: All verification paths
- `specialist_access.py`: Contract lifecycle, approval quorum, secret rejection
- `receipt_reconciliation.py`: Checkpoint matching, coverage validation
- `request_registry.py`: Registration, conflict detection, concurrency

### 11.2 P1 — High (Must pass before feature release)

- `analytics.py`: Row validation, timezone, forecast, live source
- `execution_graph.py`: Projection, redaction, bounded output
- `evaluation.py`: Suite validation, candidate comparison, promotion gate
- `optimization.py`: DAG scheduling, infeasibility, unknown cost
- `delegation_plan.py`: Compilation, validation
- `provider_receipts.py`: Normalization, reconciliation
- `inference_telemetry.py`: Parsing, snapshot comparison, endpoint safety
- `repository_conflicts.py`: Git session, conflict planning

### 11.3 P2 — Medium (Should pass before release)

- `evolution.py`: Determinism, sealed split, candidate grid
- `hierarchy.py`: Metric profiles, weighted score, plan validation
- `repository_graph.py`: Python AST, JS/TS hints, privacy
- `preview.py`: Fixture creation, execution
- `lab.py`: Action dispatch, input bounds

### 11.4 P3 — Low (Nice to have)

- Event log ordering
- Grant ID uniqueness
- Determinism verification
- Profiling benchmarks

---

## 12. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

1. Set up `pytest` configuration with coverage
2. Create fixture files and factories
3. Write missing P0 unit tests
4. Establish CI pipeline

### Phase 2: Integration (Week 3-4)

1. Write integration tests for all module interactions
2. Set up test database fixtures
3. Write E2E tests for CLI flows
4. Achieve ≥ 80% line coverage

### Phase 3: Advanced (Week 5-6)

1. Add property-based tests with Hypothesis
2. Add fuzzing with Atheris
3. Set up performance benchmarks
4. Add security test suite

### Phase 4: Frontend (Week 7-8)

1. Set up Playwright for E2E
2. Add visual regression tests
3. Add property-based tests for TypeScript
4. Achieve ≥ 70% frontend coverage

### Phase 5: Hardening (Week 9-10)

1. Achieve coverage targets
2. Performance regression testing
3. Security audit
4. Documentation

---

## 13. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Line coverage | ≥ 85% | `pytest-cov` |
| Branch coverage | ≥ 80% | `pytest-cov` |
| Test pass rate | 100% | CI pipeline |
| Flaky test rate | < 1% | CI pipeline |
| Performance regression | < 5% | Benchmark comparison |
| Security findings | 0 critical | Security test suite |
| Visual regression | 0 unexpected | Visual test suite |

---

## 14. Appendix: Existing Test Inventory

### 14.1 Python Tests (28 files)

| File | Module | Tests |
|------|--------|-------|
| `test_access.py` | `access.py` | 2 tests |
| `test_analytics.py` | `analytics.py` | 4 tests |
| `test_analytics_adversarial.py` | `analytics.py` | 4 tests |
| `test_anyjev_bridge.py` | `anyjev_bridge.py` | 5 tests |
| `test_benchmarks.py` | `benchmark_swarm.py` | 4 tests |
| `test_control.py` | `control.py` | 6 tests |
| `test_delegation_plan.py` | `delegation_plan.py` | 5 tests |
| `test_evaluation.py` | `evaluation.py` | 4 tests |
| `test_evolution.py` | `evolution.py` | 4 tests |
| `test_execution_graph.py` | `execution_graph.py` | 4 tests |
| `test_harness_runner.py` | `harness_runner.py` | 5 tests |
| `test_hierarchy.py` | `hierarchy.py` | 4 tests |
| `test_inference_telemetry.py` | `inference_telemetry.py` | 6 tests |
| `test_ledger.py` | `ledger.py` | 2 tests |
| `test_optimization.py` | `optimization.py` | 6 tests |
| `test_optimization_lab.py` | `lab.py` | 3 tests |
| `test_preview.py` | `preview.py` | 2 tests |
| `test_provider_receipts.py` | `provider_receipts.py` | 5 tests |
| `test_receipt_reconciliation.py` | `receipt_reconciliation.py` | 6 tests |
| `test_repository_conflicts.py` | `repository_conflicts.py` | 5 tests |
| `test_repository_graph.py` | `repository_graph.py` | 6 tests |
| `test_repository_privacy.py` | `repository_graph.py` | 1 test |
| `test_request_registry.py` | `request_registry.py` | 3 tests |
| `test_resource_capacity.py` | `control.py` | 3 tests |
| `test_specialist_access.py` | `specialist_access.py` | 5 tests |
| `test_specialist_contract_adversarial.py` | `specialist_access.py` | 5 tests |
| `test_worker_identity.py` | `identity.py` | 5 tests |

### 14.2 TypeScript Tests (30+ files)

| File | Area |
|------|------|
| `analytics-graph.test.ts` | Analytics visualization |
| `analytics-import.test.ts` | Analytics data import |
| `analytics-route.test.ts` | Analytics routing |
| `analytics-visual-tooltip-math.test.ts` | Tooltip calculations |
| `analytics-visuals-adversarial.test.ts` | Adversarial visualization |
| `analytics-visuals.test.ts` | Visualization rendering |
| `architecture-benchmark.test.ts` | Architecture benchmarking |
| `decision-fixture.test.ts` | Decision fixtures |
| `decision-route.test.ts` | Decision routing |
| `decision-runtime.test.ts` | Decision runtime |
| `delegation-planner.test.ts` | Delegation planning |
| `durable-dispatch.test.ts` | Durable dispatch |
| `ecosystem-catalog.test.ts` | Ecosystem catalog |
| `execution-economics.test.ts` | Execution economics |
| `execution-graph.test.ts` | Execution graph |
| `execution-request-client.test.ts` | Request client |
| `framework-adapters.test.ts` | Framework adapters |
| `graph.test.ts` | Graph rendering |
| `hermes-adapter.test.ts` | Hermes adapter |
| `integration-catalog.test.ts` | Integration catalog |
| `integration-runtime.test.ts` | Integration runtime |
| `mcp-discovery.test.ts` | MCP discovery |
| `mcp-route.test.ts` | MCP routing |
| `model-review.test.ts` | Model review |
| `model-swarm.test.ts` | Model swarm |
| `neo4j-store.test.ts` | Neo4j store |
| `optimization-route.test.ts` | Optimization routing |
| `orchestrator.test.ts` | Orchestrator |
| `planned-task.test.ts` | Planned task |
| `renderer-lifecycle.test.ts` | Renderer lifecycle |
| `skill-manifest.test.ts` | Skill manifest |
| `specialist-activation.test.ts` | Specialist activation |
| `specialist-design.test.ts` | Specialist design |
| `specialist-python-contract.test.ts` | Python contract |

---

*End of test strategy document.*
