# ApexGraphSwarm extraction boundary

This staged project is an extraction from the dirty `play-anything` working tree, not a byte-for-byte copy of its Git commit. `PROVENANCE.json` records the source HEAD and that uncommitted graph-workspace changes were included; no Git history or secrets were copied. Preserve that distinction in releases.

## Extracted capabilities and what stays behind

The domain-neutral starting points are `apps/web/lib/graph.ts` (validated graph snapshots, evidence labels, graph queries and explicit limits), `analysis.ts` / `analysis.worker.ts` (deterministic analysis), `model-review.ts` / `model-swarm.ts` (optional, explicitly invoked model analysis and citation checks), `integration-runtime.ts` plus the adapter/catalog modules, `apps/web/integrations/kernel_runner.py`, and `integrations/harness_runner.py`. Graph parsing and local analysis can become a standalone package. Provider/framework adapters should remain separate, allowlisted executors with configuration and lifecycle capabilities stated per adapter. The four AAH20 kernels remain pinned external sources, not rewritten approximations; retain exact revisions, licenses, attribution and input validation. See `integrations/kernel-sources.json` and `docs/kernel-capability-matrix.md`.

Do not make `play_anything.engine.PlayAnythingEngine`, RPG `WorldState`/`QuestPath`/`DungeonRoom`/`SkillNode`, combat, XP/rewards, player wallets/tokenomics, NPC/voice, age-based personalization, realm publishing or whale economy part of ApexGraphSwarm's core. Those concerns are in `play_anything/engine.py`, `play_anything/adapters/repo_rpg_generator.py`, `play_anything/core/models.py`, `quest_steiner_synthesizer.py`, `dungeon_partitioner.py`, `skill_tree_induction.py`, `personalization_engine.py`, `tokenomics_equilibrium.py`, `realm_studio.py`, `strategic_whales_consortium.py`, and `dashboard.html`. The current `apps/web/scripts/prepare-assets.mjs` still builds the old creator site and wires an iframe/postMessage bridge; retain it only as an optional compatibility frontend, not as a runtime dependency of the new project.

The current web runtime has bounded page workers and model calls, but `integration-runtime.ts` stores jobs and queue state in process memory. `neo4j-store.ts` stores graph revisions under one configured namespace; it is not tenant authorization or durable job storage. The harness bridge is a fixed-profile local subprocess runner, not a distributed worker. The inspected pinned kernel repositories expose local Python methods, not remote job/status/cancel services. Therefore durable jobs, event replay, leases, recovery, idempotent admission, tenant isolation, secret brokering, managed worktrees and enforceable CPU/memory/network quotas must be built as separate control-plane capabilities.

## Agent count and execution capacity

“300 agents” may describe logical agent identities or planned tasks. It does not mean 300 active model calls, child processes, GPUs, or paid requests. Current integration jobs are limited to two active jobs per Node process; the harness bridge is limited to two child processes; local/model analyses have their own smaller limits. These constants do not prove service capacity. Keep a configured active-work pool independent of the maximum logical-agent registry (the control-plane foundation starts with a maximum of 300 registered identities and a default of four active leases). Increase active concurrency only after measured queue, latency, memory, failure, provider-quota and cost tests.

## Extraction sequence

1. Keep this new repository and source workspace separate. Preserve the source branch/HEAD, dirty binary-safe diffs and untracked-file inventory in a private handoff; never overwrite or clean the user's source tree. Exclude `.env*`, `.env.local`, tokens, local harness profiles, `node_modules`, `.integration-sources`, caches and runtime databases. Do not copy `.git` history.
2. Keep graph schema/evidence, pure analysis and adapters as separate versioned contracts. Every result records snapshot identity, source revision/provider, limits, uncertainty and partial status. Keep HTTP/UI glue out of the domain package.
3. Use a transactional local SQLite control plane first, then introduce a shared database/queue only when multi-process deployment is required. Persist jobs, attempts, idempotency, budget reservations/settlement and an append-only event sequence. Use leases with heartbeat and fencing tokens; on expiry, recover only safe-to-retry work and reconcile ambiguous remote side effects rather than blindly replaying them.
4. Add tenant identity and authorization on every graph/job/event/result operation, scoped short-lived secrets, redacted audit logs, isolated read-only snapshots/worktrees, and explicit CPU/memory/time/network quotas before enabling untrusted repository execution.
5. Benchmark 300 logical identities while enforcing a separately configured active limit. Report tested concurrency, task mix, host/provider quota, throughput, p50/p95 queue and execution latency, failure/retry/cancel latency, memory and cost. Never infer active capacity from record count.

## Release gates

- A clean checkout builds and tests without importing the legacy `play_anything` application. Disabling the compatibility iframe leaves graph import/export usable.
- Golden graph fixtures preserve snapshot identity, directed paths, evidence levels, warnings and cap behavior; oversized data is rejected or explicitly labeled as reduced.
- A process-kill/restart test proves queued work resumes, completed results and ordered events remain readable, expired leases are fenced/recovered, and repeated idempotency keys do not create duplicate logical runs.
- Tests prove missing dependency/cycle rejection, per-run budget admission/settlement in integer micro-USD, active concurrency never exceeds its configured cap, cancellation and lease fencing work, and unknown paid cost is rejected.
- Cross-tenant tests, secret canaries, workspace escape tests, output/input caps and subprocess cleanup pass before production claims. Any remote adapter without a verified status/cancel surface advertises that limitation.
- The 300-logical-agent fixture completes under a fixed active cap without claiming a 300-way provider burst. Publish measurements before changing the cap or making a capacity statement.

## Capability labels

| Capability | State in extracted project |
|---|---|
| Graph validation and bounded local analysis | Implemented in extracted Next app; standalone package boundary proposed. |
| Optional model review/team | Implemented, requires server-side provider configuration and explicit invocation. |
| Four pinned kernel adapters | Implemented, requires verified source paths; local bounded calls only. |
| Framework/harness adapters | Implemented or bridge-dependent per catalog; capability varies by upstream and configuration. |
| Neo4j graph snapshots | Optional/configuration-required; namespace is not tenant isolation. |
| Durable jobs/leases/idempotency/events | Proposed control plane; in-process web jobs are not durable. |
| Multi-tenant authorization/secrets/worktrees/resource quotas | Proposed; do not advertise as currently available. |
| 300 concurrent paid agents | Unsupported and unmeasured; not a product claim. |
