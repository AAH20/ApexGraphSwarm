# Google Agent Executor (AX): integration assessment

**Evidence checked:** 2026-09-27. This is a source review, not a deployment, load test, or security audit. AX's README labels the project early development and warns of breaking changes. The current upstream release is `v0.3.1`, released 2026-09-25 at full commit `e70162a34037c221fe6fadefd98308c05a4ad8f3`; the release page reports six commits on `main` after that tag. Pin an exact tested commit and matching Agent Substrate revision rather than installing `@latest`. The protobuf API remains `v1alpha1`.

## Scale claim and provenance

I found no first-party public evidence that the open-source AX release has been load-tested at 150,000 concurrent, live model-backed agents. Google Cloud describes AX as built from lessons learned operating internal runtime systems, while its official AX site and README state very large design ambitions (billions of tasks / concurrent sessions) and Google Cloud's Agent Substrate announcement describes capacity for hundreds of millions of registered agents. Those are product/architecture claims; they are not a public benchmark report specifying machine count, active-versus-suspended mix, model traffic, workload, latency, failure rate, or reproducible test results.

A likely source of a “150,000+” mix-up is Google's separate *Advent of Agents* enablement post: it reports 150,000+ developer participants and 859,000+ browser code executions. It is not a count of AX actors, unique agent sessions, or simultaneous executions. Separately, the InSTA web-agent research paper describes attempts on 150,000 website-navigation tasks/sites; it does not establish that all were concurrent and is not an AX runtime test. Do not carry either number into ApexGraphSwarm's AX capacity claims.

**Integration recommendation:** if evaluated, model AX as an optional, externally operated distributed executor below ApexGraphSwarm's transactional control plane. Apex should own run IDs, idempotency, reservations, cancellation/reconciliation, evidence validation, and final status. AX can own sandbox placement, workspace bootstrapping, task suspend/resume, and worker lifecycle. Treat an AX `Task` as an executor allocation, not as proof that the corresponding Apex task succeeded.

## Public interface and lifecycle

The supported entry point in the current upstream tree is the `ax` Go CLI against the AX control plane over gRPC. The published verbs include:

```text
ax apply -f <multi-document-yaml>
ax get tasks [-a <atespace>]
ax get task <name>
ax describe task <name>
ax watch task <name>
ax suspend task <name>
ax resume task <name>
ax delete task <name>
ax get|describe|delete workspaces|models ...
ax --context <kube-context> ...
ax --server <control-plane-host:port> ...
```

`ax apply` parses YAML client-side and sends typed RPCs; it is not a REST/JSON run endpoint. The `ax.v1alpha1.AX` protobuf service defines `GetTask`, `ListTasks`, `UpdateTask`, `DeleteTask`, `SuspendTask`, `ResumeTask`, and streaming `WatchTask`; analogous CRUD methods exist for `Workspace` and `Model`. Task requests use `(atespace, name)`. `WatchTask` emits the Task plus an action. `TaskStatus` has phase, ID, actor, worker IP, usage (prompt/completion tokens), and conditions. This is a declarative desired-state API, not a one-call synchronous `execute(prompt) -> result` contract.

Current repo manifests expose the `ax-server` gRPC control plane on port **8080**, with HTTP `GET /healthz` on that same port. The controller talks to the Agent Substrate control API on **443** using a projected service-account token and CA bundle. Redis is internal on **6379**. Inside each task, `ax-task-runner` serves readiness and metadata on **80**; `atenet-router` routes to actors on **80** using the `ate-target-actor: <atespace>/<task>` header. These are distinct interfaces. Do not call the runner metadata URL an AX job API.

Task phases and `Ready` conditions describe provisioning/readiness. `ax suspend` checkpoints and pauses the actor; `ax resume` restores it, using the same task identity and durable `/workspace` state but a new container process tree. `ax delete` tears down and removes the task; it is cleanup, not a success signal. The runner contract explicitly says AX does not currently read the agent command's exit status. A custom harness/runner or a separate authenticated result channel is therefore required to return terminal success/failure and structured output into Apex's ledger. Before suspending a task, the harness must flush its own durable execution state; do not assume an in-memory process survives.

## Manifest and model contract

A task binds an image, command vector, optional CPU/memory requests and limits, environment variables, and one or more `Workspace` resources. The first workspace becomes the command working directory. Resource names are scoped by `atespace` and DNS-label constraints. `TaskStatus.usage` exposes prompt and completion token counters, but the reviewed public contract does not provide price, per-request provider attribution, or a complete cost ledger.

A `Workspace` may describe git checkouts, files, MCP servers/registries, skill registries, and a skills materialization path. MCP servers can use an endpoint or command/args in the protobuf. AX's runner materializes this tool landscape at startup. This is declarative tool setup, not automatic import of Apex's repository graph or tool-permission policy. The reviewed `MCPServer` message has no generic credential/header map; keep credentials in the relevant cluster secret/injected service identity rather than embedding them in a manifest.

A `Model` names a provider and model ID, provider parameters, and a Kubernetes `SecretKeyRef`. Example docs show Google or Anthropic provider secrets. Model configuration is a credential/config pointer; it does not imply a fixed model, a particular quality, or a known price. For graph-specific inputs, package only a bounded, versioned graph snapshot in an explicitly bound workspace or send it to a purpose-built task image. Record its content hash and schema version in Apex before launch; do not silently convert the graph into workspace setup goals.

AX has native Workspace fields for MCP and Google skill-registry configuration. This establishes that such resources can be set up for the task. It does not establish that arbitrary MCP/skill registries are available, that Apex's permission model is enforced inside them, or that a task can make authenticated registry calls without appropriate deployment credentials and egress. Test registry/project authorization, endpoint allowlists, and secret isolation in the target cluster.

## Setup, authentication, and security boundary

The documented deployment requires Go, `kubectl`, `ko`, a container builder/registry, Kubernetes, and Agent Substrate installed in the `ate-system` namespace. The AX deployment installs an AX API server, Redis, and controller in `ax-system`; it needs an aligned Agent Substrate control plane and a configured snapshot bucket for suspend/resume. The documented dev prerequisites specify Go 1.27+. The reviewed `main` go.mod snapshot (not asserted to match the v0.3.1 tag) declares Go 1.27.1 and direct modules `github.com/agent-substrate/env` `v0.0.11-0.20260912052224-4468a200b170`, `github.com/agent-substrate/substrate` `v0.0.0-20260911232748-672533541dbf`, `github.com/redis/go-redis/v9` `v9.22.0`, `google.golang.org/grpc` `v1.83.2`, `google.golang.org/protobuf` `v1.36.12`, and `gopkg.in/yaml.v3` `v3.0.1`, with indirect modules pinned in `go.sum`. These are Go control-plane dependencies; they must remain isolated from ApexGraphSwarm's Python 3.10+ stdlib-only control plane. Deploy AX and its container images as a separate service boundary, pin its image digests, Go module graph (`go.sum`), and compatible Substrate revision, and test upgrades separately.

The CLI docs describe Kubernetes-context selection (`kubectx`/`--context`) and `--server` routing, but do not document a user-level AX bearer-token/RBAC contract for direct access to `ax-server`. As checked on 2026-09-27, upstream issue #382 reports missing control-plane authentication/authorization. Until the pinned release is independently verified to close that gap, keep port 8080 private behind cluster network policy or a separately authenticated gateway, and scope Kubernetes credentials and namespaces/atespaces tightly. Do not expose the gRPC port to browsers or untrusted tenants. Agent Substrate's controller connection is a separate service-account-token-plus-CA flow; provider API keys are separate Kubernetes Secrets referenced by `Model`.

`spec.debug: true` enables guest process/file services behind `ax ssh`; it should stay false for ordinary jobs. The task runner receives task/workspace specs as environment YAML, provider credentials may be injected according to configured model/atespace, and workspace contents persist through suspension. Avoid credentials in task args, workspace files, shell output, debug access, or public artifacts. Add egress allowlists outside AX if the reviewed version's `Gateway` support is not available; v0.3.1's proto reserves/omits a Gateway API.

## Release and dependency pinning

Use the upstream release tag and immutable commit as separate checks: `google/ax v0.3.1` at `e70162a34037c221fe6fadefd98308c05a4ad8f3` is a concrete review baseline, not a recommended production version. The GitHub release notes disclose active development and later `main` changes; the current README and `main` proto may therefore differ from that tag. For any trial, archive the exact tag's `go.mod`, `go.sum`, generated image digests, proto descriptor, and matching Agent Substrate module/CRD revision in the deployment record. Verify the resolved commit (`git rev-parse v0.3.1^{commit}`) and module graph in CI. Never track branch `main` or use `go install ...@latest` in reproducible deployments. Re-review API, security, suspend/resume, and snapshot behavior before moving to a newer pin.

AX is Apache-2.0 licensed. Preserve the upstream license and notices in any copied/embedded code; a service integration that invokes its CLI/protocol does not require copying its implementation. AX brings a Go runtime plus Redis, Kubernetes, Agent Substrate, container images/registry, and snapshot storage; none of those dependencies should be vendored into Apex's core Python runtime.

## Cost model (all rates are deployment-specific and currently unknown here)

AX publishes no price sheet or 150k benchmark cost. Quote cost as variables and measure in the target environment; don't infer that suspended agents are free.

```text
C_total = C_AX_control + C_worker_active + C_snapshot_storage + C_snapshot_IO
        + C_model_tokens + C_tools_and_network + C_setup + C_failures_and_retries
```

- **Control plane:** Redis, API/controller replicas, Kubernetes baseline, observability, and any database/log service. These can be fixed/idle costs even with zero active work.
- **Active worker:** sum `vCPU-seconds × rate_vCPU` and `GiB-seconds × rate_GiB`, plus node or sandbox overhead. Measure provisioned/occupied time from infrastructure telemetry; AX token usage alone cannot calculate this.
- **Suspended state:** snapshot bytes × retained time × storage rate, snapshot writes/reads, object-store minimums, and cleanup. Include retained workspace volumes and backups.
- **Resume/burst:** restore I/O, scheduling/cold activation, transient duplicate capacity during handoff, queueing, and capacity headroom for burst arrivals.
- **Models:** prompt/completion tokens per provider/model × effective price, cache reads/writes where relevant, and repeated calls from retries. Obtain actual usage and billing records; `TaskStatus.usage` is not a dollar amount and may not distinguish all calls.
- **Tools/network/setup:** MCP/tool service usage, egress/transfer, image pulls, repository clone/build bootstrap, artifact storage, and secrets/KMS operations.
- **Reliability overhead:** abandoned or repeated model/tool calls, failed warmups, snapshots after errors, and reconciliation time. Deduplicate at Apex by its task idempotency key; AX retry/resume must not double-settle spend.

Compare cost per successfully completed held-out task, plus active/suspended resource-time distribution and tail latency. Show token spend and infrastructure spend separately before totaling. Unknown unit prices remain unknown.

## Benchmark plan before adoption

No AX concurrency, throughput, or latency number is claimed by this assessment. Run the following as a versioned, reproducible external evaluation; pin task image, AX/Substrate commits, cluster SKU/region, node pool, snapshot bucket, model/provider, prompts, skill/MCP versions, and workload seed. Report confidence intervals over independent runs and actual cloud/model bills.

| Workload | Roster / burst | Measure | Faults / correctness |
|---|---:|---|---|
| Control-plane CRUD with no model calls | 1, 10, 30, 100, 300, 1k, 10k tasks | apply-to-accepted, accepted-to-ready, watch propagation p50/p95/p99, queue depth, API/controller CPU, Redis ops | duplicate/replayed apply, controller restart, name/atespace isolation |
| Short deterministic fixture task | 1/10/30/100/300 active | completed/s, activation and teardown latency, worker CPU/RAM, per-task result hash | duplicate task execution, command exit vs AX phase, lost result callback |
| Bursty model-backed tasks | same roster; 10%, 50%, 100% simultaneous starts | model TTFT/total latency, provider throttles, active worker seconds, token totals, cost/task | model timeout, 429, key rotation, cancellation during request |
| Long idle / human approval | active minutes then suspended for 1m/1h/24h | snapshot bytes, suspended storage cost, suspend/resume p50/p95/p99, restore data loss | actor restart, worker loss, snapshot-store denial, stale callback |
| MCP and skill workspace bootstrap | cold/warm, 1–300 tasks | setup duration/cache hits, egress, tools called, registry/API cost | blocked egress, invalid registry auth, malicious skill/tool, secret leakage |
| Graph-consuming task | fixed graph sizes and hashes | graph ingestion correctness, evidence coverage, task success at equal model/token budget | missing/dangling nodes, stale snapshot, prompt truncation, unauthorized repo writes |
| Scale + disruption | ramp 1→300→1k; active/suspended ratios 100/0, 50/50, 10/90 | sustainable throughput, saturation knee, recovery time, availability, complete cost | API/controller/Redis/node outage, snapshot failure, duplicate resume, network partition |

Acceptance gates should be set before running and labeled proposed until measured: no unaccounted or duplicate settled task, no out-of-scope tool/write, graph inputs/results hash-verifiable, complete per-attempt cost reconciliation, and explicit terminal state for cancellation/failure. Report suspended and active counts independently. A “registered task” or “created agent” is not an active execution. Compare Apex-only, AX-backed, and single-agent baselines on equal task set, quality rubric, model version, token/budget cap, and wall-clock deadline; include infrastructure cost so a cheaper token total cannot hide more worker/snapshot cost.

## ApexGraphSwarm integration decision

**Not ready as a direct `harness_runner` profile.** The existing runner is a fixed-argv one-shot process bridge with a request body for goal/graph and run/cancel semantics. Current AX requires typed multi-resource provisioning, readiness/status observation, separate suspend/resume lifecycle, protected cluster credentials, and a completion/result channel AX does not supply from the child exit code. A single `ax ... {prompt}` command would target a different historical interface and is not this Kubernetes/Substrate AX product. Do not add a disabled profile that falsely implies compatibility.

If implemented later, add a dedicated optional external-executor adapter/profile behind an allowlisted server-side deployment configuration. Minimum contract: create or idempotently reconcile an Apex-linked Workspace/Model/Task; enforce stable AX names and immutable manifest digest; wait for `Ready`; receive authenticated, bounded terminal result and resource/token usage from a custom runner callback/artifact channel; translate Apex cancel into explicit suspend or delete per policy; poll/stream `WatchTask`; reconcile timeouts and task deletion without double-charging; and record AX task/atespace, pinned AX/Substrate revisions, manifest/graph hash, terminal phase, and cost evidence. Do not expose AX credentials, `--server`, arbitrary manifest YAML, shell, or task names to the browser.

## Sources (primary; accessed 2026-09-27)

- [Google AX source at pinned commit](https://github.com/google/ax/tree/e70162a34037c221fe6fadefd98308c05a4ad8f3) — release v0.3.1 product description, CLI, prereqs, and license; [release v0.3.1](https://github.com/google/ax/releases/tag/v0.3.1) — release timing.
- [Agent Executor product site](https://agentexecutor.io/) — published scale/resumption design claims; no reproducible concurrency benchmark details.
- [Google Cloud: Introducing Agent Executor](https://cloud.google.com/blog/products/ai-machine-learning/agent-executor-googles-distributed-agent-runtime) — internal runtime lineage and Agent Substrate architecture/capacity claims.
- [AX v1alpha1 protobuf at v0.3.1](https://github.com/google/ax/blob/v0.3.1/pkg/apis/v1alpha1/ax.proto), [AX design/API reference](https://github.com/google/ax/blob/main/DESIGN.md), [CLI/deployment README at v0.3.1](https://github.com/google/ax/blob/v0.3.1/README.md).
- [AX manifest guide](https://github.com/google/ax/blob/main/docs/manifests.md), [core concepts](https://github.com/google/ax/blob/main/docs/concepts.md), [runner contract](https://github.com/google/ax/blob/main/docs/runner.md), [networking](https://github.com/google/ax/blob/main/docs/networking.md), [deployment manifests](https://github.com/google/ax/tree/main/deploy), [go.mod](https://github.com/google/ax/blob/main/go.mod).
- [AX upstream issue #382](https://github.com/google/ax/issues/382) — open report on missing control-plane auth/authorization; used as a security caveat, not as formal API documentation.
- [Google Cloud: Advent of Agents participation](https://cloud.google.com/blog/topics/consulting/upskill-your-ai-using-daily-micro-habits) — reports 150,000+ developer participants and 859,000+ browser-based code executions, not AX concurrency.
- [Towards Internet-Scale Training for Agents (InSTA)](https://openreview.net/pdf?id=ZRiK2T2VNb) — describes 150,000 web-navigation task/site attempts for data collection; it is a research workload result, not an AX concurrent-capacity measurement.
