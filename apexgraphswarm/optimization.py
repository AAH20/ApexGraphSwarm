"""Deterministic, bounded optimization helpers for ApexGraphSwarm.

These functions produce plans and recommendations only. They never execute
work, contact providers, inspect Git state, or infer prices/telemetry that were
not supplied by the caller.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

MAX_TASKS = 500
MAX_OPTIONS = 2_000
MAX_EVIDENCE_ITEMS = 500
MAX_CLAIMS = 2_000
MAX_FILES_PER_TASK = 500
MAX_TELEMETRY_SAMPLES = 10_000
MAX_EXACT_SCHEDULE_TASKS = 8
MAX_EXACT_COVERAGE_ITEMS = 18
MAX_EXACT_SCHEDULE_COMBINATIONS = 65_536
MAX_EXACT_SCHEDULE_NODES = 200_000


class OptimizationInputError(ValueError):
    """Input is malformed or outside documented resource bounds."""


def _id(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 128 or "\x00" in value:
        raise OptimizationInputError(f"{label} must be a non-empty string of at most 128 characters")
    return value


def _finite_nonnegative(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        raise OptimizationInputError(f"{label} must be finite and non-negative")
    try:
        numeric = float(value)
    except (OverflowError, ValueError):
        raise OptimizationInputError(f"{label} must be finite and non-negative") from None
    if not math.isfinite(numeric):
        raise OptimizationInputError(f"{label} must be finite and non-negative")
    return numeric


def _nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0 or value > 2**63 - 1:
        raise OptimizationInputError(f"{label} must be a non-negative integer in signed 64-bit range")
    return value


@dataclass(frozen=True)
class ModelOption:
    model: str
    estimated_cost_microusd: int | None
    duration_estimate: float
    eligible: bool = True


@dataclass(frozen=True)
class DagTask:
    id: str
    dependencies: tuple[str, ...] = ()
    duration_estimate: float = 0.0
    options: tuple[ModelOption, ...] = ()
    deadline: float | None = None


@dataclass(frozen=True)
class ScheduledTask:
    task_id: str
    model: str
    start: float
    finish: float
    cost_microusd: int


@dataclass(frozen=True)
class ScheduleResult:
    status: str
    feasible: bool | None
    assignments: tuple[ScheduledTask, ...]
    total_cost_microusd: int | None
    makespan: float | None
    algorithm: str
    exact: bool
    limits: tuple[str, ...]


def _topological(tasks: Sequence[DagTask]) -> tuple[DagTask, ...]:
    by_id = {task.id: task for task in tasks}
    if len(by_id) != len(tasks):
        raise OptimizationInputError("task ids must be unique")
    for task in tasks:
        if len(set(task.dependencies)) != len(task.dependencies):
            raise OptimizationInputError(f"task {task.id!r} has duplicate dependencies")
        missing = set(task.dependencies) - by_id.keys()
        if missing:
            raise OptimizationInputError(f"task {task.id!r} has missing dependencies: {sorted(missing)!r}")
        if task.id in task.dependencies:
            raise OptimizationInputError(f"task {task.id!r} depends on itself")
    indegree = {task.id: len(task.dependencies) for task in tasks}
    children = {task.id: [] for task in tasks}
    for task in tasks:
        for parent in task.dependencies:
            children[parent].append(task.id)
    ready = sorted(key for key, degree in indegree.items() if degree == 0)
    ordered: list[DagTask] = []
    while ready:
        current = ready.pop(0)
        ordered.append(by_id[current])
        for child in sorted(children[current]):
            indegree[child] -= 1
            if indegree[child] == 0:
                ready.append(child)
                ready.sort()
    if len(ordered) != len(tasks):
        raise OptimizationInputError("task dependencies contain a cycle")
    return tuple(ordered)


def _validate_dag(tasks: Sequence[DagTask], model_options: Sequence[ModelOption], budget: int,
                  capacities: Mapping[str, int], deadline: float | None) -> tuple[DagTask, ...]:
    if not isinstance(tasks, (tuple, list)) or len(tasks) > MAX_TASKS:
        raise OptimizationInputError(f"tasks must be a list or tuple with at most {MAX_TASKS} entries")
    _nonnegative_int(budget, "budget_microusd")
    if deadline is not None:
        _finite_nonnegative(deadline, "deadline_seconds")
    if not isinstance(capacities, Mapping) or len(capacities) > 256:
        raise OptimizationInputError("capacities must be a mapping with at most 256 models")
    clean_caps: dict[str, int] = {}
    for model, capacity in capacities.items():
        checked_capacity = _nonnegative_int(capacity, "model capacity")
        if checked_capacity > MAX_TASKS:
            raise OptimizationInputError(f"model capacity cannot exceed {MAX_TASKS}")
        clean_caps[_id(model, "capacity model")] = checked_capacity
    if not isinstance(model_options, (tuple, list)) or len(model_options) > MAX_OPTIONS:
        raise OptimizationInputError(f"model_options must be a list or tuple with at most {MAX_OPTIONS} entries")
    clean_tasks: list[DagTask] = []
    option_total = len(model_options)
    for raw in tasks:
        if not isinstance(raw, DagTask):
            raise OptimizationInputError("each task must be a DagTask")
        task_id = _id(raw.id, "task id")
        if not isinstance(raw.dependencies, (tuple, list)):
            raise OptimizationInputError(f"task {task_id!r} dependencies must be a list or tuple")
        deps = tuple(_id(v, "dependency id") for v in raw.dependencies)
        task_duration = _finite_nonnegative(raw.duration_estimate, f"task {task_id!r} duration_estimate")
        if raw.deadline is not None:
            _finite_nonnegative(raw.deadline, f"task {task_id!r} deadline")
        if not isinstance(raw.options, (tuple, list)):
            raise OptimizationInputError(f"task {task_id!r} options must be a list or tuple")
        opts: list[ModelOption] = []
        for option in raw.options:
            if not isinstance(option, ModelOption):
                raise OptimizationInputError("each model option must be a ModelOption")
            model = _id(option.model, "model name")
            cost = None if option.estimated_cost_microusd is None else _nonnegative_int(option.estimated_cost_microusd, "estimated_cost_microusd")
            duration = _finite_nonnegative(option.duration_estimate, "option duration_estimate")
            if type(option.eligible) is not bool:
                raise OptimizationInputError("eligible must be a bool")
            opts.append(ModelOption(model, cost, duration, option.eligible))
        option_total += len(opts)
        if option_total > MAX_OPTIONS:
            raise OptimizationInputError(f"total model options must not exceed {MAX_OPTIONS}")
        clean_tasks.append(DagTask(task_id, deps, task_duration, tuple(opts), raw.deadline))
    return _topological(clean_tasks)


def schedule_dag(tasks: Sequence[DagTask], *, budget_microusd: int,
                 capacities: Mapping[str, int], deadline_seconds: float | None = None,
                 model_options: Sequence[ModelOption] = (), exact_max_tasks: int = MAX_EXACT_SCHEDULE_TASKS) -> ScheduleResult:
    """Choose options and reserve model capacity for a DAG under hard limits.

    Exact enumerates option combinations only up to the fixed task/combination
    bounds. Larger problems use a deterministic lowest-cost/shortest-fit
    heuristic and return `unknown` rather than claiming infeasibility on failure.
    Options with unknown cost, ineligible flags, or zero model capacity cannot
    be assigned. Durations and deadlines are estimates supplied by the caller.
    """
    if type(exact_max_tasks) is not int or not 1 <= exact_max_tasks <= MAX_EXACT_SCHEDULE_TASKS:
        raise OptimizationInputError(f"exact_max_tasks must be from 1 to {MAX_EXACT_SCHEDULE_TASKS}")
    if not isinstance(model_options, (tuple, list)) or len(model_options) > MAX_OPTIONS:
        raise OptimizationInputError(f"model_options must be a list or tuple with at most {MAX_OPTIONS} entries")
    clean_global_options = []
    for option in model_options:
        if not isinstance(option, ModelOption):
            raise OptimizationInputError("each global model option must be a ModelOption")
        cost = None if option.estimated_cost_microusd is None else _nonnegative_int(option.estimated_cost_microusd, "estimated_cost_microusd")
        eligible = option.eligible
        if type(eligible) is not bool:
            raise OptimizationInputError("eligible must be a bool")
        clean_global_options.append(ModelOption(_id(option.model, "model name"), cost,
                                                _finite_nonnegative(option.duration_estimate, "option duration_estimate"), eligible))
    model_options = tuple(clean_global_options)
    ordered = _validate_dag(tasks, model_options, budget_microusd, capacities, deadline_seconds)
    if not ordered:
        return ScheduleResult("feasible", True, (), 0, 0.0, "exact-empty", True, ("empty DAG",))
    capacities = dict(capacities)
    candidates: dict[str, tuple[ModelOption, ...]] = {}
    unknown_cost = False
    for task in ordered:
        opts = list(task.options)
        if not opts:
            opts = [opt for opt in model_options if opt.eligible and (opt.estimated_cost_microusd is None or opt.estimated_cost_microusd <= budget_microusd)]
            opts = [ModelOption(opt.model, opt.estimated_cost_microusd, opt.duration_estimate, opt.eligible) for opt in opts]
        for option in opts:
            if option.estimated_cost_microusd is None and option.eligible and capacities.get(option.model, 0) > 0:
                unknown_cost = True
        candidates[task.id] = tuple(sorted((o for o in opts if o.eligible and o.estimated_cost_microusd is not None and capacities.get(o.model, 0) > 0),
                                             key=lambda o: (o.estimated_cost_microusd, o.duration_estimate, o.model)))
    max_serial_duration = sum(max((option.duration_estimate for option in candidates[task.id]), default=0.0)
                              for task in ordered)
    if not math.isfinite(max_serial_duration):
        raise OptimizationInputError("eligible duration estimates overflow their bounded schedule range")
    combo_count = 1
    for task in ordered:
        combo_count *= max(1, len(candidates[task.id]))
        if combo_count > MAX_EXACT_SCHEDULE_COMBINATIONS:
            break
    # Enumerate precedence-respecting task orders too: assignment-only search
    # can miss a better schedule when independent tasks share model capacity.
    max_choices = max((len(candidates[t.id]) for t in ordered), default=1)
    node_bound = sum((math.factorial(len(ordered)) // math.factorial(len(ordered) - depth)) * (max_choices ** depth)
                     for depth in range(len(ordered) + 1))
    exact = (len(ordered) <= exact_max_tasks and combo_count * math.factorial(len(ordered)) <= MAX_EXACT_SCHEDULE_COMBINATIONS
             and node_bound <= MAX_EXACT_SCHEDULE_NODES)

    def evaluate(chosen: Mapping[str, ModelOption]) -> tuple[tuple[object, ...], tuple[ScheduledTask, ...], int, float] | None:
        calendars: dict[str, list[float]] = {model: [0.0] * count for model, count in capacities.items()}
        finished: dict[str, float] = {}
        assigned: list[ScheduledTask] = []
        spend = 0
        for task in ordered:
            option = chosen[task.id]
            cost = option.estimated_cost_microusd
            assert cost is not None
            spend += cost
            if spend > budget_microusd:
                return None
            ready = max((finished[parent] for parent in task.dependencies), default=0.0)
            slots = calendars[option.model]
            slot_index = min(range(len(slots)), key=lambda i: (max(ready, slots[i]), i))
            start = max(ready, slots[slot_index])
            finish = start + option.duration_estimate
            due_candidates = [value for value in (task.deadline, deadline_seconds) if value is not None]
            if due_candidates and finish > min(due_candidates):
                return None
            slots[slot_index] = finish
            finished[task.id] = finish
            assigned.append(ScheduledTask(task.id, option.model, start, finish, cost))
        makespan = max(finished.values(), default=0.0)
        return ((makespan, spend, tuple((a.task_id, a.model) for a in assigned)), tuple(assigned), spend, makespan)

    best = None
    if exact:
        if all(candidates[task.id] for task in ordered):
            by_id = {task.id: task for task in ordered}
            def search(remaining: frozenset[str], finished: dict[str, float],
                       calendars: dict[str, list[float]], assigned: tuple[ScheduledTask, ...],
                       spend: int) -> None:
                nonlocal best
                if not remaining:
                    makespan = max(finished.values(), default=0.0)
                    key = (makespan, spend, tuple((a.task_id, a.model, a.start) for a in assigned))
                    result = (key, assigned, spend, makespan)
                    if best is None or key < best[0]:
                        best = result
                    return
                ready_ids = sorted(key for key in remaining if set(by_id[key].dependencies) <= finished.keys())
                for task_id in ready_ids:
                    task = by_id[task_id]
                    ready_at = max((finished[parent] for parent in task.dependencies), default=0.0)
                    for option in candidates[task_id]:
                        cost = option.estimated_cost_microusd
                        assert cost is not None
                        next_spend = spend + cost
                        if next_spend > budget_microusd:
                            continue
                        slots = calendars[option.model]
                        slot_index = min(range(len(slots)), key=lambda i: (max(ready_at, slots[i]), i))
                        start = max(ready_at, slots[slot_index])
                        finish = start + option.duration_estimate
                        due_candidates = [value for value in (task.deadline, deadline_seconds) if value is not None]
                        if due_candidates and finish > min(due_candidates):
                            continue
                        new_calendars = {model: list(times) for model, times in calendars.items()}
                        new_calendars[option.model][slot_index] = finish
                        new_finished = dict(finished)
                        new_finished[task_id] = finish
                        new_assignment = ScheduledTask(task_id, option.model, start, finish, cost)
                        search(remaining - {task_id}, new_finished, new_calendars,
                               assigned + (new_assignment,), next_spend)
            search(frozenset(by_id), {}, {model: [0.0] * count for model, count in capacities.items()}, (), 0)
    else:
        # Deterministic local assignment; then verify all hard constraints.
        chosen = {}
        for task in ordered:
            if not candidates[task.id]:
                break
            chosen[task.id] = candidates[task.id][0]
        if len(chosen) == len(ordered):
            best = evaluate(chosen)
    algorithm = "bounded-exhaustive" if exact else "deterministic-lowest-cost"
    limits = (f"exact search bounded by {exact_max_tasks} tasks, {MAX_EXACT_SCHEDULE_COMBINATIONS} leaves, and {MAX_EXACT_SCHEDULE_NODES} search nodes" if exact else "heuristic has no optimality or infeasibility guarantee", "costs are caller estimates; unknown costs are excluded", "durations and deadlines are estimates")
    if best:
        return ScheduleResult("feasible", True, best[1], best[2], best[3], algorithm, exact, limits)
    if exact:
        status = "unknown" if unknown_cost else "infeasible"
        feasible = None if unknown_cost else False
    else:
        status, feasible = "unknown", None
    return ScheduleResult(status, feasible, (), None, None, algorithm, exact, limits)


@dataclass(frozen=True)
class EvidenceItem:
    id: str
    claims: tuple[str, ...]
    token_cost: int
    weights: Mapping[str, float]


@dataclass(frozen=True)
class CoverageResult:
    selected_ids: tuple[str, ...]
    covered_claims: tuple[str, ...]
    weighted_coverage: float
    tokens_used: int
    algorithm: str
    exact: bool
    limits: tuple[str, ...]


def _validate_evidence(items: Sequence[EvidenceItem], token_budget: int) -> tuple[EvidenceItem, ...]:
    if not isinstance(items, (tuple, list)) or len(items) > MAX_EVIDENCE_ITEMS:
        raise OptimizationInputError(f"items must contain at most {MAX_EVIDENCE_ITEMS} EvidenceItem entries")
    _nonnegative_int(token_budget, "token_budget")
    normalized = []
    claim_names = set()
    seen_ids = set()
    for item in items:
        if not isinstance(item, EvidenceItem):
            raise OptimizationInputError("each item must be an EvidenceItem")
        item_id = _id(item.id, "evidence id")
        if item_id in seen_ids:
            raise OptimizationInputError("evidence ids must be unique")
        seen_ids.add(item_id)
        cost = _nonnegative_int(item.token_cost, "token_cost")
        if not isinstance(item.claims, (tuple, list)):
            raise OptimizationInputError("claims must be a list or tuple")
        claims = tuple(_id(c, "claim") for c in item.claims)
        if len(set(claims)) != len(claims):
            raise OptimizationInputError(f"evidence item {item_id!r} has duplicate claims")
        if not isinstance(item.weights, Mapping):
            raise OptimizationInputError("weights must be a mapping from claim to weight")
        weights = {}
        for claim, weight in item.weights.items():
            claim = _id(claim, "weighted claim")
            val = _finite_nonnegative(weight, "claim weight")
            weights[claim] = val
            claim_names.add(claim)
        claim_names.update(claims)
        normalized.append(EvidenceItem(item_id, claims, cost, weights))
    if len(claim_names) > MAX_CLAIMS:
        raise OptimizationInputError(f"at most {MAX_CLAIMS} distinct claims are supported")
    return tuple(sorted(normalized, key=lambda e: e.id))


def select_evidence(items: Sequence[EvidenceItem], *, token_budget: int,
                    exact_max_items: int = MAX_EXACT_COVERAGE_ITEMS) -> CoverageResult:
    """Select a token-bounded evidence set maximizing weighted unique coverage.

    A claim's weight is taken as the maximum supplied weight across all items
    that mention it, avoiding double-counting repeated evidence. Claims without
    weights have weight 1. Exact search is bounded to `exact_max_items`; the
    deterministic greedy baseline ranks marginal weighted coverage per token.
    """
    if type(exact_max_items) is not int or not 1 <= exact_max_items <= MAX_EXACT_COVERAGE_ITEMS:
        raise OptimizationInputError(f"exact_max_items must be from 1 to {MAX_EXACT_COVERAGE_ITEMS}")
    evidence = _validate_evidence(items, token_budget)
    universe = set(c for item in evidence for c in item.claims) | set(c for item in evidence for c in item.weights)
    weights = {c: max([item.weights.get(c, 1.0) for item in evidence if c in item.claims or c in item.weights], default=1.0) for c in universe}
    if not math.isfinite(sum(weights.values())):
        raise OptimizationInputError("aggregate claim weights exceed the finite coverage range")
    exact = len(evidence) <= exact_max_items

    def score(indices: Sequence[int]) -> tuple[float, int, tuple[str, ...], tuple[str, ...]]:
        selected = [evidence[i] for i in indices]
        claims = set(c for item in selected for c in item.claims)
        value = sum(weights[c] for c in claims)
        used = sum(item.token_cost for item in selected)
        ids = tuple(item.id for item in selected)
        return value, used, ids, tuple(sorted(claims))

    best = (0.0, 0, (), ())
    if exact:
        n = len(evidence)
        for mask in range(1 << n):
            chosen = tuple(i for i in range(n) if mask & (1 << i))
            used = sum(evidence[i].token_cost for i in chosen)
            if used > token_budget:
                continue
            candidate = score(chosen)
            # Maximize coverage, then minimize tokens, then lexicographic ids.
            if (candidate[0] > best[0] or
                    (candidate[0] == best[0] and (candidate[1] < best[1] or
                     (candidate[1] == best[1] and candidate[2] < best[2])))):
                best = candidate
        algorithm = "bounded-exhaustive"
    else:
        selected: list[int] = []
        remaining = set(range(len(evidence)))
        used = 0
        covered: set[str] = set()
        while remaining:
            choices = []
            for index in remaining:
                item = evidence[index]
                if used + item.token_cost > token_budget:
                    continue
                marginal = sum(weights[c] for c in set(item.claims) - covered)
                ratio = marginal / max(1, item.token_cost)
                choices.append((-ratio, -marginal, item.token_cost, item.id, index))
            if not choices:
                break
            _, marginal_neg, cost, _, index = min(choices)
            if -marginal_neg <= 0:
                break
            selected.append(index)
            remaining.remove(index)
            used += cost
            covered.update(evidence[index].claims)
        best = score(selected)
        algorithm = "deterministic-marginal-per-token-greedy"
    return CoverageResult(best[2], best[3], best[0], best[1], algorithm, exact,
                          (f"exact enumeration limited to {exact_max_items} items", "claim coverage is weighted set coverage; item synergies are not modeled"))


@dataclass(frozen=True)
class CodeTask:
    id: str
    dependencies: tuple[str, ...] = ()
    reads: tuple[str, ...] = ()
    writes: tuple[str, ...] = ()


@dataclass(frozen=True)
class FileConflict:
    first_task: str
    second_task: str
    files: tuple[str, ...]


@dataclass(frozen=True)
class WavePlan:
    status: str
    waves: tuple[tuple[str, ...], ...]
    conflicts: tuple[FileConflict, ...]
    algorithm: str
    limits: tuple[str, ...]


def plan_waves(tasks: Sequence[CodeTask]) -> WavePlan:
    """Plan conflict-free concurrent waves from declared paths and DAG edges.

    File conflicts add deterministic serialization edges in task-id order when
    dependencies do not already order the pair. This is a plan only: it does
    not inspect a checkout, run commands, or perform Git operations.
    """
    if not isinstance(tasks, (tuple, list)) or len(tasks) > MAX_TASKS:
        raise OptimizationInputError(f"tasks must contain at most {MAX_TASKS} CodeTask entries")
    by_id: dict[str, CodeTask] = {}
    for task in tasks:
        if not isinstance(task, CodeTask):
            raise OptimizationInputError("each task must be a CodeTask")
        task_id = _id(task.id, "task id")
        if task_id in by_id:
            raise OptimizationInputError("task ids must be unique")
        def paths(values: object, label: str) -> tuple[str, ...]:
            if not isinstance(values, (tuple, list)) or len(values) > MAX_FILES_PER_TASK:
                raise OptimizationInputError(f"{label} must have at most {MAX_FILES_PER_TASK} paths")
            raw_paths = tuple(_id(path, "file path") for path in values)
            out = tuple(_canonical_repo_path(path) for path in raw_paths)
            if len(set(out)) != len(out):
                raise OptimizationInputError(f"{label} contains duplicate or aliased paths")
            return out
        deps = paths(task.dependencies, f"task {task_id!r} dependencies")
        reads = paths(task.reads, f"task {task_id!r} reads")
        writes = paths(task.writes, f"task {task_id!r} writes")
        by_id[task_id] = CodeTask(task_id, deps, reads, writes)
    for task in by_id.values():
        missing = set(task.dependencies) - by_id.keys()
        if missing:
            raise OptimizationInputError(f"task {task.id!r} has missing dependencies: {sorted(missing)!r}")
        if task.id in task.dependencies:
            raise OptimizationInputError(f"task {task.id!r} depends on itself")
    edges: dict[str, set[str]] = {key: set(task.dependencies) for key, task in by_id.items()}

    def ancestors(task_id: str) -> set[str]:
        reached: set[str] = set()
        stack = list(edges[task_id])
        while stack:
            current = stack.pop()
            if current not in reached:
                reached.add(current)
                stack.extend(edges[current])
        return reached

    conflicts = []
    ids = sorted(by_id)
    for i, left_id in enumerate(ids):
        left = by_id[left_id]
        for right_id in ids[i + 1:]:
            right = by_id[right_id]
            shared = (set(left.writes) & (set(right.reads) | set(right.writes))) | (set(right.writes) & set(left.reads))
            if not shared:
                continue
            conflicts.append(FileConflict(left_id, right_id, tuple(sorted(shared))))
            if left_id in ancestors(right_id):
                continue
            if right_id in ancestors(left_id):
                continue
            # Choose a deterministic direction. Revalidate for cycles below.
            edges[right_id].add(left_id)
    # Kahn frontier layering: all nodes in a wave are dependency/file-disjoint.
    indegree = {key: len(deps) for key, deps in edges.items()}
    children = {key: [] for key in edges}
    for child, deps in edges.items():
        for dep in deps:
            children[dep].append(child)
    remaining = set(edges)
    waves: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(sorted(key for key in remaining if indegree[key] == 0))
        if not ready:
            raise OptimizationInputError("task dependencies and file conflicts contain a cycle")
        waves.append(ready)
        for key in ready:
            remaining.remove(key)
            for child in children[key]:
                indegree[child] -= 1
    return WavePlan("planned", tuple(waves), tuple(conflicts), "dependency-frontiers-with-file-serialization",
                    ("uses declared read/write paths only", "conflicting unordered tasks are serialized by task id", "plan only; no Git or command execution"))


@dataclass(frozen=True)
class TelemetrySample:
    concurrency: int
    throughput: float
    latency_seconds: float
    utilization: float
    queue_depth: int = 0


@dataclass(frozen=True)
class CapacityRecommendation:
    recommended_concurrency: int | None
    status: str
    basis: str
    measurements_used: int
    algorithm: str
    limits: tuple[str, ...]


def recommend_capacity(samples: Sequence[TelemetrySample], *, target_utilization: float = 0.75) -> CapacityRecommendation:
    """Recommend concurrency from caller-supplied measurements only.

    Selects the highest measured throughput point at or below target utilization,
    breaking ties toward lower latency and concurrency. If all observations are
    above target utilization, chooses the least loaded measured point as a
    conservative reference. This is descriptive, not a live capacity test.
    """
    if not isinstance(samples, (tuple, list)) or len(samples) > MAX_TELEMETRY_SAMPLES:
        raise OptimizationInputError(f"samples must contain at most {MAX_TELEMETRY_SAMPLES} TelemetrySample entries")
    target = _finite_nonnegative(target_utilization, "target_utilization")
    if target <= 0 or target > 1:
        raise OptimizationInputError("target_utilization must be greater than 0 and at most 1")
    clean = []
    for sample in samples:
        if not isinstance(sample, TelemetrySample):
            raise OptimizationInputError("each sample must be a TelemetrySample")
        if type(sample.concurrency) is not int or sample.concurrency < 1 or sample.concurrency > 100_000:
            raise OptimizationInputError("concurrency must be an integer from 1 to 100000")
        throughput = _finite_nonnegative(sample.throughput, "throughput")
        latency = _finite_nonnegative(sample.latency_seconds, "latency_seconds")
        utilization = _finite_nonnegative(sample.utilization, "utilization")
        if utilization > 1:
            raise OptimizationInputError("utilization must be from 0 to 1")
        queue = _nonnegative_int(sample.queue_depth, "queue_depth")
        clean.append(TelemetrySample(sample.concurrency, throughput, latency, utilization, queue))
    if not clean:
        return CapacityRecommendation(None, "insufficient_data", "no telemetry supplied", 0, "measured-point-selection", ("no live measurements or prices are fetched",))
    acceptable = [sample for sample in clean if sample.utilization <= target]
    if acceptable:
        chosen = min(acceptable, key=lambda s: (-s.throughput, s.latency_seconds, s.concurrency))
        basis = "highest observed throughput among points at or below target utilization"
    else:
        chosen = min(clean, key=lambda s: (s.utilization, s.latency_seconds, s.concurrency))
        basis = "lowest observed utilization because no point met target"
    return CapacityRecommendation(chosen.concurrency, "recommended", basis, len(clean), "measured-point-selection",
                                  ("based only on supplied measurements", "recommendation does not extrapolate beyond observed concurrency", "throughput and latency are measured values, not provider guarantees"))


def optimize(payload: Mapping[str, object]) -> dict[str, object]:
    """Strict JSON-compatible dispatcher for schedule/evidence/waves/capacity.

    See docs/optimization-engine.md for the version-1 payload schemas.
    """
    if not isinstance(payload, Mapping):
        raise OptimizationInputError("payload must be a mapping")
    action = payload.get("action")
    if action == "schedule":
        _keys(payload, {"action", "tasks", "model_options", "budget_microusd", "capacities", "deadline_seconds"})
        _required(payload, {"tasks", "budget_microusd", "capacities"}, "schedule payload")
        options = tuple(_json_option(o, "global model option") for o in _records(payload.get("model_options", ()), "model_options", MAX_OPTIONS))
        tasks = []
        for raw in _records(payload.get("tasks", ()), "tasks", MAX_TASKS):
            task = _record(raw, "task", {"id", "dependencies", "duration_estimate", "options", "deadline"}, {"id"})
            task_options = tuple(_json_option(o, "task model option") for o in _records(task.get("options", ()), "task options", MAX_OPTIONS))
            tasks.append(DagTask(task["id"], _sequence(task.get("dependencies", ()), "dependencies", MAX_TASKS), task.get("duration_estimate", 0.0), task_options, task.get("deadline")))
        return _asdict(schedule_dag(tasks, model_options=options, budget_microusd=payload["budget_microusd"], capacities=payload["capacities"], deadline_seconds=payload.get("deadline_seconds")))
    if action == "evidence":
        _keys(payload, {"action", "items", "token_budget"})
        _required(payload, {"items", "token_budget"}, "evidence payload")
        items = []
        for raw in _records(payload.get("items", ()), "items", MAX_EVIDENCE_ITEMS):
            item = _record(raw, "evidence item", {"id", "claims", "token_cost", "weights"}, {"id", "token_cost"})
            items.append(EvidenceItem(item["id"], _sequence(item.get("claims", ()), "claims", MAX_CLAIMS), item["token_cost"], item.get("weights", {})))
        return _asdict(select_evidence(items, token_budget=payload["token_budget"]))
    if action == "waves":
        _keys(payload, {"action", "tasks"})
        _required(payload, {"tasks"}, "waves payload")
        tasks = []
        for raw in _records(payload.get("tasks", ()), "tasks", MAX_TASKS):
            task = _record(raw, "coding task", {"id", "dependencies", "reads", "writes"}, {"id"})
            tasks.append(CodeTask(task["id"], _sequence(task.get("dependencies", ()), "dependencies", MAX_TASKS), _sequence(task.get("reads", ()), "reads", MAX_FILES_PER_TASK), _sequence(task.get("writes", ()), "writes", MAX_FILES_PER_TASK)))
        return _asdict(plan_waves(tasks))
    if action == "capacity":
        _keys(payload, {"action", "samples", "target_utilization"})
        _required(payload, {"samples"}, "capacity payload")
        samples = []
        for raw in _records(payload.get("samples", ()), "samples", MAX_TELEMETRY_SAMPLES):
            sample = _record(raw, "telemetry sample", {"concurrency", "throughput", "latency_seconds", "utilization", "queue_depth"}, {"concurrency", "throughput", "latency_seconds", "utilization"})
            samples.append(TelemetrySample(sample["concurrency"], sample["throughput"], sample["latency_seconds"], sample["utilization"], sample.get("queue_depth", 0)))
        return _asdict(recommend_capacity(samples, target_utilization=payload.get("target_utilization", 0.75)))
    raise OptimizationInputError("action must be one of: schedule, evidence, waves, capacity")


def _keys(payload: Mapping[str, object], allowed: set[str]) -> None:
    extra = set(payload) - allowed
    if extra:
        raise OptimizationInputError(f"unexpected fields: {sorted(extra)!r}")


def _required(payload: Mapping[str, object], required: set[str], label: str) -> None:
    missing = required - set(payload)
    if missing:
        raise OptimizationInputError(f"{label} is missing required fields: {sorted(missing)!r}")


def _canonical_repo_path(value: str) -> str:
    """Normalize lexical path aliases without consulting the filesystem."""
    path = value.replace("\\", "/")
    if path.startswith("/") or (len(path) >= 2 and path[1] == ":"):
        raise OptimizationInputError("declared file paths must be relative repository paths")
    parts: list[str] = []
    for part in path.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                raise OptimizationInputError("declared file path cannot escape the repository root")
            parts.pop()
        else:
            parts.append(part)
    if not parts:
        raise OptimizationInputError("declared file path must name a repository file")
    return "/".join(parts)


def _record(value: object, label: str, allowed: set[str], required: set[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise OptimizationInputError(f"{label} must be a mapping")
    _keys(value, allowed)
    missing = required - set(value)
    if missing:
        raise OptimizationInputError(f"{label} is missing required fields: {sorted(missing)!r}")
    return value


def _records(values: object, label: str, maximum: int) -> tuple[object, ...]:
    if not isinstance(values, (list, tuple)) or len(values) > maximum:
        raise OptimizationInputError(f"{label} must be a list with at most {maximum} entries")
    return tuple(values)


def _sequence(values: object, label: str, maximum: int) -> tuple[object, ...]:
    if not isinstance(values, (list, tuple)) or len(values) > maximum:
        raise OptimizationInputError(f"{label} must be a list with at most {maximum} entries")
    return tuple(values)


def _json_option(raw: object, label: str) -> ModelOption:
    option = _record(raw, label, {"model", "estimated_cost_microusd", "duration_estimate", "eligible"}, {"model", "duration_estimate"})
    return ModelOption(option["model"], option.get("estimated_cost_microusd"), option["duration_estimate"], option.get("eligible", True))


def _asdict(value: object) -> dict[str, object]:
    from dataclasses import asdict
    return asdict(value)
