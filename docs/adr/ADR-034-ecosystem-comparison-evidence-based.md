# ADR-034: Ecosystem comparison without installation claims

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must compare orchestration frameworks (LangGraph, CrewAI, Deep Agents, Paperclip, Google AX), retrieval frameworks (GraphRAG, Cognee, LightRAG), and vector databases (Neo4j, pgvector, Qdrant, Milvus, Weaviate). These comparisons must be based on documented evidence, not on installed or benchmarked projects.

## Decision

**Ecosystem comparisons are evidence-based assessments, not installed integrations.** Key characteristics:

- **Evidence levels**: Published third-party reports, documented features, proposed tests, and locally measured results have different evidence levels.
- **No installation**: "Inclusion in a comparison does not install or benchmark a project."
- **No endorsement**: "Inclusion in a catalog is not endorsement, certification, or an implemented integration."
- **Comparison design**: The Architecture lab exposes source evidence and limitations, allows comparison-candidate selection, and exports a workload-specific benchmark design.

**Compared systems:**
- Orchestration: LangChain/DeepAgents, CrewAI, Paperclip, Google AX
- Retrieval: Microsoft GraphRAG, Cognee, LightRAG
- Vector stores: Neo4j, pgvector, Qdrant, Milvus, Weaviate

## Alternatives considered

1. **Install and benchmark all frameworks**: Would provide direct evidence but is time-consuming, expensive, and requires credentials.
2. **No comparisons**: Would simplify the system but would prevent informed framework selection.
3. **Marketing-based comparisons**: Would be misleading; evidence-based assessments are more reliable.

## Consequences

- **Positive**: Informed framework selection; clear evidence levels; no false claims; reproducible comparison design.
- **Negative**: Comparisons are not direct benchmarks; users must run their own benchmarks for definitive results.
- **Critical statement**: "Inclusion in a comparison does not install or benchmark a project."

## Related

- ADR-004 (Next.js web frontend)
- ADR-012 (explicit adapter pattern)
- ADR-013 (evaluation and promotion gates)
- ADR-033 (optimization kernels pinned adapters)
