# ADR-020: Decision intelligence as structured tool

- Status: Accepted
- Date: 2026-09-27
- Deciders: ApexGraphSwarm maintainers

## Context

The system must support fast typed decisions (probability distributions, provider comparisons, cost estimates) using external decision providers (Laya, AnyJev). These tools must be clearly separated from the control plane and must not grant permissions or execute swarm work.

## Decision

**Decision intelligence is a structured tool, not a research engine or execution system.** Key characteristics:

- **Typed questions**: Users supply bounded context and typed choice, score, or yes/no questions.
- **Provider comparison**: Run one configured provider or compare both (Laya and AnyJev).
- **Results**: Probability distributions, user-selected review threshold, measured request latency, and operator-configured cost estimates.
- **Explicit limitations**: "Actual costs stay unknown unless independently measured; an estimate is not a provider billing cap."
- **No permissions or execution**: "Decisions do not grant permissions or execute swarm work."
- **Provider separation**: Laya uses its native HTTP decision API; AnyJev uses the optional ApexGraphSwarm bridge around its Python SDK and a separately operated vLLM server. These runtimes remain outside the Python standard-library control plane.

**Scope boundaries:**
- Structured decision tools, not unrestricted long-form research engines.
- Confidence needs validation on held-out domain data.
- Input coverage depends on the checkpoint context limit.
- No millisecond performance claim applies to your hardware until measured.
- Existing graph-cited model review remains the route for longer explanatory answers.

## Alternatives considered

1. **Unrestricted research engine**: Would be more flexible but would be slower, more expensive, and less auditable.
2. **Integrated into control plane**: Would simplify architecture but would couple decision-making to the stdlib control plane.
3. **No decision support**: Would simplify the system but would prevent fast typed decisions.

## Consequences

- **Positive**: Fast typed decisions; clear provider comparison; explicit cost estimates; no execution side effects.
- **Negative**: Limited to structured questions; confidence requires validation; provider availability depends on configuration.
- **Critical statement**: "These are structured decision tools, not unrestricted long-form research engines."

## Related

- ADR-002 (stdlib-only control plane)
- ADR-011 (integer micro-USD cost accounting)
- ADR-012 (explicit adapter pattern)
