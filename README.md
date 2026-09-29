# ApexGraphSwarm

**Source-grounded graph intelligence, NP-hard solver kernels, and agent governance — unified monorepo.**

## Overview

ApexGraphSwarm is a production-grade platform for graph-based reasoning, combinatorial optimization, and autonomous agent orchestration. It combines:

- **22 NP-hard solver kernels** — deterministic, zero-dependency Python 3.10+
- **World-class graph visualization** — Sigma.js v4, WebGL shaders, 3D, 25 layout templates
- **Agent governance** — ISO 42001, SOC 2, PCI DSS compliance frameworks
- **4 consensus protocols** — Raft, Paxos, BFT, HotStuff
- **Complete DevOps** — CI/CD, Docker, Kubernetes, Prometheus + Grafana

## Quick Start

```bash
# Install dependencies
pnpm install

# Run all tests
pnpm test

# Build all packages
pnpm build

# Dev mode (web app on :3010)
pnpm dev

# Python tests
python -m pytest tests/

# Docker
docker-compose up --build
```

## Repository Structure

```
apexgraphswarm/
├── apps/
│   └── web/                    # Next.js 16 + React 19 + TypeScript 7
│       ├── app/                # 14 pages, 17 API routes
│       ├── components/         # 34 React components
│       ├── lib/                # 44 library modules
│       └── tests/              # 991 E2E + 1,780 integration + 60 property tests
├── packages/
│   └── governance/             # Shared TypeScript governance types & logic
├── kernels/                    # 22 Python solver kernels (zero-dependency)
│   ├── consensus/              # Raft, Paxos, BFT, HotStuff
│   ├── scheduling/             # Job shop, flow shop, open shop
│   ├── linear_programming/     # Simplex, interior point, branch-and-bound
│   ├── integer_programming/    # Branch-and-cut, branch-and-price
│   ├── graph_coloring/         # DSatur, LF, SLF
│   ├── max_flow/               # Edmonds-Karp, Dinic, push-relabel
│   ├── tsp/                    # Christofides, Lin-Kernighan, 2-opt
│   ├── knapsack/               # Branch-and-bound, DP, greedy
│   ├── graph_partitioning/     # Kernighan-Lin, spectral, multilevel
│   ├── community_detection/    # Louvain, Leiden, label propagation
│   ├── shortest_path/          # Dijkstra, A*, Bellman-Ford, Floyd-Warshall
│   ├── mst/                    # Prim, Kruskal, Borůvka
│   ├── bipartite_matching/     # Hopcroft-Karp, Hungarian, auction
│   ├── sat/                    # DPLL, CDCL, WalkSAT
│   ├── csp/                    # AC-3, backtracking, forward checking
│   ├── game_theory/            # Nash, Stackelberg, VCG, GSP
│   ├── formal_verification/    # Z3 SMT integration
│   ├── escrow/                 # 3-party escrow with AI judge
│   ├── agent_hypervisor/       # Execution rings, VFS, DID, saga
│   ├── jailbreak_firewall/     # 400+ attack patterns, containment
│   ├── threat_matrix/          # 11 tactic domains, 44 techniques
│   ├── conformance_eval/       # 4-dimension evaluation harness
│   ├── red_team/               # 18 surfaces, 17 vulns, 5 exploit chains
│   ├── grc_integration/        # ISO 42001, SOC 2, PCI DSS, DORA, SEC 8-K, FFIEC
│   ├── audit_trail/            # SHA-256 hash chaining, evidence vault
│   └── policy_engine/          # JSON Schema, Rego parser/evaluator
├── apexgraphswarm/             # Python control plane (stdlib-only)
├── tests/                      # 513 unit + 137 security + 43 fuzzing + 60 property
├── docs/                       # OpenAPI 3.1, 10 tutorials, 35 ADRs, 60 examples
├── examples/                   # 60 code examples
├── scripts/                    # CI/CD and benchmark scripts
├── monitoring/                 # Prometheus + Grafana (5 services, 12 alerts)
├── k8s/                        # 12 Kubernetes manifests
├── reports/                    # 10 audit reports + benchmarks
├── Dockerfile                  # Multi-stage build
├── docker-compose.yml          # All services
├── .github/workflows/          # CI/CD, deploy, benchmark
├── pyproject.toml              # Python package config
├── package.json                # Workspace root
├── pnpm-workspace.yaml         # pnpm workspaces
├── turbo.json                  # Turborepo pipeline
└── tsconfig.base.json          # Shared TypeScript config
```

## Solver Kernels (22)

| Kernel | Algorithms | Tests |
|--------|-----------|-------|
| Graph coloring | DSatur, LF, SLF | 62 |
| Max flow | Edmonds-Karp, Dinic, push-relabel | 33 |
| TSP | Christofides, Lin-Kernighan, 2-opt | 37 |
| Knapsack | Branch-and-bound, DP, greedy | 49 |
| Scheduling | Job shop, flow shop, open shop | 27 |
| Graph partitioning | Kernighan-Lin, spectral, multilevel | 37 |
| Community detection | Louvain, Leiden, label propagation | 47 |
| Shortest path | Dijkstra, A*, Bellman-Ford, Floyd-Warshall | 54 |
| MST | Prim, Kruskal, Borůvka | 29 |
| Bipartite matching | Hopcroft-Karp, Hungarian, auction | 31 |
| SAT | DPLL, CDCL, WalkSAT | 35 |
| CSP | AC-3, backtracking, forward checking | 26 |
| Linear programming | Simplex, interior point | 7 |
| Integer programming | Branch-and-cut, branch-and-price | 6 |
| Game theory | Nash, Stackelberg, VCG, GSP | 25 |
| Formal verification | Z3 SMT integration | — |
| Consensus | Raft, Paxos, BFT, HotStuff | 15 |
| Escrow | 3-party with AI judge | 53 |
| Agent hypervisor | Rings, VFS, DID, saga | 129 |
| Jailbreak firewall | 400+ patterns, containment | 15 |
| Threat matrix | 11 domains, 44 techniques | 51 |
| Conformance eval | 4 dimensions, scorecards | 44 |
| Red team | 18 surfaces, 17 vulns | 23 |
| GRC integration | 191 controls, 6 frameworks | 35 |
| Audit trail | Hash chaining, evidence vault | 32 |
| Policy engine | JSON Schema, Rego | 54 |

**Total: 861+ solver tests**

## Graph Visualization

- **Sigma.js v4** — WebGL renderer, 60fps at 50K+ nodes
- **WebGL shaders** — Custom node/edge rendering with glow, halos, gradients
- **3D renderer** — Three.js force-directed with orbit controls
- **25 layout templates** — ForceAtlas2, Fruchterman-Reingold, circular, radial, sunburst, chord, hierarchical, tree, org chart, Sankey, grid, timeline, and more
- **Community detection** — Louvain, Leiden, label propagation
- **Centrality visualization** — PageRank, betweenness, eigenvector, degree
- **Minimap** — Spatial indexing, adaptive clustering
- **Search & filter** — Fuzzy search, faceted filters, query builder
- **Time slider** — Temporal graph animation
- **Export** — PNG, SVG, PDF, JSON, CSV, Neo4j Cypher
- **Graph editor** — Drag-and-drop, undo/redo, auto-layout
- **Real-time sync** — WebSocket collaborative editing with CRDT

### Performance Benchmarks

| Library | 100K nodes | FPS | Memory |
|---------|-----------|-----|--------|
| **ApexGraphSwarm** | 2,002ms | 35 | 98MB |
| vis-network | — | — | ❌ Fails at 10K |
| AntV G6 | — | — | ❌ Fails at 10K |
| Cytoscape.js | — | — | ❌ Fails at 10K |

**ApexGraphSwarm is the only library that renders 100K nodes.**

## Governance & Security

- **ISO 42001** — 22 controls for AI governance
- **SOC 2** — 32 Trust Service Criteria
- **PCI DSS** — 61 requirements for payment security
- **EU DORA** — 23 ICT risk management controls
- **SEC 8-K** — 29 material event disclosure controls
- **FFIEC CAT** — 24 cybersecurity assessment controls
- **Audit trail** — SHA-256 hash chaining, tamper-evident
- **Policy engine** — JSON Schema + Rego parser/evaluator
- **Agent hypervisor** — Execution rings 0-3, VFS namespacing, DID identity
- **Jailbreak firewall** — 400+ attack patterns, multi-turn escalation detection
- **Red team** — 18 attack surfaces, 17 vulnerabilities, 5 exploit chains

## Consensus Protocols

| Protocol | Lines | Tests | Key Features |
|----------|-------|-------|--------------|
| Raft | 137 | 3-node cluster | Leader election, log replication, term safety |
| Paxos | 187 | 5 | Multi-decree, conflicting proposals, majority failure |
| BFT (PBFT) | 166 | 7 | PrePrepare → Prepare → Commit, f < n/3 tolerance |
| HotStuff | 98 + 93 | 4 | Linear communication, 3-chain commit rule |

## Test Suite

| Category | Count | Tool |
|----------|-------|------|
| Solver unit tests | 513 | pytest |
| API integration tests | 1,780 | TypeScript |
| E2E tests | 991 | Playwright |
| Security tests | 137 | pytest |
| Fuzzing tests | 43 | Hypothesis + fast-check |
| Property tests | 60 | Hypothesis + fast-check |
| Visual regression | 14 | Playwright + pixelmatch |
| Performance tests | 13 | k6 + Artillery |
| **Total** | **~4,300+** | |

## CI/CD

- **GitHub Actions** — 3 workflows (CI, deploy, benchmark)
- **Multi-platform** — ubuntu, macos, windows
- **Multi-version** — Python 3.10, 3.11, 3.12
- **Regression detection** — Configurable thresholds
- **Artifact upload** — JSON reports, build artifacts

## Deployment

### Docker

```bash
docker-compose up --build
```

### Kubernetes

```bash
# Fill in secrets first, then:
kubectl apply -k k8s/
```

12 manifests: namespace, configmap, secret, PVC, deployment, service, ingress, HPA, PDB, networkpolicy, serviceaccount, kustomization.

### Monitoring

```bash
cd monitoring && docker compose up -d
```

5 services: Prometheus (:9090), Grafana (:3000), Alertmanager (:9093), Exporter (:8000), Node Exporter (:9100).

12 alert rules, 16 metric families, 2 Grafana dashboards.

## Documentation

- **README.md** — This file
- **OpenAPI 3.1** — `docs/openapi.yaml` (17 endpoints, 40 schemas)
- **Tutorials** — `docs/tutorials/` (10 tutorials, 1,878 lines)
- **ADRs** — `docs/adr/` (35 architecture decision records)
- **Examples** — `examples/` (60 code examples)
- **Migration guides** — `docs/MIGRATION.md`
- **Changelog** — `CHANGELOG.md`
- **Benchmarks** — `BENCHMARKS.md`

## Scripts

```bash
# Run all tests (Python + TypeScript)
./scripts/run-all-tests.sh

# Build all packages
./scripts/build-all.sh

# Run benchmarks
python scripts/run_ci_benchmarks.py

# Run performance tests
cd tests/performance && ./run-tests.sh all k6

# Run visual regression
cd apps/web && npm run test:visual

# Update visual baselines
cd apps/web && npm run test:visual:update
```

## License

MIT

## Contributing

See `AGENTS.md` for engineering contract and contribution guidelines.
