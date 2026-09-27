"""Bounded local evolution of named algorithm configurations on synthetic fixtures.

This module runs a fixed weighted-max-coverage greedy implementation with a
small supported exponent grid. It is configuration search, not code generation.
No arbitrary code, provider, network, repository, or promotion side effect is
executed. Fixture objective scores are synthetic and monetary cost stays unknown.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import time
from typing import Any, Mapping, Sequence

from .evaluation import Attempt, Candidate, EvaluationError, EvaluationSuite, compare_candidates, evaluate_candidate

PROTOCOL = "bounded-config-evolution-v1"
GENERATOR_VERSION = "weighted-max-coverage-fixture-v1"
ALGORITHM_VERSION = "weighted-coverage-greedy-v1"
MAX_ITEMS = 14
MAX_CLAIMS = 16
MAX_TRAIN = 12
MAX_HELDOUT = 12
MAX_SEALED = 12
MAX_CANDIDATES = 4
MAX_EXACT_WORK = 4_200_000
MAX_TOKEN_BUDGET = 1000
SUPPORTED_EXPONENTS = (0.0, 0.5, 1.0, 1.5)
UINT64_MASK = (1 << 64) - 1


class EvolutionError(ValueError):
    """Invalid request or failed built-in candidate execution."""


@dataclass(frozen=True)
class _Item:
    item_id: str
    token_cost: int
    claim_mask: int


@dataclass(frozen=True)
class _Fixture:
    task_id: str
    split: str
    claim_weights: tuple[int, ...]
    items: tuple[_Item, ...]

    @property
    def token_units(self) -> int:
        return sum(item.token_cost for item in self.items)

    def canonical(self) -> dict[str, Any]:
        return {"taskId": self.task_id, "split": self.split,
                "claimWeights": list(self.claim_weights),
                "items": [{"id": item.item_id, "tokenCost": item.token_cost,
                           "claimMask": item.claim_mask} for item in self.items]}


def run_evolution(payload: Mapping[str, object]) -> dict[str, object]:
    """Generate fixture splits, execute a bounded candidate grid, and gate held-out results.

    The candidate is selected using only training objective ratios. Held-out
    results are compared afterwards with the repository's conservative gate.
    The sealed split is generated and hashed but never passed to a solver.
    """
    values = _validate_payload(payload)
    seed = values["seed"]
    counts = {"train": values["trainCount"], "heldout": values["heldoutCount"],
              "sealed": values["sealedCount"]}
    scored_count = counts["train"] + counts["heldout"]
    configs = _candidate_configs(values["costExponents"])
    work_components = _work_bound_components(
        train_count=counts["train"], heldout_count=counts["heldout"],
        item_count=values["itemsPerInstance"], claim_count=values["claimCount"],
        candidate_count=len(configs))
    work_bound = sum(work_components.values())
    if work_bound > MAX_EXACT_WORK:
        raise EvolutionError("bounded algorithm loop-work estimate exceeds the configured hard cap")

    fixtures = {split: tuple(_make_fixture(seed, split, index, values["itemsPerInstance"],
                                           values["claimCount"])
                             for index in range(count))
                for split, count in counts.items()}
    dataset_payload = {"generator": GENERATOR_VERSION, "seed": seed,
                       "itemsPerInstance": values["itemsPerInstance"],
                       "claimCount": values["claimCount"],
                       "splits": {split: [item.canonical() for item in fixtures[split]]
                                  for split in ("train", "heldout", "sealed")}}
    dataset_digest = _digest(dataset_payload)
    split_digests = {split: _digest([fixture.canonical() for fixture in fixtures[split]])
                     for split in ("train", "heldout", "sealed")}

    baseline_id = "baseline-density"
    candidates = [Candidate(candidate_id=config["candidateId"], version=ALGORITHM_VERSION,
                            config=config["config"]) for config in configs]
    by_candidate = {candidate.candidate_id: candidate for candidate in candidates}

    observations: dict[str, dict[str, list[dict[str, Any]]]] = {
        candidate.candidate_id: {"train": [], "heldout": []} for candidate in candidates
    }
    attempts: list[Attempt] = []
    oracle_by_task: dict[str, dict[str, Any]] = {}
    oracle_times: dict[str, float] = {}
    oracle_by_task, oracle_times = _solve_oracles(fixtures["train"], values["tokenBudget"])
    _run_split(candidates, fixtures["train"], "train", oracle_by_task, oracle_times,
               observations, attempts, values)

    # Selection is complete before held-out fixtures are sent to either solver.
    train_scores = {
        candidate.candidate_id: _mean(
            row["objectiveRatio"] for row in observations[candidate.candidate_id]["train"])
        for candidate in candidates
    }
    selected_id = min(train_scores, key=lambda candidate_id: (-train_scores[candidate_id], candidate_id))
    selection = {"candidateId": selected_id, "selectionSplit": "train",
                 "criterion": "mean_exact_oracle_objective_ratio",
                 "meanObjectiveRatioByCandidate": train_scores,
                 "sealedSetUsedForSelection": False}

    heldout_oracles, heldout_oracle_times = _solve_oracles(
        fixtures["heldout"], values["tokenBudget"])
    oracle_by_task.update(heldout_oracles)
    oracle_times.update(heldout_oracle_times)
    _run_split(candidates, fixtures["heldout"], "heldout", heldout_oracles,
               heldout_oracle_times, observations, attempts, values)

    suite = EvaluationSuite.from_dict({
        "suiteId": "local-config-evolution", "suiteVersion": PROTOCOL,
        "tasksetId": GENERATOR_VERSION, "tasksetVersion": GENERATOR_VERSION,
        "evaluatorId": "exact-synthetic-fixture", "evaluatorVersion": GENERATOR_VERSION,
        "trainTaskIds": [fixture.task_id for fixture in fixtures["train"]],
        "heldoutTaskIds": [fixture.task_id for fixture in fixtures["heldout"]],
        "sealedTaskIds": [fixture.task_id for fixture in fixtures["sealed"]],
        "qualityFloor": values["qualityFloor"],
        "maxLatencyMs": values["maxAlgorithmLatencyMs"],
        "maxPolicyViolations": 0, "confidenceAlpha": 0.05,
        "maxAttemptsPerTask": 1,
        # Deliberately absent: local synthetic measurements do not establish a
        # monetary actual cost or an enforced provider spending cap.
        "maxCostMicrousdPerTask": None, "costCapEnforcementId": None,
    })
    reports: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        reports[candidate.candidate_id] = {
            split: evaluate_candidate(candidate, suite, attempts, split)
            for split in ("train", "heldout")
        }

    try:
        heldout_decision = compare_candidates(
            reports[baseline_id]["heldout"], reports[selected_id]["heldout"], suite)
    except EvaluationError as exc:
        raise EvolutionError("internal held-out reports failed the promotion validator") from exc

    report_metrics: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        report_metrics[candidate.candidate_id] = {
            "config": candidate.to_dict(),
            "splits": {split: _aggregate(observations[candidate.candidate_id][split])
                       for split in ("train", "heldout")},
            "evaluationReports": reports[candidate.candidate_id],
        }
    scored_observations = [row for per_split in observations.values()
                           for split in ("train", "heldout") for row in per_split[split]]
    source_hashes = _source_hashes()
    config_digest = _digest({"suite": suite.to_dict(),
                             "candidates": [candidate.to_dict() for candidate in candidates],
                             "tokenBudgetUnits": values["tokenBudget"]})
    return {
        "evolutionProtocol": PROTOCOL,
        "claim": "bounded algorithm-configuration search; no novel algorithm or generated code",
        "sourceHashes": source_hashes,
        "configurationSha256": config_digest,
        "dataset": {
            "generator": GENERATOR_VERSION, "seed": seed,
            "sha256": dataset_digest, "splitSha256": split_digests,
            "trainCount": counts["train"], "heldoutCount": counts["heldout"],
            "sealedCount": counts["sealed"],
            "itemsPerInstance": values["itemsPerInstance"], "claimCount": values["claimCount"],
            "scoredInstanceCount": scored_count,
        },
        "algorithm": {"name": ALGORITHM_VERSION,
                      "objective": "sum of weights of covered claims under token-unit budget",
                      "exactOracle": "subset enumeration with dynamic programming over all item subsets",
                      "exactOracleMaxItems": MAX_ITEMS,
                      "workBound": {"units": work_bound, "maximum": MAX_EXACT_WORK,
                                    "unit": "conservative counted loop-body/scan estimate, not CPU instructions",
                                    "components": work_components}},
        "candidateGeneration": {"method": "fixed supported cost-exponent grid",
                                "candidates": len(candidates),
                                "knob": "costExponent in " + ", ".join(map(str, SUPPORTED_EXPONENTS)),
                                "baselineCandidateId": baseline_id},
        "trainingSelection": selection,
        "candidates": report_metrics,
        "heldoutPromotionDecision": heldout_decision,
        "sealedSet": {"count": counts["sealed"], "splitSha256": split_digests["sealed"],
                       "status": "generated_not_executed_or_scored_or_selected",
                       "usedForSelection": False},
        "economics": {
            "fixtureTokenCostUnit": "synthetic_evidence_token_units",
            "tokenBudgetUnitsPerInstance": values["tokenBudget"],
            "meanSelectedTokenUnitsByCandidate": {
                candidate.candidate_id: _mean(row["tokenUnitsUsed"]
                    for split in ("train", "heldout")
                    for row in observations[candidate.candidate_id][split])
                for candidate in candidates},
            "measuredAlgorithmLatencyMs": {
                candidate.candidate_id: _aggregate(
                    observations[candidate.candidate_id]["train"] +
                    observations[candidate.candidate_id]["heldout"])["meanLatencyMs"]
                for candidate in candidates},
            "workUnits": {
                candidate.candidate_id: sum(row["workUnits"]
                    for split in ("train", "heldout")
                    for row in observations[candidate.candidate_id][split])
                for candidate in candidates},
            "actualModelTokens": None,
            "actualCostMicrousd": None,
            "estimatedMonetaryCostMicrousd": None,
            "computeCost": None,
            "note": "Synthetic fixture token units and local algorithm latency are not model usage, GPU utilization, provider charges, or a monetary compute estimate.",
            "unknownCostBlocksPromotion": True,
        },
        "evaluation": {"suite": suite.to_dict(), "attemptCount": len(attempts),
                       "attemptCostState": "unknown_for_all_local_fixture_runs",
                       "attemptsWithUnknownCost": len(attempts),
                       "measuredRows": len(scored_observations),
                       "sealedSetUsedForSelection": False},
        "limitations": [
            "The runner searches one supported greedy implementation's configuration grid; it does not evolve source code or discover algorithms.",
            "Weighted-max-coverage fixtures are synthetic and do not establish quality on repository tasks or provider/model behavior.",
            "Exact oracle results apply only to generated instances at or below the declared item bound.",
            "Latency is local wall-clock measurement and may vary between runs; selection uses deterministic training objectives, not timing.",
            "No paid model or GPU was used; monetary actual and estimated costs remain unknown.",
            "The held-out gate is conservative and may withhold promotion because no monetary cost receipt or enforced cost cap exists.",
            "The sealed split is generated for later independent use but is neither solved nor scored here.",
        ],
    }


def evolve(payload: Mapping[str, object]) -> dict[str, object]:
    """Public concise alias for the JSON runner."""
    return run_evolution(payload)


def _validate_payload(payload: Mapping[str, object]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise EvolutionError("payload must be an object")
    allowed = {"action", "seed", "trainCount", "heldoutCount", "sealedCount",
               "itemsPerInstance", "claimCount", "tokenBudget", "costExponents",
               "qualityFloor", "maxAlgorithmLatencyMs"}
    if set(payload) - allowed:
        raise EvolutionError("payload contains unsupported fields")
    if payload.get("action", "evolve") != "evolve":
        raise EvolutionError("action must be evolve")
    seed = payload.get("seed", 7)
    if type(seed) is not int or not 0 <= seed <= 2**32 - 1:
        raise EvolutionError("seed must be an integer from 0 to 2^32-1")
    train_count = _bounded_int(payload.get("trainCount", 6), "trainCount", 2, MAX_TRAIN)
    heldout_count = _bounded_int(payload.get("heldoutCount", 6), "heldoutCount", 2, MAX_HELDOUT)
    sealed_count = _bounded_int(payload.get("sealedCount", 2), "sealedCount", 1, MAX_SEALED)
    items = _bounded_int(payload.get("itemsPerInstance", 10), "itemsPerInstance", 4, MAX_ITEMS)
    claims = _bounded_int(payload.get("claimCount", 8), "claimCount", 3, MAX_CLAIMS)
    token_budget = _bounded_int(payload.get("tokenBudget", 20), "tokenBudget", 1, MAX_TOKEN_BUDGET)
    raw_exponents = payload.get("costExponents", list(SUPPORTED_EXPONENTS[:3]))
    if not isinstance(raw_exponents, list) or not 1 <= len(raw_exponents) <= MAX_CANDIDATES:
        raise EvolutionError("costExponents must be a non-empty bounded list")
    exponents: list[float] = []
    for value in raw_exponents:
        if type(value) not in (int, float) or not math.isfinite(value) or value not in SUPPORTED_EXPONENTS:
            raise EvolutionError("costExponents contains an unsupported greedy exponent")
        exponent = float(value)
        if exponent in exponents:
            raise EvolutionError("costExponents must be unique")
        exponents.append(exponent)
    quality_floor = _finite_range(payload.get("qualityFloor", 0.5), "qualityFloor", 0.0, 1.0)
    latency = _finite_range(payload.get("maxAlgorithmLatencyMs", 60_000.0),
                            "maxAlgorithmLatencyMs", 1.0, 60_000.0)
    if train_count + heldout_count > MAX_TRAIN + MAX_HELDOUT:
        raise EvolutionError("scored fixture count exceeds its hard bound")
    return {"seed": seed, "trainCount": train_count, "heldoutCount": heldout_count,
            "sealedCount": sealed_count, "itemsPerInstance": items, "claimCount": claims,
            "tokenBudget": token_budget, "costExponents": tuple(exponents),
            "qualityFloor": quality_floor, "maxAlgorithmLatencyMs": latency}


def _make_fixture(seed: int, split: str, index: int, item_count: int, claim_count: int) -> _Fixture:
    split_tag = {"train": 0x1020304050607080, "heldout": 0x8090A0B0C0D0E0F0,
                 "sealed": 0xF0E0D0C0B0A09080}[split]
    base = _splitmix64(seed ^ split_tag ^ (index * 0x9E3779B97F4A7C15 & UINT64_MASK))
    claim_weights = tuple(1 + _splitmix64(base + claim * 0xD1B54A32D192ED03 & UINT64_MASK) % 100
                          for claim in range(claim_count))
    items: list[_Item] = []
    for item_index in range(item_count):
        if item_index == 0:
            token_cost = 1
        else:
            token_cost = 1 + _splitmix64(base + 0xA0761D6478BD642F + item_index * 0xE7037ED1A0B428DB & UINT64_MASK) % 10
        mask = 0
        for claim_index in range(claim_count):
            value = _splitmix64(base + 0x8EBC6AF09C88C6E3 +
                                item_index * 0x589965CC75374CC3 +
                                claim_index * 0x1D8E4E27C47D124F & UINT64_MASK)
            if value % 100 < 32:
                mask |= 1 << claim_index
        if mask == 0:
            mask = 1 << (_splitmix64(base + item_index * 17) % claim_count)
        items.append(_Item(f"evidence-{item_index:02d}", int(token_cost), mask))
    return _Fixture(f"{split}-{index:03d}", split, claim_weights, tuple(items))


def _splitmix64(value: int) -> int:
    z = (value + 0x9E3779B97F4A7C15) & UINT64_MASK
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & UINT64_MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & UINT64_MASK
    return (z ^ (z >> 31)) & UINT64_MASK


def _work_bound_components(*, train_count: int, heldout_count: int,
                           item_count: int, claim_count: int,
                           candidate_count: int) -> dict[str, int]:
    """Count conservative bounded scan/loop bodies for every scored fixture.

    These named units are algorithm-specific accounting for Python loops and
    scans, not a promise about CPU instructions or elapsed time.
    """
    scored_count = train_count + heldout_count
    subsets = 1 << item_count
    triangle = item_count * (item_count + 1) // 2
    greedy_per_run = {
        "greedySelectionPassChecks": item_count + 1,
        "greedyEligibilityChecks": triangle,
        "greedyClaimWeightScans": triangle * claim_count,
        "greedyRankKeyEvaluations": triangle,
        "greedyRemovalFilterChecks": item_count * item_count,
        "greedySelectionBookkeeping": item_count,
    }
    components = {
        "oracleSubsetIterationChecks": scored_count * subsets,
        "oracleCostMaskRecurrenceAssignments": scored_count * 2 * (subsets - 1),
        "oracleClaimWeightScans": scored_count * subsets * claim_count,
        "oracleIdentifierScans": scored_count * subsets * item_count,
        "oracleObjectiveTieComparisonChecks": scored_count * 2 * subsets,
    }
    for name, units in greedy_per_run.items():
        components[name] = scored_count * candidate_count * units
    return components


def _solve_oracles(fixtures: Sequence[_Fixture], token_budget: int
                   ) -> tuple[dict[str, dict[str, Any]], dict[str, float]]:
    oracle_by_task: dict[str, dict[str, Any]] = {}
    oracle_times: dict[str, float] = {}
    for fixture in fixtures:
        started = time.perf_counter_ns()
        oracle = _exact_oracle(fixture, token_budget)
        oracle_times[fixture.task_id] = (time.perf_counter_ns() - started) / 1_000_000.0
        oracle_by_task[fixture.task_id] = oracle
    return oracle_by_task, oracle_times


def _run_split(candidates: Sequence[Candidate], fixtures: Sequence[_Fixture], split: str,
               oracle_by_task: Mapping[str, Mapping[str, Any]],
               oracle_times: Mapping[str, float],
               observations: dict[str, dict[str, list[dict[str, Any]]]],
               attempts: list[Attempt], values: Mapping[str, Any]) -> None:
    for candidate in candidates:
        exponent = candidate.config["costExponent"]
        for fixture in fixtures:
            try:
                started = time.perf_counter_ns()
                result = _run_greedy(fixture, values["tokenBudget"], exponent)
                elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000.0
            except Exception:
                raise EvolutionError("built-in candidate execution failed; no selection was produced") from None
            oracle = oracle_by_task[fixture.task_id]
            ratio = result["objective"] / oracle["objective"] if oracle["objective"] else 0.0
            if not math.isfinite(ratio) or not 0.0 <= ratio <= 1.0:
                raise EvolutionError("candidate objective did not reconcile with the exact oracle")
            observation = {
                "taskId": fixture.task_id,
                "objective": result["objective"],
                "oracleObjective": oracle["objective"],
                "objectiveRatio": ratio,
                "feasible": True,
                "tokenUnitsUsed": result["tokenUnitsUsed"],
                "tokenBudgetUnits": values["tokenBudget"],
                "selectedItemIds": result["selectedItemIds"],
                "measuredAlgorithmLatencyMs": elapsed_ms,
                "oracleLatencyMs": oracle_times[fixture.task_id],
                "workUnits": result["workUnits"],
                "workBreakdown": result["workBreakdown"],
                "algorithm": ALGORITHM_VERSION,
            }
            observations[candidate.candidate_id][split].append(observation)
            attempts.append(Attempt(
                attempt_id=f"{candidate.candidate_id}:{fixture.task_id}:1",
                candidate_id=candidate.candidate_id, task_id=fixture.task_id,
                evaluator_id="exact-synthetic-fixture",
                evaluator_version=GENERATOR_VERSION, attempt_index=1,
                status="succeeded", elapsed_ms=elapsed_ms,
                actual_cost_microusd=None, quality_score=ratio,
                accepted=ratio >= values["qualityFloor"], policy_violations=0,
            ))


def _exact_oracle(fixture: _Fixture, token_budget: int) -> dict[str, Any]:
    item_count = len(fixture.items)
    if item_count > MAX_ITEMS:
        raise EvolutionError("fixture exceeds exact-oracle item limit")
    subset_count = 1 << item_count
    costs = [0] * subset_count
    masks = [0] * subset_count
    best_value = -1
    best_cost = 0
    best_ids: tuple[str, ...] = ()
    feasible_subsets = 0
    for subset in range(subset_count):
        if subset:
            bit = subset & -subset
            item_index = bit.bit_length() - 1
            prior = subset ^ bit
            costs[subset] = costs[prior] + fixture.items[item_index].token_cost
            masks[subset] = masks[prior] | fixture.items[item_index].claim_mask
        cost = costs[subset]
        if cost > token_budget:
            continue
        feasible_subsets += 1
        covered = masks[subset]
        score = sum(weight for index, weight in enumerate(fixture.claim_weights)
                    if covered & (1 << index))
        ids = tuple(fixture.items[index].item_id for index in range(item_count)
                    if subset & (1 << index))
        if score > best_value or (score == best_value and (cost, ids) < (best_cost, best_ids)):
            best_value, best_cost, best_ids = score, cost, ids
    if best_value < 0:
        raise EvolutionError("exact oracle found no feasible subset")
    work_breakdown = {
        "subsetIterationChecks": subset_count,
        "costMaskRecurrenceAssignments": 2 * (subset_count - 1),
        "claimWeightScans": feasible_subsets * len(fixture.claim_weights),
        "identifierScans": feasible_subsets * item_count,
        "objectiveTieComparisonChecks": 2 * feasible_subsets,
    }
    return {"objective": best_value, "tokenUnitsUsed": best_cost,
            "selectedItemIds": list(best_ids), "subsetsEnumerated": subset_count,
            "feasibleSubsetsConsidered": feasible_subsets,
            "workBreakdown": work_breakdown,
            "workUnits": sum(work_breakdown.values())}


def _run_greedy(fixture: _Fixture, token_budget: int, cost_exponent: float) -> dict[str, Any]:
    remaining = list(fixture.items)
    selected: list[_Item] = []
    covered = 0
    spent = 0
    work = {"selectionPassChecks": 0, "eligibilityChecks": 0,
            "claimWeightScans": 0, "rankKeyEvaluations": 0,
            "removalFilterChecks": 0, "selectionBookkeeping": 0}
    while remaining:
        work["selectionPassChecks"] += 1
        choices: list[tuple[float, int, str, _Item, int]] = []
        for item in remaining:
            work["eligibilityChecks"] += 1
            if spent + item.token_cost > token_budget:
                continue
            marginal = 0
            for index, weight in enumerate(fixture.claim_weights):
                work["claimWeightScans"] += 1
                if item.claim_mask & (1 << index) and not covered & (1 << index):
                    marginal += weight
            if marginal <= 0:
                continue
            score = marginal / (item.token_cost ** cost_exponent)
            choices.append((score, marginal, item.item_id, item, marginal))
        if not choices:
            break
        # Maximize the configured marginal score, then gain, then lexicographic ID.
        work["rankKeyEvaluations"] += len(choices)
        _, _, _, chosen, _ = min(choices, key=lambda row: (-row[0], -row[1], row[2]))
        selected.append(chosen)
        work["selectionBookkeeping"] += 1
        spent += chosen.token_cost
        covered |= chosen.claim_mask
        next_remaining: list[_Item] = []
        for item in remaining:
            work["removalFilterChecks"] += 1
            if item.item_id != chosen.item_id:
                next_remaining.append(item)
        remaining = next_remaining
    objective = sum(weight for index, weight in enumerate(fixture.claim_weights)
                    if covered & (1 << index))
    return {"objective": objective, "tokenUnitsUsed": spent,
            "selectedItemIds": [item.item_id for item in selected],
            "workUnits": sum(work.values()), "workBreakdown": work}


def _candidate_configs(exponents: Sequence[float]) -> list[dict[str, Any]]:
    all_exponents = sorted(set(exponents) | {1.0})
    output = []
    for exponent in all_exponents:
        if exponent == 1.0:
            candidate_id = "baseline-density"
        else:
            token = "0" if exponent == 0 else str(exponent).replace(".", "_")
            candidate_id = "greedy-exp-" + token
        output.append({"candidateId": candidate_id,
                       "config": {"algorithm": ALGORITHM_VERSION,
                                   "costExponent": exponent,
                                   "tieBreak": "marginal_gain_then_item_id"}})
    if len(output) > MAX_CANDIDATES:
        raise EvolutionError("candidate grid exceeds its hard bound")
    return output


def _aggregate(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {"instanceCount": 0, "meanObjective": None, "meanOracleObjective": None,
                "meanObjectiveRatio": None, "meanLatencyMs": None,
                "maxLatencyMs": None, "meanTokenUnitsUsed": None,
                "totalWorkUnits": 0, "allFeasible": False}
    return {
        "instanceCount": len(rows),
        "meanObjective": _mean(row["objective"] for row in rows),
        "meanOracleObjective": _mean(row["oracleObjective"] for row in rows),
        "meanObjectiveRatio": _mean(row["objectiveRatio"] for row in rows),
        "meanLatencyMs": _mean(row["measuredAlgorithmLatencyMs"] for row in rows),
        "maxLatencyMs": max(row["measuredAlgorithmLatencyMs"] for row in rows),
        "meanTokenUnitsUsed": _mean(row["tokenUnitsUsed"] for row in rows),
        "totalWorkUnits": sum(row["workUnits"] for row in rows),
        "allFeasible": all(row["feasible"] for row in rows),
    }


def _mean(values: Sequence[float] | Any) -> float:
    numbers = list(values)
    return sum(numbers) / len(numbers) if numbers else 0.0


def _source_hashes() -> dict[str, str]:
    root = Path(__file__).resolve().parent
    return {name: hashlib.sha256((root / filename).read_bytes()).hexdigest()
            for name, filename in (("evolution", "evolution.py"),
                                   ("optimizer", "optimization.py"),
                                   ("evaluation", "evaluation.py"))}


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bounded_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise EvolutionError(f"{name} must be an integer from {low} to {high}")
    return value


def _finite_range(value: Any, name: str, low: float, high: float) -> float:
    if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
        raise EvolutionError(f"{name} must be finite and between {low} and {high}")
    return float(value)
