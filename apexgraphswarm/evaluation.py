"""Versioned, paired evaluation and promotion gates for supplied optimizer runs.

This module never executes candidate code. Callers supply scalar configuration
records and evaluator-produced attempt records; unknown spend is preserved and
blocks a favorable promotion decision.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Any, Mapping, Sequence


class EvaluationError(ValueError):
    """Invalid or incomparable evaluation data."""


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 256 or "\x00" in value:
        raise EvaluationError("%s must be a non-empty string of at most 256 characters" % name)
    return value.strip()


def _finite_number(value: Any, name: str, *, low: float | None = None,
                   high: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise EvaluationError("%s must be a finite number" % name)
    number = float(value)
    if not math.isfinite(number) or (low is not None and number < low) or (high is not None and number > high):
        raise EvaluationError("%s is outside its valid range" % name)
    return number


def _ids(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or not value or len(value) > 10_000:
        raise EvaluationError("%s must be a non-empty list of at most 10,000 task IDs" % name)
    out = tuple(_required_text(item, name + " item") for item in value)
    if len(set(out)) != len(out):
        raise EvaluationError("%s contains duplicate IDs" % name)
    return out


def _safe_config(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvaluationError("candidate config must be a JSON object")
    # Restrict configs to inert JSON data; no code, non-finite values, or custom types.
    try:
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise EvaluationError("candidate config must contain finite JSON values") from exc
    if len(encoded.encode("utf-8")) > 16_384:
        raise EvaluationError("candidate config exceeds 16 KiB")
    return json.loads(encoded)


@dataclass(frozen=True)
class EvaluationSuite:
    suite_id: str
    suite_version: str
    taskset_id: str
    taskset_version: str
    evaluator_id: str
    evaluator_version: str
    train_task_ids: tuple[str, ...]
    heldout_task_ids: tuple[str, ...]
    sealed_task_ids: tuple[str, ...]
    quality_floor: float = 0.8
    max_latency_ms: float = 60_000.0
    max_policy_violations: int = 0
    confidence_alpha: float = 0.05
    max_attempts_per_task: int = 3
    max_accept_rate_regression: float = 0.02
    max_cost_microusd_per_task: int | None = None
    cost_cap_enforcement_id: str | None = None

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "EvaluationSuite":
        if not isinstance(raw, Mapping):
            raise EvaluationError("suite must be an object")
        train = _ids(raw.get("trainTaskIds"), "trainTaskIds")
        heldout = _ids(raw.get("heldoutTaskIds"), "heldoutTaskIds")
        sealed = _ids(raw.get("sealedTaskIds"), "sealedTaskIds")
        if set(train) & set(heldout) or set(train) & set(sealed) or set(heldout) & set(sealed):
            raise EvaluationError("training, held-out, and sealed task IDs must be disjoint")
        violations = raw.get("maxPolicyViolations", 0)
        attempts = raw.get("maxAttemptsPerTask", 3)
        cost_cap = raw.get("maxCostMicrousdPerTask")
        if cost_cap is not None and (isinstance(cost_cap, bool) or not isinstance(cost_cap, int) or not 0 <= cost_cap <= 2**63 - 1):
            raise EvaluationError("maxCostMicrousdPerTask must be a non-negative signed 64-bit integer or null")
        enforcement_id = raw.get("costCapEnforcementId")
        if enforcement_id is not None:
            enforcement_id = _required_text(enforcement_id, "costCapEnforcementId")
        if isinstance(violations, bool) or not isinstance(violations, int) or violations < 0:
            raise EvaluationError("maxPolicyViolations must be a non-negative integer")
        if isinstance(attempts, bool) or not isinstance(attempts, int) or not 1 <= attempts <= 10:
            raise EvaluationError("maxAttemptsPerTask must be an integer from 1 to 10")
        alpha = _finite_number(raw.get("confidenceAlpha", 0.05), "confidenceAlpha", low=0.001, high=0.25)
        return cls(
            suite_id=_required_text(raw.get("suiteId"), "suiteId"),
            suite_version=_required_text(raw.get("suiteVersion"), "suiteVersion"),
            taskset_id=_required_text(raw.get("tasksetId"), "tasksetId"),
            taskset_version=_required_text(raw.get("tasksetVersion"), "tasksetVersion"),
            evaluator_id=_required_text(raw.get("evaluatorId"), "evaluatorId"),
            evaluator_version=_required_text(raw.get("evaluatorVersion"), "evaluatorVersion"),
            train_task_ids=train,
            heldout_task_ids=heldout,
            sealed_task_ids=sealed,
            quality_floor=_finite_number(raw.get("qualityFloor", 0.8), "qualityFloor", low=0, high=1),
            max_latency_ms=_finite_number(raw.get("maxLatencyMs", 60_000), "maxLatencyMs", low=0),
            max_policy_violations=violations,
            confidence_alpha=alpha,
            max_attempts_per_task=attempts,
            max_accept_rate_regression=_finite_number(
                raw.get("maxAcceptRateRegression", 0.02), "maxAcceptRateRegression", low=0, high=1),
            max_cost_microusd_per_task=cost_cap,
            cost_cap_enforcement_id=enforcement_id,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "suiteId": self.suite_id, "suiteVersion": self.suite_version,
            "tasksetId": self.taskset_id, "tasksetVersion": self.taskset_version,
            "evaluatorId": self.evaluator_id, "evaluatorVersion": self.evaluator_version,
            "trainTaskIds": list(self.train_task_ids), "heldoutTaskIds": list(self.heldout_task_ids),
            "sealedTaskIds": list(self.sealed_task_ids), "qualityFloor": self.quality_floor,
            "maxLatencyMs": self.max_latency_ms, "maxPolicyViolations": self.max_policy_violations,
            "confidenceAlpha": self.confidence_alpha, "maxAttemptsPerTask": self.max_attempts_per_task,
            "maxAcceptRateRegression": self.max_accept_rate_regression,
            "maxCostMicrousdPerTask": self.max_cost_microusd_per_task,
            "costCapEnforcementId": self.cost_cap_enforcement_id,
        }


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    version: str
    config: dict[str, Any]

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Candidate":
        config = _safe_config(raw.get("config"))
        return cls(_required_text(raw.get("candidateId"), "candidateId"),
                   _required_text(raw.get("version"), "candidate version"), config)

    @property
    def config_sha256(self) -> str:
        payload = json.dumps(self.config, sort_keys=True, separators=(",", ":"), allow_nan=False)
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {"candidateId": self.candidate_id, "version": self.version,
                "config": self.config, "configSha256": self.config_sha256}


@dataclass(frozen=True)
class Attempt:
    attempt_id: str
    candidate_id: str
    task_id: str
    evaluator_id: str
    evaluator_version: str
    attempt_index: int
    status: str
    elapsed_ms: float
    actual_cost_microusd: int | None
    quality_score: float | None
    accepted: bool | None
    policy_violations: int

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Attempt":
        status = raw.get("status")
        if status not in ("succeeded", "failed", "timed_out", "cancelled"):
            raise EvaluationError("attempt status must be succeeded, failed, timed_out, or cancelled")
        index = raw.get("attemptIndex", 1)
        if isinstance(index, bool) or not isinstance(index, int) or index < 1:
            raise EvaluationError("attemptIndex must be a positive integer")
        cost = raw.get("actualCostMicrousd")
        if cost is not None and (isinstance(cost, bool) or not isinstance(cost, int) or not 0 <= cost <= 2**63 - 1):
            raise EvaluationError("actualCostMicrousd must be a non-negative signed 64-bit integer or null")
        quality = raw.get("qualityScore")
        if quality is not None:
            quality = _finite_number(quality, "qualityScore", low=0, high=1)
        accepted = raw.get("accepted")
        if accepted is not None and not isinstance(accepted, bool):
            raise EvaluationError("accepted must be boolean or null")
        if status != "succeeded" and accepted is True:
            raise EvaluationError("unsuccessful attempt cannot be accepted")
        violations = raw.get("policyViolations", 0)
        if isinstance(violations, bool) or not isinstance(violations, int) or violations < 0:
            raise EvaluationError("policyViolations must be a non-negative integer")
        return cls(
            _required_text(raw.get("attemptId"), "attemptId"),
            _required_text(raw.get("candidateId"), "attempt candidateId"),
            _required_text(raw.get("taskId"), "attempt taskId"),
            _required_text(raw.get("evaluatorId"), "attempt evaluatorId"),
            _required_text(raw.get("evaluatorVersion"), "attempt evaluatorVersion"),
            index, status,
            _finite_number(raw.get("elapsedMs"), "elapsedMs", low=0),
            cost, quality, accepted, violations,
        )


def _bounded_mean_interval(values: Sequence[float], low: float, high: float,
                           alpha: float) -> tuple[float, float]:
    """Two-sided Hoeffding interval for independent observations in [low, high]."""
    if not values:
        return low, high
    mean = sum(values) / len(values)
    radius = (high - low) * math.sqrt(math.log(2.0 / alpha) / (2.0 * len(values)))
    return max(low, mean - radius), min(high, mean + radius)


def _paired_difference_interval(baseline: Sequence[int], candidate: Sequence[int], alpha: float) -> dict[str, float]:
    if len(baseline) != len(candidate) or not baseline:
        raise EvaluationError("paired held-out task outcomes are incomplete")
    differences = [float(c - b) for b, c in zip(baseline, candidate)]
    mean = sum(differences) / len(differences)
    n = len(differences)
    if n < 2:
        radius = 2.0
    else:
        sample_variance = sum((x - mean) ** 2 for x in differences) / (n - 1)
        log_term = math.log(3.0 / alpha)
        # Empirical Bernstein bound for paired differences in [-1, 1]. The
        # range correction remains non-zero even when observed pairs all tie.
        radius = min(2.0, math.sqrt(2.0 * sample_variance * log_term / n)
                     + (14.0 * log_term) / (3.0 * (n - 1)))
    return {"mean": mean, "lower": max(-1.0, mean - radius), "upper": min(1.0, mean + radius)}


def evaluate_candidate(candidate: Candidate, suite: EvaluationSuite, attempts: Sequence[Attempt], split: str) -> dict[str, Any]:
    if split not in ("train", "heldout", "sealed"):
        raise EvaluationError("split must be train, heldout, or sealed")
    task_ids = getattr(suite, split + "_task_ids")
    relevant = [a for a in attempts if a.candidate_id == candidate.candidate_id and a.task_id in task_ids]
    all_seen_ids = [a.attempt_id for a in relevant]
    if len(set(all_seen_ids)) != len(all_seen_ids):
        raise EvaluationError("duplicate attemptId for candidate/split")
    by_task: dict[str, list[Attempt]] = {task_id: [] for task_id in task_ids}
    for attempt in relevant:
        if attempt.evaluator_id != suite.evaluator_id or attempt.evaluator_version != suite.evaluator_version:
            raise EvaluationError("attempt evaluator identity does not match suite")
        by_task[attempt.task_id].append(attempt)
    finals: list[Attempt | None] = []
    task_latency: list[float | None] = []
    accepted_bits: list[int | None] = []
    task_costs: list[int | None] = []
    task_known_costs: list[int] = []
    unknown_costs_by_task: list[int] = []
    policy_by_task: list[int] = []
    final_statuses: list[str | None] = []
    final_accepted: list[bool | None] = []
    final_quality: list[float | None] = []
    quality_sum = 0.0
    quality_count = 0
    policy_count = 0
    unknown_cost_attempts = 0
    total_cost = 0
    attempt_count = 0
    attempts_per_task: dict[str, int] = {}
    for task_id in task_ids:
        rows = sorted(by_task[task_id], key=lambda a: (a.attempt_index, a.attempt_id))
        if len(rows) > suite.max_attempts_per_task:
            raise EvaluationError("task %s exceeds maxAttemptsPerTask" % task_id)
        if [a.attempt_index for a in rows] != list(range(1, len(rows) + 1)):
            raise EvaluationError("attempt indexes must be contiguous from 1 per candidate/task")
        attempts_per_task[task_id] = len(rows)
        finals.append(rows[-1] if rows else None)
        final_statuses.append(rows[-1].status if rows else None)
        final_accepted.append(rows[-1].accepted if rows else None)
        final_quality.append(rows[-1].quality_score if rows else None)
        task_latency.append(sum(a.elapsed_ms for a in rows) if rows else None)
        task_cost = 0
        task_cost_known = bool(rows)
        unknown_for_task = 0
        policy_for_task = 0
        attempt_count += len(rows)
        for row in rows:
            if row.actual_cost_microusd is None:
                unknown_cost_attempts += 1
                task_cost_known = False
                unknown_for_task += 1
            else:
                total_cost += row.actual_cost_microusd
                task_cost += row.actual_cost_microusd
            policy_count += row.policy_violations
            policy_for_task += row.policy_violations
            if row.quality_score is not None:
                quality_sum += row.quality_score
                quality_count += 1
        task_known_costs.append(task_cost)
        unknown_costs_by_task.append(unknown_for_task)
        policy_by_task.append(policy_for_task)
        task_costs.append(task_cost if task_cost_known else None)
    for final in finals:
        if final is None:
            accepted_bits.append(None)
        else:
            accepted = bool(final.status == "succeeded" and final.accepted is True
                            and final.quality_score is not None and final.quality_score >= suite.quality_floor)
            accepted_bits.append(1 if accepted else 0)
    n = len(task_ids)
    accepted_count = sum(bit == 1 for bit in accepted_bits)
    missing_task_count = sum(bit is None for bit in accepted_bits)
    complete = missing_task_count == 0
    known_latencies = [value for value in task_latency if value is not None]
    sorted_latencies = sorted(known_latencies)
    p95_index = max(0, math.ceil(0.95 * n) - 1)
    success_rate = accepted_count / n if complete else None
    cost_per_accepted = (total_cost / accepted_count if complete and accepted_count and unknown_cost_attempts == 0 else None)
    gate_alpha = suite.confidence_alpha / 6.0
    if complete:
        accepted_rate_lower, accepted_rate_upper = _bounded_mean_interval(
            [float(bit) for bit in accepted_bits if bit is not None], 0.0, 1.0, gate_alpha)
    else:
        accepted_rate_lower, accepted_rate_upper = None, None
    cap = suite.max_cost_microusd_per_task
    cost_cap_exceeded = sum(value is not None and cap is not None and value > cap for value in task_costs)
    cost_mean_lower = cost_mean_upper = None
    cpa_lower = cpa_upper = None
    if complete and unknown_cost_attempts == 0 and cap is not None:
        cost_mean_lower, cost_mean_upper = _bounded_mean_interval(
            [float(value) for value in task_costs if value is not None], 0.0, float(cap), gate_alpha)
        if accepted_rate_upper and accepted_rate_lower is not None and accepted_rate_lower > 0:
            cpa_upper = cost_mean_upper / accepted_rate_lower
        if accepted_rate_upper and cost_mean_lower is not None:
            cpa_lower = cost_mean_lower / accepted_rate_upper
    reasons = []
    if missing_task_count:
        reasons.append("missing_task_attempts")
    if unknown_cost_attempts:
        reasons.append("unknown_actual_cost")
    if cap is None or not suite.cost_cap_enforcement_id:
        reasons.append("missing_enforced_cost_cap")
    if cost_cap_exceeded:
        reasons.append("task_cost_cap_exceeded")
    if policy_count > suite.max_policy_violations:
        reasons.append("policy_violation_limit_exceeded")
    if complete and sorted_latencies[p95_index] > suite.max_latency_ms:
        reasons.append("p95_task_latency_exceeded")
    if not complete or accepted_rate_lower is None or accepted_rate_lower < suite.quality_floor:
        reasons.append("quality_floor_not_met_with_uncertainty")
    return {
        "candidate": candidate.to_dict(), "suite": suite.to_dict(), "split": split,
        "taskCount": n, "attemptCount": attempt_count, "attemptsPerTask": attempts_per_task,
        "acceptedCount": accepted_count, "acceptedRate": success_rate,
        "acceptedRateLowerBound": accepted_rate_lower,
        "acceptedRateUpperBound": accepted_rate_upper,
        "meanQualityAcrossScoredAttempts": quality_sum / quality_count if quality_count else None,
        "scoredAttemptCount": quality_count, "policyViolations": policy_count,
        "p95TaskLatencyMs": sorted_latencies[p95_index] if complete and sorted_latencies else None,
        "maxTaskLatencyMs": max(sorted_latencies) if complete and sorted_latencies else None,
        "missingTaskAttemptCount": missing_task_count,
        "knownActualCostMicrousd": total_cost, "unknownCostAttemptCount": unknown_cost_attempts,
        "costPerAcceptedMicrousd": cost_per_accepted,
        "costCapMicrousdPerTask": cap, "costCapEnforcementId": suite.cost_cap_enforcement_id,
        "costCapExceededTaskCount": cost_cap_exceeded,
        "taskCostMicrousd": {task_id: task_known_costs[i] if unknown_costs_by_task[i] == 0 else None
                              for i, task_id in enumerate(task_ids)},
        "knownTaskCostMicrousd": {task_id: task_known_costs[i] for i, task_id in enumerate(task_ids)},
        "unknownCostAttemptsByTask": {task_id: unknown_costs_by_task[i] for i, task_id in enumerate(task_ids)},
        "taskLatencyMs": {task_id: task_latency[i] for i, task_id in enumerate(task_ids)},
        "taskPolicyViolations": {task_id: policy_by_task[i] for i, task_id in enumerate(task_ids)},
        "taskFinalStatus": {task_id: final_statuses[i] for i, task_id in enumerate(task_ids)},
        "taskFinalAccepted": {task_id: final_accepted[i] for i, task_id in enumerate(task_ids)},
        "taskFinalQualityScore": {task_id: final_quality[i] for i, task_id in enumerate(task_ids)},
        "meanCostPerTaskLowerBoundMicrousd": cost_mean_lower,
        "meanCostPerTaskUpperBoundMicrousd": cost_mean_upper,
        "costPerAcceptedMicrousdLowerBound": cpa_lower,
        "costPerAcceptedMicrousdUpperBound": cpa_upper,
        "hardGatesPassed": not reasons, "gateFailures": reasons,
        "taskOutcomes": {task_id: accepted_bits[i] for i, task_id in enumerate(task_ids)},
    }


def _validate_heldout_report(report: Mapping[str, Any], suite: EvaluationSuite) -> None:
    """Reject malformed/tampered summary mappings before they enter a gate."""
    if not isinstance(report, Mapping) or report.get("split") != "heldout" or report.get("suite") != suite.to_dict():
        raise EvaluationError("promotion requires a held-out report for the exact suite")
    raw_candidate = report.get("candidate")
    if not isinstance(raw_candidate, Mapping):
        raise EvaluationError("held-out report is missing candidate identity")
    candidate = Candidate.from_dict(raw_candidate)
    if raw_candidate.get("configSha256") != candidate.config_sha256:
        raise EvaluationError("candidate configuration hash does not match report")
    if (report.get("costCapMicrousdPerTask") != suite.max_cost_microusd_per_task
            or report.get("costCapEnforcementId") != suite.cost_cap_enforcement_id):
        raise EvaluationError("held-out report cost-cap provenance does not match suite")
    task_ids = suite.heldout_task_ids
    maps = ("taskOutcomes", "attemptsPerTask", "taskCostMicrousd", "knownTaskCostMicrousd",
            "unknownCostAttemptsByTask", "taskLatencyMs", "taskPolicyViolations",
            "taskFinalStatus", "taskFinalAccepted", "taskFinalQualityScore")
    for field in maps:
        value = report.get(field)
        if not isinstance(value, Mapping) or list(value) != list(task_ids):
            raise EvaluationError("held-out report %s does not cover the exact ordered task set" % field)
    outcomes = report["taskOutcomes"]
    attempt_counts = report["attemptsPerTask"]
    unknown_by_task = report["unknownCostAttemptsByTask"]
    known_by_task = report["knownTaskCostMicrousd"]
    cost_by_task = report["taskCostMicrousd"]
    latency_by_task = report["taskLatencyMs"]
    policy_by_task = report["taskPolicyViolations"]
    statuses = report["taskFinalStatus"]
    final_accepted = report["taskFinalAccepted"]
    final_quality = report["taskFinalQualityScore"]
    accepted_bits: list[int] = []
    latency_values: list[float] = []
    total_attempts = total_unknown = total_known_cost = total_policy = 0
    exceeded = 0
    for task_id in task_ids:
        attempts_n = attempt_counts[task_id]
        if type(attempts_n) is not int or not 1 <= attempts_n <= suite.max_attempts_per_task:
            raise EvaluationError("held-out report contains incomplete attempt coverage")
        unknown_n = unknown_by_task[task_id]
        known_cost = known_by_task[task_id]
        if type(unknown_n) is not int or unknown_n < 0 or unknown_n > attempts_n:
            raise EvaluationError("held-out report has invalid unknown-cost attempt count")
        if type(known_cost) is not int or known_cost < 0:
            raise EvaluationError("held-out report has invalid known task cost")
        total_attempts += attempts_n
        total_unknown += unknown_n
        total_known_cost += known_cost
        if cost_by_task[task_id] != (None if unknown_n else known_cost):
            raise EvaluationError("held-out report task cost does not reconcile")
        if suite.max_cost_microusd_per_task is not None and not unknown_n and known_cost > suite.max_cost_microusd_per_task:
            exceeded += 1
        latency = _finite_number(latency_by_task[task_id], "task latency", low=0)
        latency_values.append(latency)
        policy = policy_by_task[task_id]
        if isinstance(policy, bool) or not isinstance(policy, int) or policy < 0:
            raise EvaluationError("held-out report has invalid task policy violations")
        total_policy += policy
        status = statuses[task_id]
        accepted_flag = final_accepted[task_id]
        quality = final_quality[task_id]
        if status not in ("succeeded", "failed", "timed_out", "cancelled"):
            raise EvaluationError("held-out report has invalid final attempt status")
        if accepted_flag is not None and not isinstance(accepted_flag, bool):
            raise EvaluationError("held-out report has invalid final acceptance value")
        if quality is not None:
            quality = _finite_number(quality, "final quality score", low=0, high=1)
        expected = int(status == "succeeded" and accepted_flag is True and quality is not None
                       and quality >= suite.quality_floor)
        bit = outcomes[task_id]
        if type(bit) is not int or bit not in (0, 1) or bit != expected:
            raise EvaluationError("held-out report task outcomes do not reconcile")
        accepted_bits.append(bit)
    if type(report.get("taskCount")) is not int or report.get("taskCount") != len(task_ids) or type(report.get("missingTaskAttemptCount")) is not int or report.get("missingTaskAttemptCount") != 0:
        raise EvaluationError("held-out report task coverage is incomplete")
    if type(report.get("attemptCount")) is not int or report.get("attemptCount") != total_attempts:
        raise EvaluationError("held-out report attempt count does not reconcile")
    if type(report.get("unknownCostAttemptCount")) is not int or report.get("unknownCostAttemptCount") != total_unknown or type(report.get("knownActualCostMicrousd")) is not int or report.get("knownActualCostMicrousd") != total_known_cost:
        raise EvaluationError("held-out report spend does not reconcile")
    if type(report.get("policyViolations")) is not int or report.get("policyViolations") != total_policy or type(report.get("costCapExceededTaskCount")) is not int or report.get("costCapExceededTaskCount") != exceeded:
        raise EvaluationError("held-out report policy/cap totals do not reconcile")
    ordered_latency = sorted(latency_values)
    p95 = ordered_latency[max(0, math.ceil(0.95 * len(ordered_latency)) - 1)]
    if report.get("p95TaskLatencyMs") != p95 or report.get("maxTaskLatencyMs") != max(ordered_latency):
        raise EvaluationError("held-out report latency statistics do not reconcile")
    successes = sum(accepted_bits)
    success_rate = successes / len(task_ids)
    alpha = suite.confidence_alpha / 6.0
    success_lower, success_upper = _bounded_mean_interval([float(v) for v in accepted_bits], 0.0, 1.0, alpha)
    cap = suite.max_cost_microusd_per_task
    mean_cost_lower = mean_cost_upper = cpa_lower = cpa_upper = None
    if total_unknown == 0 and cap is not None:
        costs = [float(known_by_task[t]) for t in task_ids]
        mean_cost_lower, mean_cost_upper = _bounded_mean_interval(costs, 0.0, float(cap), alpha)
        if success_lower > 0:
            cpa_upper = mean_cost_upper / success_lower
        if success_upper > 0:
            cpa_lower = mean_cost_lower / success_upper
    expected_values = {
        "acceptedCount": successes, "acceptedRate": success_rate,
        "acceptedRateLowerBound": success_lower, "acceptedRateUpperBound": success_upper,
        "costPerAcceptedMicrousd": total_known_cost / successes if successes and total_unknown == 0 else None,
        "meanCostPerTaskLowerBoundMicrousd": mean_cost_lower,
        "meanCostPerTaskUpperBoundMicrousd": mean_cost_upper,
        "costPerAcceptedMicrousdLowerBound": cpa_lower,
        "costPerAcceptedMicrousdUpperBound": cpa_upper,
    }
    for field, expected_value in expected_values.items():
        actual = report.get(field)
        if type(expected_value) is int:
            if type(actual) is not int or actual != expected_value:
                raise EvaluationError("held-out report %s does not reconcile" % field)
        elif isinstance(expected_value, float):
            if not isinstance(actual, (int, float)) or isinstance(actual, bool) or not math.isclose(actual, expected_value, rel_tol=1e-12, abs_tol=1e-9):
                raise EvaluationError("held-out report %s does not reconcile" % field)
        elif actual != expected_value:
            raise EvaluationError("held-out report %s does not reconcile" % field)
    reasons = []
    if total_unknown:
        reasons.append("unknown_actual_cost")
    if cap is None or not suite.cost_cap_enforcement_id:
        reasons.append("missing_enforced_cost_cap")
    if exceeded:
        reasons.append("task_cost_cap_exceeded")
    if total_policy > suite.max_policy_violations:
        reasons.append("policy_violation_limit_exceeded")
    if p95 > suite.max_latency_ms:
        reasons.append("p95_task_latency_exceeded")
    if success_lower < suite.quality_floor:
        reasons.append("quality_floor_not_met_with_uncertainty")
    if report.get("gateFailures") != reasons or report.get("hardGatesPassed") is not (not reasons):
        raise EvaluationError("held-out report hard-gate summary does not reconcile")


def compare_candidates(baseline: Mapping[str, Any], candidate: Mapping[str, Any], suite: EvaluationSuite) -> dict[str, Any]:
    _validate_heldout_report(baseline, suite)
    _validate_heldout_report(candidate, suite)
    if baseline.get("split") != "heldout" or candidate.get("split") != "heldout":
        raise EvaluationError("promotion comparison must use held-out reports only")
    if baseline.get("suite") != suite.to_dict() or candidate.get("suite") != suite.to_dict():
        raise EvaluationError("reports must have identical suite/taskset/evaluator identity")
    base_id = baseline["candidate"]["candidateId"]
    cand_id = candidate["candidate"]["candidateId"]
    base_outcomes = baseline.get("taskOutcomes", {})
    cand_outcomes = candidate.get("taskOutcomes", {})
    if list(base_outcomes) != list(suite.heldout_task_ids) or list(cand_outcomes) != list(suite.heldout_task_ids):
        raise EvaluationError("held-out reports must cover the exact ordered task set")
    if baseline.get("missingTaskAttemptCount", 0) or candidate.get("missingTaskAttemptCount", 0):
        raise EvaluationError("held-out reports are incomplete; every task needs an attempt")
    paired = _paired_difference_interval([base_outcomes[t] for t in suite.heldout_task_ids],
                                         [cand_outcomes[t] for t in suite.heldout_task_ids],
                                         suite.confidence_alpha / 6.0)
    failures = []
    if cand_id == base_id:
        failures.append("candidate_is_baseline")
    if not candidate.get("hardGatesPassed"):
        failures.extend(candidate.get("gateFailures", []))
    if baseline.get("unknownCostAttemptCount", 0) or candidate.get("unknownCostAttemptCount", 0):
        failures.append("unknown_cost_blocks_promotion")
    if (suite.max_cost_microusd_per_task is None or not suite.cost_cap_enforcement_id
            or baseline.get("costCapExceededTaskCount", 0) or candidate.get("costCapExceededTaskCount", 0)):
        failures.append("enforced_cost_cap_missing_or_exceeded")
    # Non-inferiority: upper confidence evidence must rule out an accepted-rate drop
    # larger than 2 percentage points. This margin is versioned in the decision output.
    noninferiority_margin = suite.max_accept_rate_regression
    if paired["lower"] < -noninferiority_margin:
        failures.append("heldout_quality_noninferiority_not_established")
    base_cpa = baseline.get("costPerAcceptedMicrousdLowerBound")
    candidate_cpa = candidate.get("costPerAcceptedMicrousdUpperBound")
    if base_cpa is None or candidate_cpa is None:
        failures.append("cost_per_accepted_outcome_uncertainty_unavailable")
    elif candidate_cpa >= base_cpa:
        failures.append("cost_per_accepted_outcome_improvement_not_established")
    return {
        "baselineCandidateId": base_id, "candidateId": cand_id, "split": "heldout",
        "pairedAcceptedRateDifference": paired, "noninferiorityMargin": noninferiority_margin,
        "baselineCostPerAcceptedMicrousdLowerBound": base_cpa,
        "candidateCostPerAcceptedMicrousdUpperBound": candidate_cpa,
        "promote": not failures, "failures": failures,
        "sealedSetUsedForSelection": False,
        "note": "This gate compares supplied evaluator results; it does not establish external validity.",
    }


def evaluate(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Evaluate candidate attempts by split and select using training only.

    Input is inert JSON: {suite, candidates, attempts, baselineCandidateId}.
    The selected candidate minimizes the training cost-per-accepted upper bound
    among candidates passing training hard gates. Sealed attempts are ignored and
    no sealed scores are returned by this call.
    """
    if not isinstance(payload, Mapping):
        raise EvaluationError("payload must be an object")
    suite = EvaluationSuite.from_dict(payload.get("suite", {}))
    candidates_raw = payload.get("candidates")
    attempts_raw = payload.get("attempts")
    if not isinstance(candidates_raw, list) or not 2 <= len(candidates_raw) <= 32:
        raise EvaluationError("candidates must contain 2 to 32 candidate objects")
    if not isinstance(attempts_raw, list) or len(attempts_raw) > 20_000:
        raise EvaluationError("attempts must be a list of at most 20,000 records")
    candidates = [Candidate.from_dict(c) for c in candidates_raw]
    if len({c.candidate_id for c in candidates}) != len(candidates):
        raise EvaluationError("candidate IDs must be unique")
    attempts = [Attempt.from_dict(a) for a in attempts_raw]
    if len({a.attempt_id for a in attempts}) != len(attempts):
        raise EvaluationError("attemptId values must be globally unique")
    candidate_ids = {c.candidate_id for c in candidates}
    all_task_ids = set(suite.train_task_ids + suite.heldout_task_ids + suite.sealed_task_ids)
    if any(a.candidate_id not in candidate_ids or a.task_id not in all_task_ids for a in attempts):
        raise EvaluationError("attempt references unknown candidate or task")
    baseline_id = _required_text(payload.get("baselineCandidateId"), "baselineCandidateId")
    if baseline_id not in candidate_ids:
        raise EvaluationError("baselineCandidateId does not exist")
    reports = {c.candidate_id: {split: evaluate_candidate(c, suite, attempts, split)
                                for split in ("train", "heldout")} for c in candidates}
    train_eligible = [c for c in candidates if c.candidate_id != baseline_id
                      and reports[c.candidate_id]["train"]["hardGatesPassed"]
                      and reports[c.candidate_id]["train"]["costPerAcceptedMicrousdUpperBound"] is not None]
    selected = min(train_eligible, key=lambda c: (reports[c.candidate_id]["train"]["costPerAcceptedMicrousdUpperBound"], c.candidate_id)) if train_eligible else None
    decision = None
    if selected is not None and selected.candidate_id != baseline_id:
        baseline_heldout = reports[baseline_id]["heldout"]
        candidate_heldout = reports[selected.candidate_id]["heldout"]
        if baseline_heldout["missingTaskAttemptCount"] or candidate_heldout["missingTaskAttemptCount"]:
            decision = {
                "baselineCandidateId": baseline_id, "candidateId": selected.candidate_id,
                "split": "heldout", "pairedAcceptedRateDifference": None,
                "noninferiorityMargin": suite.max_accept_rate_regression,
                "baselineCostPerAcceptedMicrousdLowerBound": baseline_heldout["costPerAcceptedMicrousdLowerBound"],
                "candidateCostPerAcceptedMicrousdUpperBound": candidate_heldout["costPerAcceptedMicrousdUpperBound"],
                "promote": False, "failures": ["incomplete_heldout_evidence"],
                "sealedSetUsedForSelection": False,
            }
        else:
            decision = compare_candidates(baseline_heldout, candidate_heldout, suite)
    else:
        decision = {"promote": False, "failures": ["no_train_eligible_candidate" if selected is None else "training_selection_is_baseline"],
                    "sealedSetUsedForSelection": False}
    return {
        "evaluationProtocol": "paired-heldout-v1", "suite": suite.to_dict(),
        "candidateReports": reports,
        "trainingSelection": {"selectedCandidateId": selected.candidate_id if selected else None,
                              "selectionSplit": "train", "sealedSetUsedForSelection": False},
        "promotionDecision": decision,
        "sealedSet": {"taskCount": len(suite.sealed_task_ids), "status": "not_scored_or_returned_by_this_call"},
    }
