# Skill manifest interoperability and trust

**Status: imported skills remain pending human review.** ApexGraphSwarm accepts exact, user-provided `SKILL.md` text and optional HTTPS provenance. It parses a deliberately small YAML frontmatter subset into a locked review manifest, computes SHA-256 over the exact UTF-8 input bytes, and preserves both the raw frontmatter fields and full text. Import does not fetch a URL, clone a repository, read local paths, install a skill, execute a script, activate a harness, or invoke an MCP/provider tool. A source reference without pasted text returns `content-required`; it does not invent a hash or silently fetch remote content.

## Format support

The manifest follows the current Agent Skills `SKILL.md` structure: YAML frontmatter followed by Markdown, with required `name` and `description`; optional `license`, `compatibility`, `metadata`, and experimental `allowed-tools`. Name and description are checked against the format’s documented limits and name syntax. Since this importer accepts pasted text rather than a skill directory, it cannot verify that a directory basename equals the declared `name`.

The parser is not a general YAML implementation. It accepts plain strings, single-quoted strings, JSON-compatible double-quoted strings, and a flat two-space `metadata` mapping with scalar values. It rejects block scalars, lists, flow collections, tags, anchors, aliases, duplicate fields, unexpected indentation, and ambiguous plain scalars with explicit errors. This avoids silently changing semantics or executing YAML constructors. `permissions`, `capabilities`, and `supported-harnesses` are optional ApexGraphSwarm scalar extensions; they are preserved as raw fields and interpreted only as user-declared values. `allowed-tools` is recorded as a declaration, not enforced as a sandbox policy.

The resulting manifest includes a content hash and ID, optional source URL and asserted revision, parsed declarations, compatibility/license values, raw fields, original text, `locked: true`, and `trustReviewStatus: "pending-review"`. Locking makes the reviewed content a stable snapshot. An edit creates a different content hash and requires a fresh review. A matching hash proves only that two byte strings match: it does not establish who published the skill, whether the source repository is trustworthy, whether its license is accurate, or whether the instructions are safe.

## Registry and harness mapping

[skills.sh](https://skills.sh/) is a discovery directory for the open skills ecosystem. Its companion [`vercel-labs/skills` tool](https://github.com/vercel-labs/skills) resolves sources across several repository formats and can install, link, update, remove, or run selected skills for supported agents. ApexGraphSwarm treats a skills.sh entry or repository URL only as provenance input. It does not invoke the CLI or reproduce its remote source resolution in the import path; users paste the version they intend to review and provide an immutable commit/tag when available.

The [Agent Skills standard](https://agentskills.io/specification) is designed for progressive instruction loading and permits a skill directory to contain executable `scripts/` and additional references/assets. This importer receives only one text file. Its hash does not cover linked files, scripts, or any remote resources named in the body. Review the full source bundle separately before enabling it anywhere.

`compatibility` is free-form metadata, and `allowed-tools` support is explicitly experimental in the standard. A declared harness list is an assertion for review, not a compatibility guarantee: harnesses differ in paths, activation rules, tool names, permission boundaries, and how they interpret SKILL.md. The import tool keeps exact known harness IDs (`codex`, `claude-code`, `cursor`, `antigravity`, `opencode`, `hermes`) and allows syntactically valid custom IDs with an “unknown/custom” warning. It does not infer harness support from product names, `compatibility` prose, or filesystem layout.

## Reviews, licensing, and execution cost

Before a separate, explicitly authorized install or activation, a reviewer should:

1. Verify the exact source URL and revision against the publisher; confirm the pasted content hash matches the reviewed text.
2. Read the full instructions for prompt injection, secret access, filesystem/network scope, shell commands, destructive actions, unbounded loops, and assumptions that bypass policy.
3. Inspect every referenced asset, script, and remote dependency independently. SKILL.md instructions can request actions even though this importer never performs them.
4. Check the stated license and source repository terms. A manifest preserves the skill’s `license` field but does not validate ownership, grant rights, or infer a license when missing.
5. Map declarations to a specific harness version and enforced tool/permission policy. Remove unsupported tools and keep untrusted content isolated.
6. Estimate costs for the intended run: model selection and reasoning tokens, API/gateway or subscription allowances, MCP/service request charges, search and other tool fees, local CPU/GPU time, and retries. A skill itself does not carry a universal price, and a “free” directory entry does not make the services it invokes free.

Execution plans should export a locked manifest reference (ID, hash, source and revision), reviewer decision, selected harness/version, approved capabilities, and separately recorded budget/rate provenance. They must not mark the skill trusted based on import, claim that a model/tool entitlement exists, or include provider secrets. Any actual execution path must independently enforce auth, permissions, budgets, and cancellation.

## Sources

- Agent Skills format and validation constraints: [Specification](https://agentskills.io/specification).
- `skills.sh` discovery directory: [skills.sh](https://skills.sh/).
- Source formats, supported agents, and install/use behaviors: [`vercel-labs/skills` README](https://github.com/vercel-labs/skills).
- Reference validator named by the standard: [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref).

Sources checked 2026-09-27. The imported file’s `exactRevision` is supplied by the user and not remotely verified by this implementation; only `contentSha256` is computed locally.
