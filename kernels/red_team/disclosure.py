"""Responsible disclosure reporting for ApexGraphSwarm red team.

Generates structured disclosure reports following responsible disclosure
best practices: private notification, coordinated disclosure timeline,
and public disclosure after remediation.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from .vulnerability import Vulnerability, Severity
from .exploit_chain import ExploitChain


class DisclosureStage(enum.Enum):
    """Stages of responsible disclosure."""
    DISCOVERED = "discovered"
    REPORTED = "reported"
    ACKNOWLEDGED = "acknowledged"
    REMEDIATION_PLANNED = "remediation_planned"
    REMEDIATION_IN_PROGRESS = "remediation_in_progress"
    FIX_DEPLOYED = "fix_deployed"
    VERIFICATION_PENDING = "verification_pending"
    DISCLOSED = "disclosed"
    WITHDRAWN = "withdrawn"


@dataclass
class DisclosureReport:
    """A responsible disclosure report."""

    id: str
    title: str
    reporter: str
    discovered_at: datetime
    stage: DisclosureStage
    vulnerabilities: list[Vulnerability] = field(default_factory=list)
    exploit_chains: list[ExploitChain] = field(default_factory=list)
    description: str = ""
    impact_summary: str = ""
    remediation_timeline: list[dict[str, Any]] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    cve_ids: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "reporter": self.reporter,
            "discoveredAt": self.discovered_at.isoformat(),
            "stage": self.stage.value,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "exploitChains": [c.to_dict() for c in self.exploit_chains],
            "description": self.description,
            "impactSummary": self.impact_summary,
            "remediationTimeline": list(self.remediation_timeline),
            "references": list(self.references),
            "cveIds": list(self.cve_ids),
            "notes": self.notes,
        }

    def advance_stage(self) -> DisclosureStage:
        """Advance to the next disclosure stage."""
        stages = list(DisclosureStage)
        current_idx = stages.index(self.stage)
        if current_idx < len(stages) - 1:
            self.stage = stages[current_idx + 1]
        return self.stage

    def add_timeline_entry(self, event: str, details: str = "") -> None:
        """Add an entry to the remediation timeline."""
        self.remediation_timeline.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": event,
            "details": details,
        })


def create_disclosure_report(
    vulnerabilities: list[Vulnerability],
    exploit_chains: list[ExploitChain],
    *,
    reporter: str = "red-team",
    title: str = "ApexGraphSwarm Red Team Findings",
) -> DisclosureReport:
    """Create a responsible disclosure report from findings."""
    critical_count = sum(1 for v in vulnerabilities if v.severity == Severity.CRITICAL)
    high_count = sum(1 for v in vulnerabilities if v.severity == Severity.HIGH)
    medium_count = sum(1 for v in vulnerabilities if v.severity == Severity.MEDIUM)
    low_count = sum(1 for v in vulnerabilities if v.severity == Severity.LOW)

    impact_parts = []
    if critical_count:
        impact_parts.append(f"{critical_count} critical")
    if high_count:
        impact_parts.append(f"{high_count} high")
    if medium_count:
        impact_parts.append(f"{medium_count} medium")
    if low_count:
        impact_parts.append(f"{low_count} low")

    impact_summary = (
        f"Red team assessment identified {len(vulnerabilities)} vulnerabilities "
        f"({', '.join(impact_parts)}) and {len(exploit_chains)} exploit chains."
    )

    report = DisclosureReport(
        id=f"RD-{datetime.utcnow().strftime('%Y%m%d')}-001",
        title=title,
        reporter=reporter,
        discovered_at=datetime.utcnow(),
        stage=DisclosureStage.DISCOVERED,
        vulnerabilities=vulnerabilities,
        exploit_chains=exploit_chains,
        description="Automated red team assessment of ApexGraphSwarm control plane.",
        impact_summary=impact_summary,
    )

    report.add_timeline_entry("Assessment completed", "Automated red team scan finished")
    return report


def generate_disclosure_summary(report: DisclosureReport) -> str:
    """Generate a human-readable disclosure summary."""
    lines = [
        f"Disclosure Report: {report.id}",
        f"Title: {report.title}",
        f"Stage: {report.stage.value}",
        f"Discovered: {report.discovered_at.isoformat()}",
        "",
        "Impact Summary:",
        f"  {report.impact_summary}",
        "",
        "Vulnerabilities:",
    ]

    for vuln in report.vulnerabilities:
        lines.append(f"  [{vuln.severity.value.upper()}] {vuln.id}: {vuln.title}")

    if report.exploit_chains:
        lines.extend(["", "Exploit Chains:"])
        for chain in report.exploit_chains:
            lines.append(f"  [{chain.overall_severity.value.upper()}] {chain.id}: {chain.name}")

    if report.remediation_timeline:
        lines.extend(["", "Timeline:"])
        for entry in report.remediation_timeline:
            lines.append(f"  {entry['timestamp']}: {entry['event']}")

    return "\n".join(lines)


def get_disclosure_recommendations(report: DisclosureReport) -> list[str]:
    """Get recommendations for next disclosure steps."""
    recommendations: list[str] = []

    if report.stage == DisclosureStage.DISCOVERED:
        recommendations.append("Notify security team privately")
        recommendations.append("Request acknowledgment within 7 days")
    elif report.stage == DisclosureStage.REPORTED:
        recommendations.append("Follow up if no acknowledgment within 7 days")
        recommendations.append("Prepare detailed reproduction steps")
    elif report.stage == DisclosureStage.ACKNOWLEDGED:
        recommendations.append("Coordinate remediation timeline")
        recommendations.append("Request CVE assignment for critical findings")
    elif report.stage == DisclosureStage.REMEDIATION_PLANNED:
        recommendations.append("Monitor remediation progress")
        recommendations.append("Prepare verification tests")
    elif report.stage == DisclosureStage.REMEDIATION_IN_PROGRESS:
        recommendations.append("Verify fixes as they are deployed")
        recommendations.append("Update disclosure timeline")
    elif report.stage == DisclosureStage.FIX_DEPLOYED:
        recommendations.append("Conduct verification testing")
        recommendations.append("Prepare public disclosure draft")
    elif report.stage == DisclosureStage.VERIFICATION_PENDING:
        recommendations.append("Complete verification testing")
        recommendations.append("Schedule public disclosure")
    elif report.stage == DisclosureStage.DISCLOSED:
        recommendations.append("Monitor for public response")
        recommendations.append("Update documentation")

    return recommendations
