# Reproducible evaluation and promotion gate

`apexgraphswarm.evaluation` evaluates supplied candidate configurations and evaluator-produced attempt records. It never imports, compiles, or executes candidate code. A candidate `config` is inert JSON (maximum 16 KiB) and receives a canonical SHA-256 digest in every report.

## Protocol

Every suite identifies its own version, task-set ID/version, and evaluator ID/version. It requires distinct, nonempty train, held-out, and sealed task ID lists. Attempts carry the evaluator identity, candidate/task identity, attempt index, terminal status, elapsed time, actual cost in integer micro-USD (or `null`), evaluator quality score/acceptance, and policy violation count. Attempt IDs are globally unique; per-task attempt indices are contiguous and bounded (default maximum three). Failed, timed-out, and cancelled attempts count toward spend and latency exactly like successful attempts.

The `evaluate(payload)` dispatcher accepts:

```json
{
  "suite": {
    "suiteId": "repo-optimization", "suiteVersion": "1",
    "tasksetId": "repo-tasks", "tasksetVersion": "heldout-2026-09",
    "evaluatorId": "sandbox-checks", "evaluatorVersion": "4",
    "trainTaskIds": ["train-01", "train-02"],
    "heldoutTaskIds": ["hold-01", "hold-02"],
    "sealedTaskIds": ["seal-01"],
    "qualityFloor": 0.8, "maxLatencyMs": 60000,
    "maxPolicyViolations": 0, "confidenceAlpha": 0.05,
    "maxAttemptsPerTask": 3, "maxAcceptRateRegression": 0.02,
    "maxCostMicrousdPerTask": 10000,
    "costCapEnforcementId": "control-plane-run-budget-v1"
  },
  "candidates": [
    {"candidateId": "baseline", "version": "1", "config": {"workers": 2}},
    {"candidateId": "proposal-a", "version": "1", "config": {"workers": 4}}
  ],
  "attempts": [],
  "baselineCandidateId": "baseline"
}
```

Candidate selection uses **training reports only**: among non-baseline candidates that pass training gates and have known cost per accepted task, it picks the lowest conservative upper bound. Promotion comparison then uses the exact ordered held-out task set. Every expected task must have at least one attempt; missing held-out evidence returns a rejected decision, and missing training evidence excludes that candidate. Each task's final attempt determines its accepted outcome; all attempt costs are summed, so retries do not disappear from economics. Any unknown actual cost blocks promotion. A policy violation beyond the configured limit or held-out p95 cumulative per-task latency over its SLO blocks promotion. The quality floor applies both to each accepted final output's evaluator score and to a conservative Hoeffding lower bound for the accepted-task rate.

The suite must also declare `maxCostMicrousdPerTask` and a `costCapEnforcementId` identifying the mechanism/history that enforced that cumulative per-task cap. Missing cap provenance or any task exceeding the cap blocks promotion. The cap is an input assertion; the evaluator must independently verify enforcement and preserve its audit reference. Unknown cost cannot be treated as zero.

The acceptance-rate quality floor, paired acceptance non-inferiority, and candidate/baseline cost-per-accepted bounds use a family-wise `confidenceAlpha` split across six one-sided bounds in the base protocol. Acceptance rates and per-task spend use Hoeffding bounds; paired candidate-minus-baseline acceptance uses an empirical-Bernstein interval for paired differences in `[-1, 1]`. Cost per accepted outcome is bounded conservatively by dividing the bounded mean task-cost by the corresponding bounded accepted-task probability. Promotion requires the paired lower bound to be no worse than the configured `maxAcceptRateRegression` margin (default 2 percentage points), and the candidate cost-per-accepted upper bound to be below the baseline lower bound. Small samples are expected to remain inconclusive; the report surfaces intervals and gate failures instead of forcing a decision.

Optionally add a versioned `suite.metricProfile` with `profileId`, `profileVersion`, `minimumWeightedScore`, and `maxScoreRegression`. A complete evaluator-produced `metricScores` vector is required on each final task attempt; a missing metric is a hard gate and is never renormalized. Profiles use registered domain metrics and weights; custom weights require a complete integer-percent vector summing to 100 and an explicit `weightSetVersion`. Weighted task scores receive a Hoeffding bound and candidate/baseline held-out differences use a paired empirical-Bernstein interval. Profile-enabled runs split `confidenceAlpha` over eight bounds. Promotion must also clear the conservative profile floor and paired profile-score non-inferiority gate. A composite score cannot compensate for the existing policy, budget, latency, quality, or cost failures. See [field profiles and hierarchy planning](hierarchical-orchestration.md).

Sealed task IDs are checked for overlap with train and held-out, but this call does not score or return sealed attempts. Keep sealed data outside candidate-selection runs; only expose it through a separately versioned post-selection audit after the candidate and decision have been frozen. The function cannot prevent an operator from reusing leaked task content, so task custody and evaluator separation remain operational responsibilities.

## Reproducible local benchmark

Run:

```sh
python3 scripts/benchmark_optimization.py  # or: python3 -m scripts.benchmark_optimization
```

Import `scripts.benchmark_optimization.benchmark_report()` for JSON-friendly output. It measures local wall-clock time for deterministic scheduling, evidence selection, declared-file conflict waves, capacity recommendation over **synthetic** telemetry, and a paired gate demonstration. The demo uses synthetic task outcomes and fixture micro-USD amounts; the report marks them as synthetic, lists zero provider calls, and makes no public benchmark or model-performance claim. It is a smoke/performance regression fixture for local algorithms, not a live inference benchmark or price estimate.

## Provenance and limitations

- Pin source revision, suite/task-set/evaluator versions, candidate config hash, Python/runtime version, fixture or repository snapshot digest, attempt records, and the source of every cost/latency observation.
- Set `actualCostMicrousd` to `null` when accounting is unknown; do not copy estimates into actual-usage fields. Unknown cost prevents favorable promotion even when known spend appears low.
- Evaluator acceptance, score, policy flags, and cost-cap enforcement ID are caller assertions. This module does not independently inspect artifacts, check permissions, verify citations, cryptographically validate cap enforcement, or establish that task IDs are representative.
- Hoeffding and paired empirical-Bernstein bounds assume independent task sampling and a true enforced per-task cost bound. Repeated or correlated tasks can make uncertainty appear smaller than it should. Use held-out task families and disclose dependence.
- Selection and comparison use only the optimization results provided by the caller. No provider is contacted and no result implies capacity beyond the measured synthetic inputs.
