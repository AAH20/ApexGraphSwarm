# ADR-005: Evidence-bearing repository graph with confidence levels

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must analyze local repositories and produce a graph of modules, files, symbols, and relationships. The graph must distinguish between observed facts (e.g., a file exists) and inferred relationships (e.g., a function call that may or may not resolve to a specific definition). Users must be able to assess the reliability of each relationship before treating it as authoritative.

## Decision

The repository graph is **evidence-bearing with explicit confidence levels**. Every node and edge carries a `confidence` field:

- **`parsed`**: Python AST declarations, imports, and lexical calls with full scope resolution.
- **`observed`**: File/directory inventory, module containment.
- **`inferred`**: JavaScript/TypeScript lexical hints, heuristic import resolution, dynamic dispatch that may be unresolved.
- **`illustrative`**: Demo or example content.
- **`aggregated`**: Summary statistics.

**Language support is intentionally bounded:**

| Language | Analysis depth |
|----------|---------------|
| Python | AST scope resolution (declarations, imports, calls) |
| JavaScript/TypeScript | Lexical hints only; not compiler-complete semantic resolution |
| Rust/Go/C++ | File inventory only; compiler-backed semantic modules are planned |

**Operating limits:**

- 1,800 visible nodes / 12,000 visible edges in the UI
- Graph imports up to 25,000 nodes / 100,000 edges / 15 MB
- Default analyzer limits: 2,000 files / 10,000 symbols / 1 MB per source file
- Force-layout worker: 3-second computation budget

## Alternatives considered

1. **Full semantic analysis for all languages**: Would require compiler integrations (rustc, gopls, clangd) that are complex, slow, and language-specific. The current approach prioritizes Python (the control plane's language) and provides lexical hints for JS/TS.
2. **No confidence levels**: Would simplify the graph but would mislead users into treating inferred relationships as authoritative.
3. **Universal parser (tree-sitter)**: Would provide more languages but adds a native dependency that conflicts with the stdlib-only constraint.
4. **Runtime analysis (executing code)**: Would resolve dynamic dispatch but is unsafe, slow, and contradicts the "without executing repository code" principle.

## Consequences

- **Positive**: Users can assess reliability; Python (the primary language) gets full analysis; the graph is honest about its limitations; no code execution required.
- **Negative**: JS/TS analysis is incomplete; Rust/Go/C++ have no semantic analysis; dynamic dispatch in Python remains unresolved; users must understand confidence levels.
- **Migration path**: Compiler-backed language semantics are planned for future increments.

## Related

- ADR-002 (stdlib-only control plane)
- ADR-004 (Next.js web frontend)
- ADR-010 (bounded execution model)
