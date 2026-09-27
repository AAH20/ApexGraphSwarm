# Retrieval and graph-store landscape

**Evidence checked:** 2026-09-27. This is a source-grounded comparison for architecture selection, not a compatibility matrix, endorsement, pricing sheet, or claim that ApexGraphSwarm already integrates every project listed. Recheck the cited versioned documentation before implementation: products and APIs change.

## Keep the layers distinct

GraphRAG names a retrieval/indexing approach: create structured context from a corpus, then retrieve it to answer questions. Microsoft GraphRAG, Cognee, and LightRAG provide some combination of ingestion, graph construction, retrieval strategies, prompts, and orchestration. They are not interchangeable with a database.

Neo4j is a graph store and query engine. pgvector, Qdrant, Milvus, and Weaviate are vector-search/storage choices with different relational, filtering, hybrid-search, and operations models. Neo4j itself also documents vector and full-text indexes. A framework may use one or more stores, but each combination requires a verified adapter, compatible data model, and operational plan. This catalog does **not** assert those combinations are wired in ApexGraphSwarm.

Choose only the layers the workload needs. A vector store does not create trustworthy entity relationships or summaries by itself. A graph database does not automatically extract a graph from source text. A GraphRAG framework's “hybrid” mode is a retrieval strategy, not proof that every backend can be combined without configuration.

## Evidence by system

| System | Layer | Practical role | Evidence boundary |
|---|---|---|---|
| Microsoft GraphRAG | GraphRAG framework | Extract entities/relationships and community summaries; local, global, DRIFT, and basic-vector query modes. | The official docs describe global map-reduce as resource-intensive and recommend prompt tuning. Indexing/model choice affects cost and results. |
| Cognee | GraphRAG / memory framework | Ingest, cognify, and search across chunks, graph relationships, summaries, and vectors. | Its BEAM report is a publisher-authored evaluation of synthetic conversational memory with LLM judging; its 10M run is explicitly exploratory and tuned on the reported question set. |
| LightRAG | GraphRAG framework | Graph-aware and vector retrieval with multiple query modes and configurable stores. | Its README says default in-memory stores with local persistence are intended for small-scale testing/evaluation/debugging, not production; use the reproduction protocol before interpreting paper results. |
| Neo4j | Graph store | Persist and query nodes/relationships; vector and full-text indexes can supply hybrid candidates followed by graph expansion. | Semantic-index docs are capability documentation, not a cross-database benchmark. Keep score fusion explicit. |
| pgvector | Vector store | Add exact or approximate vector search to PostgreSQL relational data and SQL filters. | Approximate filtering can underfill result sets; iterative scans, partial indexes, or partitioning may change recall and cost. |
| Qdrant | Vector store | Dense/sparse/multi-vector search, filters, and staged/hybrid query composition. | Qdrant documents itself as vector search and says it does not provide built-in ontologies/knowledge graphs or non-vector ranking functions. |
| Milvus | Vector store | ANN search with metadata filters and multi-vector hybrid retrieval. | Filter strategy, index parameters and deployment topology matter. VectorDBBench is maintained by Zilliz, the company behind Milvus. |
| Weaviate | Vector store | Object/vector search with configurable hybrid fusion of vector and BM25F results. | Candidate depth, fusion weights, versions, and cloud-only features affect results; database retrieval metrics alone do not score final answers. |

Detailed evidence, source URLs and adoption considerations are also available in [`retrievalEvidence`](../apps/web/lib/retrieval-evidence.ts).

## Benchmark evidence is not one leaderboard

Use published benchmark artifacts as context, not as a substitute for a workload-specific evaluation. These projects measure different layers and questions:

- **VectorDBBench** ([source](https://github.com/zilliztech/VectorDBBench)) runs scenario-specific vector database cases. Its repository reports metrics such as recall, QPS, and latency, and describes datasets, filtering, payload profiles, and server/client hardware for standard runs. It is maintained by Zilliz, which should be disclosed when citing its cross-product results. A leaderboard aggregate is not a universal fit score; cases, versions, systems, and hardware may differ.
- **ANN-Benchmarks** ([source](https://github.com/erikbern/ann-benchmarks)) compares approximate-nearest-neighbor algorithms/libraries using dataset ground truth and recall/performance tradeoffs. It is not a full database, multi-tenant filtering, graph traversal, or RAG answer-quality comparison.
- **BEIR** ([paper](https://arxiv.org/abs/2104.08663), [reference implementation](https://github.com/beir-cellar/beir)) evaluates retrieval systems across heterogeneous information-retrieval tasks and datasets, with metrics including nDCG, MAP, Recall, Precision, and MRR. It primarily informs retrieval-model relevance; it does not benchmark database operations, tenant isolation, graph building, or end-to-end application cost.
- **Framework reports and papers** (for example, Cognee's [BEAM report](https://github.com/topoteretes/cognee/blob/main/cognee/eval_framework/beam/REPORT.md) or LightRAG's [reproduction guide](https://github.com/HKUDS/LightRAG/blob/main/docs/Reproduce.md)) are publisher/project evidence under their stated corpus, models, prompts, retrieval settings, and scoring. Preserve that provenance; do not convert such results into an unqualified product ranking.

A local run is a separate evidence class. It should record exact commit/release and configuration, test corpus and held-out query set, chunking and embedding model/version, index and distance settings, top-k, filters and selectivity, candidate/fusion/reranker settings, concurrency, warm/cold cache state, and client/server hardware and placement. Report retrieval relevance (for example recall@k, MRR, or nDCG@k where labels permit), latency percentiles, throughput, build/update time, resource use, and failure rate. For RAG, separately score answer correctness/faithfulness and citation support; retrieval recall does not imply an answer is correct.

For graph-aware indexing, include extraction and summarization time and model/token usage, incremental-update behavior, graph traversal cost, and source-citation accuracy. For hybrid systems, compare against dense-only, lexical/sparse-only, and graph-aware baselines on the same queries. State filter selectivity and whether filtered recall uses a correct filtered ground truth. Repeat enough times to expose variance; do not compare runs with different embeddings, prompts, hardware, concurrency, or cache assumptions as if only the database changed.

### Minimal local comparison protocol

1. Freeze a representative corpus and a held-out query set with adjudicated relevant source IDs; stratify entity lookup, exact identifier, multi-hop, and corpus-wide questions.
2. Run a simple lexical or dense baseline before graph extraction. Keep chunking, embedding model, candidate count, and answer model fixed where possible.
3. Add one graph-aware component at a time. Measure indexing/build and updates as well as query-time quality and latency.
4. Record query-level evidence, not only one aggregate. Include citation precision/coverage and answer faithfulness for generated responses.
5. Publish local measurements as local measurements with date, hardware, versions, configurations, and run artifacts. Keep publisher results in a distinct column/section.

No prices are asserted here. Open-source licensing does not make hosting, storage, embedding, extraction, or answer generation free. Obtain current quotes for managed offerings separately and price model calls from the exact provider/model/rate card actually configured.

## Sources

Primary documentation and repositories reviewed on 2026-09-27:

- [Microsoft GraphRAG overview](https://microsoft.github.io/graphrag/) and [query overview](https://microsoft.github.io/graphrag/query/overview/)
- [Cognee repository](https://github.com/topoteretes/cognee) and [Cognee BEAM technical report](https://github.com/topoteretes/cognee/blob/main/cognee/eval_framework/beam/REPORT.md)
- [LightRAG repository and production-storage notes](https://github.com/HKUDS/LightRAG) and [reproduction guide](https://github.com/HKUDS/LightRAG/blob/main/docs/Reproduce.md)
- [Neo4j semantic indexes](https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/) and [hybrid-search guide](https://neo4j.com/developer/genai-ecosystem/hybrid-search/)
- [pgvector README](https://github.com/pgvector/pgvector)
- [Qdrant hybrid queries](https://qdrant.tech/documentation/search/hybrid-queries/), [filtering](https://qdrant.tech/documentation/search/filtering/), and [FAQ](https://qdrant.tech/documentation/faq/)
- [Milvus overview](https://milvus.io/docs/overview.md), [filtered search](https://milvus.io/docs/filtered-search.md), and [multi-vector search](https://milvus.io/docs/multi-vector-search.md)
- [Weaviate hybrid search](https://docs.weaviate.io/weaviate/search/hybrid) and [search concepts](https://docs.weaviate.io/weaviate/concepts/search)
- [VectorDBBench](https://github.com/zilliztech/VectorDBBench), [ANN-Benchmarks](https://github.com/erikbern/ann-benchmarks), [BEIR paper](https://arxiv.org/abs/2104.08663), and [BEIR implementation](https://github.com/beir-cellar/beir)
