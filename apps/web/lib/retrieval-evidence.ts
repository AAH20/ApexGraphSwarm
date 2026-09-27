export type RetrievalLayer = 'graphrag' | 'graph-store' | 'vector-store';

export type RetrievalEvidence = {
  id: string;
  name: string;
  layer: RetrievalLayer;
  role: string;
  strengths: string[];
  limits: string[];
  benchmark: {
    status: string;
    description: string;
    source: string;
  };
  sources: string[];
  adoption: string;
  asOf: '2026-09-27';
};

/** Evidence-oriented catalog: entries describe distinct layers, not enabled adapters. */
export const retrievalEvidence = [
  {
    id: 'microsoft-graphrag',
    name: 'Microsoft GraphRAG',
    layer: 'graphrag',
    role: 'A graph-building and retrieval pipeline that extracts entities and relationships, forms hierarchical communities, and offers local, global, DRIFT, and basic-vector query modes.',
    strengths: [
      'Global queries can reason over generated community reports; local queries combine graph-derived context with source text units.',
      'The basic vector mode provides a useful baseline within the same query framework.',
      'Index artifacts and query configuration are explicit and configurable.'
    ],
    limits: [
      'Index construction uses model-backed extraction and summaries; indexing and global map-reduce queries can be resource-intensive.',
      'Quality depends on corpus, prompts, model, index configuration, and question type; prompt tuning is recommended.',
      'It is a retrieval pipeline, not evidence that every graph/vector storage backend is natively supported by this application.'
    ],
    benchmark: {
      status: 'Publisher methodology and product documentation; no local ApexGraphSwarm run.',
      description: 'Do not infer a universal quality or latency win. Compare query modes on a fixed corpus and held-out questions, include index-build model/token cost, and report graph-grounded citation quality alongside retrieval metrics.',
      source: 'https://microsoft.github.io/graphrag/query/overview/'
    },
    sources: [
      'https://microsoft.github.io/graphrag/',
      'https://microsoft.github.io/graphrag/query/overview/',
      'https://microsoft.github.io/graphrag/get_started/'
    ],
    adoption: 'Consider when corpus-wide synthesis or entity-centered multi-hop questions justify an extraction/indexing stage. First compare with basic vector retrieval on representative held-out questions; budget indexing separately.',
    asOf: '2026-09-27'
  },
  {
    id: 'cognee',
    name: 'Cognee',
    layer: 'graphrag',
    role: 'An AI memory and data-processing framework with add/cognify/search flows that can combine chunks, entity-relation graphs, summaries, and vector retrieval.',
    strengths: [
      'Offers multiple retrieval views over ingested data and configurable hybrid retrieval.',
      'Its BEAM evaluation report records ingestion, retrieval settings, prompts, model assignments, and repeated answer/judge runs for audit.'
    ],
    limits: [
      'Framework behavior and supported storage combinations depend on selected versions and backends; verify the exact deployment path rather than assuming one universal setup.',
      'The published BEAM scores are specific to synthetic conversational-memory data, LLM judging, and the reported configuration; the 10M result is explicitly exploratory and selected on the scored questions.',
      'Not a vector or graph database by itself; storage backend selection and operational limits remain relevant.'
    ],
    benchmark: {
      status: 'Publisher-authored BEAM technical report; not an independent cross-framework comparison and not run locally.',
      description: 'The report describes synthetic multi-session conversations, rubric-based LLM judging, four repeated QA/evaluation rounds for its held-out 100K result, and a 10M exploratory run whose settings were tuned against the scored question set. These conditions do not establish a general ranking.',
      source: 'https://github.com/topoteretes/cognee/blob/main/cognee/eval_framework/beam/REPORT.md'
    },
    sources: [
      'https://github.com/topoteretes/cognee',
      'https://github.com/topoteretes/cognee/blob/main/cognee/eval_framework/beam/REPORT.md'
    ],
    adoption: 'Consider for applications that need a memory-ingestion and retrieval framework, especially when its data model and required backends fit. Pin versions and validate deployment/storage support before migration.',
    asOf: '2026-09-27'
  },
  {
    id: 'lightrag',
    name: 'LightRAG',
    layer: 'graphrag',
    role: 'A retrieval-augmented generation framework combining graph-derived entity/relationship context with vector and keyword-style retrieval and multiple query modes.',
    strengths: [
      'Supports local, global, hybrid, and mix-style retrieval paths and configurable KV, vector, graph, and document-status storage.',
      'Can use specialized graph and vector stores as configured backends.'
    ],
    limits: [
      'The project states that default in-memory stores with local-file persistence are for small-scale testing/evaluation/debugging, not production.',
      'Production deployments require deliberate backend configuration; examples and community integrations may have different support maturity.',
      'Paper/project comparisons are configuration- and dataset-specific and should be reproduced before applying to a different corpus.'
    ],
    benchmark: {
      status: 'Project/paper-reported comparisons with a reproduction guide; no local ApexGraphSwarm run.',
      description: 'Treat the reported task-specific comprehensiveness/diversity comparisons as publisher research evidence. Reproduce with the stated corpus, prompts, models, and evaluation method; they do not establish a universal speed, quality, or cost ranking.',
      source: 'https://github.com/HKUDS/LightRAG/blob/main/docs/Reproduce.md'
    },
    sources: [
      'https://github.com/HKUDS/LightRAG',
      'https://github.com/HKUDS/LightRAG/blob/main/docs/Reproduce.md'
    ],
    adoption: 'Consider when a graph-aware RAG pipeline and flexible store backends are wanted together. Prototype against a baseline and select production backends explicitly; do not treat default local persistence as a production deployment.',
    asOf: '2026-09-27'
  },
  {
    id: 'neo4j',
    name: 'Neo4j',
    layer: 'graph-store',
    role: 'A property graph database for durable nodes, relationships, and graph queries; it also supports vector and full-text semantic indexes for hybrid retrieval.',
    strengths: [
      'Graph traversals and relational context can be queried in the same database as node/relationship properties.',
      'Vector and full-text indexes can be combined as hybrid retrieval inputs.',
      'Supports graph expansion after initial semantic retrieval.'
    ],
    limits: [
      'A graph database is a storage/query layer, not a complete GraphRAG extraction, prompt, or evaluation pipeline.',
      'Index readiness, schema, query plans, access patterns, and deployment sizing must be validated for the target workload.',
      'Raw similarity scores from different retrieval sources should not be compared directly; use an explicit fusion/reranking method.'
    ],
    benchmark: {
      status: 'Vendor documentation for capabilities; no comparative local run.',
      description: 'The cited semantic-index documentation describes index behavior and combining full-text/vector search, not a controlled ranking against other graph or vector stores. Measure graph traversal plus retrieval on the same graph, filters, and hardware.',
      source: 'https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/'
    },
    sources: [
      'https://neo4j.com/docs/cypher-manual/current/indexes/semantic-indexes/',
      'https://neo4j.com/developer/genai-ecosystem/hybrid-search/'
    ],
    adoption: 'Consider when relationship queries, graph persistence, and a single graph/vector deployment are useful. Pair with a separately chosen ingestion/retrieval framework only after validating its adapter and query semantics.',
    asOf: '2026-09-27'
  },
  {
    id: 'pgvector',
    name: 'pgvector',
    layer: 'vector-store',
    role: 'A PostgreSQL extension providing vector types and exact or approximate nearest-neighbor search within relational tables.',
    strengths: [
      'Vector data and application metadata can live in PostgreSQL with SQL filtering and transaction semantics.',
      'Offers exact search and approximate HNSW/IVFFlat indexes; iterative scans can continue searching when filters leave too few results.',
      'Useful where an existing Postgres operational database should also serve vector retrieval.'
    ],
    limits: [
      'It does not provide a knowledge-graph model or GraphRAG extraction pipeline.',
      'Approximate index filtering may underfill results because filters can be applied after index scanning; iterative scans, partial indexes, or partitioning may be needed.',
      'Sharing an approximate index across tenants can affect recall and speed; benchmark the chosen isolation and query plan.'
    ],
    benchmark: {
      status: 'Project documentation describes algorithms and filtering behavior; no local comparative run.',
      description: 'For VectorDBBench comparisons, record the exact PostgreSQL/pgvector versions, index/build parameters, dimensions, dataset, filter selectivity, returned payload, recall@k, and host configuration. A database benchmark does not determine application answer quality.',
      source: 'https://github.com/pgvector/pgvector'
    },
    sources: ['https://github.com/pgvector/pgvector'],
    adoption: 'Consider when PostgreSQL is already a trusted system of record and the target volume/filtering fit its operational model. Compare exact and approximate search under production-shaped filters before choosing ANN.',
    asOf: '2026-09-27'
  },
  {
    id: 'qdrant',
    name: 'Qdrant',
    layer: 'vector-store',
    role: 'A vector search engine with payload filtering, dense/sparse or multi-vector query support, and hybrid or multi-stage query composition.',
    strengths: [
      'Can fuse dense and sparse retrieval or execute staged prefetch/query plans.',
      'Payload filters support metadata constraints; payload indexes can improve filtered search.',
      'Offers explicit multitenancy options including logical filtering and shard-based approaches.'
    ],
    limits: [
      'The project describes itself primarily as vector search and does not provide built-in ontologies or knowledge graphs.',
      'Payload indexes consume resources and should be designed around actual filter fields and selectivity.',
      'Hybrid retrieval adds indexing/storage/query work; gains over dense or sparse alone must be measured.'
    ],
    benchmark: {
      status: 'Vendor docs and benchmark-suite support; no local comparative run.',
      description: 'VectorDBBench has Qdrant scenarios, but its standard runs and cases change over time. Record the exact case/version, dataset and ground truth, filter/tenant shape, recall, p50/p95/p99 latency, QPS, payload response, and server/client hardware; do not read its leaderboard as a universal result.',
      source: 'https://github.com/zilliztech/VectorDBBench'
    },
    sources: [
      'https://qdrant.tech/documentation/search/hybrid-queries/',
      'https://qdrant.tech/documentation/search/filtering/',
      'https://qdrant.tech/documentation/faq/',
      'https://github.com/zilliztech/VectorDBBench'
    ],
    adoption: 'Consider as a vector retrieval component when payload filters, sparse+dense fusion, or its multitenancy model match the use case. Add a graph system separately if explicit entity/relationship queries are required.',
    asOf: '2026-09-27'
  },
  {
    id: 'milvus',
    name: 'Milvus',
    layer: 'vector-store',
    role: 'A vector database for ANN search with metadata filtering and hybrid search across multiple vector fields.',
    strengths: [
      'Supports dense, sparse, and multi-vector retrieval with ranker/fusion flows.',
      'Standard filtered search can constrain metadata before ANN search; iterative filtering is another documented path.',
      'Offers multiple tenancy/isolation scopes and a broad set of index/search configurations.'
    ],
    limits: [
      'It is a vector database, not a property graph or complete GraphRAG framework.',
      'Performance and recall depend on index type/parameters, filter strategy, data layout, consistency, and deployment topology.',
      'VectorDBBench is maintained by Zilliz, the company behind Milvus; publisher affiliation should be visible when interpreting comparisons.'
    ],
    benchmark: {
      status: 'Vendor capability docs plus a vendor-sponsored benchmark suite; no local comparative run.',
      description: 'VectorDBBench publishes scenario-specific recall, QPS and latency, including filters. Results are tied to version, dataset, configuration, server/client hardware, concurrency and payload profile; publisher-maintained runs are evidence to reproduce, not a universal ordering.',
      source: 'https://github.com/zilliztech/VectorDBBench'
    },
    sources: [
      'https://milvus.io/docs/overview.md',
      'https://milvus.io/docs/filtered-search.md',
      'https://milvus.io/docs/multi-vector-search.md',
      'https://github.com/zilliztech/VectorDBBench'
    ],
    adoption: 'Consider when large-scale ANN or multiple vector representations are central and the operational footprint is acceptable. Benchmark the intended filter/selectivity and update workload at the intended deployment topology.',
    asOf: '2026-09-27'
  },
  {
    id: 'weaviate',
    name: 'Weaviate',
    layer: 'vector-store',
    role: 'A vector database with object storage, vector/keyword retrieval, and configurable hybrid fusion between vector similarity and BM25F results.',
    strengths: [
      'Hybrid search exposes a configurable fusion method and relative weighting for keyword and vector results.',
      'Supports vector search and metadata-filtered object retrieval through its collection model.',
      'Useful when keyword matches and semantic similarity need to be fused in one search path.'
    ],
    limits: [
      'It is a vector/object search layer rather than a graph-RAG extraction and reasoning framework.',
      'Fusion weights and candidate windows affect results; evaluate on query classes where lexical exact-match and semantic recall differ.',
      'Cloud-only features and version-specific behavior must be distinguished from self-hosted capabilities.'
    ],
    benchmark: {
      status: 'Vendor documentation and benchmark-suite support; no local comparative run.',
      description: 'VectorDBBench includes selected Weaviate scenarios, but those do not measure end-to-end GraphRAG answer correctness. Freeze database/version, embedding model, dataset, filters, fusion settings, hardware, and exact benchmark case before comparing.',
      source: 'https://github.com/zilliztech/VectorDBBench'
    },
    sources: [
      'https://docs.weaviate.io/weaviate/search/hybrid',
      'https://docs.weaviate.io/weaviate/concepts/search',
      'https://github.com/zilliztech/VectorDBBench'
    ],
    adoption: 'Consider when object-centric vector retrieval and configurable keyword/vector fusion meet the retrieval needs. Add graph storage or graph-aware indexing only through a separately verified component and explicit integration.',
    asOf: '2026-09-27'
  }
] satisfies readonly RetrievalEvidence[];
