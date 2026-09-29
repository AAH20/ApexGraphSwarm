# ADR-003: SQLite as the durable control plane

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The control plane needs durable persistence for task DAGs, lease tokens, fenced completion, ordered events, recovery state, and integer micro-USD accounting. The system must survive process restarts, support concurrent workers, and provide transactional guarantees. It must run locally without a separate database server.

## Decision

**SQLite with WAL mode and `BEGIN IMMEDIATE` transactions** is the sole durable store for the control plane. Key characteristics:

- **WAL (Write-Ahead Logging)**: Allows concurrent readers with a writer; survives process restart.
- **`BEGIN IMMEDIATE`**: Serializes claims and state transitions; prevents race conditions between workers.
- **Single database file**: Stored at `.apexgraphswarm/control.sqlite3` by default; must be outside public/static web directories and out of Git.
- **Database-wide active lease cap**: Defaults to 4; persisted in the DB; reopening with a different cap is rejected.
- **300 logical agents**: Independent of the active execution cap; design/benchmark target, not a claim of 300 simultaneous paid model calls.

## Alternatives considered

1. **PostgreSQL/MySQL**: Would provide better concurrency, replication, and multi-tenancy but requires a separate server process, credentials, and deployment complexity that conflicts with local-first.
2. **Redis**: Would provide fast in-memory operations with optional persistence but is not durable by default, requires a separate process, and lacks the transactional SQL model needed for the control plane.
3. **File-based JSON persistence**: Would be simpler but lacks atomic transactions, concurrent write safety, and query capabilities.
4. **Embedded key-value stores (LevelDB, RocksDB)**: Would provide fast embedded storage but lack the relational model, SQL queries, and transactional guarantees needed for the control plane's status documents and event log.

## Consequences

- **Positive**: Zero configuration; single file backup; survives process restart; transactional integrity; no separate server process; works offline.
- **Negative**: Single-host only; no distributed queue; no tenant/RBAC model; no network access; concurrent write throughput is limited by SQLite's single-writer model.
- **Operational note**: Do not place the SQLite database on an unreliable shared/network filesystem. Back up the database and test restore before using it for valuable state.
- **Migration path**: Multi-tenant deployments must include a verified tenant scope in the admission layer/key and add tenant authorization to stored records before sharing a DB.

## Related

- ADR-001 (local-first architecture)
- ADR-002 (stdlib-only control plane)
- ADR-008 (lease-based task claiming)
- ADR-009 (execution classes)
