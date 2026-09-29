# ADR-002: Python standard-library-only control plane

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The Python control plane (`apexgraphswarm/`) is the core scheduler, graph analyzer, optimization engine, and evaluation framework. It must run on any machine with Python 3.10+ without requiring `pip install` of third-party packages. This constraint is stated in `AGENTS.md`: "Keep the Python control plane Python 3.10+ standard-library only."

## Decision

The Python control plane uses **only the Python standard library**. No third-party Python packages are required for the core system. This includes:

- `sqlite3` for the durable control plane
- `ast` for Python source analysis
- `re` for lexical JavaScript/TypeScript analysis
- `json`, `hashlib`, `hmac`, `secrets`, `math`, `decimal` for data handling
- `urllib` for bounded HTTP requests (telemetry, decision providers)
- `subprocess` for Git commands during repository analysis

The web frontend (`apps/web/`) has its own npm dependencies and is explicitly separate from the Python control plane.

## Alternatives considered

1. **Third-party scheduler libraries (Celery, RQ, Prefect)**: Would provide mature task queue features but add deployment complexity, version coupling, and potential licensing concerns.
2. **Third-party graph libraries (NetworkX, igraph)**: Would simplify graph analysis but the repository graph is custom-built for evidence-bearing relationships with confidence levels.
3. **Third-party SQLite wrappers (SQLAlchemy, peewee)**: Would provide ORM features but the control plane needs precise transactional control and custom fencing logic that is clearer with raw SQL.
4. **Third-party HTTP library (requests, httpx)**: Would simplify HTTP but `urllib` is sufficient for the bounded, read-only telemetry and decision provider use cases.

## Consequences

- **Positive**: Zero Python dependency installation; works in restricted environments; no supply-chain risk from Python packages; easier to audit and verify; Python 3.10+ compatibility is the only requirement.
- **Negative**: More boilerplate for some operations (e.g., HTTP requests, graph algorithms); no access to optimized graph libraries; manual implementation of features that libraries provide.
- **Trade-off**: The control plane is intentionally minimal and focused on correctness and auditability over feature richness. External frameworks (LangGraph, CrewAI, etc.) are assessed as comparison candidates, not dependencies.

## Related

- ADR-001 (local-first architecture)
- ADR-003 (SQLite control plane)
- ADR-012 (explicit adapter pattern)
