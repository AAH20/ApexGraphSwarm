import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from apexgraphswarm.analytics import AnalyticsError, build_analytics


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)


def event(i, day, *, cost=10, outcome="succeeded", tool="model:test"):
    start = datetime(2026, 9, day, 10, i % 60, tzinfo=timezone.utc).timestamp()
    return {"attemptId": f"attempt-{i}", "taskId": f"task-{i}", "tool": tool,
            "resource": "pool-a", "startedAt": start, "settledAt": start + 10,
            "outcome": outcome, "actualCostMicrousd": cost}


class AnalyticsTests(unittest.TestCase):
    def test_import_metrics_timezone_filter_and_unknown_liability(self):
        rows = [event(1, 26), event(2, 27, cost=None, outcome="unknown"),
                event(3, 27, tool="integration:other:review")]
        result = build_analytics({"source": "import", "days": 30, "rows": rows}, now=NOW)
        self.assertEqual(result["kpis"]["attempts"], 3)
        self.assertEqual(result["kpis"]["succeeded"], 2)
        self.assertEqual(result["quality"]["unknownCostRows"], 1)
        self.assertIsNone(result["kpis"]["costPerSuccessMicrousd"])
        self.assertEqual(result["forecast"]["status"], "blocked_incomplete_coverage")
        self.assertEqual(result["latency"]["p50"], 10)
        filtered = build_analytics({"source": "import", "days": 30, "tool": "model:test", "rows": rows}, now=NOW)
        self.assertEqual(filtered["kpis"]["attempts"], 2)
        self.assertEqual(filtered["quality"]["selectedRows"], 2)
        self.assertEqual(filtered["heatmap"][0]["day"], 5)  # Saturday in UTC.

    def test_strict_request_and_row_validation_is_bounded(self):
        with self.assertRaises(AnalyticsError):
            build_analytics({"source": "import", "days": 366, "rows": []}, now=NOW)
        with self.assertRaises(AnalyticsError):
            build_analytics({"source": "import", "rows": [{"secret": "no"}]}, now=NOW)
        malformed = event(1, 27)
        malformed["receipt"] = "private"
        with self.assertRaises(AnalyticsError):
            build_analytics({"source": "import", "rows": [malformed]}, now=NOW)
        with self.assertRaises(AnalyticsError):
            build_analytics({"source": "import", "rows": [event(i, 27) for i in range(10_001)]}, now=NOW)

    def test_demo_is_deterministic_and_forecast_uses_disjoint_holdout(self):
        a = build_analytics({"source": "demo", "days": 30}, now=NOW)
        b = build_analytics({"source": "demo", "days": 30}, now=NOW)
        self.assertEqual(a, b)
        self.assertEqual(a["quality"]["selectedRows"], sum(x["attempts"] for x in a["daily"]))
        fc = a["forecast"]
        self.assertEqual(fc["status"], "available")
        self.assertEqual(len(fc["holdoutDates"]), 3)
        self.assertTrue(set(fc["trainingDates"]).isdisjoint(fc["holdoutDates"]))
        self.assertEqual(len(fc["points"]), 7)
        self.assertIn("not confidence intervals", " ".join(fc["limitations"]))
        self.assertLessEqual(len(a["scatter"]), 200)
        self.assertLessEqual(len(a["graph"]["nodes"]), 200)

    def test_live_missing_path_does_not_create_database(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "missing.sqlite"
            out = build_analytics({"source": "live"}, db_path=missing, now=NOW)
            self.assertFalse(missing.exists())
            self.assertEqual(out["kpis"]["attempts"], 0)
            self.assertFalse(out["quality"]["selectionKnownCoverage"])
            self.assertIn("missing", out["quality"]["message"])

    def test_live_reads_existing_ledger_readonly_and_detects_legacy_gap(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / "ledger.sqlite"
            conn = sqlite3.connect(db)
            conn.executescript("""
                CREATE TABLE execution_attempts(attempt_id TEXT, task_id TEXT, tool_id TEXT, resource_id TEXT,
                  started_at REAL, settled_at REAL, outcome TEXT, actual_cost_microusd INTEGER);
                CREATE TABLE tasks(task_id TEXT, attempts INTEGER);
                INSERT INTO tasks VALUES('task-1',2);
            """)
            e = event(1, 27)
            conn.execute("INSERT INTO execution_attempts VALUES(?,?,?,?,?,?,?,?)",
                         (e["attemptId"], e["taskId"], e["tool"], e["resource"], e["startedAt"],
                          e["settledAt"], e["outcome"], e["actualCostMicrousd"]))
            conn.commit()
            before = conn.execute("PRAGMA schema_version").fetchone()[0]
            conn.close()
            out = build_analytics({"source": "live", "days": 30}, db_path=db, now=NOW)
            self.assertEqual(out["kpis"]["attempts"], 1)
            self.assertFalse(out["quality"]["selectionKnownCoverage"])
            conn = sqlite3.connect(db)
            self.assertEqual(conn.execute("PRAGMA schema_version").fetchone()[0], before)
            conn.close()

    def test_import_forecast_requires_calendar_and_active_day_coverage(self):
        rows = [event(i, 20 + i) for i in range(8)]
        out = build_analytics({"source": "import", "days": 14, "rows": rows}, now=NOW)
        self.assertEqual(out["forecast"]["status"], "insufficient_data")
        self.assertEqual(out["forecast"]["holdoutDates"], [])

    def test_import_rejects_future_settlement_as_of_generated_time(self):
        row = event(1, 27)
        row["settledAt"] = NOW.timestamp() + 1
        with self.assertRaises(AnalyticsError):
            build_analytics({"source": "import", "rows": [row]}, now=NOW)


if __name__ == "__main__":
    unittest.main()
