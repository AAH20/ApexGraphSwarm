# ADR-030: Skills review as provenance check without installation

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support skill manifests for specialist team design. However, skills from external libraries (skills.sh or others) must not be automatically fetched, installed, or executed. The system must be clear about what it does and does not do.

## Decision

**Skills review accepts manifests/content for provenance and metadata checks only.** Key characteristics:

- **Provenance checks**: Skill ID, source URL, pinned revision, and SHA-256 reference are recorded.
- **No installation**: "It does not fetch, install, or execute arbitrary packages from skills.sh or another library."
- **Hash limitation**: "A recorded hash is not proof that content was fetched, verified, installed, or trusted."
- **Design-time only**: Skills are part of the specialist design, not executable components.

## Alternatives considered

1. **Automatic skill installation**: Would be convenient but would be unsafe and could execute arbitrary code.
2. **No skill support**: Would simplify the system but would prevent skill-based team design.
3. **Full skill execution environment**: Would be more powerful but would require sandboxing and safety controls that are out of scope.

## Consequences

- **Positive**: Safe provenance tracking; no arbitrary code execution; clear limitations.
- **Negative**: Skills are not executable; hashes do not prove content integrity; users must verify skills independently.
- **Critical statement**: "A recorded hash is not proof that content was fetched, verified, installed, or trusted."

## Related

- ADR-010 (specialist team design)
- ADR-012 (explicit adapter pattern)
- ADR-029 (MCP discovery bounded subset)
