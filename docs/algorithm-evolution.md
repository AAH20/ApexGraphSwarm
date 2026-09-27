# Bounded algorithm-configuration evolution

`apexgraphswarm.evolution.run_evolution(payload)` runs a deterministic local
configuration search for weighted maximum coverage. It exercises the named
`weighted-coverage-greedy-v1` strategy with a small supported `costExponent`
grid, using exact subset enumeration as an oracle on tiny synthetic fixtures.
This is configuration evolution: it does not write or execute generated code,
discover general-purpose algorithms, contact a model provider, or promote a
production model.

The runner returns JSON-compatible dictionaries (also available as
`evolve(payload)`). The payload uses strict camel-case JSON fields:

```json
{
  "action": "evolve",
  "seed": 7,
  "trainCount": 6,
  "heldoutCount": 6,
  "sealedCount": 2,
  "itemsPerInstance": 10,
  "claimCount": 8,
  "tokenBudget": 20,
  "costExponents": [0, 0.5, 1],
  "qualityFloor": 0.5,
  "maxAlgorithmLatencyMs": 60000
}
```

All fields except `action` are optional and have the defaults shown. Unknown
fields are rejected. Inputs are finite and bounded: train/held-out each allow
2–12 fixtures, sealed allows 1–12, each fixture has 4–14 items and 3–16 claims,
token budget is 1–1000, and at most four unique exponents from `[0, 0.5, 1,
1.5]` are accepted. The baseline exponent `1` is always included. Before any
solver runs, the runner calculates named conservative loop-work components:
oracle subset iterations, cost/mask recurrence assignments, claim-weight
scans, identifier scans and objective/tie checks, plus candidate greedy
selection passes, eligibility checks, claim scans, rank-key evaluations,
removal-filter checks, and selection bookkeeping. Inputs exceeding 4.2 million
of these counted loop-body/scan units are rejected before solving. These units
bound modeled algorithm loops; they are not CPU instructions or a runtime
guarantee.

Fixtures and each split are hashed with the generator version, seed, and
canonical sorted JSON. The result includes generator, source, and candidate
configuration SHA-256 values. Train results alone select the configuration,
using mean exact-oracle objective ratio and stable candidate-ID tie breaking.
Selection is complete before held-out fixtures are sent to either solver.
The held-out split is then evaluated separately using the repository's
conservative `evaluation.compare_candidates` gate. The sealed split is only
generated and hashed; it is never run through a candidate/oracle or used for
selection. A changed sealed count therefore cannot affect the selected result.

The report distinguishes synthetic evidence token units, measured local
algorithm wall-clock latency, and algorithm work units. It reports actual model
tokens, monetary cost, estimated monetary cost, and compute cost as unknown.
Since no provider receipts or enforced monetary cost cap exist for this local
run, the held-out gate must withhold promotion on unknown cost; a favorable
synthetic objective or speed result cannot override that gate. A candidate
execution error fails the whole run rather than producing a partial selection.

## Interpretation limits

- The generated weighted-coverage tasks are deterministic test fixtures, not
  repository tasks, a production workload, or evidence about model quality.
- The exact objective is guaranteed only by subset enumeration within the
  declared item bound. Greedy configurations are not claimed to be optimal.
- Training selection is not an independent quality guarantee. Held-out
  confidence gates may remain inconclusive for these small fixture counts.
- Sealed fixtures are reserved for a later independent evaluation; this runner
  does not reveal their scores because it does not compute them.
- Local latency is environment-dependent and is reported as measurement, not
  used to decide which configuration wins.
- No arbitrary code, network access, paid model call, GPU measurement, actual
  invoice cost, or monetary estimate is involved.
