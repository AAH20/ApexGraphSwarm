# Verification — 2026-09-27

## Scope

ApexGraphSwarm local project; no paid model, external framework, cloud deployment or live coding-harness execution was performed. Existing Play Anything code was preserved.

## Passed checks

- 31 Python tests, including durable scheduling, unknown-spend reconciliation, budget overruns, fixtures, graph privacy, benchmark invariants and local runner behavior. Full suite took about 5.6 seconds on this machine; no claim of the parent charter’s historical 0.05-second target.
- 63 web tests; TypeScript validation and production Next.js build.
- Authenticated Next API → Python → SQLite flow: 30 fixture tasks, repeated create idempotency, persisted reload, zero model calls, rejected unauthenticated/foreign-origin requests and rejected caller-selected database paths.
- All four pinned AAH20 kernels and the combined suite executed through the new project’s API on its 28-module, 41-edge view.
- Browser: source graph identity, active WebGL, fullscreen/Escape, responsive navigation, no horizontal overflow, cost controls and benchmark artifact display.
- Private workspace tokens excluded from candidate tracked files; original credentials were not copied.

## Measured scheduler baseline

The artifact at `apps/web/public/benchmarks/local-swarm.json` is the authoritative result with timing, source hashes, environment and seed. The largest fixture had **300 logical agents, 600 tasks and 32 active workers**, completed in approximately **6.27 seconds** (~95.7 tasks/s), with zero duplicate completions, consistent zero API-cost accounting, and restart/recovery/fencing checks passing. Timing varies with machine load.

These results measure local SQLite orchestration of harmless fixed tasks. They do not measure model quality, tool execution speed, provider concurrency, or 300 simultaneous autonomous coding agents. Zero API cost does not mean zero machine/engineering cost.

## Remaining deployment gates

Real model/harness credentials and quotas, workload-specific held-out evaluations, provider usage/invoice reconciliation, isolated workers, multi-tenant authorization and distributed deployment remain separate activation/production work. The native external framework adapters have contract tests, not live service certification. The existing integration job registry is still process-local and is not automatically made durable by the new control-plane database.

## Ecosystem interoperability — 2026-09-27

- Python regression suite: 31/31 passed in 5.378 seconds; no Python runtime dependencies or Python source changes introduced.
- Web suite: 86/86 passed in 0.891 seconds. Includes cost unknown-value propagation, skill exact-content hashing and malformed metadata rejection, MCP handshake/version/session/pagination/SSE limits, cancellation, schema bounds, protected route validation and an actual loopback HTTP MCP fixture. No paid model calls or external MCP tools were invoked.
- TypeScript and Next.js production build pass with the new `/ecosystem` and `/api/ecosystem/mcp` routes.
- Production API smoke on port 3010 passed for empty configuration, absent bearer authentication, cross-origin access and arbitrary endpoint rejection.
- Browser verification: connection filtering; empty MCP configuration state; successful pending-review skill manifest; rejected unsupported YAML; live cost subtotal with incomplete totals remaining unavailable; no browser console errors. At 390px width, page scroll width remains 390px and all six navigation destinations remain available. Temporary viewport override was reset.
- AX documentation is a pinned source assessment only. AX was not installed or benchmarked. MCP discovery supports its documented handshake/HTTP subset, not every protocol revision/auth mode. Skill review does not fetch, install or execute skill packages.

## Orchestration, retrieval and optimization comparison — 2026-09-27

- Python regression suite: 31/31 passed in 5.284 seconds. No Python source or dependency changes.
- Web suite: 90/90 passed in 0.851 seconds. Added benchmark-design tests cover missing evidence/unknown budget, non-executable complete designs, candidate allowlists, resource/quality/latency/cost constraints and immutable input handling. Cost calculations now include five additional retrieval/indexing categories.
- TypeScript and Next.js production build passed with `/ecosystem/research`.
- Browser: selected candidates across orchestration and retrieval categories; verified eight retrieval cards and eight bottleneck entries; switching workload updated control baseline/metrics; an active-worker value of 300 displayed a constraint error and disabled export. Filling all design fields displayed “References still need verification; execution remains disabled.” No console errors.
- Desktop layout and 390px mobile comparison/bottleneck views checked. Mobile document width and scroll width both measured 390px; viewport override reset and temporary test inputs cleared by reload.
- Source symbol references render as code rather than invalid HTTP links. Published methodology, third-party reports, feature documentation and absent benchmark evidence are labeled separately. No new framework/database performance measurements, installs, provider calls or cloud deployments were made.


## Specialist design and identity contracts — 2026-09-27

- Python regression suite: 31/31 passed in 6.268 seconds. No Python runtime changes or new dependencies.
- Web suite: 101/101 passed in 0.886 seconds, including bounded import validation, exact team/resource assignments, approval previews, rejected privileged actions, TTL, malformed URLs, and unconnected infrastructure nodes.
- Production build includes `/teams`. The designer stores only design metadata; custom team execution and IAM enforcement are not connected.
- Browser: custom team membership and node assignment, pinned skill references, exact MCP tool/gateway references, read-request eligibility, denied actuation, stale-preview invalidation, hierarchy drilldown/zoom/search, and Graph Studio node attachment verified. A clean starter draft reloads from browser storage; synthetic test grants were not saved.
- Source reviews of both identity projects are pinned in `specialist-identity-integrations.md`. Their tests were inspected, not executed. No external IAM credentials, model calls, MCP tool execution or physical commands were performed.
- Final responsive graph fix: ResizeObserver chooses one to five readable card columns and centers the focus node. Browser verification at 390px measured 390px document/scroll width, a 320px SVG viewBox, and the focused node fully inside its viewport. Zoom to 115% remained usable; viewport override reset. No console errors or warnings.
- Final TypeScript check and Next.js production build passed after the responsive correction.

## Optimization foundations — 2026-09-27

Implemented the delegated access/ledger, optimizer and evaluation workstreams and integrated `/optimization` plus the Swarm Control attempt ledger. Independent review added regressions for omitted evaluator rows, tampered reports, path aliases, floating-point overflow, deadline precedence and browser integer precision.

- `python3 -m unittest discover tests`: **70 passed**, 6.137 seconds on this machine. Loopback integration tests ran with local socket permission.
- `npm --prefix apps/web test`: **104 passed**, 0 failed, 913.297 ms. The six experiment templates crossed the authenticated route and actual local Python subprocess.
- `npm --prefix apps/web run typecheck` and `npm --prefix apps/web run build`: passed.
- `python3 -m py_compile` for all seven changed/new runtime and benchmark modules: passed. Static import audit found no new third-party Python runtime dependency.
- Browser: benchmark execution, schedule assignment/result graph, task selection, ten-task fixture completion and ten ledger receipts verified. No captured browser errors/warnings. At 390×844 and 1280×900, page content width matched viewport width; wide tables/graphs scroll within their containers. Temporary viewport overrides were reset.
- Regular preview restarted on `127.0.0.1:3010`; temporary verification server on 3011 stopped. No paid provider calls.

The [measured local benchmark artifact](benchmarks/optimization-local.json) includes five synthetic cases, source hashes and environment details. The small held-out demo withholds promotion; its costs, telemetry and outcomes are fixtures, not external benchmark results. Statistical statements assume bounded independent task observations and an independently checked cost-cap enforcement reference.

Production identity integration, universal adapter enforcement, provider invoice reconciliation, isolated worktree dispatch and pinned external benchmark execution remain milestones in [the optimization program](optimization-roadmap.md).


## Authenticated adapters, provider receipts and inference telemetry — 2026-09-27

- Python regression suite: **106 tests passed in 8.071 seconds**, including loopback telemetry fixtures, enrollment/lease revocation, checkpoint validation and unknown-cost reconciliation.
- Web regression suite: **114 tests passed in 3,071.761 ms**, zero failures. Coverage includes real default dispatch into temporary SQLite stores with mocked provider responses, partial sibling receipts, zero-budget rejection, revoked-grant rejection before invocation, request-key mismatch and cancellation slot retention.
- TypeScript check and Next.js production build passed. Fourteen Python modules parsed with no imports outside the standard library and this repository.
- Browser verification on an isolated production preview: all seven experiment templates appeared; telemetry passed through the authenticated HTTP route and local Python runner, returning explicit unconfigured status with unknown timestamps instead of invented metrics. Navigation to Control room worked; no console warnings/errors. Temporary preview and tab were closed.
- No paid model calls, live GPU measurements, cloud deployments, automatic worker enrollment or production grants were performed. Tests use mocks or local loopback fixtures. Admission reservations and call limits are not provider-enforced spending caps. At this checkpoint request deduplication was bounded and process-local; the persistent registry below supersedes that limitation for `/api/integrations`.


## Execution graph, reconciliation and bounded experiments — 2026-09-27

- Execution graph browser checks: a temporary 30-task fixture completed; its projection exposed 95 nodes and 140 edges. Fullscreen, neighborhood filtering, keyboard selection, related-node navigation, zoom and empty search were verified. At 390px, document width remained 390px after fixing grid minimum widths. Graph reads do not create a missing database directory.
- OpenRouter reconciliation now binds each generation to one task/attempt/call, including atomic migration of historical checkpoints and audit receipts. Conflicts fail closed; replay is idempotent. Operator-supplied evidence remains explicitly labeled.
- `/api/integrations` now registers credential-scoped hashed idempotency keys persistently before dispatch. Restart recovery does not silently replay model calls. Cross-credential sharing was rejected by automatic approval review; credential rotation intentionally creates a separate namespace. The review/swarm routes do not yet use this registry.
- The workbench exposes nine templates. Algorithm evolution and delegation compilation both executed through the authenticated browser-to-Python path. Candidate tables, withheld monetary promotion, mapped assignment costs and dependency inspection were verified. Mobile width was 390px at a 390px viewport; no captured console warnings/errors.
- No paid provider calls, production grants, GPU provisioning or cloud deployment occurred. Durable schedule compilation is metadata, not automatic worker dispatch; its per-model concurrency and timing constraints need a separate enforcing dispatcher. Local algorithm fixtures do not establish model quality or current prices.

Final frozen validation: **141 Python tests passed in 7.254 seconds; 119 web tests passed in 3,045.042 ms; TypeScript and production build passed**. Eighteen Python modules compiled with no external import roots. The conservative evolution work bound rejects oversized work before fixture creation; train selection now precedes held-out solver invocation. Selected model aliases sharing a resource or adapter/model endpoint are rejected before plan compilation. All nine browser templates are covered by the authenticated route regression.


## Capacity-enforced planned workers — 2026-09-27

- **154 Python tests passed in 8.468 seconds; 129 web tests passed in 4,991.168 ms.** TypeScript and the production build passed. Full-suite loopback tests ran with required local socket permissions.
- Capacity tests cover competing database connections, global and per-run limits, exact task selection, saturated-resource skipping, lease-expiry holds, reconciliation, and completed-output/unknown-cost separation.
- Worker tests compile through the Python lab, create the actual plan, then execute against mocked provider responses. They cover original-run ledger attribution, duplicate triggers, dependencies, model/resource/reservation mismatches, abort liability, authenticated HTTP execution, and input-override rejection.
- Browser: a compiled vLLM review executed against an isolated loopback fixture endpoint using a temporary database and fixture credentials. Its original run entered needs_reconciliation, retained $0.001000 in reserved liability and one unknown-cost attempt. The button became disabled after its sole attempt. The graph returned eight evidence nodes/nine edges, including its exact resource. No real inference, paid model, production grant or cloud service was used.
- Mobile document width matched the 390px viewport. No captured browser warnings/errors. Temporary viewport restored.


## Specialist activation and committed Git evidence

The final local checkpoint passes 174 Python tests and 134 web tests, plus
TypeScript checking, a production Next.js build and Python compilation. The core
import audit remains standard-library only. Focused tests cover distinct live
approvers, immutable input binding, expiry/revocation, idempotent replay, safe
execution-graph attribution and TypeScript-to-Python activation compatibility.

Browser verification on an isolated localhost preview imported a nonsecret
specialist design and compiled plan, inspected its exact input, and exported the
operator request without issuing authority. The Git experiment displayed actual
committed changes and rechecked them as current. A browser-found numeric JSON
roundtrip mismatch was fixed and protected by an actual Node parse/stringify
regression. Temporary preview tabs and fixture-token server were cleaned up.

These checks used in-memory/temporary state and loopback fixtures; no paid
provider calls or production permission changes occurred. Contract references do
not independently establish source-resource ownership or remote ACL permission.


## Data science and continuous intelligence

The analytics workspace at `/analytics` adds authenticated read-only ledger
queries, validated CSV/JSON imports, opt-in visible-page refresh, operational
statistics, cohort economics, graph relationships and a guarded seven-day
spending baseline. Its synthetic example is explicitly labeled.

Validation: 193 Python tests and 142 web tests passed, plus TypeScript checking
and the production build. Browser checks covered synthetic views, graph node
selection, forecast tables, authenticated imports, unknown-cost suppression and
a 390 px mobile layout without page overflow. The isolated fixture token was
used only on a temporary local preview.

The reproducible 50,000-row SQLite fixture selected all rows without truncation,
with 516 unknown-cost records correctly blocking prediction. Saved machine-local
timing and Python allocation measurements are in `benchmarks/analytics-local.json`.
The cap is 200,000 selected live rows; the capped result is materialized in memory,
so these checks do not establish distributed big-data or production throughput.


## BI visualization gallery and shared graph renderer

The Visualizations view provides 21 implemented chart/detail choices, with
explicit requirements for ribbon history, geographic fields, fitted key-influencer
models and isolated custom-script adapters. Tests cover displayed-value percentage
denominators, omitted categories, partial costs, chronological date limits and
zero/single-slice pie geometry. The Relationships view now uses the same
GraphCanvas WebGL renderer, force-layout worker and SVG fallback as Graph Studio.

Validation for this change: 193 Python tests passed in 9.963 seconds; 166 web
tests and TypeScript checking passed. Browser checks exercised all 21 implemented
choices, the four requirement panels, gauge targets, category selection,
single-category pies, empty filters, known-cost formatting and the tool/resource
matrix. A 390 px viewport had no horizontal page overflow. SVG and JSON exports were downloaded and parsed: the SVG retained its namespace,
viewBox, two slices and value titles; JSON retained source, selection, limitations
and rows summing to its displayed total. The browser download-event helper timed
out, so the actual saved artifacts were verified in the local Downloads folder.

The production build passed. Final browser verification at `127.0.0.1:3010`
confirmed Sigma WebGL, labeled nodes, grouped/force layout, search, category and
neighborhood filters, selection cost details, and fullscreen entry/exit. A
browser-found fullscreen flex-sizing mismatch was corrected; the canvas and
outer frame now share a non-shrinking height. No console errors were reported in
the final production-preview check. No paid provider calls were made.


## Laya and AnyJev decision intelligence

The `/decisions` workspace, contextual navigation and Graph Studio integration
link expose bounded typed question batches. The native Laya adapter and optional
AnyJev L0/vLLM bridge preserve choice, ordinal score and yes/no semantics.
Provider response distributions, conservative estimated budgets, timeout/size
bounds and unavailable-provider states are independently validated.

Validation: 200 Python tests passed in 14.000 seconds; 180 web tests passed in
15.290 seconds. TypeScript checking, Python compilation and the production build
passed. The bridge CLI help works without importing AnyJev. Browser verification
covered both adapters against an explicitly synthetic loopback HTTP service,
choice/score/yes-no output, malformed JSON, insufficient budget rejection,
contextual navigation and a 390 px layout without horizontal overflow. The final
production preview shows both providers unconfigured and offers a clearly labeled
synthetic fixture; its distributions sum to one and match displayed answers.
No console errors were reported in the final preview.

No model packages, tokenizer assets or weights were installed, and no real
Laya/AnyJev inference or paid provider calls occurred. The synthetic service and
temporary credential-bearing preview were stopped. Fixture timings establish
HTTP/UI integration behavior only, not model speed, accuracy or production scale.


## Interactive analytics detail cards — 2026-09-27

- Python regression suite: 200 tests passed in 14.088 seconds.
- Complete web suite: 183 tests passed in 15.298 seconds. After the final horizontal-bar selection callback fix, the 21 visualization tests passed again in 0.172 seconds.
- Web typecheck and final production build passed. No new runtime dependency was added.
- Browser checks used the explicitly labeled synthetic dataset. All 20 supported chart/detail families exposed inspection targets (the narrative remains prose; gated extensions still require setup). Verified pie 61/112 share and 56 successes; stacked geometry matched 47 successes plus 4 other attempts; gauge showed 112 against target 100; histogram, scatter, heatmap, daily trend, matrix, and forecast cards exposed their underlying values.
- Verified first-click pinning, keyboard focus, Escape dismissal, category selection, and tooltip placement at a 390-pixel viewport without horizontal overflow. Pointer enter/move/leave handlers share the same card implementation; browser automation exercised click/focus rather than a dedicated hover command.
- Forecast inspection uses a full date-column hit area and explicitly labels its bounds as heuristic. Final production browser console showed no errors. The preview was refreshed at http://127.0.0.1:3010/analytics.

## Shareable Swarm Arena — 2026-09-27

- Final Python regression suite: 200 tests passed in 14.711 seconds.
- Final web regression suite: 183 tests passed in 15.408 seconds.
- TypeScript typecheck and optimized production build passed; `/arena` generated as a static page.
- End-to-end browser run used an ephemeral local preview token only. It returned the five-case deterministic fixture report, source hashes, platform/runtime pins, and zero provider calls. The paired synthetic promotion example remained not promoted because its uncertainty/quality gates were inconclusive.
- Generated a share snapshot from the authenticated local fixture endpoint and opened it from a fresh page. SHA-256 integrity validation passed and the page restored all five case measurements and the held-out gate. The encoded snapshot was 4,868 bytes before base64url encoding.
- The page clearly labels snapshots unsigned, exposes that the complete benchmark output/environment/hashes are URL encoded, excludes the token, and does not claim a hosted leaderboard. No model or external provider calls were made.
- Production preview at `http://127.0.0.1:3010/arena` was restarted with the normal local environment after end-to-end verification. Console errors: none.
