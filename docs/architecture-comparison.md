# Architecture comparison and adoption plan

The Architecture lab at `/ecosystem/research` compares orchestration projects, retrieval frameworks/stores and optimization opportunities. It exposes source evidence and limitations, allows comparison-candidate selection, and exports a workload-specific benchmark design. Research catalog entries are not enabled execution adapters.

## Starting architecture

1. Keep Apex's task identity, durable leases and cost ledger authoritative while comparing one execution stack at a time. Evaluate Deep Agents over its LangChain/LangGraph foundation for long-horizon repository work; compare CrewAI Crews/Flows on the same tasks. LangGraph is a workflow runtime, Deep Agents is a harness, and an application built with either still needs its own isolation and budget enforcement.
2. Consider Paperclip for organization-level responsibilities, approvals and recurring work. Decide whether it or Apex owns each task, cancellation and spend record before connecting them. Do not create two independent authorities or nested retry loops. Google AX remains a separate distributed executor candidate with its own deployment and lifecycle contract.
3. Establish lexical and vector-only retrieval baselines before adding GraphRAG. Compare Microsoft GraphRAG, Cognee or LightRAG when multi-hop evidence, memory or corpus-wide synthesis justify extraction costs. Choose graph/vector storage by workload and operational requirements rather than adding every store. Neo4j, pgvector, Qdrant, Milvus and Weaviate have different query/index/deployment tradeoffs.
4. Apply an optimization kernel only after measuring a corresponding bottleneck. Keep the durable execution state machine authoritative; kernel output is a proposed plan. Validate plan completeness, prerequisites, resource capacities and budget feasibility before admission.

These are proposed adoption priorities, not a claim that one framework wins all workloads. See the [orchestration evidence](orchestration-landscape.md), [retrieval evidence](retrieval-landscape.md), [kernel audit](optimization-bottlenecks.md), and [AX assessment](google-ax-assessment.md).

## Reproducible comparison design

The UI provides repository engineering, GraphRAG/retrieval and durable-operation profiles. Each has a baseline, required metrics and recovery/cost gates. Exported designs preserve candidate evidence, pins supplied by the user, active worker assumptions, held-out task/trial counts, an explicit scenario cap and quality/latency/cost thresholds. Missing evidence stays visible. Even complete design fields do not enable execution or prove that the references are valid.

Use paired tasks and repeated trials; report uncertainty, raw failures and actual receipts. Keep model/provider, token ceilings, tool permissions and corpus snapshots constant when measuring framework effects. Report unavoidable configuration differences. Separate:

- Task success and citation-grounded answer quality from scheduler or index speed.
- Cold ingestion, graph extraction, embedding and index build from warm queries.
- ANN recall at a fixed k/filter distribution from database throughput.
- End-to-end wall time from queue wait, model time and framework overhead.
- Measured local fixture results from publisher-reported or externally reproduced results.

A Terminal-Bench harness score, a memory benchmark score and an ANN QPS result answer different questions. They must not be collapsed into a shared leaderboard. Local experiments for the newly reviewed frameworks/stores have not been run. The existing fixture benchmark only measures Apex's scheduler with fixed payloads.

## Cost model extension

The Ecosystem cost table now includes embedding ingestion/refresh, reranker requests, graph/vector index storage, managed retrieval fees and index compute. Add graph-extraction LLM tokens to model usage; the index-compute row excludes that token charge. Include failed runs, retry traffic, replicas/idle capacity and reindexing, and amortize shared ingest cost over a stated query volume. Avoid double-counting managed service compute in both per-query fees and allocated platform costs. Record rate source/date and reconcile estimates against actual receipts before promotion.

## Execution milestones

- **First:** pin candidate versions and construct representative held-out task/corpus fixtures; agree acceptance thresholds.
- **Next:** implement one isolated adapter with persistent remote run IDs, cancellation, idempotency/side-effect policy and normalized usage receipts. Review credentials and tool scope separately.
- **Then:** run bounded baseline-versus-candidate trials, failure injection and small-instance exact-oracle comparisons for kernel heuristics. Keep failed/cancelled runs in cost accounting.
- **Promote only with evidence:** quality, latency, cost and recovery gates must pass on representative held-out work. Increase active concurrency in measured steps while preserving rate limits and budget admission.

No new Python dependencies, external framework installations, provider calls or database deployments are part of this research increment.
