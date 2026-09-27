# ApexGraphSwarm

A dedicated local engineering workspace for repository graphs, bounded agent orchestration, evaluation and cost-aware delegation. Extracted from the current Play Anything Graph Studio working tree; see `PROVENANCE.json`. This is an independent project, not a published GitHub fork.

## Quick start

Requires Python 3.10+ and a Node version supported by the pinned Next.js release. The Python control plane uses only the standard library.

```sh
npm --prefix apps/web ci
python3 scripts/setup_integration_kernels.py --write-env
npm --prefix apps/web run dev
```

Open **http://127.0.0.1:3010**. Play Anything remains on its original port. Kernel setup fetches the four pinned public source repositories if absent; it does not invoke any model. This prepared local project already includes ignored local copies and a fresh private workspace token. Copy `INTEGRATION_ACCESS_TOKEN` from `apps/web/.env.local` into execution controls when needed. Provider keys are not copied from the original project, and tokens are never exported.

## Workspaces

- **Graph Studio** — fullscreen graph exploration, source evidence, search, filtering, paths, optional Neo4j storage and framework integrations.
- **Swarm control** — SQLite-backed task DAGs, transactional leases, fenced completion, recovery and integer micro-USD accounting. The UI executor runs deterministic fixtures only; actual framework executions remain in their separate adapter runtime.
- **Delegation & cost** — extensible model/harness candidates, eligibility constraints, dated/editable rate assumptions and cost per successful result. Unknown costs remain unknown. Exported plans do not execute models.
- **Ecosystem** — Google AX execution architecture, MCP endpoint discovery, skills.sh / Agent Skills review imports, compatibility boundaries and complete operating-cost assumptions. Open `/ecosystem`; selected integrations export a plan, not a deployment.
- **Evaluation lab** — actual local scheduler measurements, reproducible benchmark provenance, held-out evaluation design and gated configuration evolution.

The four original AAH20 kernels are retained as optional pinned adapters. Cognee, MiroFish, LangGraph, CrewAI, Hermes, OpenManus, Understand Anything, OpenRouter and vLLM require their documented service/profile setup. Subscription authentication uses supported harness clients; it is not interchangeable with API billing.

See [AX assessment](docs/google-ax-assessment.md), [MCP discovery setup](docs/mcp-interoperability.md), [skill review](docs/skills-interoperability.md), and [ecosystem architecture](docs/ecosystem-interoperability.md).

## Verification

```sh
python3 -m unittest discover tests
npm --prefix apps/web test
npm --prefix apps/web run typecheck
npm --prefix apps/web run build
python3 scripts/benchmark_swarm.py --help
```

Runner tests use harmless subprocesses and localhost sockets. Benchmarks exercise local scheduling, not paid agents or model intelligence. Review each result's scope and environment before comparing it with another system.

## Current operating boundary

This is a local, single-workspace engineering foundation. 300 registered logical agents is distinct from 300 simultaneous model calls. Active work is capped; provider quotas, tool permissions, context limits and budgets remain separate constraints. SQLite durability does not make the existing framework-job registry durable, nor does it provide distributed tenancy, OS isolation, or a cloud worker fleet.

Production gates include isolated workers/worktrees, durable adapter receipts and idempotency, multi-tenant authorization, provider quota admission, distributed storage/queues, live model evaluation, incident recovery and invoice reconciliation. Do not mount the local SQLite database on an unreliable shared/network filesystem.

See [control-plane contracts](docs/control-plane.md), [extraction and architecture](docs/apexgraphswarm-extraction.md), [evaluation design](docs/apexgraphswarm-evaluation.md), [cost and routing](docs/apexgraphswarm-cost-routing.md), and [integration setup](docs/agent-integrations.md).

## Provenance and licenses

The original Apache 2.0 license is preserved. Third-party kernels keep their own licenses and pinned source references. Original project history was not rewritten; this extraction contains current local enhancements that may not be present in the upstream HEAD. No upstream GitHub repository was created or pushed.
