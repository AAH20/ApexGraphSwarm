---
name: map
description: Build and inspect an ApexGraphSwarm repository graph with explicit source evidence and parser limits.
argument-hint: [repository path]
---

Create a deterministic repository graph for `$ARGUMENTS` using the ApexGraphSwarm analyzer. If no path was provided, use `.`.

1. Resolve the target repository path. Confirm it is a Git worktree and that the `apexgraphswarm` package is available from that repository root. Do not install dependencies or call a remote model.
2. Run `python3 -m apexgraphswarm graph <repository-path> --output /tmp/apex-repository-graph.json` with the path quoted safely as a single argument. If the command fails, report its error and stop; do not fabricate a graph.
3. Read the graph summary and warnings from `/tmp/apex-repository-graph.json`. Report counts, truncation, unresolved references, and parser warnings.
4. Summarize architecture using only node and edge evidence from the artifact. For each relationship claim, give the exact source and target node IDs, relation, confidence, and source path/line when present.
5. Distinguish observed inventory, parsed Python AST relationships, and inferred JavaScript/TypeScript lexical hints. Never describe a lexical hint as compiler-resolved semantics. Call out unsupported-language files as inventory-only.
6. State that source summaries and graph edges are navigation aids, not proof of runtime behavior or semantic truth. Ask which module or relationship neighborhood the user wants to inspect next if the request is broad.

The graph artifact is local and may contain repository paths and source-derived summaries. Do not publish it or paste it into an external service unless the user explicitly requests that transfer.
