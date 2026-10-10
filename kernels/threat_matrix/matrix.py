"""Core threat matrix data structures for adversary emulation.

Defines the 11 tactic domains, techniques, severity levels, and the
ThreatMatrix container that organizes the full kill-chain model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Severity(str, Enum):
    """Impact severity for a technique."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class TacticDomain(str, Enum):
    """The 11 adversary emulation tactic domains."""
    RECONNAISSANCE = "reconnaissance"
    SEMANTIC_INGRESS = "semantic_ingress"
    CONTEXT_CONTAMINATION = "context_contamination"
    TOOL_DISCIPLINE = "tool_discipline"
    SANDBOX_ESCAPE = "sandbox_escape"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SWARM_CONTAGION = "swarm_contagion"
    TELEMETRY_SUPPRESSION = "telemetry_suppression"
    FINANCIAL_RAIL = "financial_rail"
    STATE_EXFILTRATION = "state_exfiltration"
    RESOURCE_EXHAUSTION = "resource_exhaustion"


@dataclass(frozen=True)
class Technique:
    """A single adversary technique within a tactic domain."""
    id: str
    name: str
    description: str
    severity: Severity
    kill_chain_phase: str
    prerequisites: tuple[str, ...] = ()
    indicators: tuple[str, ...] = ()
    detection_refs: tuple[str, ...] = ()
    mitigation_refs: tuple[str, ...] = ()


@dataclass
class ThreatMatrix:
    """Container for the full 11-domain threat matrix."""
    domains: dict[TacticDomain, list[Technique]] = field(default_factory=dict)
    version: str = "1.0.0"

    def add_technique(self, domain: TacticDomain, technique: Technique) -> None:
        """Add a technique to a tactic domain."""
        if domain not in self.domains:
            self.domains[domain] = []
        self.domains[domain].append(technique)

    def techniques_for(self, domain: TacticDomain) -> list[Technique]:
        """Get all techniques for a given domain."""
        return list(self.domains.get(domain, []))

    def all_techniques(self) -> list[Technique]:
        """Get all techniques across all domains."""
        return [t for techniques in self.domains.values() for t in techniques]

    def critical_count(self) -> int:
        """Count of critical-severity techniques."""
        return sum(1 for t in self.all_techniques() if t.severity == Severity.CRITICAL)

    def by_severity(self, severity: Severity) -> list[Technique]:
        """Filter techniques by severity level."""
        return [t for t in self.all_techniques() if t.severity == severity]

    def to_dict(self) -> dict[str, Any]:
        """Serialize the matrix to a plain dictionary."""
        return {
            "version": self.version,
            "domains": {
                domain.value: [
                    {
                        "id": t.id,
                        "name": t.name,
                        "description": t.description,
                        "severity": t.severity.value,
                        "kill_chain_phase": t.kill_chain_phase,
                        "prerequisites": list(t.prerequisites),
                        "indicators": list(t.indicators),
                        "detectionRefs": list(t.detection_refs),
                        "mitigationRefs": list(t.mitigation_refs),
                    }
                    for t in techniques
                ]
                for domain, techniques in self.domains.items()
            },
            "summary": {
                "totalTechniques": len(self.all_techniques()),
                "criticalCount": self.critical_count(),
                "domains": len(self.domains),
            },
        }


def build_default_matrix() -> ThreatMatrix:
    """Construct the full 11-domain threat matrix with all techniques."""
    matrix = ThreatMatrix()

    # ── 1. Reconnaissance ─────────────────────────────────────────────────
    matrix.add_technique(TacticDomain.RECONNAISSANCE, Technique(
        id="RECON-001",
        name="Control Plane Endpoint Discovery",
        description="Probe for exposed scheduler endpoints, SQLite databases, and API surfaces.",
        severity=Severity.HIGH,
        kill_chain_phase="reconnaissance",
        prerequisites=(),
        indicators=("unusual port scanning", "repeated 404/401 patterns", "timing anomalies"),
        detection_refs=("DETECT-001",),
        mitigation_refs=("MITIG-001",),
    ))
    matrix.add_technique(TacticDomain.RECONNAISSANCE, Technique(
        id="RECON-002",
        name="Worker Credential Enumeration",
        description="Enumerate valid worker IDs through error-message differentials or timing side-channels.",
        severity=Severity.HIGH,
        kill_chain_phase="reconnaissance",
        prerequisites=("RECON-001",),
        indicators=("systematic worker_id probing", "authentication timing variance"),
        detection_refs=("DETECT-002",),
        mitigation_refs=("MITIG-002",),
    ))
    matrix.add_technique(TacticDomain.RECONNAISSANCE, Technique(
        id="RECON-003",
        name="Plan Schema Inference",
        description="Infer internal plan/task schema by submitting malformed plans and analyzing validation errors.",
        severity=Severity.MEDIUM,
        kill_chain_phase="reconnaissance",
        prerequisites=("RECON-001",),
        indicators=("high volume of malformed plan submissions", "error message diversity"),
        detection_refs=("DETECT-003",),
        mitigation_refs=("MITIG-003",),
    ))
    matrix.add_technique(TacticDomain.RECONNAISSANCE, Technique(
        id="RECON-004",
        name="Telemetry Endpoint Mapping",
        description="Identify Prometheus metrics endpoints and telemetry data flows for later suppression.",
        severity=Severity.MEDIUM,
        kill_chain_phase="reconnaissance",
        prerequisites=("RECON-001",),
        indicators=("metrics endpoint access", "unusual scrape patterns"),
        detection_refs=("DETECT-004",),
        mitigation_refs=("MITIG-004",),
    ))

    # ── 2. Semantic Ingress ───────────────────────────────────────────────
    matrix.add_technique(TacticDomain.SEMANTIC_INGRESS, Technique(
        id="SEMI-001",
        name="Prompt Injection via Task Payload",
        description="Embed instructions in task payloads to override system prompts or redirect agent behavior.",
        severity=Severity.CRITICAL,
        kill_chain_phase="delivery",
        prerequisites=("RECON-003",),
        indicators=("instruction-like strings in payloads", "role-confusion patterns", "override attempts"),
        detection_refs=("DETECT-005",),
        mitigation_refs=("MITIG-005",),
    ))
    matrix.add_technique(TacticDomain.SEMANTIC_INGRESS, Technique(
        id="SEMI-002",
        name="Tool Argument Smuggling",
        description="Pass malicious arguments through tool parameters that bypass validation or trigger unintended actions.",
        severity=Severity.CRITICAL,
        kill_chain_phase="delivery",
        prerequisites=("RECON-003",),
        indicators=("unexpected tool argument patterns", "boundary violations in parameters"),
        detection_refs=("DETECT-006",),
        mitigation_refs=("MITIG-006",),
    ))
    matrix.add_technique(TacticDomain.SEMANTIC_INGRESS, Technique(
        id="SEMI-003",
        name="Context Window Overflow",
        description="Flood the context window to push out safety instructions or inject at the boundary.",
        severity=Severity.HIGH,
        kill_chain_phase="delivery",
        prerequisites=("SEMI-001",),
        indicators=("abnormally large inputs", "context boundary artifacts", "truncation patterns"),
        detection_refs=("DETECT-007",),
        mitigation_refs=("MITIG-007",),
    ))
    matrix.add_technique(TacticDomain.SEMANTIC_INGRESS, Technique(
        id="SEMI-004",
        name="Multi-Turn Instruction Accumulation",
        description="Gradually build up instructions across multiple turns that individually appear benign.",
        severity=Severity.HIGH,
        kill_chain_phase="delivery",
        prerequisites=("SEMI-001",),
        indicators=("progressive instruction building", "benign-to-malicious drift"),
        detection_refs=("DETECT-008",),
        mitigation_refs=("MITIG-008",),
    ))

    # ── 3. Context Contamination ──────────────────────────────────────────
    matrix.add_technique(TacticDomain.CONTEXT_CONTAMINATION, Technique(
        id="CTXC-001",
        name="Knowledge Base Poisoning",
        description="Inject false or misleading data into the repository graph or knowledge base to corrupt downstream decisions.",
        severity=Severity.CRITICAL,
        kill_chain_phase="persistence",
        prerequisites=("SEMI-001",),
        indicators=("unauthorized graph modifications", "source integrity violations", "confidence score anomalies"),
        detection_refs=("DETECT-009",),
        mitigation_refs=("MITIG-009",),
    ))
    matrix.add_technique(TacticDomain.CONTEXT_CONTAMINATION, Technique(
        id="CTXC-002",
        name="Checkpoint Data Manipulation",
        description="Alter execution checkpoints to inject false progress or redirect task outcomes.",
        severity=Severity.HIGH,
        kill_chain_phase="persistence",
        prerequisites=("SEMI-002",),
        indicators=("checkpoint content anomalies", "hash mismatches", "unexpected checkpoint fields"),
        detection_refs=("DETECT-010",),
        mitigation_refs=("MITIG-010",),
    ))
    matrix.add_technique(TacticDomain.CONTEXT_CONTAMINATION, Technique(
        id="CTXC-003",
        name="Specialist Contract Tampering",
        description="Modify specialist contracts to expand scope or bypass approval requirements.",
        severity=Severity.CRITICAL,
        kill_chain_phase="persistence",
        prerequisites=("SEMI-001", "RECON-003"),
        indicators=("contract scope drift", "approval bypass attempts", "quorum manipulation"),
        detection_refs=("DETECT-011",),
        mitigation_refs=("MITIG-011",),
    ))
    matrix.add_technique(TacticDomain.CONTEXT_CONTAMINATION, Technique(
        id="CTXC-004",
        name="Execution Graph Projection Poisoning",
        description="Corrupt the read-only execution graph projection to hide or misrepresent execution history.",
        severity=Severity.MEDIUM,
        kill_chain_phase="defense_evasion",
        prerequisites=("CTXC-001",),
        indicators=("projection inconsistencies", "missing nodes/edges", "status mismatches"),
        detection_refs=("DETECT-012",),
        mitigation_refs=("MITIG-012",),
    ))

    # ── 4. Tool Discipline ────────────────────────────────────────────────
    matrix.add_technique(TacticDomain.TOOL_DISCIPLINE, Technique(
        id="TOOL-001",
        name="Unauthorized Tool Invocation",
        description="Call tools outside the granted capability scope or without valid access grants.",
        severity=Severity.CRITICAL,
        kill_chain_phase="execution",
        prerequisites=("SEMI-002",),
        indicators=("capability violations", "unauthorized tool_id usage", "resource access outside grant"),
        detection_refs=("DETECT-013",),
        mitigation_refs=("MITIG-013",),
    ))
    matrix.add_technique(TacticDomain.TOOL_DISCIPLINE, Technique(
        id="TOOL-002",
        name="Grant Budget Exhaustion Attack",
        description="Rapidly consume grant budgets to trigger denial of service for legitimate operations.",
        severity=Severity.HIGH,
        kill_chain_phase="impact",
        prerequisites=("TOOL-001",),
        indicators=("budget exhaustion patterns", "high-frequency dispatch", "spend rate anomalies"),
        detection_refs=("DETECT-014",),
        mitigation_refs=("MITIG-014",),
    ))
    matrix.add_technique(TacticDomain.TOOL_DISCIPLINE, Technique(
        id="TOOL-003",
        name="Tool Output Forgery",
        description="Submit fabricated tool results or receipts to the control plane.",
        severity=Severity.CRITICAL,
        kill_chain_phase="execution",
        prerequisites=("SEMI-002",),
        indicators=("receipt validation failures", "output hash mismatches", "impossible tool responses"),
        detection_refs=("DETECT-015",),
        mitigation_refs=("MITIG-015",),
    ))
    matrix.add_technique(TacticDomain.TOOL_DISCIPLINE, Technique(
        id="TOOL-004",
        name="Lease Token Theft",
        description="Steal or forge lease tokens to hijack running tasks.",
        severity=Severity.CRITICAL,
        kill_chain_phase="credential_access",
        prerequisites=("SEMI-001",),
        indicators=("lease token reuse from different workers", "token timing anomalies", "concurrent lease usage"),
        detection_refs=("DETECT-016",),
        mitigation_refs=("MITIG-016",),
    ))

    # ── 5. Sandbox Escape ─────────────────────────────────────────────────
    matrix.add_technique(TacticDomain.SANDBOX_ESCAPE, Technique(
        id="SBEX-001",
        name="Subprocess Boundary Violation",
        description="Execute commands that escape the intended subprocess isolation via shell injection or unsafe deserialization.",
        severity=Severity.CRITICAL,
        kill_chain_phase="privilege_escalation",
        prerequisites=("SEMI-002",),
        indicators=("shell metacharacters in arguments", "unexpected process spawning", "file system boundary crossings"),
        detection_refs=("DETECT-017",),
        mitigation_refs=("MITIG-017",),
    ))
    matrix.add_technique(TacticDomain.SANDBOX_ESCAPE, Technique(
        id="SBEX-002",
        name="File System Namespace Escape",
        description="Break out of VFS namespacing to access host files or other tenant data.",
        severity=Severity.CRITICAL,
        kill_chain_phase="privilege_escalation",
        prerequisites=("SBEX-001",),
        indicators=("path traversal patterns", "access to host-level paths", "namespace boundary violations"),
        detection_refs=("DETECT-018",),
        mitigation_refs=("MITIG-018",),
    ))
    matrix.add_technique(TacticDomain.SANDBOX_ESCAPE, Technique(
        id="SBEX-003",
        name="Network Namespace Escape",
        description="Access network resources outside the sandbox's allowed egress policy.",
        severity=Severity.HIGH,
        kill_chain_phase="command_and_control",
        prerequisites=("SBEX-001",),
        indicators=("unexpected outbound connections", "DNS queries to unknown hosts", "egress policy violations"),
        detection_refs=("DETECT-019",),
        mitigation_refs=("MITIG-019",),
    ))
    matrix.add_technique(TacticDomain.SANDBOX_ESCAPE, Technique(
        id="SBEX-004",
        name="Ring Transition Exploit",
        description="Exploit ring transition policies to escalate from untrusted to trusted execution context.",
        severity=Severity.CRITICAL,
        kill_chain_phase="privilege_escalation",
        prerequisites=("SBEX-001",),
        indicators=("unauthorized ring transitions", "policy bypass attempts", "execution context anomalies"),
        detection_refs=("DETECT-020",),
        mitigation_refs=("MITIG-020",),
    ))

    # ── 6. Privilege Escalation ───────────────────────────────────────────
    matrix.add_technique(TacticDomain.PRIVILEGE_ESCALATION, Technique(
        id="PRIV-001",
        name="Worker Identity Spoofing",
        description="Forge or steal worker credentials to impersonate legitimate workers.",
        severity=Severity.CRITICAL,
        kill_chain_phase="credential_access",
        prerequisites=("RECON-002",),
        indicators=("credential reuse across workers", "identity mismatch patterns", "token hash collisions"),
        detection_refs=("DETECT-021",),
        mitigation_refs=("MITIG-021",),
    ))
    matrix.add_technique(TacticDomain.PRIVILEGE_ESCALATION, Technique(
        id="PRIV-002",
        name="Principal Impersonation",
        description="Act as a different principal by manipulating authentication context or grant associations.",
        severity=Severity.CRITICAL,
        kill_chain_phase="credential_access",
        prerequisites=("PRIV-001",),
        indicators=("principal ID mismatches", "grant scope expansion", "cross-principal activity"),
        detection_refs=("DETECT-022",),
        mitigation_refs=("MITIG-022",),
    ))
    matrix.add_technique(TacticDomain.PRIVILEGE_ESCALATION, Technique(
        id="PRIV-003",
        name="Approval Quorum Bypass",
        description="Manipulate specialist contract approval quorum by enrolling shadow workers for the same principal.",
        severity=Severity.HIGH,
        kill_chain_phase="privilege_escalation",
        prerequisites=("PRIV-001", "CTXC-003"),
        indicators=("duplicate principal enrollments", "quorum satisfaction anomalies", "shadow worker patterns"),
        detection_refs=("DETECT-023",),
        mitigation_refs=("MITIG-023",),
    ))
    matrix.add_technique(TacticDomain.PRIVILEGE_ESCALATION, Technique(
        id="PRIV-004",
        name="Revocation Timing Attack",
        description="Exploit the window between revocation decision and enforcement to perform unauthorized actions.",
        severity=Severity.MEDIUM,
        kill_chain_phase="privilege_escalation",
        prerequisites=("PRIV-001",),
        indicators=("actions after revocation timestamp", "lease renewal after revocation", "heartbeat after revoke"),
        detection_refs=("DETECT-024",),
        mitigation_refs=("MITIG-024",),
    ))

    # ── 7. Swarm Contagion ────────────────────────────────────────────────
    matrix.add_technique(TacticDomain.SWARM_CONTAGION, Technique(
        id="SWAR-001",
        name="Cross-Worker State Poisoning",
        description="Propagate malicious state through shared checkpoints or execution graphs to compromise other workers.",
        severity=Severity.CRITICAL,
        kill_chain_phase="lateral_movement",
        prerequisites=("CTXC-001", "CTXC-002"),
        indicators=("shared state corruption", "cross-task contamination", "propagated false checkpoints"),
        detection_refs=("DETECT-025",),
        mitigation_refs=("MITIG-025",),
    ))
    matrix.add_technique(TacticDomain.SWARM_CONTAGION, Technique(
        id="SWAR-002",
        name="Delegation Chain Hijack",
        description="Intercept or manipulate delegation plans to redirect tasks to compromised workers.",
        severity=Severity.HIGH,
        kill_chain_phase="lateral_movement",
        prerequisites=("PRIV-001",),
        indicators=("delegation target anomalies", "unexpected task routing", "plan dependency manipulation"),
        detection_refs=("DETECT-026",),
        mitigation_refs=("MITIG-026",),
    ))
    matrix.add_technique(TacticDomain.SWARM_CONTAGION, Technique(
        id="SWAR-003",
        name="Consensus Protocol Disruption",
        description="Disrupt Paxos/Raft consensus to split-brain the swarm or prevent task commitment.",
        severity=Severity.CRITICAL,
        kill_chain_phase="impact",
        prerequisites=("SBEX-003",),
        indicators=("ballot conflicts", "leader election instability", "log divergence"),
        detection_refs=("DETECT-027",),
        mitigation_refs=("MITIG-027",),
    ))
    matrix.add_technique(TacticDomain.SWARM_CONTAGION, Technique(
        id="SWAR-004",
        name="Contract Scope Propagation",
        description="Use a single compromised specialist contract to affect multiple workers and tasks.",
        severity=Severity.HIGH,
        kill_chain_phase="lateral_movement",
        prerequisites=("CTXC-003",),
        indicators=("contract scope expansion", "multi-worker contract binding", "approval chain anomalies"),
        detection_refs=("DETECT-028",),
        mitigation_refs=("MITIG-028",),
    ))

    # ── 8. Telemetry Suppression ──────────────────────────────────────────
    matrix.add_technique(TacticDomain.TELEMETRY_SUPPRESSION, Technique(
        id="TELX-001",
        name="Metrics Endpoint Flooding",
        description="Flood the telemetry endpoint to mask malicious activity in noise or cause monitoring blind spots.",
        severity=Severity.HIGH,
        kill_chain_phase="defense_evasion",
        prerequisites=("RECON-004",),
        indicators=("metrics scrape flooding", "monitoring saturation", "alert fatigue patterns"),
        detection_refs=("DETECT-029",),
        mitigation_refs=("MITIG-029",),
    ))
    matrix.add_technique(TacticDomain.TELEMETRY_SUPPRESSION, Technique(
        id="TELX-002",
        name="Ledger Entry Suppression",
        description="Prevent or delay ledger entries from being written to hide execution history.",
        severity=Severity.CRITICAL,
        kill_chain_phase="defense_evasion",
        prerequisites=("SBEX-001",),
        indicators=("missing ledger entries", "settlement gaps", "attempt count mismatches"),
        detection_refs=("DETECT-030",),
        mitigation_refs=("MITIG-030",),
    ))
    matrix.add_technique(TacticDomain.TELEMETRY_SUPPRESSION, Technique(
        id="TELX-003",
        name="Log Injection for Alert Evasion",
        description="Inject misleading log entries to trigger false alerts or suppress real ones.",
        severity=Severity.MEDIUM,
        kill_chain_phase="defense_evasion",
        prerequisites=("SEMI-001",),
        indicators=("log format anomalies", "alert threshold manipulation", "false positive flooding"),
        detection_refs=("DETECT-031",),
        mitigation_refs=("MITIG-031",),
    ))
    matrix.add_technique(TacticDomain.TELEMETRY_SUPPRESSION, Technique(
        id="TELX-004",
        name="Analytics Data Poisoning",
        description="Corrupt analytics data to produce misleading reports that hide attack progress.",
        severity=Severity.MEDIUM,
        kill_chain_phase="defense_evasion",
        prerequisites=("CTXC-001",),
        indicators=("analytics anomalies", "forecast manipulation", "KPI inconsistencies"),
        detection_refs=("DETECT-032",),
        mitigation_refs=("MITIG-032",),
    ))

    # ── 9. Financial Rail ─────────────────────────────────────────────────
    matrix.add_technique(TacticDomain.FINANCIAL_RAIL, Technique(
        id="FINR-001",
        name="Budget Reservation Manipulation",
        description="Manipulate cost reservations to bypass budget controls or accumulate unauthorized spend.",
        severity=Severity.CRITICAL,
        kill_chain_phase="impact",
        prerequisites=("TOOL-002",),
        indicators=("reservation anomalies", "budget bypass patterns", "cost accounting mismatches"),
        detection_refs=("DETECT-033",),
        mitigation_refs=("MITIG-033",),
    ))
    matrix.add_technique(TacticDomain.FINANCIAL_RAIL, Technique(
        id="FINR-002",
        name="Provider Receipt Forgery",
        description="Submit forged provider receipts to reconcile false costs or hide actual spend.",
        severity=Severity.CRITICAL,
        kill_chain_phase="impact",
        prerequisites=("TOOL-003",),
        indicators=("receipt validation failures", "cost reconciliation anomalies", "impossible receipt chains"),
        detection_refs=("DETECT-034",),
        mitigation_refs=("MITIG-034",),
    ))
    matrix.add_technique(TacticDomain.FINANCIAL_RAIL, Technique(
        id="FINR-003",
        name="Grant Budget Double-Spend",
        description="Exploit race conditions in grant budget tracking to spend beyond allocated limits.",
        severity=Severity.HIGH,
        kill_chain_phase="impact",
        prerequisites=("TOOL-001",),
        indicators=("concurrent budget consumption", "overspend patterns", "race condition artifacts"),
        detection_refs=("DETECT-035",),
        mitigation_refs=("MITIG-035",),
    ))
    matrix.add_technique(TacticDomain.FINANCIAL_RAIL, Technique(
        id="FINR-004",
        name="Cost Telemetry Manipulation",
        description="Manipulate cost telemetry to hide the true financial impact of operations.",
        severity=Severity.HIGH,
        kill_chain_phase="defense_evasion",
        prerequisites=("TELX-002",),
        indicators=("cost reporting anomalies", "telemetry gaps", "financial metric inconsistencies"),
        detection_refs=("DETECT-036",),
        mitigation_refs=("MITIG-036",),
    ))

    # ── 10. State Exfiltration ────────────────────────────────────────────
    matrix.add_technique(TacticDomain.STATE_EXFILTRATION, Technique(
        id="EXFX-001",
        name="Credential Exfiltration via Tool Output",
        description="Extract worker credentials or lease tokens through tool result channels.",
        severity=Severity.CRITICAL,
        kill_chain_phase="exfiltration",
        prerequisites=("TOOL-001", "SBEX-003"),
        indicators=("credential patterns in outputs", "token-like strings in results", "unusual output sizes"),
        detection_refs=("DETECT-037",),
        mitigation_refs=("MITIG-037",),
    ))
    matrix.add_technique(TacticDomain.STATE_EXFILTRATION, Technique(
        id="EXFX-002",
        name="Task Payload Exfiltration",
        description="Extract sensitive task payloads through execution graph projections or analytics.",
        severity=Severity.HIGH,
        kill_chain_phase="exfiltration",
        prerequisites=("CTXC-004",),
        indicators=("payload data in projections", "unauthorized data access patterns", "projection boundary violations"),
        detection_refs=("DETECT-038",),
        mitigation_refs=("MITIG-038",),
    ))
    matrix.add_technique(TacticDomain.STATE_EXFILTRATION, Technique(
        id="EXFX-003",
        name="Specialist Contract Data Theft",
        description="Extract specialist contract designs, assignments, and execution inputs from the control store.",
        severity=Severity.HIGH,
        kill_chain_phase="exfiltration",
        prerequisites=("PRIV-002",),
        indicators=("contract data access patterns", "unauthorized contract reads", "scope data leakage"),
        detection_refs=("DETECT-039",),
        mitigation_refs=("MITIG-039",),
    ))
    matrix.add_technique(TacticDomain.STATE_EXFILTRATION, Technique(
        id="EXFX-004",
        name="Side-Channel Data Leakage",
        description="Extract sensitive information through timing, error messages, or resource usage patterns.",
        severity=Severity.MEDIUM,
        kill_chain_phase="exfiltration",
        prerequisites=("RECON-001",),
        indicators=("timing side-channels", "error message information leakage", "resource usage patterns"),
        detection_refs=("DETECT-040",),
        mitigation_refs=("MITIG-040",),
    ))

    # ── 11. Resource Exhaustion ───────────────────────────────────────────
    matrix.add_technique(TacticDomain.RESOURCE_EXHAUSTION, Technique(
        id="RSRX-001",
        name="Task Flood DoS",
        description="Flood the scheduler with tasks to exhaust MAX_TASKS, MAX_ACTIVE, or other capacity limits.",
        severity=Severity.HIGH,
        kill_chain_phase="impact",
        prerequisites=("RECON-001",),
        indicators=("task creation rate anomalies", "capacity limit approaches", "queue saturation"),
        detection_refs=("DETECT-041",),
        mitigation_refs=("MITIG-041",),
    ))
    matrix.add_technique(TacticDomain.RESOURCE_EXHAUSTION, Technique(
        id="RSRX-002",
        name="Checkpoint Storage Exhaustion",
        description="Consume checkpoint storage limits to cause denial of service for legitimate task progress.",
        severity=Severity.MEDIUM,
        kill_chain_phase="impact",
        prerequisites=("SEMI-002",),
        indicators=("checkpoint count anomalies", "storage limit approaches", "checkpoint size patterns"),
        detection_refs=("DETECT-042",),
        mitigation_refs=("MITIG-042",),
    ))
    matrix.add_technique(TacticDomain.RESOURCE_EXHAUSTION, Technique(
        id="RSRX-003",
        name="Lease Exhaustion Attack",
        description="Hold leases without heartbeating to exhaust MAX_ACTIVE slots and block legitimate workers.",
        severity=Severity.HIGH,
        kill_chain_phase="impact",
        prerequisites=("TOOL-004",),
        indicators=("lease holding patterns", "heartbeat absence", "active slot saturation"),
        detection_refs=("DETECT-043",),
        mitigation_refs=("MITIG-043",),
    ))
    matrix.add_technique(TacticDomain.RESOURCE_EXHAUSTION, Technique(
        id="RSRX-004",
        name="Consensus Log Flooding",
        description="Flood the consensus log with entries to exhaust storage and processing capacity.",
        severity=Severity.MEDIUM,
        kill_chain_phase="impact",
        prerequisites=("SWAR-003",),
        indicators=("log entry rate anomalies", "consensus storage growth", "replication lag"),
        detection_refs=("DETECT-044",),
        mitigation_refs=("MITIG-044",),
    ))

    return matrix
