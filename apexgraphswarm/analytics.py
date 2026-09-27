"""Bounded, read-only analytics over execution attempt ledgers.

This module intentionally does not import ControlStore: opening a ledger for
analytics must never create, migrate, or mutate its database.
"""
from __future__ import annotations

import json
import math
import sqlite3
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime, time as dt_time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

VERSION = 1
MAX_SAFE_INTEGER = 2**53 - 1
MAX_INPUT_BYTES = 2 * 1024 * 1024
MAX_IMPORT_ROWS = 10_000
MAX_LIVE_ROWS = 200_000
MAX_METRIC_SAMPLE = 5_000
MAX_COHORTS = 100
MAX_GRAPH_NODES = 200
MAX_SCATTER = 200
MAX_HISTOGRAM_BINS = 20
MAX_TOOLS = 100
OUTCOMES = {"running", "unknown", "succeeded", "failed", "cancelled", "not_started", "expired_retryable"}
EVENT_KEYS = {"attemptId", "taskId", "tool", "resource", "startedAt", "settledAt", "outcome", "actualCostMicrousd"}


class AnalyticsError(ValueError):
    """A request is invalid or its aggregate cannot be represented safely."""


def _utc_now(now: datetime | int | float | None) -> datetime:
    if now is None:
        return datetime.now(timezone.utc)
    if isinstance(now, (int, float)) and not isinstance(now, bool) and math.isfinite(now):
        return datetime.fromtimestamp(now, timezone.utc)
    if isinstance(now, datetime):
        return now.replace(tzinfo=timezone.utc) if now.tzinfo is None else now.astimezone(timezone.utc)
    raise AnalyticsError("now must be a finite epoch or datetime")


def _iso(ts: datetime) -> str:
    return ts.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _safe_text(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if not isinstance(value, str) or not value or len(value) > 256 or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError(field)
    return value


def _validate_event(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict) or set(row) != EVENT_KEYS:
        raise ValueError("shape")
    attempt = _safe_text(row["attemptId"], "attemptId")
    task = _safe_text(row["taskId"], "taskId")
    tool = _safe_text(row["tool"], "tool", nullable=True)
    resource = _safe_text(row["resource"], "resource", nullable=True)
    started = row["startedAt"]
    settled = row["settledAt"]
    cost = row["actualCostMicrousd"]
    outcome = row["outcome"]
    if isinstance(started, bool) or not isinstance(started, (int, float)) or not math.isfinite(started) or not 0 <= started <= 253402300799:
        raise ValueError("startedAt")
    if settled is not None and (isinstance(settled, bool) or not isinstance(settled, (int, float)) or not math.isfinite(settled) or not started <= settled <= 253402300799):
        raise ValueError("settledAt")
    if cost is not None and (isinstance(cost, bool) or not isinstance(cost, int) or cost < 0 or cost > MAX_SAFE_INTEGER):
        raise ValueError("actualCostMicrousd")
    if outcome not in OUTCOMES:
        raise ValueError("outcome")
    if (outcome == "running") != (settled is None):
        # Non-running ambiguous outcomes may be unsettled; settledAt describes
        # observed completion, while unknown liability remains independent.
        if outcome == "running" or settled is None and outcome in {"succeeded", "failed", "cancelled"}:
            raise ValueError("settlement")
    if outcome == "running" and cost is not None:
        raise ValueError("running cost")
    return {"attemptId": attempt, "taskId": task, "tool": tool or "(unspecified)",
            "resource": resource or "(unspecified)", "startedAt": float(started),
            "settledAt": float(settled) if settled is not None else None,
            "outcome": outcome, "actualCostMicrousd": cost}


def _date_epoch(day: date) -> float:
    return datetime.combine(day, dt_time.min, timezone.utc).timestamp()


def _check_integer(value: int) -> int:
    if value > MAX_SAFE_INTEGER:
        raise AnalyticsError("aggregate exceeds the safe integer range")
    return value


def _fit_line(values: list[float]) -> tuple[float, float]:
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mx = (n - 1) / 2
    my = sum(values) / n
    denom = sum((i - mx) ** 2 for i in range(n))
    slope = sum((i - mx) * (v - my) for i, v in enumerate(values)) / denom if denom else 0.0
    return my - slope * mx, slope


def _forecast(daily_values: list[int], dates: list[date], blocked: bool) -> dict[str, Any]:
    out = {"status": "insufficient_data", "points": [], "backtestMAE": None, "naiveMAE": None,
           "method": "OLS linear trend over daily known spend; 3-day holdout; 7-day horizon",
           "trainingDates": [], "holdoutDates": [],
           "limitations": ["Prediction bands are heuristic residual bands, not confidence intervals."]}
    active = sum(v > 0 for v in daily_values)
    if blocked:
        out["status"] = "blocked_incomplete_coverage"
        out["limitations"].append("Forecast suppressed because ledger coverage or costs are incomplete.")
        return out
    if len(dates) < 14 or active < 8:
        out["limitations"].append("Requires at least 14 calendar days and 8 active-spend days.")
        return out
    train_n = len(daily_values) - 3
    out["trainingDates"] = [d.isoformat() for d in dates[:train_n]]
    out["holdoutDates"] = [d.isoformat() for d in dates[train_n:]]
    train = [float(v) for v in daily_values[:train_n]]
    intercept, slope = _fit_line(train)
    test = daily_values[train_n:]
    predictions = [max(0.0, intercept + slope * i) for i in range(train_n, len(daily_values))]
    out["backtestMAE"] = round(sum(abs(a - p) for a, p in zip(test, predictions)) / 3, 3)
    # A fixed-origin, three-step naive forecast uses only the final training
    # observation. It does not peek at prior holdout actuals.
    naive = [float(daily_values[train_n - 1])] * 3
    out["naiveMAE"] = round(sum(abs(a - p) for a, p in zip(test, naive)) / 3, 3)
    residuals = [v - (intercept + slope * i) for i, v in enumerate(train)]
    rmse = math.sqrt(sum(x*x for x in residuals) / max(1, len(residuals)))
    intercept, slope = _fit_line([float(v) for v in daily_values])
    start = dates[-1] + timedelta(days=1)
    for j in range(7):
        pred = max(0, int(round(intercept + slope * (len(daily_values) + j))))
        band = int(round(1.96 * rmse))
        out["points"].append({"date": (start + timedelta(days=j)).isoformat(), "predictedMicrousd": pred,
                              "lowerMicrousd": max(0, pred - band), "upperMicrousd": _check_integer(pred + band)})
    out["status"] = "available"
    return out


def _empty(source: str, now: datetime, days: int, message: str) -> dict[str, Any]:
    start_day = now.date() - timedelta(days=days - 1)
    daily = [{"date": (start_day + timedelta(days=i)).isoformat(), "attempts": 0, "succeeded": 0,
              "knownCostMicrousd": 0, "unknownCostRows": 0} for i in range(days)]
    return {"version": VERSION, "source": source, "generatedAt": _iso(now),
            "windowStart": _iso(datetime.combine(start_day, dt_time.min, timezone.utc)),
            "quality": {"scannedRows": 0, "selectedRows": 0, "unknownCostRows": 0, "invalidRows": 0,
                        "truncated": False, "selectionKnownCoverage": source in {"demo", "import"}, "message": message},
            "kpis": {"attempts": 0, "succeeded": 0, "failed": 0, "running": 0,
                     "knownCostMicrousd": 0, "costPerSuccessMicrousd": None, "successRate": None},
            "latency": {"count": 0, "p50": None, "p95": None, "mean": None, "stddev": None,
                        "histogram": [], "sampled": False}, "daily": daily, "cohorts": [],
            "heatmap": [], "graph": {"nodes": [], "edges": []},
            "forecast": _forecast([], [], True), "anomalies": [], "correlation": {"n": 0, "pearsonR": None},
            "scatter": [], "limitations": [message], "availableTools": []}


def _demo_events(now: datetime) -> list[dict[str, Any]]:
    # Stable formula-based synthetic data, anchored to current UTC date.
    rows = []
    anchor = now.date() - timedelta(days=27)
    for i in range(28):
        day = anchor + timedelta(days=i)
        count = 2 + (i * 7 % 5)
        for j in range(count):
            start = _date_epoch(day) + ((j * 3 + i) % 24) * 3600 + 120
            duration = 12 + ((i * 11 + j * 17) % 140)
            if start + duration > now.timestamp():
                continue
            outcome = "failed" if (i * 3 + j) % 13 == 0 else "succeeded"
            rows.append({"attemptId": f"demo-{i:02d}-{j:02d}", "taskId": f"demo-task-{(i+j)%9:02d}",
                         "tool": "model:demo-small" if j % 2 else "integration:demo:review",
                         "resource": "demo-pool-a" if j % 3 else "demo-pool-b", "startedAt": start,
                         "settledAt": start + duration, "outcome": outcome,
                         "actualCostMicrousd": 8 + (i * 19 + j * 23) % 170})
    return rows


def _read_live(db_path: str | Path, start_epoch: float, max_rows: int, timeout: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    p = Path(db_path)
    if not p.is_file():
        return [], {"scannedRows": 0, "invalidRows": 0, "truncated": False,
                    "selectionKnownCoverage": False, "message": "Ledger database is missing; no file was created."}
    uri = "file:" + quote(str(p.resolve()), safe="/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=min(1.0, timeout))
    conn.row_factory = sqlite3.Row
    deadline = time.monotonic() + timeout
    conn.set_progress_handler(lambda: 1 if time.monotonic() > deadline else 0, 1000)
    rows: list[dict[str, Any]] = []
    invalid = scanned = 0
    truncated = False
    message = None
    try:
        conn.execute("PRAGMA query_only=ON")
        conn.execute("BEGIN")
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "execution_attempts" not in tables:
            return [], {"scannedRows": 0, "invalidRows": 0, "truncated": False,
                        "selectionKnownCoverage": False, "message": "No execution_attempts ledger table is available."}
        query = ("SELECT attempt_id,task_id,tool_id,resource_id,started_at,settled_at,outcome,actual_cost_microusd "
                 "FROM execution_attempts WHERE started_at>=? ORDER BY started_at,attempt_id")
        cur = conn.execute(query, (start_epoch,))
        while True:
            if time.monotonic() > deadline:
                truncated, message = True, "Query time limit reached; results are partial."
                break
            chunk = cur.fetchmany(min(1000, max_rows - scanned + 1))
            if not chunk:
                break
            for row in chunk:
                scanned += 1
                if scanned > max_rows:
                    truncated, message = True, "Row limit reached; results are partial."
                    break
                try:
                    rows.append(_validate_event({"attemptId": row["attempt_id"], "taskId": row["task_id"],
                        "tool": row["tool_id"], "resource": row["resource_id"], "startedAt": row["started_at"],
                        "settledAt": row["settled_at"], "outcome": row["outcome"],
                        "actualCostMicrousd": row["actual_cost_microusd"]}))
                except (ValueError, TypeError, OverflowError):
                    invalid += 1
            if truncated:
                break
        # Reconcile each task independently. A global sum can hide a missing
        # attempt on one task behind an extra/malformed row on another.
        coverage = False
        if "tasks" in tables:
            try:
                mismatch = conn.execute("""
                    SELECT COUNT(*) FROM tasks t LEFT JOIN execution_attempts a ON a.task_id=t.task_id
                    GROUP BY t.task_id HAVING t.attempts != COUNT(a.attempt_id) LIMIT 1
                """).fetchone()
                orphans = conn.execute("""
                    SELECT COUNT(*) FROM execution_attempts a LEFT JOIN tasks t ON t.task_id=a.task_id
                    WHERE t.task_id IS NULL
                """).fetchone()[0]
                coverage = mismatch is None and orphans == 0
            except sqlite3.Error:
                coverage = False
        if not coverage:
            message = message or "Task attempt coverage could not be verified."
            # Retain a useful distinction for the common legacy partial-ledger case.
            if "tasks" in tables:
                message = "Legacy, missing, or inconsistent per-task attempt records make coverage incomplete."
        coverage = coverage and not truncated and invalid == 0
        return rows, {"scannedRows": min(scanned, max_rows), "invalidRows": invalid, "truncated": truncated,
                      "selectionKnownCoverage": coverage, "message": message}
    except sqlite3.Error:
        return [], {"scannedRows": scanned, "invalidRows": invalid, "truncated": True,
                    "selectionKnownCoverage": False, "message": "Ledger query failed; partial data was discarded."}
    finally:
        conn.close()


def _aggregate(source: str, raw_rows: Iterable[Any], *, days: int, tool_filter: str | None,
               now: datetime, base_quality: dict[str, Any]) -> dict[str, Any]:
    first_day = now.date() - timedelta(days=days - 1)
    start_epoch = _date_epoch(first_day)
    clean: list[dict[str, Any]] = []
    invalid = int(base_quality.get("invalidRows", 0))
    seen = set()
    for item in raw_rows:
        try:
            event = _validate_event(item)
            if event["startedAt"] > now.timestamp() or (event["settledAt"] is not None and event["settledAt"] > now.timestamp()):
                raise ValueError("future event time")
            if event["attemptId"] in seen:
                raise ValueError("duplicate")
            seen.add(event["attemptId"])
            if event["startedAt"] < start_epoch:
                continue
            if tool_filter is None or event["tool"] == tool_filter:
                clean.append(event)
        except (ValueError, TypeError, OverflowError):
            if source == "import":
                raise AnalyticsError("import contains an invalid or duplicate event")
            invalid += 1
    clean.sort(key=lambda e: (e["startedAt"], e["attemptId"]))
    scanned = int(base_quality.get("scannedRows", len(clean)))
    truncated = bool(base_quality.get("truncated", False))
    unknown = sum(e["actualCostMicrousd"] is None for e in clean)
    known_sum = _check_integer(sum(e["actualCostMicrousd"] or 0 for e in clean))
    succeeded = sum(e["outcome"] == "succeeded" for e in clean)
    failed = sum(e["outcome"] in {"failed", "cancelled"} for e in clean)
    running = sum(e["outcome"] in {"running", "unknown", "not_started", "expired_retryable"} for e in clean)
    success_rate = round(succeeded / len(clean), 6) if clean else None
    known_complete = not unknown and not truncated and invalid == 0 and bool(base_quality.get("selectionKnownCoverage", source in {"demo", "import"}))
    cost_per = int(round(known_sum / succeeded)) if succeeded and known_complete else None

    latencies = [e["settledAt"] - e["startedAt"] for e in clean if e["settledAt"] is not None]
    sampled = len(latencies) > MAX_METRIC_SAMPLE
    if sampled:
        sample = [latencies[(i * (len(latencies) - 1)) // (MAX_METRIC_SAMPLE - 1)] for i in range(MAX_METRIC_SAMPLE)]
    else:
        sample = list(latencies)
    sample.sort()
    percentile = lambda q: round(sample[min(len(sample)-1, int(math.ceil(q * len(sample)))-1)], 3) if sample else None
    mean = statistics.fmean(sample) if sample else None
    stdev = statistics.pstdev(sample) if len(sample) > 1 else (0.0 if sample else None)
    max_latency = max(sample, default=0)
    bins = min(MAX_HISTOGRAM_BINS, max(1, int(math.sqrt(len(sample))))) if sample else 0
    histogram = []
    if sample:
        width = max(max_latency / bins, 1e-9)
        counts = [0] * bins
        for value in sample:
            counts[min(bins - 1, int(value / width))] += 1
        histogram = [{"label": f"{i*width:.0f}-{(i+1)*width:.0f}s", "count": counts[i]} for i in range(bins)]

    daily_map = {first_day + timedelta(days=i): {"attempts": 0, "succeeded": 0, "cost": 0, "unknown": 0} for i in range(days)}
    cohorts = defaultdict(lambda: {"attempts": 0, "succeeded": 0, "cost": 0, "unknown": 0, "latencies": []})
    tool_counts = Counter()
    heat = Counter()
    graph_nodes = {}
    edge_map = defaultdict(lambda: {"attempts": 0, "cost": 0})
    cost_latency = []
    scatter_candidates = []
    for e in clean:
        dt = datetime.fromtimestamp(e["startedAt"], timezone.utc)
        d = dt.date()
        rec = daily_map[d]
        rec["attempts"] += 1
        rec["succeeded"] += e["outcome"] == "succeeded"
        if e["actualCostMicrousd"] is None:
            rec["unknown"] += 1
        else:
            rec["cost"] += e["actualCostMicrousd"]
        key = (e["tool"], e["resource"])
        c = cohorts[key]
        c["attempts"] += 1
        c["succeeded"] += e["outcome"] == "succeeded"
        c["unknown"] += e["actualCostMicrousd"] is None
        c["cost"] += e["actualCostMicrousd"] or 0
        if e["settledAt"] is not None:
            latency = e["settledAt"] - e["startedAt"]
            c["latencies"].append(latency)
            if e["actualCostMicrousd"] is not None:
                cost_latency.append((latency, e["actualCostMicrousd"]))
                scatter_candidates.append({"latencySeconds": round(latency, 3), "costMicrousd": e["actualCostMicrousd"]})
        tool_counts[e["tool"]] += 1
        heat[(dt.weekday(), dt.hour)] += 1
        tid = "tool:" + e["tool"]
        rid = "resource:" + e["resource"]
        graph_nodes[tid] = {"id": tid, "label": e["tool"], "kind": "tool"}
        graph_nodes[rid] = {"id": rid, "label": e["resource"], "kind": "resource"}
        edge = edge_map[(tid, rid)]
        edge["attempts"] += 1
        edge["cost"] += e["actualCostMicrousd"] or 0
    for d in daily_map:
        _check_integer(daily_map[d]["cost"])
    cohort_items = []
    for (tool, resource), v in cohorts.items():
        cohort_items.append({"tool": tool, "resource": resource, "attempts": v["attempts"],
            "succeeded": v["succeeded"], "knownCostMicrousd": _check_integer(v["cost"]),
            "unknownCostRows": v["unknown"], "meanLatencySeconds": round(statistics.fmean(v["latencies"]), 3) if v["latencies"] else None})
    cohort_items.sort(key=lambda x: (-x["attempts"], x["tool"], x["resource"]))
    cohorts_truncated = len(cohort_items) > MAX_COHORTS
    cohort_items = cohort_items[:MAX_COHORTS]
    available_tools = sorted(tool_counts)
    tools_truncated = len(available_tools) > MAX_TOOLS
    available_tools = available_tools[:MAX_TOOLS]
    sorted_edge_rows = sorted(edge_map.items(), key=lambda p: (-p[1]["attempts"], p[0][0], p[0][1]))
    chosen_edges = []
    chosen_nodes = set()
    for (a, b), v in sorted_edge_rows:
        new_nodes = {a, b} - chosen_nodes
        if len(chosen_nodes) + len(new_nodes) > MAX_GRAPH_NODES:
            continue
        chosen_nodes.update(new_nodes)
        chosen_edges.append({"source": a, "target": b, "attempts": v["attempts"],
                             "knownCostMicrousd": _check_integer(v["cost"])})
    nodes = [graph_nodes[n] for n in sorted(chosen_nodes)]
    edges = chosen_edges
    graph_truncated = len(chosen_edges) < len(edge_map)
    scatter_candidates.sort(key=lambda p: (p["latencySeconds"], p["costMicrousd"]))
    scatter_sampled = len(scatter_candidates) > MAX_SCATTER
    if scatter_sampled:
        scatter = [scatter_candidates[(i * (len(scatter_candidates) - 1)) // (MAX_SCATTER - 1)] for i in range(MAX_SCATTER)]
    else:
        scatter = scatter_candidates
    correlation = None
    if len(cost_latency) >= 2:
        xs, ys = [p[0] for p in cost_latency], [p[1] for p in cost_latency]
        mx, my = statistics.fmean(xs), statistics.fmean(ys)
        den = math.sqrt(sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys))
        correlation = round(sum((x-mx)*(y-my) for x, y in zip(xs, ys)) / den, 6) if den else None
    daily = [{"date": d.isoformat(), "attempts": v["attempts"], "succeeded": v["succeeded"],
              "knownCostMicrousd": _check_integer(v["cost"]), "unknownCostRows": v["unknown"]}
             for d, v in daily_map.items()]
    # Today's UTC bucket is partial. Forecast only complete dates from first
    # observed activity through yesterday; zero-padding before that is not
    # evidence of zero spend.
    observed = [d for d, v in daily_map.items() if d < now.date() and v["attempts"] > 0]
    forecast_pairs = ([(d, v["cost"]) for d, v in daily_map.items()
                       if observed and observed[0] <= d < now.date()])
    forecast_dates = [p[0] for p in forecast_pairs]
    daily_costs = [p[1] for p in forecast_pairs]
    forecast_blocked = not known_complete or cohorts_truncated or tools_truncated or sampled or graph_truncated
    forecast = _forecast(daily_costs, forecast_dates, forecast_blocked)
    anomalies = []
    vals = [v for v in daily_costs if v > 0]
    if known_complete and len(vals) >= 6:
        med = statistics.median(vals)
        mad = statistics.median(abs(v-med) for v in vals)
        if mad > 0:
            for row in daily:
                z = 0.6745 * (row["knownCostMicrousd"] - med) / mad
                if abs(z) >= 3.5:
                    anomalies.append({"date": row["date"], "value": row["knownCostMicrousd"], "reason": "robust_mad_outlier"})
        anomalies = anomalies[:20]
    quality = {"scannedRows": scanned, "selectedRows": len(clean), "unknownCostRows": unknown,
        "invalidRows": invalid, "truncated": truncated, "selectionKnownCoverage": bool(base_quality.get("selectionKnownCoverage", source in {"demo", "import"})) and not truncated and invalid == 0,
        "cohortsTruncated": cohorts_truncated, "toolsTruncated": tools_truncated,
        "scatterSampled": scatter_sampled, "latencySampled": sampled,
        "graphTruncated": graph_truncated, "message": base_quality.get("message")}
    limitations = []
    if source == "demo": limitations.append("Synthetic 28-day deterministic fixture; not observed execution data.")
    if source == "import": limitations.append("Imported rows are only as complete as the caller-provided snapshot.")
    if source == "live" and not quality["selectionKnownCoverage"]: limitations.append("Ledger coverage is incomplete or could not be verified.")
    if unknown: limitations.append("Unknown costs are liabilities, not zero; unit-cost and forecast claims are suppressed.")
    if truncated: limitations.append("Result is partial because a query bound was reached.")
    if sampled or scatter_sampled: limitations.append("Latency/scatter summaries use deterministic evenly spaced bounded samples.")
    if graph_truncated: limitations.append("Graph contains the highest-volume edges that fit the node bound.")
    if not limitations: limitations.append("Local ledger analytics; not a warehouse-scale or predictive guarantee.")
    return {"version": VERSION, "source": source, "generatedAt": _iso(now),
        "windowStart": _iso(datetime.combine(first_day, dt_time.min, timezone.utc)), "quality": quality,
        "kpis": {"attempts": len(clean), "succeeded": succeeded, "failed": failed, "running": running,
                 "knownCostMicrousd": known_sum, "costPerSuccessMicrousd": cost_per, "successRate": success_rate},
        "latency": {"count": len(latencies), "p50": percentile(.5), "p95": percentile(.95),
            "mean": round(mean, 3) if mean is not None else None, "stddev": round(stdev, 3) if stdev is not None else None,
            "histogram": histogram, "sampled": sampled}, "daily": daily, "cohorts": cohort_items,
        "heatmap": [{"day": d, "hour": h, "count": heat[(d, h)]} for d, h in sorted(heat)],
        "graph": {"nodes": nodes, "edges": edges}, "forecast": forecast, "anomalies": anomalies,
        "correlation": {"n": len(cost_latency), "pearsonR": correlation}, "scatter": scatter,
        "limitations": limitations, "availableTools": available_tools}


def build_analytics(request: dict[str, Any], *, db_path: str | Path | None = None,
                    now: datetime | int | float | None = None,
                    max_rows: int = MAX_LIVE_ROWS, query_timeout_seconds: float = 5.0) -> dict[str, Any]:
    """Build a bounded analytics response from demo, imported, or live ledger rows."""
    if not isinstance(request, dict) or set(request) - {"source", "days", "tool", "rows"}:
        raise AnalyticsError("request has unsupported fields")
    source = request.get("source")
    if source not in {"live", "demo", "import"}:
        raise AnalyticsError("source must be live, demo, or import")
    if source != "import" and "rows" in request:
        raise AnalyticsError("rows are only accepted for import source")
    days = request.get("days", 30)
    if isinstance(days, bool) or not isinstance(days, int) or not 1 <= days <= 365:
        raise AnalyticsError("days must be an integer from 1 to 365")
    tool = request.get("tool")
    if tool is not None:
        try:
            tool = _safe_text(tool, "tool")
        except ValueError as exc:
            raise AnalyticsError("tool filter is invalid") from exc
    current = _utc_now(now)
    max_rows = min(MAX_LIVE_ROWS, max_rows) if isinstance(max_rows, int) and max_rows > 0 else MAX_LIVE_ROWS
    if not isinstance(query_timeout_seconds, (int, float)) or not math.isfinite(query_timeout_seconds) or query_timeout_seconds <= 0:
        raise AnalyticsError("query timeout must be positive")
    base: dict[str, Any]
    if source == "demo":
        rows = _demo_events(current)
        base = {"scannedRows": len(rows), "invalidRows": 0, "truncated": False, "selectionKnownCoverage": True}
    elif source == "import":
        rows = request.get("rows")
        if not isinstance(rows, list) or len(rows) > MAX_IMPORT_ROWS:
            raise AnalyticsError("import rows must be an array of at most 10000 events")
        base = {"scannedRows": len(rows), "invalidRows": 0, "truncated": False, "selectionKnownCoverage": True}
    else:
        if db_path is None:
            raise AnalyticsError("live source requires a server-provided database path")
        start_epoch = _date_epoch(current.date() - timedelta(days=days - 1))
        rows, base = _read_live(db_path, start_epoch, max_rows, float(query_timeout_seconds))
    result = _aggregate(source, rows, days=days, tool_filter=tool, now=current, base_quality=base)
    if source == "demo":
        result["limitations"].insert(0, "Demo timestamps are anchored to generatedAt and span 28 UTC dates.")
    if source == "live" and not rows and base.get("message"):
        result["quality"]["message"] = base["message"]
        result["limitations"].insert(0, base["message"])
    return result


def main() -> int:
    try:
        payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(payload) > MAX_INPUT_BYTES:
            raise AnalyticsError("request exceeds 2 MiB")
        request = json.loads(payload.decode("utf-8"))
        if not isinstance(request, dict):
            raise AnalyticsError("request must be a JSON object")
        allowed = {"source", "days", "tool", "rows", "dbPath"}
        if set(request) - allowed:
            raise AnalyticsError("request has unsupported fields")
        db_path = request.pop("dbPath", None)
        if db_path is not None and (not isinstance(db_path, str) or len(db_path) > 4096):
            raise AnalyticsError("invalid database path")
        response = build_analytics(request, db_path=db_path)
        sys.stdout.write(json.dumps(response, separators=(",", ":"), ensure_ascii=True, allow_nan=False))
        return 0
    except (AnalyticsError, UnicodeDecodeError, json.JSONDecodeError):
        sys.stderr.write("analytics request rejected\n")
        return 2
    except Exception:
        # Never expose local paths, SQL errors, or event contents in CLI errors.
        sys.stderr.write("analytics unavailable\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
