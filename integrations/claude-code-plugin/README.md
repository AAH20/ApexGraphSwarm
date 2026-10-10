# ApexGraphSwarm repository evidence plugin for Claude Code

A small Claude Code plugin that invokes ApexGraphSwarm's deterministic repository analyzer and guides Claude through evidence-bounded architecture explanations. It does not dispatch a swarm, contact a model provider, execute repository code, or verify that a natural-language claim is semantically true.

## Requirements

- Python 3.10+
- Run the command from an ApexGraphSwarm checkout (or another environment where its `apexgraphswarm` package is importable).
- Git metadata at the target repository root; the analyzer uses tracked and non-ignored untracked files.

## Install locally for development

From the ApexGraphSwarm repository root:

```sh
claude --plugin-dir integrations/claude-code-plugin
```

Then run:

```text
/apex-repository-evidence:map .
```

The analyzer's output is saved to `/tmp/apex-repository-graph.json`. Review it before sharing because it contains file paths and source-derived summaries.

## Evidence and limits

The command reports the analyzer's counts, unresolved references, and warnings. Python relationships are parser-derived; JavaScript and TypeScript relationships are lexical hints; unsupported languages are inventory-only. See the repository's [Graph Intelligence documentation](../../README.md#graph-intelligence) for configured size limits and known gaps. Graph structure provides navigation evidence, not proof of runtime behavior or semantic entailment.

The plugin intentionally requires the host repository's analyzer rather than vendoring or duplicating it. It does not claim compatibility with arbitrary checkouts that lack ApexGraphSwarm.

## Validation

From the repository root:

```sh
python3 -m unittest discover tests
```

The plugin is instructions and metadata only. To validate Claude's runtime behavior, load it with `--plugin-dir` and run the command on a small public test repository, then compare every reported relationship against the JSON artifact and source files.
