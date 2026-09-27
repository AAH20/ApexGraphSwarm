# Ecosystem interoperability

ApexGraphSwarm separates four concerns: control-plane policy/accounting, execution runtimes, MCP tool access, and reusable skill content. `/ecosystem` exposes a selectable source catalog, configured endpoint discovery, local SKILL.md review and operating-cost scenario export. None of these selections enables paid execution.

## Google AX

AX is an external distributed executor candidate, not a model or a drop-in harness command. Its current Task/Workspace/Model resources and Agent Substrate requirements differ from older AX interfaces. See the [pinned assessment](google-ax-assessment.md). The 150K+ simultaneous-agent claim is unverified. The local SQLite control plane remains bounded and does not inherit AX's scale claims.

The next adapter must map an Apex task/idempotency key to a namespaced AX task, persist the remote identifier before polling, normalize lifecycle events, reconcile unknown outcomes and actual usage, and provide durable result receipts. Checkpoint/resume requires fenced ownership and tested side-effect semantics. Do not use runner process liveness as proof of task success. Before enabling the adapter, verify authentication/network isolation, quotas, budget admission and release-specific contracts against the deployed cluster.

## MCP and gateways

A protocol adapter allows compatible direct servers or gateways without enumerating every vendor. The current implementation performs bounded read-only discovery using an explicit server-owned allowlist. It never calls discovered tools. See [configuration and limitations](mcp-interoperability.md).

The official registry, agentgateway and Docker MCP Gateway are external discovery/deployment references. Their presence in the catalog does not certify installation, endpoint compatibility or tool permissions. Future execution needs an immutable server/tool identity, input schema validation, per-tool policy, a durable invocation receipt, timeout/cancellation semantics, quota admission and usage reconciliation. MCP capability annotations remain untrusted data. Model access via OpenRouter/vLLM stays in the existing provider/harness layer.

## Skills libraries

skills.sh and arbitrary source repositories can supply pasted SKILL.md text to the bounded review importer. Exact content hashes and user-entered revision references are exported for review. No reference is fetched and no script is launched. Additional assets, licenses, declared tools and harness mapping need explicit review before adoption. A content hash is not a trust verdict. See [skills interoperability](skills-interoperability.md).

## Cost and benchmark contract

The scenario calculator sums quantity × USD/unit for model use, active compute, suspended storage, gateway/tool calls, resume operations, egress and allocated platform overhead. A category with a missing quantity or rate blocks a complete total and cost per successful result; an explicit zero records an inapplicable category. Values and date/source references are user assumptions, not verified rate cards. Weighted token rates must come from the model-specific input/output/cache calculation in Delegation & cost. Include retry and failed-work usage in quantities. Expected successes are a scenario denominator, not a measured quality result.

Use the existing integer micro-USD ledger for admission/accounting. This floating-point planning calculator is not a billing ledger. Do not add a shared allocation twice across model/harness/runtime budgets. Free license price does not imply free compute, model access, gateway calls or operations.

Evaluation gates for external executors: dispatch and resume p50/p95/p99, queue wait, task throughput, active vs suspended resource use, duplicate side effects, recovery correctness, success on held-out tasks, provider throttling and actual cost per successful result. Report workload, hardware, versions, concurrency, retries and sample sizes. Local deterministic fixture benchmarks remain distinct from live agent or AX benchmarks.

## Primary references

- https://github.com/google/ax
- https://modelcontextprotocol.io/specification/2025-11-25
- https://registry.modelcontextprotocol.io
- https://github.com/agentgateway/agentgateway
- https://github.com/docker/mcp-gateway
- https://skills.sh/docs
- https://agentskills.io/specification
