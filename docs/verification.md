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
