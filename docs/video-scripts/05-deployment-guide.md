# Video Script Outline: ApexGraphSwarm Deployment Guide

**Target length:** 10–12 minutes  
**Audience:** Platform engineers and developers who want to run ApexGraphSwarm locally, understand the deployment model, and plan for production  
**Goal:** Walk through the quick start, local production build, optional kernel setup, analytics benchmark, and the explicit production roadmap — with clear commands and honest boundaries.

---

## Scene 1 — Deployment Philosophy (0:00–1:00)

**Visual:** A slide with the title "Deployment in ApexGraphSwarm" and a subtitle: "Local-first, single-workspace, loopback-bound." Cut to a terminal.

**Narration:**
> "ApexGraphSwarm is designed to run locally, on a single workspace, bound to loopback. There's no one-click Vercel, Cloudflare, or Supabase production deployment claimed by this repository. A hosted frontend alone cannot safely replace a durable local database, a long-running runner, or private infrastructure connectivity. Let's get it running."

---

## Scene 2 — Quick Start (1:00–3:00)

**Visual:** Screen recording of a terminal. Run the commands live. Cut to the browser at `http://127.0.0.1:3010`.

**Narration:**
> "The quick start is two commands. First, install dependencies and start the dev server."

**On-screen text:**
```sh
npm --prefix apps/web ci
npm --prefix apps/web run dev
```

**Narration (continued):**
> "Then open `http://127.0.0.1:3010`. You'll see the control room — the entry point for the entire workspace. Start with the prepared repository graph, the team designer, architecture comparisons, and cost/evaluation planning. Viewing and designing do not require a model API key.
>
> For a local production build, run `npm --prefix apps/web run build` and then `npm --prefix apps/web run start`. The build prepares the project graph assets. Development and production commands use port 3010 by default. Stop the existing server before starting another on that port."

**Requirements overlay:**
- Python 3.10+ (standard library only)
- Node.js and npm (compatible with pinned Next.js release)
- Git (including network access if fetching optional kernel sources)

---

## Scene 3 — Analyzing Another Repository (3:00–4:00)

**Visual:** Terminal. Run the analyzer on a different repository. Import the graph in Graph Studio.

**Narration:**
> "To analyze a local repository, run the Python analyzer from the repository root."

**On-screen text:**
```sh
python3 -m apexgraphswarm graph /absolute/path/to/repository --output /tmp/repository-graph.json
```

**Narration (continued):**
> "Then in Graph Studio, choose 'Import graph' and select the generated JSON. A graph snapshot contains repository metadata and source-derived summaries. Review its contents before sharing it — it's your codebase in a file."

---

## Scene 4 — Optional Kernel Setup (4:00–5:30)

**Visual:** Terminal. Run the setup script. Show the `.env.local` file being created (with the token redacted). Show the check command.

**Narration:**
> "The four original optimization kernels are optional. To set them up, run the setup script."

**On-screen text:**
```sh
python3 scripts/setup_integration_kernels.py --write-env
python3 scripts/setup_integration_kernels.py --check
```

**Narration (continued):**
> "Setup fetches the four pinned public source repositories when absent and adds missing local configuration while preserving existing values. It does not invoke a model. Source pins are recorded in `integrations/kernel-sources.json`; downloaded sources are ignored by Git.
>
> Execution controls require the private workspace token configured as `INTEGRATION_ACCESS_TOKEN` in `apps/web/.env.local`. Enter it only in the local execution control that requests it. Keep it out of screenshots, shared exports, and commits. Review the environment template and integration setup docs before enabling services. Provider credentials are separate from this workspace token."

**Security overlay:** "Keep secrets server-side and outside Git. Browser design fields should contain non-secret references, not tokens or connection strings."

---

## Scene 5 — Running Benchmarks (5:30–7:30)

**Visual:** Terminal. Run the swarm benchmark and the optimization benchmark. Show the output JSON.

**Narration:**
> "There are two reproducible benchmarks you should run to verify your installation.
>
> First, the swarm benchmark. This runs the deterministic fixture and produces a JSON artifact with classification, environment, source hashes, seed, configuration, timing, accounting, and recovery checks."

**On-screen text:**
```sh
python3 scripts/benchmark_swarm.py --counts 30 100 300 --workers 32 --output /tmp/apex-swarm-benchmark.json
```

**Narration (continued):**
> "Second, the optimization benchmark. This runs the synthetic fixture suite and records source hashes, environment details, timings, and gate outcomes."

**On-screen text:**
```sh
python3 -m scripts.benchmark_optimization
# Or send one bounded JSON request on stdin:
printf '%s\n' '{"action":"benchmark"}' | python3 -m apexgraphswarm.lab
```

**Narration (continued):**
> "The fixture suite measures local algorithm runtime and gate behavior. It does not establish performance on PSPLIB, GraphRAG-Bench, ToolSandbox, Terminal-Bench, or real agent workloads. Synthetic costs and telemetry are explicitly labeled; unknown costs remain unknown."

---

## Scene 6 — Analytics Benchmark (7:30–8:30)

**Visual:** Terminal. Run the analytics benchmark. Show the output.

**Narration:**
> "There's also an analytics benchmark. This runs a reproducible temporary SQLite fixture with 50,000 rows and records measured evidence in the local benchmark artifact."

**On-screen text:**
```sh
python3 -m scripts.benchmark_analytics --rows 50000
```

**Narration (continued):**
> "The stdlib engine caps live scans at 200,000 rows and imports at 10,000 rows. SQLite reads are batched; the capped selection is materialized in memory. This is a bounded local analytics implementation, not a distributed warehouse or a calibrated predictive model."

---

## Scene 7 — Verification Suite (8:30–9:30)

**Visual:** Terminal. Run the test suite. Show the results.

**Narration:**
> "Before you start extending the system, run the full verification suite."

**On-screen text:**
```sh
python3 -m unittest discover tests
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
```

**Narration (continued):**
> "The latest local verification recorded 214 Python tests and 183 web tests passing, plus typecheck and production build. Tests use harmless subprocesses and loopback sockets where required. They do not establish that real provider credentials or separately deployed services work. No paid model run is required for the regression suite."

---

## Scene 8 — Production Roadmap (9:30–11:00)

**Visual:** A slide with the six production milestones, each with a one-line description. Cut to the README's "Deployment and roadmap" section.

**Narration:**
> "The supported starting point is a local, single-workspace deployment bound to loopback. The production roadmap has six milestones."

**Milestones:**

| # | Milestone | What it means |
|---|-----------|---------------|
| 1 | Production specialist identity | Extend local enforced review contracts with externally verified tenant identity, JIT credentials, resource ACLs, and auditable adapter receipts |
| 2 | Durable adapter integration | Unify task lifecycle and remote job status with idempotency, bounded retries, reconciliation, quotas, and isolated workers/worktrees |
| 3 | Graph scale and fidelity | Incremental ingestion, compiler-backed language semantics, measured layout budgets, and storage-backed graph queries |
| 4 | Evidence-driven delegation | Live model evaluations on held-out workloads, provider usage capture, rate provenance, and invoice reconciliation |
| 5 | Private infrastructure adapters | Begin with inventory and telemetry, then add explicitly authorized command capabilities with independent safety controls |
| 6 | Hosted operation | Select durable storage/queues, secrets management, tenant isolation, recovery, observability, and budget admission before exposing execution endpoints |

**Narration (continued):**
> "Do not place the local SQLite database on an unreliable shared or network filesystem. Framework-job durability, distributed tenancy, and cloud worker provisioning remain separate engineering tasks."

---

## Scene 9 — Close (11:00–12:00)

**Visual:** Return to the control room in the browser. The workspace is fully loaded with demo data. Fade to a summary slide with the quick-start commands.

**Narration:**
> "ApexGraphSwarm is a local-first engineering workspace. The deployment model is intentionally simple: local, single-workspace, loopback-bound. The quick start is two commands. The verification suite is four. The production roadmap is six milestones, each explicit about what's needed. Start local. Verify everything. And when you're ready for production, the roadmap tells you exactly what to build."

**On-screen text:**
```
npm --prefix apps/web ci
npm --prefix apps/web run dev
# → http://127.0.0.1:3010
```

**End card:** Repo link, docs link, "Read AGENTS.md before contributing."

---

## Production Notes

- **Real runs:** All commands should be run live in the terminal. No mocked output.
- **Pacing:** The quick start (Scene 2) should be fast — the audience wants to see it work. The production roadmap (Scene 8) should be deliberate — let each milestone land.
- **Security:** The `INTEGRATION_ACCESS_TOKEN` should never appear on screen. Redact it in any `.env.local` display.
- **Prerequisites:** Viewers should have Python 3.10+ and Node.js installed. A brief "check your versions" overlay is helpful.
