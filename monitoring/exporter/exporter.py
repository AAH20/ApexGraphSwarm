#!/usr/bin/env python3
"""Prometheus exporter for ApexGraphSwarm.

Reads from the SQLite control store and exposes metrics in Prometheus format.
Runs an HTTP server on port 8000 by default.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DEFAULT_DB_PATH = os.environ.get("APEXGRAPH_DB", "./control.db")
DEFAULT_PORT = int(os.environ.get("APEXGRAPH_METRICS_PORT", "8000"))
DEFAULT_INTERVAL = int(os.environ.get("APEXGRAPH_SCRAPE_INTERVAL", "15"))

OUTCOMES = ("succeeded", "failed", "cancelled", "running", "unknown", "not_started", "expired_retryable")


class MetricsRegistry:
    """Thread-safe metrics registry."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._gauges: dict[str, dict[str, Any]] = {}
        self._counters: dict[str, dict[str, Any]] = {}
        self._histograms: dict[str, dict[str, Any]] = {}
        self._errors = 0
        self._last_scrape: float | None = None

    def set_gauge(self, name: str, labels: dict[str, str], value: float, help_text: str = "") -> None:
        with self._lock:
            key = name
            if key not in self._gauges:
                self._gauges[key] = {"help": help_text, "labels": labels, "value": value}
            else:
                self._gauges[key]["labels"] = labels
                self._gauges[key]["value"] = value

    def inc_counter(self, name: str, labels: dict[str, str], value: float = 1.0, help_text: str = "") -> None:
        with self._lock:
            key = name
            label_key = json.dumps(labels, sort_keys=True)
            if key not in self._counters:
                self._counters[key] = {"help": help_text, "series": {}}
            self._counters[key]["series"][label_key] = {"labels": labels, "value": value}

    def observe_histogram(self, name: str, labels: dict[str, str], value: float, help_text: str = "") -> None:
        with self._lock:
            key = name
            label_key = json.dumps(labels, sort_keys=True)
            if key not in self._histograms:
                self._histograms[key] = {"help": help_text, "series": {}}
            self._histograms[key]["series"][label_key] = {"labels": labels, "value": value}

    def inc_errors(self) -> None:
        with self._lock:
            self._errors += 1

    def set_last_scrape(self, ts: float) -> None:
        with self._lock:
            self._last_scrape = ts

    def render(self) -> str:
        """Render all metrics in Prometheus text exposition format."""
        with self._lock:
            lines: list[str] = []

            # Gauges
            for name, data in sorted(self._gauges.items()):
                if data["help"]:
                    lines.append(f"# HELP {name} {data['help']}")
                lines.append(f"# TYPE {name} gauge")
                label_str = _format_labels(data["labels"])
                lines.append(f"{name}{label_str} {data['value']}")

            # Counters
            for name, data in sorted(self._counters.items()):
                if data["help"]:
                    lines.append(f"# HELP {name} {data['help']}")
                lines.append(f"# TYPE {name} counter")
                for series in data["series"].values():
                    label_str = _format_labels(series["labels"])
                    lines.append(f"{name}{label_str} {series['value']}")

            # Histograms (simplified - expose as summary)
            for name, data in sorted(self._histograms.items()):
                if data["help"]:
                    lines.append(f"# HELP {name} {data['help']}")
                lines.append(f"# TYPE {name} summary")
                for series in data["series"].values():
                    label_str = _format_labels(series["labels"])
                    lines.append(f"{name}_sum{label_str} {series['value']}")
                    lines.append(f"{name}_count{label_str} 1")

            # Exporter self-metrics
            lines.append("# HELP apexgraphswarm_exporter_errors_total Total exporter errors")
            lines.append("# TYPE apexgraphswarm_exporter_errors_total counter")
            lines.append(f"apexgraphswarm_exporter_errors_total {self._errors}")

            if self._last_scrape is not None:
                lines.append("# HELP apexgraphswarm_exporter_last_scrape_timestamp Unix timestamp of last scrape")
                lines.append("# TYPE apexgraphswarm_exporter_last_scrape_timestamp gauge")
                lines.append(f"apexgraphswarm_exporter_last_scrape_timestamp {self._last_scrape}")

            return "\n".join(lines) + "\n"


def _format_labels(labels: dict[str, str]) -> str:
    if not labels:
        return ""
    parts = [f'{k}="{v}"' for k, v in sorted(labels.items())]
    return "{" + ",".join(parts) + "}"


def collect_metrics(db_path: str, registry: MetricsRegistry) -> None:
    """Collect metrics from the SQLite control store."""
    if not Path(db_path).is_file():
        return

    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA query_only=ON")

        # Attempt outcomes
        rows = conn.execute("""
            SELECT outcome, COUNT(*) as count
            FROM execution_attempts
            GROUP BY outcome
        """).fetchall()
        for row in rows:
            registry.inc_counter(
                "apexgraphswarm_attempts_total",
                {"outcome": row["outcome"]},
                float(row["count"]),
                "Total attempts by outcome",
            )

        # Running attempts
        running = conn.execute("""
            SELECT COUNT(*) as count FROM execution_attempts WHERE outcome='running'
        """).fetchone()["count"]
        registry.set_gauge(
            "apexgraphswarm_attempts_running",
            {},
            float(running),
            "Currently running attempts",
        )

        # Task states
        for state in ("pending", "running", "succeeded", "failed", "cancelled", "blocked", "needs_reconciliation"):
            count = conn.execute(
                "SELECT COUNT(*) as count FROM tasks WHERE status=?", (state,)
            ).fetchone()["count"]
            registry.set_gauge(
                f"apexgraphswarm_tasks_{state}",
                {},
                float(count),
                f"Tasks in {state} state",
            )

        # Active agents
        agents = conn.execute("SELECT COUNT(*) as count FROM workers WHERE revoked=0").fetchone()["count"]
        registry.set_gauge(
            "apexgraphswarm_agents_active",
            {},
            float(agents),
            "Active (non-revoked) workers",
        )

        # Budget metrics per run
        runs = conn.execute("""
            SELECT run_id, budget_microusd, spent_microusd
            FROM runs WHERE budget_microusd IS NOT NULL
        """).fetchall()
        for run in runs:
            labels = {"run_id": run["run_id"]}
            registry.set_gauge(
                "apexgraphswarm_budget_microusd",
                labels,
                float(run["budget_microusd"]),
                "Budget in micro-USD",
            )
            registry.set_gauge(
                "apexgraphswarm_spent_microusd",
                labels,
                float(run["spent_microusd"] or 0),
                "Spent in micro-USD",
            )

        # Cost totals
        cost_rows = conn.execute("""
            SELECT run_id, SUM(actual_cost_microusd) as total
            FROM execution_attempts
            WHERE actual_cost_microusd IS NOT NULL
            GROUP BY run_id
        """).fetchall()
        for row in cost_rows:
            registry.inc_counter(
                "apexgraphswarm_cost_microusd_total",
                {"run_id": row["run_id"]},
                float(row["total"]),
                "Total cost in micro-USD",
            )

        # Resource utilization
        resource_rows = conn.execute("""
            SELECT resource_id, global_limit, global_occupied
            FROM resource_capacity
        """).fetchall()
        for row in resource_rows:
            labels = {"resource_id": row["resource_id"]}
            registry.set_gauge(
                "apexgraphswarm_resource_limit",
                labels,
                float(row["global_limit"] or 0),
                "Resource limit",
            )
            registry.set_gauge(
                "apexgraphswarm_resource_occupied",
                labels,
                float(row["global_occupied"] or 0),
                "Resource occupied",
            )

        # Attempt durations (for latency histogram)
        duration_rows = conn.execute("""
            SELECT run_id,
                   started_at, settled_at,
                   (settled_at - started_at) as duration
            FROM execution_attempts
            WHERE settled_at IS NOT NULL AND started_at IS NOT NULL
              AND outcome IN ('succeeded', 'failed', 'cancelled')
            ORDER BY settled_at DESC
            LIMIT 1000
        """).fetchall()
        for row in duration_rows:
            if row["duration"] is not None and row["duration"] >= 0:
                registry.observe_histogram(
                    "apexgraphswarm_attempt_duration_seconds",
                    {"run_id": row["run_id"]},
                    float(row["duration"]),
                    "Attempt duration in seconds",
                )

        # Attempts by tool
        tool_rows = conn.execute("""
            SELECT tool_id, COUNT(*) as count
            FROM execution_attempts
            WHERE tool_id IS NOT NULL
            GROUP BY tool_id
        """).fetchall()
        for row in tool_rows:
            registry.inc_counter(
                "apexgraphswarm_attempts_by_tool_total",
                {"tool": row["tool_id"]},
                float(row["count"]),
                "Attempts by tool",
            )

    except sqlite3.Error:
        registry.inc_errors()
    finally:
        conn.close()


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler for Prometheus metrics endpoint."""

    registry: MetricsRegistry = None  # type: ignore

    def do_GET(self) -> None:
        if self.path == "/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
            self.end_headers()
            self.wfile.write(self.registry.render().encode("utf-8"))
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"ok\n")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        pass  # Suppress request logging


def main() -> int:
    parser = argparse.ArgumentParser(description="ApexGraphSwarm Prometheus exporter")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to SQLite control store")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="HTTP port")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Scrape interval seconds")
    args = parser.parse_args()

    registry = MetricsRegistry()
    MetricsHandler.registry = registry

    # Initial scrape
    collect_metrics(args.db, registry)
    registry.set_last_scrape(time.time())

    # Start background scraper
    def scraper_loop() -> None:
        while True:
            time.sleep(args.interval)
            try:
                collect_metrics(args.db, registry)
                registry.set_last_scrape(time.time())
            except Exception:
                registry.inc_errors()

    thread = threading.Thread(target=scraper_loop, daemon=True)
    thread.start()

    # Start HTTP server
    server = HTTPServer(("0.0.0.0", args.port), MetricsHandler)
    print(f"ApexGraphSwarm exporter listening on :{args.port}", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
