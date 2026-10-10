"""Adversary emulation engine for the threat matrix.

Simulates attack techniques against ApexGraphSwarm control-plane primitives
and produces structured emulation results for purple-team exercises.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from .matrix import Severity, TacticDomain, Technique, ThreatMatrix, build_default_matrix


class EmulationStatus(str, Enum):
    """Outcome status for an emulated technique."""
    SUCCESS = "success"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    DETECTED = "detected"


@dataclass
class EmulationResult:
    """Result of emulating a single technique."""
    technique_id: str
    domain: TacticDomain
    status: EmulationStatus
    severity: Severity
    description: str
    simulated_action: str
    expected_detection: str
    expected_mitigation: str
    prerequisites_met: bool = False
    indicators_observed: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "techniqueId": self.technique_id,
            "domain": self.domain.value,
            "status": self.status.value,
            "severity": self.severity.value,
            "description": self.description,
            "simulatedAction": self.simulated_action,
            "expectedDetection": self.expected_detection,
            "expectedMitigation": self.expected_mitigation,
            "prerequisitesMet": self.prerequisites_met,
            "indicatorsObserved": self.indicators_observed,
            "metadata": self.metadata,
        }


@dataclass
class EmulationReport:
    """Aggregate report from a full emulation run."""
    results: list[EmulationResult] = field(default_factory=list)
    matrix_version: str = "1.0.0"

    @property
    def total_techniques(self) -> int:
        return len(self.results)

    @property
    def successful(self) -> int:
        return sum(1 for r in self.results if r.status == EmulationStatus.SUCCESS)

    @property
    def blocked(self) -> int:
        return sum(1 for r in self.results if r.status == EmulationStatus.BLOCKED)

    @property
    def detected(self) -> int:
        return sum(1 for r in self.results if r.status == EmulationStatus.DETECTED)

    @property
    def critical_gaps(self) -> list[EmulationResult]:
        return [r for r in self.results
                if r.severity == Severity.CRITICAL and r.status == EmulationStatus.SUCCESS]

    def by_domain(self, domain: TacticDomain) -> list[EmulationResult]:
        return [r for r in self.results if r.domain == domain]

    def to_dict(self) -> dict[str, Any]:
        return {
            "matrixVersion": self.matrix_version,
            "summary": {
                "totalTechniques": self.total_techniques,
                "successful": self.successful,
                "blocked": self.blocked,
                "detected": self.detected,
                "criticalGaps": len(self.critical_gaps),
            },
            "results": [r.to_dict() for r in self.results],
        }


class AdversaryEmulator:
    """Emulates adversary techniques against ApexGraphSwarm primitives.

    This emulator models attack techniques against the control plane's
    documented security properties. It does not execute real attacks;
    it simulates the decision logic that would apply when an adversary
    attempts each technique.
    """

    def __init__(self, matrix: ThreatMatrix | None = None):
        self.matrix = matrix or build_default_matrix()
        self._technique_handlers: dict[str, Callable[[Technique], EmulationResult]] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register simulation handlers for each technique."""
        for technique in self.matrix.all_techniques():
            self._technique_handlers[technique.id] = self._default_handler

    def register_handler(self, technique_id: str,
                         handler: Callable[[Technique], EmulationResult]) -> None:
        """Register a custom handler for a specific technique."""
        self._technique_handlers[technique_id] = handler

    def emulate_technique(self, technique: Technique) -> EmulationResult:
        """Emulate a single technique and return the result."""
        handler = self._technique_handlers.get(technique.id, self._default_handler)
        return handler(technique)

    def emulate_domain(self, domain: TacticDomain) -> list[EmulationResult]:
        """Emulate all techniques in a tactic domain."""
        return [self.emulate_technique(t) for t in self.matrix.techniques_for(domain)]

    def emulate_all(self) -> EmulationReport:
        """Run full emulation across all 11 domains."""
        results: list[EmulationResult] = []
        for domain in TacticDomain:
            results.extend(self.emulate_domain(domain))
        return EmulationReport(results=results, matrix_version=self.matrix.version)

    def _default_handler(self, technique: Technique) -> EmulationResult:
        """Default simulation logic for any technique.

        Models the control plane's security controls and determines
        whether the technique would succeed, be blocked, or be detected
        based on the technique's properties and the system's defenses.
        """
        # Critical techniques with no prerequisites are more likely to succeed
        # if the system lacks specific controls
        if technique.severity == Severity.CRITICAL and not technique.prerequisites:
            status = EmulationStatus.SUCCESS
        elif technique.severity == Severity.CRITICAL:
            status = EmulationStatus.PARTIAL
        elif technique.severity == Severity.HIGH:
            status = EmulationStatus.DETECTED
        else:
            status = EmulationStatus.BLOCKED

        # Techniques with detection refs are more likely to be caught
        if technique.detection_refs and status == EmulationStatus.SUCCESS:
            status = EmulationStatus.DETECTED

        return EmulationResult(
            technique_id=technique.id,
            domain=_domain_for_technique(technique),
            status=status,
            severity=technique.severity,
            description=technique.description,
            simulated_action=f"Simulated {technique.name}",
            expected_detection=technique.detection_refs[0] if technique.detection_refs else "none",
            expected_mitigation=technique.mitigation_refs[0] if technique.mitigation_refs else "none",
            prerequisites_met=bool(technique.prerequisites),
            indicators_observed=list(technique.indicators[:2]),
        )


def _domain_for_technique(technique: Technique) -> TacticDomain:
    """Determine which domain a technique belongs to based on its ID prefix."""
    prefix_map = {
        "RECON": TacticDomain.RECONNAISSANCE,
        "SEMI": TacticDomain.SEMANTIC_INGRESS,
        "CTXC": TacticDomain.CONTEXT_CONTAMINATION,
        "TOOL": TacticDomain.TOOL_DISCIPLINE,
        "SBEX": TacticDomain.SANDBOX_ESCAPE,
        "PRIV": TacticDomain.PRIVILEGE_ESCALATION,
        "SWAR": TacticDomain.SWARM_CONTAGION,
        "TELX": TacticDomain.TELEMETRY_SUPPRESSION,
        "FINR": TacticDomain.FINANCIAL_RAIL,
        "EXFX": TacticDomain.STATE_EXFILTRATION,
        "RSRX": TacticDomain.RESOURCE_EXHAUSTION,
    }
    prefix = technique.id.split("-")[0]
    return prefix_map.get(prefix, TacticDomain.RECONNAISSANCE)
