---
name: repository-evidence
description: Use when mapping an ApexGraphSwarm-supported repository, explaining module or symbol relationships, or checking whether a repository architecture claim is grounded in the generated graph artifact.
---

# Repository evidence workflow

Use `/apex-repository-evidence:map` to build `/tmp/apex-repository-graph.json` from a repository that has the ApexGraphSwarm package available at its root.

When answering a repo-structure question:

- Read the generated artifact, identify the relevant node IDs and edges, and cite exact paths and line numbers where available.
- Keep the claim proportional to its evidence. `observed` means inventory/containment; `parsed` means parser-derived; `inferred` means heuristic or lexical evidence.
- Treat unresolved references, parse warnings, truncation, language coverage, and graph limits as part of the result, not footnotes to omit.
- Do not infer runtime call behavior, semantic correctness, ownership, security authorization, or execution order from graph adjacency alone.
- Separate facts found in source from hypotheses and suggested follow-up checks.
- Avoid dumping the graph wholesale. Filter to the requested node neighborhood and summarize it.

If the artifact is stale or belongs to another repository revision, regenerate it before relying on it. Never claim that an LLM-generated summary itself is validated by the graph; only the references and reported structure can be checked deterministically.
