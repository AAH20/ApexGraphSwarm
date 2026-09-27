# Execution analytics

`apexgraphswarm.analytics` builds a versioned JSON analytics response from the local execution-attempt ledger, a caller-supplied event snapshot, or a deterministic demo fixture. It uses only the Python standard library and never constructs `ControlStore`.

The supported Python entry point is:

```python
from apexgraphswarm.analytics import build_analytics

result = build_analytics(
    {"source": "live", "days": 30, "tool": "model:review"},
    db_path="runtime/control.sqlite",
)
```

The CLI accepts one JSON object on stdin:

```json
{"source":"live","days":30,"tool":"model:review","dbPath":"runtime/control.sqlite"}
```

`dbPath` is a local CLI/server argument. A browser request must never choose the ledger path; the server supplies it from its configured control database. The CLI reads at most 2 MiB and emits JSON only on success. Errors are intentionally generic and do not echo paths, SQL errors, credentials, or event contents.

Requests accept only `source`, `days`, `tool`, and `rows`. `source` is `live`, `demo`, or `import`; `days` defaults to 30 and is limited to 1–365. `rows` is required only for imports and is capped at 10,000. Every imported event must have exactly these fields:

```json
{"attemptId":"a-1","taskId":"t-1","tool":"model:review","resource":"pool-a","startedAt":1790503200,"settledAt":1790503210,"outcome":"succeeded","actualCostMicrousd":12}
```

Times are finite Unix seconds. `settledAt` and `actualCostMicrousd` may be `null`; unknown cost remains an unknown liability and is never converted into a known zero. Unknown fields, invalid values, and duplicate attempt IDs reject the import. Imported completeness is caller-owned: the engine can validate the supplied snapshot but cannot establish whether an upstream exporter omitted events.

`demo` generates a deterministic synthetic 28-day fixture relative to the supplied `now` value (or the current UTC time). It is explicitly marked synthetic in the response. For a stable fixture, pass a fixed UTC datetime to `build_analytics`.

Live reads open SQLite with `mode=ro`, set `query_only`, start a read transaction, and use `fetchmany`; a missing file returns an empty response without creating it. The query is limited to 200,000 rows and five seconds by default. The engine retains a bounded in-memory result for those rows, so this is suitable for local operational dashboards, not an unbounded streaming warehouse. Hitting either limit marks the response truncated, suppresses forecast and complete unit-cost claims, and explains the partial result. Legacy missing attempts are detected by comparing task attempt counters with attempt-ledger row counts; coverage is conservative, especially when filtering by tool.

The v1 response includes KPIs, UTC daily totals, tool/resource cohorts, a weekday/hour heatmap, bounded tool-to-resource graph, latency distribution, correlation, bounded scatter points, anomalies, and a spend forecast. The latency/scatter displays use deterministic evenly spaced samples above their caps. Cohorts, tools, graph nodes, histograms, and imported rows have explicit caps; quality flags disclose output truncation.

Forecasts use complete UTC dates through yesterday, beginning at the first observed attempt date. They require at least 14 such dates, at least eight days with known positive spend, known costs for all selected attempts, and verified coverage. The last three dates are held out for a fixed-origin comparison against a last-training-day naive baseline; `trainingDates` and `holdoutDates` expose that split. The final line trend is refit on the full eligible history for a seven-day horizon. The displayed residual bands are heuristic ranges, not confidence intervals or guarantees. Forecasting is suppressed when relevant cost or coverage is incomplete.

The engine performs descriptive local analysis only. It does not invoke providers, infer missing receipts, establish external identity, or claim predictive accuracy beyond the stated backtest.
