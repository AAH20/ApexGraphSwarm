"""Four-dimension conformance evaluation harness with cryptographic scorecards.

Dimensions:
  1. Formal invariants — graph schema, referential integrity, DAG constraints
  2. Computer-use precision — tool call accuracy, path/command correctness
  3. Zero-trust tool discipline — capability checks, least privilege, audit coverage
  4. Latency/cost conformance — p95 latency SLO, cost caps, budget adherence

Zero-dependency Python 3.10+. All scorecards are SHA-256 content-addressed and
chained for tamper evidence. HMAC-SHA256 provides integrity verification.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import math
import re
import statistics
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ConformanceError(ValueError):
    """Invalid conformance input or unverifiable scorecard."""


# ---------------------------------------------------------------------------
# Dimension 1: Formal Invariants
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GraphNode:
    node_id: str
    node_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source_id: str
    target_id: str
    edge_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FormalInvariantReport:
    dimension: str
    total_nodes: int
    total_edges: int
    duplicate_node_ids: list[str]
    duplicate_edge_ids: list[str]
    dangling_edge_references: list[str]
    invalid_node_types: list[str]
    invalid_edge_types: list[str]
    self_loops: list[str]
    detected_cycles: list[str]
    schema_violations: list[str]
    passed: bool
    score: float


_VALID_NODE_TYPES = frozenset({
    "file", "function", "class", "module", "variable", "import",
    "export", "interface", "type", "enum", "constant", "test",
})

_VALID_EDGE_TYPES = frozenset({
    "calls", "imports", "exports", "defines", "references", "inherits",
    "implements", "depends_on", "contains", "tests", "overrides",
})

_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:/\-]{0,255}$")


def _validate_id(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ConformanceError(f"{name} must be a non-empty string of at most 256 characters")
    if not _ID_RE.match(value):
        raise ConformanceError(f"{name} contains unsupported characters: {value!r}")
    return value


def _detect_cycles(nodes: Sequence[GraphNode], edges: Sequence[GraphEdge]) -> list[str]:
    """Return list of node IDs participating in any cycle (DFS-based)."""
    adjacency: dict[str, list[str]] = {n.node_id: [] for n in nodes}
    for e in edges:
        if e.source_id in adjacency and e.target_id in adjacency:
            adjacency[e.source_id].append(e.target_id)

    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {n.node_id: WHITE for n in nodes}
    in_cycle: set[str] = set()

    def dfs(u: str, path: list[str]) -> None:
        color[u] = GRAY
        path.append(u)
        for v in adjacency[u]:
            if color[v] == GRAY:
                idx = path.index(v)
                in_cycle.update(path[idx:])
            elif color[v] == WHITE:
                dfs(v, path)
        path.pop()
        color[u] = BLACK

    for n in nodes:
        if color[n.node_id] == WHITE:
            dfs(n.node_id, [])
    return sorted(in_cycle)


def evaluate_formal_invariants(
    nodes: Sequence[GraphNode],
    edges: Sequence[GraphEdge],
    *,
    require_dag: bool = True,
    allowed_node_types: frozenset[str] | set[str] | None = None,
    allowed_edge_types: frozenset[str] | set[str] | None = None,
) -> FormalInvariantReport:
    """Evaluate graph formal invariants: schema, referential integrity, DAG."""
    if not nodes:
        raise ConformanceError("at least one graph node is required")
    if not edges:
        raise ConformanceError("at least one graph edge is required")

    node_types = allowed_node_types if allowed_node_types is not None else _VALID_NODE_TYPES
    edge_types = allowed_edge_types if allowed_edge_types is not None else _VALID_EDGE_TYPES

    node_ids = [n.node_id for n in nodes]
    edge_ids = [e.edge_id for e in edges]
    node_id_set = set(node_ids)

    # Duplicate detection
    seen_nodes: set[str] = set()
    dup_nodes: list[str] = []
    for nid in node_ids:
        if nid in seen_nodes and nid not in dup_nodes:
            dup_nodes.append(nid)
        seen_nodes.add(nid)

    seen_edges: set[str] = set()
    dup_edges: list[str] = []
    for eid in edge_ids:
        if eid in seen_edges and eid not in dup_edges:
            dup_edges.append(eid)
        seen_edges.add(eid)

    # Dangling references
    dangling: list[str] = []
    for e in edges:
        if e.source_id not in node_id_set:
            dangling.append(f"{e.edge_id}:source:{e.source_id}")
        if e.target_id not in node_id_set:
            dangling.append(f"{e.edge_id}:target:{e.target_id}")

    # Type validation
    invalid_node_types: list[str] = []
    for n in nodes:
        if n.node_type not in node_types:
            invalid_node_types.append(f"{n.node_id}:{n.node_type}")

    invalid_edge_types: list[str] = []
    for e in edges:
        if e.edge_type not in edge_types:
            invalid_edge_types.append(f"{e.edge_id}:{e.edge_type}")

    # Self-loops
    self_loops: list[str] = []
    for e in edges:
        if e.source_id == e.target_id:
            self_loops.append(e.edge_id)

    # Cycle detection
    cycles = _detect_cycles(nodes, edges) if require_dag else []

    # Schema violations (property key validation)
    schema_violations: list[str] = []
    for n in nodes:
        for key in n.properties:
            if not isinstance(key, str) or not key:
                schema_violations.append(f"{n.node_id}:bad_property_key")
                break

    all_issues = dup_nodes + dup_edges + dangling + invalid_node_types + invalid_edge_types + self_loops + cycles + schema_violations
    total_checks = len(nodes) + len(edges) * 4 + 1  # rough weighting
    score = max(0.0, 1.0 - len(all_issues) / max(total_checks, 1))

    return FormalInvariantReport(
        dimension="formal_invariants",
        total_nodes=len(nodes),
        total_edges=len(edges),
        duplicate_node_ids=sorted(dup_nodes),
        duplicate_edge_ids=sorted(dup_edges),
        dangling_edge_references=sorted(dangling),
        invalid_node_types=sorted(invalid_node_types),
        invalid_edge_types=sorted(invalid_edge_types),
        self_loops=sorted(self_loops),
        detected_cycles=cycles,
        schema_violations=sorted(schema_violations),
        passed=len(all_issues) == 0,
        score=round(score, 6),
    )


# ---------------------------------------------------------------------------
# Dimension 2: Computer-Use Precision
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolCall:
    call_id: str
    tool_name: str
    arguments: dict[str, Any]
    expected_outcome: str | None = None
    actual_outcome: str | None = None
    success: bool | None = None
    path_precision: float | None = None  # 0..1
    command_precision: float | None = None  # 0..1


@dataclass(frozen=True)
class ComputerUseReport:
    dimension: str
    total_calls: int
    successful_calls: int
    failed_calls: int
    mean_path_precision: float | None
    mean_command_precision: float | None
    calls_with_imprecise_paths: list[str]
    calls_with_imprecise_commands: list[str]
    outcome_mismatches: list[str]
    passed: bool
    score: float


def evaluate_computer_use_precision(
    calls: Sequence[ToolCall],
    *,
    path_threshold: float = 0.8,
    command_threshold: float = 0.8,
) -> ComputerUseReport:
    """Evaluate computer-use precision: tool call accuracy and path/command correctness."""
    if not calls:
        raise ConformanceError("at least one tool call is required")

    total = len(calls)
    successful = sum(1 for c in calls if c.success is True)
    failed = sum(1 for c in calls if c.success is False)

    path_precisions = [c.path_precision for c in calls if c.path_precision is not None]
    cmd_precisions = [c.command_precision for c in calls if c.command_precision is not None]

    mean_path = statistics.mean(path_precisions) if path_precisions else None
    mean_cmd = statistics.mean(cmd_precisions) if cmd_precisions else None

    imprecise_paths = [c.call_id for c in calls if c.path_precision is not None and c.path_precision < path_threshold]
    imprecise_cmds = [c.call_id for c in calls if c.command_precision is not None and c.command_precision < command_threshold]

    outcome_mismatches: list[str] = []
    for c in calls:
        if c.expected_outcome is not None and c.actual_outcome is not None:
            if c.expected_outcome != c.actual_outcome:
                outcome_mismatches.append(c.call_id)

    # Score: weighted combination
    success_rate = successful / total if total else 0.0
    path_score = mean_path if mean_path is not None else 0.0
    cmd_score = mean_cmd if mean_cmd is not None else 0.0
    mismatch_penalty = len(outcome_mismatches) / total if total else 0.0

    score = max(0.0, 0.4 * success_rate + 0.3 * path_score + 0.3 * cmd_score - 0.5 * mismatch_penalty)
    score = round(min(1.0, score), 6)

    passed = (
        not imprecise_paths
        and not imprecise_cmds
        and not outcome_mismatches
        and failed == 0
    )

    return ComputerUseReport(
        dimension="computer_use_precision",
        total_calls=total,
        successful_calls=successful,
        failed_calls=failed,
        mean_path_precision=round(mean_path, 6) if mean_path is not None else None,
        mean_command_precision=round(mean_cmd, 6) if mean_cmd is not None else None,
        calls_with_imprecise_paths=sorted(imprecise_paths),
        calls_with_imprecise_commands=sorted(imprecise_cmds),
        outcome_mismatches=sorted(outcome_mismatches),
        passed=passed,
        score=score,
    )


# ---------------------------------------------------------------------------
# Dimension 3: Zero-Trust Tool Discipline
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolAction:
    action_id: str
    principal_id: str
    tool_id: str
    resource_id: str
    action_type: str  # "read", "write", "execute", "delete"
    capability_granted: bool
    capability_checked: bool
    policy_violation: bool
    audit_logged: bool
    denied: bool


@dataclass(frozen=True)
class ZeroTrustReport:
    dimension: str
    total_actions: int
    granted_actions: int
    denied_actions: int
    policy_violations: int
    audit_coverage: float  # 0..1
    ungranted_attempts: list[str]
    unchecked_capability_attempts: list[str]
    unaudited_actions: list[str]
    passed: bool
    score: float


def evaluate_zero_trust_discipline(
    actions: Sequence[ToolAction],
    *,
    require_audit: bool = True,
) -> ZeroTrustReport:
    """Evaluate zero-trust tool discipline: capability checks, least privilege, audit."""
    if not actions:
        raise ConformanceError("at least one tool action is required")

    total = len(actions)
    granted = sum(1 for a in actions if a.capability_granted and not a.denied)
    denied = sum(1 for a in actions if a.denied)
    violations = sum(1 for a in actions if a.policy_violation)
    audited = sum(1 for a in actions if a.audit_logged)

    ungranted = [a.action_id for a in actions if not a.capability_granted and not a.denied]
    unchecked = [a.action_id for a in actions if not a.capability_checked and not a.denied]
    unaudited = [a.action_id for a in actions if not a.audit_logged]

    audit_coverage = audited / total if total else 0.0

    # Score: violations are catastrophic, ungranted attempts are serious
    violation_penalty = violations / total if total else 0.0
    ungranted_penalty = len(ungranted) / total if total else 0.0
    unchecked_penalty = len(unchecked) / total if total else 0.0
    audit_score = audit_coverage if require_audit else 1.0

    score = max(0.0, audit_score - 2.0 * violation_penalty - 1.0 * ungranted_penalty - 0.5 * unchecked_penalty)
    score = round(min(1.0, score), 6)

    passed = violations == 0 and not ungranted and not unchecked and (not require_audit or not unaudited)

    return ZeroTrustReport(
        dimension="zero_trust_tool_discipline",
        total_actions=total,
        granted_actions=granted,
        denied_actions=denied,
        policy_violations=violations,
        audit_coverage=round(audit_coverage, 6),
        ungranted_attempts=sorted(ungranted),
        unchecked_capability_attempts=sorted(unchecked),
        unaudited_actions=sorted(unaudited),
        passed=passed,
        score=score,
    )


# ---------------------------------------------------------------------------
# Dimension 4: Latency/Cost Conformance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TaskExecution:
    task_id: str
    elapsed_ms: float
    cost_microusd: int | None
    deadline_ms: float | None = None
    budget_microusd: int | None = None
    status: str = "succeeded"  # succeeded, failed, timed_out, cancelled


@dataclass(frozen=True)
class LatencyCostReport:
    dimension: str
    total_tasks: int
    succeeded_tasks: int
    failed_tasks: int
    mean_latency_ms: float | None
    p50_latency_ms: float | None
    p95_latency_ms: float | None
    max_latency_ms: float | None
    deadline_violations: list[str]
    total_cost_microusd: int | None
    unknown_cost_tasks: list[str]
    budget_violations: list[str]
    mean_cost_microusd: float | None
    passed: bool
    score: float


def _percentile(sorted_values: Sequence[float], p: float) -> float:
    """Nearest-rank percentile."""
    if not sorted_values:
        return 0.0
    idx = max(0, math.ceil(p / 100.0 * len(sorted_values)) - 1)
    return sorted_values[idx]


def evaluate_latency_cost(
    tasks: Sequence[TaskExecution],
    *,
    latency_slo_ms: float | None = None,
    cost_cap_microusd: int | None = None,
) -> LatencyCostReport:
    """Evaluate latency and cost conformance against SLOs and budgets."""
    if not tasks:
        raise ConformanceError("at least one task execution is required")

    total = len(tasks)
    succeeded = sum(1 for t in tasks if t.status == "succeeded")
    failed = sum(1 for t in tasks if t.status != "succeeded")

    latencies = [t.elapsed_ms for t in tasks if t.elapsed_ms is not None]
    sorted_lat = sorted(latencies)

    mean_lat = statistics.mean(latencies) if latencies else None
    p50 = _percentile(sorted_lat, 50) if sorted_lat else None
    p95 = _percentile(sorted_lat, 95) if sorted_lat else None
    max_lat = max(latencies) if latencies else None

    deadline_violations = [
        t.task_id for t in tasks
        if t.deadline_ms is not None and t.elapsed_ms > t.deadline_ms
    ]

    known_costs = [t.cost_microusd for t in tasks if t.cost_microusd is not None]
    unknown_cost = [t.task_id for t in tasks if t.cost_microusd is None]
    total_cost = sum(known_costs) if known_costs else None
    mean_cost = statistics.mean(known_costs) if known_costs else None

    budget_violations = [
        t.task_id for t in tasks
        if t.budget_microusd is not None and t.cost_microusd is not None and t.cost_microusd > t.budget_microusd
    ]

    # Score components
    success_rate = succeeded / total if total else 0.0
    latency_score = 1.0
    if latency_slo_ms is not None and p95 is not None:
        latency_score = max(0.0, 1.0 - max(0.0, p95 - latency_slo_ms) / latency_slo_ms)
    cost_score = 1.0
    if cost_cap_microusd is not None and mean_cost is not None:
        cost_score = max(0.0, 1.0 - max(0.0, mean_cost - cost_cap_microusd) / cost_cap_microusd)
    unknown_penalty = len(unknown_cost) / total if total else 0.0

    score = max(0.0, 0.4 * success_rate + 0.3 * latency_score + 0.3 * cost_score - 0.5 * unknown_penalty)
    score = round(min(1.0, score), 6)

    passed = (
        not deadline_violations
        and not budget_violations
        and not unknown_cost
        and (latency_slo_ms is None or (p95 is not None and p95 <= latency_slo_ms))
        and (cost_cap_microusd is None or (mean_cost is not None and mean_cost <= cost_cap_microusd))
    )

    return LatencyCostReport(
        dimension="latency_cost_conformance",
        total_tasks=total,
        succeeded_tasks=succeeded,
        failed_tasks=failed,
        mean_latency_ms=round(mean_lat, 3) if mean_lat is not None else None,
        p50_latency_ms=round(p50, 3) if p50 is not None else None,
        p95_latency_ms=round(p95, 3) if p95 is not None else None,
        max_latency_ms=round(max_lat, 3) if max_lat is not None else None,
        deadline_violations=sorted(deadline_violations),
        total_cost_microusd=total_cost,
        unknown_cost_tasks=sorted(unknown_cost),
        budget_violations=sorted(budget_violations),
        mean_cost_microusd=round(mean_cost, 3) if mean_cost is not None else None,
        passed=passed,
        score=score,
    )


# ---------------------------------------------------------------------------
# Cryptographic Scorecard
# ---------------------------------------------------------------------------

def _canonical_json(obj: Any) -> str:
    """Deterministic JSON serialization for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def _sha256_hex(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Scorecard:
    """Cryptographic scorecard with tamper-evident chaining."""
    scorecard_id: str
    run_id: str
    timestamp_unix: float
    dimension_reports: dict[str, Any]
    overall_score: float
    overall_passed: bool
    previous_scorecard_hash: str | None
    scorecard_hash: str
    hmac_signature: str | None = None

    def verify(self, hmac_key: str | None = None) -> bool:
        """Verify scorecard integrity: hash chain and optional HMAC."""
        # Recompute hash
        payload = {
            "scorecardId": self.scorecard_id,
            "runId": self.run_id,
            "timestampUnix": self.timestamp_unix,
            "dimensionReports": self.dimension_reports,
            "overallScore": self.overall_score,
            "overallPassed": self.overall_passed,
            "previousScorecardHash": self.previous_scorecard_hash,
        }
        expected_hash = _sha256_hex(_canonical_json(payload))
        if expected_hash != self.scorecard_hash:
            return False

        if hmac_key is not None and self.hmac_signature is not None:
            expected_hmac = hmac.new(
                hmac_key.encode("utf-8"),
                self.scorecard_hash.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
            if not hmac.compare_digest(expected_hmac, self.hmac_signature):
                return False

        return True

    def to_dict(self) -> dict[str, Any]:
        return {
            "scorecardId": self.scorecard_id,
            "runId": self.run_id,
            "timestampUnix": self.timestamp_unix,
            "dimensionReports": self.dimension_reports,
            "overallScore": self.overall_score,
            "overallPassed": self.overall_passed,
            "previousScorecardHash": self.previous_scorecard_hash,
            "scorecardHash": self.scorecard_hash,
            "hmacSignature": self.hmac_signature,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Scorecard":
        return cls(
            scorecard_id=raw["scorecardId"],
            run_id=raw["runId"],
            timestamp_unix=raw["timestampUnix"],
            dimension_reports=raw["dimensionReports"],
            overall_score=raw["overallScore"],
            overall_passed=raw["overallPassed"],
            previous_scorecard_hash=raw.get("previousScorecardHash"),
            scorecard_hash=raw["scorecardHash"],
            hmac_signature=raw.get("hmacSignature"),
        )


def build_scorecard(
    *,
    run_id: str,
    timestamp_unix: float,
    formal_report: FormalInvariantReport,
    computer_use_report: ComputerUseReport,
    zero_trust_report: ZeroTrustReport,
    latency_cost_report: LatencyCostReport,
    previous_scorecard_hash: str | None = None,
    hmac_key: str | None = None,
) -> Scorecard:
    """Build a cryptographic scorecard from four dimension reports."""
    dimension_reports = {
        "formalInvariants": {
            "dimension": formal_report.dimension,
            "totalNodes": formal_report.total_nodes,
            "totalEdges": formal_report.total_edges,
            "duplicateNodeIds": formal_report.duplicate_node_ids,
            "duplicateEdgeIds": formal_report.duplicate_edge_ids,
            "danglingEdgeReferences": formal_report.dangling_edge_references,
            "invalidNodeTypes": formal_report.invalid_node_types,
            "invalidEdgeTypes": formal_report.invalid_edge_types,
            "selfLoops": formal_report.self_loops,
            "detectedCycles": formal_report.detected_cycles,
            "schemaViolations": formal_report.schema_violations,
            "passed": formal_report.passed,
            "score": formal_report.score,
        },
        "computerUsePrecision": {
            "dimension": computer_use_report.dimension,
            "totalCalls": computer_use_report.total_calls,
            "successfulCalls": computer_use_report.successful_calls,
            "failedCalls": computer_use_report.failed_calls,
            "meanPathPrecision": computer_use_report.mean_path_precision,
            "meanCommandPrecision": computer_use_report.mean_command_precision,
            "callsWithImprecisePaths": computer_use_report.calls_with_imprecise_paths,
            "callsWithImpreciseCommands": computer_use_report.calls_with_imprecise_commands,
            "outcomeMismatches": computer_use_report.outcome_mismatches,
            "passed": computer_use_report.passed,
            "score": computer_use_report.score,
        },
        "zeroTrustToolDiscipline": {
            "dimension": zero_trust_report.dimension,
            "totalActions": zero_trust_report.total_actions,
            "grantedActions": zero_trust_report.granted_actions,
            "deniedActions": zero_trust_report.denied_actions,
            "policyViolations": zero_trust_report.policy_violations,
            "auditCoverage": zero_trust_report.audit_coverage,
            "ungrantedAttempts": zero_trust_report.ungranted_attempts,
            "uncheckedCapabilityAttempts": zero_trust_report.unchecked_capability_attempts,
            "unauditedActions": zero_trust_report.unaudited_actions,
            "passed": zero_trust_report.passed,
            "score": zero_trust_report.score,
        },
        "latencyCostConformance": {
            "dimension": latency_cost_report.dimension,
            "totalTasks": latency_cost_report.total_tasks,
            "succeededTasks": latency_cost_report.succeeded_tasks,
            "failedTasks": latency_cost_report.failed_tasks,
            "meanLatencyMs": latency_cost_report.mean_latency_ms,
            "p50LatencyMs": latency_cost_report.p50_latency_ms,
            "p95LatencyMs": latency_cost_report.p95_latency_ms,
            "maxLatencyMs": latency_cost_report.max_latency_ms,
            "deadlineViolations": latency_cost_report.deadline_violations,
            "totalCostMicrousd": latency_cost_report.total_cost_microusd,
            "unknownCostTasks": latency_cost_report.unknown_cost_tasks,
            "budgetViolations": latency_cost_report.budget_violations,
            "meanCostMicrousd": latency_cost_report.mean_cost_microusd,
            "passed": latency_cost_report.passed,
            "score": latency_cost_report.score,
        },
    }

    scores = [
        formal_report.score,
        computer_use_report.score,
        zero_trust_report.score,
        latency_cost_report.score,
    ]
    overall_score = round(sum(scores) / len(scores), 6)
    overall_passed = all(r.passed for r in [formal_report, computer_use_report, zero_trust_report, latency_cost_report])

    scorecard_id = _sha256_hex(f"{run_id}:{timestamp_unix}:{overall_score}")

    payload = {
        "scorecardId": scorecard_id,
        "runId": run_id,
        "timestampUnix": timestamp_unix,
        "dimensionReports": dimension_reports,
        "overallScore": overall_score,
        "overallPassed": overall_passed,
        "previousScorecardHash": previous_scorecard_hash,
    }
    scorecard_hash = _sha256_hex(_canonical_json(payload))

    hmac_sig = None
    if hmac_key is not None:
        hmac_sig = hmac.new(
            hmac_key.encode("utf-8"),
            scorecard_hash.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    return Scorecard(
        scorecard_id=scorecard_id,
        run_id=run_id,
        timestamp_unix=timestamp_unix,
        dimension_reports=dimension_reports,
        overall_score=overall_score,
        overall_passed=overall_passed,
        previous_scorecard_hash=previous_scorecard_hash,
        scorecard_hash=scorecard_hash,
        hmac_signature=hmac_sig,
    )


# ---------------------------------------------------------------------------
# Full Conformance Evaluation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConformanceResult:
    """Complete four-dimension conformance evaluation result."""
    run_id: str
    timestamp_unix: float
    formal: FormalInvariantReport
    computer_use: ComputerUseReport
    zero_trust: ZeroTrustReport
    latency_cost: LatencyCostReport
    scorecard: Scorecard

    def to_dict(self) -> dict[str, Any]:
        return {
            "runId": self.run_id,
            "timestampUnix": self.timestamp_unix,
            "formalInvariants": {
                "dimension": self.formal.dimension,
                "totalNodes": self.formal.total_nodes,
                "totalEdges": self.formal.total_edges,
                "duplicateNodeIds": self.formal.duplicate_node_ids,
                "duplicateEdgeIds": self.formal.duplicate_edge_ids,
                "danglingEdgeReferences": self.formal.dangling_edge_references,
                "invalidNodeTypes": self.formal.invalid_node_types,
                "invalidEdgeTypes": self.formal.invalid_edge_types,
                "selfLoops": self.formal.self_loops,
                "detectedCycles": self.formal.detected_cycles,
                "schemaViolations": self.formal.schema_violations,
                "passed": self.formal.passed,
                "score": self.formal.score,
            },
            "computerUsePrecision": {
                "dimension": self.computer_use.dimension,
                "totalCalls": self.computer_use.total_calls,
                "successfulCalls": self.computer_use.successful_calls,
                "failedCalls": self.computer_use.failed_calls,
                "meanPathPrecision": self.computer_use.mean_path_precision,
                "meanCommandPrecision": self.computer_use.mean_command_precision,
                "callsWithImprecisePaths": self.computer_use.calls_with_imprecise_paths,
                "callsWithImpreciseCommands": self.computer_use.calls_with_imprecise_commands,
                "outcomeMismatches": self.computer_use.outcome_mismatches,
                "passed": self.computer_use.passed,
                "score": self.computer_use.score,
            },
            "zeroTrustToolDiscipline": {
                "dimension": self.zero_trust.dimension,
                "totalActions": self.zero_trust.total_actions,
                "grantedActions": self.zero_trust.granted_actions,
                "deniedActions": self.zero_trust.denied_actions,
                "policyViolations": self.zero_trust.policy_violations,
                "auditCoverage": self.zero_trust.audit_coverage,
                "ungrantedAttempts": self.zero_trust.ungranted_attempts,
                "uncheckedCapabilityAttempts": self.zero_trust.unchecked_capability_attempts,
                "unauditedActions": self.zero_trust.unaudited_actions,
                "passed": self.zero_trust.passed,
                "score": self.zero_trust.score,
            },
            "latencyCostConformance": {
                "dimension": self.latency_cost.dimension,
                "totalTasks": self.latency_cost.total_tasks,
                "succeededTasks": self.latency_cost.succeeded_tasks,
                "failedTasks": self.latency_cost.failed_tasks,
                "meanLatencyMs": self.latency_cost.mean_latency_ms,
                "p50LatencyMs": self.latency_cost.p50_latency_ms,
                "p95LatencyMs": self.latency_cost.p95_latency_ms,
                "maxLatencyMs": self.latency_cost.max_latency_ms,
                "deadlineViolations": self.latency_cost.deadline_violations,
                "totalCostMicrousd": self.latency_cost.total_cost_microusd,
                "unknownCostTasks": self.latency_cost.unknown_cost_tasks,
                "budgetViolations": self.latency_cost.budget_violations,
                "meanCostMicrousd": self.latency_cost.mean_cost_microusd,
                "passed": self.latency_cost.passed,
                "score": self.latency_cost.score,
            },
            "scorecard": self.scorecard.to_dict(),
        }


def evaluate_conformance(
    *,
    run_id: str,
    timestamp_unix: float,
    nodes: Sequence[GraphNode],
    edges: Sequence[GraphEdge],
    tool_calls: Sequence[ToolCall],
    tool_actions: Sequence[ToolAction],
    task_executions: Sequence[TaskExecution],
    require_dag: bool = True,
    latency_slo_ms: float | None = None,
    cost_cap_microusd: int | None = None,
    hmac_key: str | None = None,
    previous_scorecard_hash: str | None = None,
) -> ConformanceResult:
    """Run full four-dimension conformance evaluation and produce a scorecard."""
    formal = evaluate_formal_invariants(nodes, edges, require_dag=require_dag)
    computer_use = evaluate_computer_use_precision(tool_calls)
    zero_trust = evaluate_zero_trust_discipline(tool_actions)
    latency_cost = evaluate_latency_cost(
        task_executions,
        latency_slo_ms=latency_slo_ms,
        cost_cap_microusd=cost_cap_microusd,
    )

    scorecard = build_scorecard(
        run_id=run_id,
        timestamp_unix=timestamp_unix,
        formal_report=formal,
        computer_use_report=computer_use,
        zero_trust_report=zero_trust,
        latency_cost_report=latency_cost,
        previous_scorecard_hash=previous_scorecard_hash,
        hmac_key=hmac_key,
    )

    return ConformanceResult(
        run_id=run_id,
        timestamp_unix=timestamp_unix,
        formal=formal,
        computer_use=computer_use,
        zero_trust=zero_trust,
        latency_cost=latency_cost,
        scorecard=scorecard,
    )
