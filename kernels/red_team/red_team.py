"""Red team orchestrator for ApexGraphSwarm.

Coordinates automated attack generation, vulnerability discovery,
exploit chaining, and responsible disclosure reporting.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from .attack_surface import AttackSurface, SurfaceType, discover_all_surfaces
from .vulnerability import Vulnerability, Severity, discover_vulnerabilities
from .exploit_chain import ExploitChain, build_exploit_chains
from .disclosure import (
    DisclosureReport,
    DisclosureStage,
    create_disclosure_report,
    generate_disclosure_summary,
    get_disclosure_recommendations,
)


@dataclass
class RedTeamConfig:
    """Configuration for red team operations."""

    target: str = "apexgraphswarm"
    max_vulnerabilities: int = 100
    min_severity: Severity = Severity.LOW
    include_info: bool = False
    generate_chains: bool = True
    generate_disclosure: bool = True
    output_dir: str = "."
    reporter: str = "red-team"


@dataclass
class RedTeamResult:
    """Result of a red team assessment."""

    config: RedTeamConfig
    surfaces: list[AttackSurface] = field(default_factory=list)
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    exploit_chains: list[ExploitChain] = field(default_factory=list)
    disclosure_report: DisclosureReport | None = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "config": {
                "target": self.config.target,
                "maxVulnerabilities": self.config.max_vulnerabilities,
                "minSeverity": self.config.min_severity.value,
                "includeInfo": self.config.include_info,
                "generateChains": self.config.generate_chains,
                "generateDisclosure": self.config.generate_disclosure,
            },
            "surfaces": [s.to_dict() for s in self.surfaces],
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "exploitChains": [c.to_dict() for c in self.exploit_chains],
            "disclosureReport": self.disclosure_report.to_dict() if self.disclosure_report else None,
            "startedAt": self.started_at.isoformat(),
            "completedAt": self.completed_at.isoformat() if self.completed_at else None,
        }

    def summary(self) -> dict[str, Any]:
        """Generate a summary of the assessment."""
        severity_counts: dict[str, int] = {}
        for vuln in self.vulnerabilities:
            key = vuln.severity.value
            severity_counts[key] = severity_counts.get(key, 0) + 1

        surface_counts: dict[str, int] = {}
        for surface in self.surfaces:
            key = surface.surface_type.value
            surface_counts[key] = surface_counts.get(key, 0) + 1

        return {
            "target": self.config.target,
            "surfacesDiscovered": len(self.surfaces),
            "vulnerabilitiesFound": len(self.vulnerabilities),
            "exploitChainsBuilt": len(self.exploit_chains),
            "severityBreakdown": severity_counts,
            "surfaceBreakdown": surface_counts,
            "disclosureStage": self.disclosure_report.stage.value if self.disclosure_report else None,
        }


class RedTeamOrchestrator:
    """Orchestrates red team assessments of ApexGraphSwarm."""

    def __init__(self, config: RedTeamConfig | None = None):
        self.config = config or RedTeamConfig()
        self._result: RedTeamResult | None = None

    def run(self) -> RedTeamResult:
        """Execute a full red team assessment."""
        self._result = RedTeamResult(config=self.config)

        # Phase 1: Attack surface discovery
        self._result.surfaces = discover_all_surfaces()

        # Phase 2: Vulnerability discovery
        all_vulns = discover_vulnerabilities(self._result.surfaces)
        self._result.vulnerabilities = self._filter_vulnerabilities(all_vulns)

        # Phase 3: Exploit chaining
        if self.config.generate_chains:
            self._result.exploit_chains = build_exploit_chains(self._result.vulnerabilities)

        # Phase 4: Responsible disclosure
        if self.config.generate_disclosure:
            self._result.disclosure_report = create_disclosure_report(
                self._result.vulnerabilities,
                self._result.exploit_chains,
                reporter=self.config.reporter,
            )

        self._result.completed_at = datetime.utcnow()
        return self._result

    def _filter_vulnerabilities(self, vulnerabilities: list[Vulnerability]) -> list[Vulnerability]:
        """Filter vulnerabilities by severity and count."""
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        min_order = severity_order.get(self.config.min_severity, 4)

        filtered = [
            v for v in vulnerabilities
            if severity_order.get(v.severity, 4) <= min_order
            or (v.severity == Severity.INFO and self.config.include_info)
        ]

        # Sort by severity (most severe first)
        filtered.sort(key=lambda v: severity_order.get(v.severity, 4))

        return filtered[: self.config.max_vulnerabilities]

    def export_json(self, path: str | Path | None = None) -> str:
        """Export results to JSON."""
        if self._result is None:
            raise RuntimeError("No assessment has been run. Call run() first.")

        if path is None:
            path = Path(self.config.output_dir) / f"red-team-{self._result.started_at.strftime('%Y%m%d-%H%M%S')}.json"
        else:
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._result.to_dict(), f, indent=2, default=str)

        return str(path)

    def export_markdown(self, path: str | Path | None = None) -> str:
        """Export results to Markdown report."""
        if self._result is None:
            raise RuntimeError("No assessment has been run. Call run() first.")

        if path is None:
            path = Path(self.config.output_dir) / f"red-team-{self._result.started_at.strftime('%Y%m%d-%H%M%S')}.md"
        else:
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)

        lines = self._generate_markdown()
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return str(path)

    def _generate_markdown(self) -> list[str]:
        """Generate Markdown report lines."""
        assert self._result is not None
        result = self._result

        lines = [
            f"# Red Team Assessment: {result.config.target}",
            "",
            f"**Date:** {result.started_at.isoformat()}",
            f"**Status:** {'Completed' if result.completed_at else 'In Progress'}",
            "",
            "## Summary",
            "",
            f"- **Attack Surfaces Discovered:** {len(result.surfaces)}",
            f"- **Vulnerabilities Found:** {len(result.vulnerabilities)}",
            f"- **Exploit Chains Built:** {len(result.exploit_chains)}",
            "",
        ]

        # Severity breakdown
        severity_counts: dict[str, int] = {}
        for vuln in result.vulnerabilities:
            key = vuln.severity.value
            severity_counts[key] = severity_counts.get(key, 0) + 1

        lines.extend([
            "### Severity Breakdown",
            "",
        ])
        for sev in ["critical", "high", "medium", "low", "info"]:
            count = severity_counts.get(sev, 0)
            if count > 0:
                lines.append(f"- **{sev.upper()}:** {count}")
        lines.append("")

        # Vulnerabilities
        if result.vulnerabilities:
            lines.extend([
                "## Vulnerabilities",
                "",
            ])
            for vuln in result.vulnerabilities:
                lines.extend([
                    f"### {vuln.id}: {vuln.title}",
                    "",
                    f"**Severity:** {vuln.severity.value.upper()}",
                    f"**Surface:** {vuln.surface_type.value}",
                    "",
                    f"**Description:** {vuln.description}",
                    "",
                    f"**Attack Vector:** {vuln.attack_vector}",
                    "",
                    f"**Impact:** {vuln.impact}",
                    "",
                    f"**Remediation:** {vuln.remediation}",
                    "",
                ])
                if vuln.cwe_id:
                    lines.append(f"**CWE:** {vuln.cwe_id}")
                if vuln.cvss_score is not None:
                    lines.append(f"**CVSS:** {vuln.cvss_score}")
                lines.append("")

        # Exploit chains
        if result.exploit_chains:
            lines.extend([
                "## Exploit Chains",
                "",
            ])
            for chain in result.exploit_chains:
                lines.extend([
                    f"### {chain.id}: {chain.name}",
                    "",
                    f"**Severity:** {chain.overall_severity.value.upper()}",
                    f"**Impact:** {chain.impact}",
                    "",
                    "**Steps:**",
                    "",
                ])
                for step in chain.steps:
                    lines.append(f"{step.order}. [{step.status.value}] {step.description}")
                lines.append("")

        # Disclosure
        if result.disclosure_report:
            lines.extend([
                "## Responsible Disclosure",
                "",
                f"**Report ID:** {result.disclosure_report.id}",
                f"**Stage:** {result.disclosure_report.stage.value}",
                "",
                generate_disclosure_summary(result.disclosure_report),
                "",
            ])

        return lines

    @property
    def result(self) -> RedTeamResult | None:
        """Get the assessment result."""
        return self._result


def run_red_team(
    *,
    target: str = "apexgraphswarm",
    max_vulnerabilities: int = 100,
    min_severity: Severity = Severity.LOW,
    include_info: bool = False,
    generate_chains: bool = True,
    generate_disclosure: bool = True,
    output_dir: str = ".",
    reporter: str = "red-team",
    export_json: bool = True,
    export_markdown: bool = True,
) -> RedTeamResult:
    """Convenience function to run a red team assessment."""
    config = RedTeamConfig(
        target=target,
        max_vulnerabilities=max_vulnerabilities,
        min_severity=min_severity,
        include_info=include_info,
        generate_chains=generate_chains,
        generate_disclosure=generate_disclosure,
        output_dir=output_dir,
        reporter=reporter,
    )
    orchestrator = RedTeamOrchestrator(config)
    result = orchestrator.run()

    if export_json:
        orchestrator.export_json()
    if export_markdown:
        orchestrator.export_markdown()

    return result
