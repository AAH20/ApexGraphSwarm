"""Adversarial checks for bounded, read-only attempt analytics."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path

from apexgraphswarm.analytics import AnalyticsError, build_analytics


NOW = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)


def event(attempt_id, day, *, tool="model:alpha", resource="pool-a", hour=10,
          cost=100, outcome="succeeded", duration=30):
    started = datetime.combine(day, datetime.min.time(), timezone.utc).timestamp() + hour * 3600
    return {"attemptId": attempt_id, "taskId": f"task-{attempt_id}", "tool": tool,
            "resource": resource, "startedAt": started,
            "settledAt": started + duration if outcome != "running" else None,
            "outcome": outcome, "actualCostMicrousd": cost}


def daily_rows(count=20):
    # Use the latest `count` UTC dates and one settled event per date.
    return [event(f"a-{i}", NOW.date().fromordinal(NOW.date().toordinal() - count + 1 + i),
                  cost=100 + i * 10) for i in range(count)]


class AnalyticsAdversarialTests(unittest.TestCase):
    def test_request_and_row_validation_fail_closed_or_count_invalid_rows(self):
        for request in (
            {"source": "live", "days": True},
            {"source": "live", "days": 366},
            {"source": "demo", "unexpected": "field"},
        ):
            with self.subTest(request=request), self.assertRaises(AnalyticsError):
                build_analytics(request, db_path=":memory:", now=NOW)

        with self.assertRaises(ValueError):
            build_analytics({"source": "import", "tool": "bad\nfilter", "rows": []}, now=NOW)
        valid = event("valid", NOW.date())
        duplicate = dict(valid)
        malformed = dict(event("bad", NOW.date()), unexpected="payload")
        for rows in ([valid, duplicate], [valid, malformed]):
            with self.subTest(rows=rows), self.assertRaises(AnalyticsError):
                build_analytics({"source": "import", "days": 30, "rows": rows}, now=NOW)

    def test_utc_daily_heatmap_and_exact_tool_filter(self):
        day = date(2026, 9, 26)
        rows = [event("utc-a", day, tool="model:alpha", hour=23),
                event("utc-b", date(2026, 9, 27), tool="model:beta", hour=1)]
        report = build_analytics({"source": "import", "days": 3,
                                  "tool": "model:alpha", "rows": rows}, now=NOW)
        self.assertEqual(report["kpis"]["attempts"], 1)
        self.assertEqual({cohort["tool"] for cohort in report["cohorts"]}, {"model:alpha"})
        self.assertEqual(report["availableTools"], ["model:alpha"])
        self.assertEqual(report["daily"][-2]["date"], "2026-09-26")
        self.assertEqual(report["daily"][-2]["attempts"], 1)
        self.assertEqual(report["heatmap"], [{"day": 5, "hour": 23, "count": 1}])

    def test_import_rejects_started_or_settled_events_after_as_of_time(self):
        base = event("future-base", NOW.date(), hour=8)
        future_start = event("future-start", NOW.date(), hour=13)
        with self.assertRaises(AnalyticsError):
            build_analytics({"source": "import", "days": 2, "rows": [base, future_start]}, now=NOW)
        future_settlement = event("future-settlement", NOW.date(), hour=11)
        future_settlement["settledAt"] = NOW.timestamp() + 60
        with self.assertRaises(AnalyticsError):
            build_analytics({"source": "import", "days": 2,
                             "rows": [base, future_settlement]}, now=NOW)

    def test_forecast_exposes_nonoverlapping_training_and_holdout_dates(self):
        rows = daily_rows(20)
        report = build_analytics({"source": "import", "days": 20, "rows": rows}, now=NOW)
        forecast = report["forecast"]
        self.assertEqual(forecast["status"], "available")
        self.assertEqual(len(forecast["trainingDates"]), 16)
        self.assertEqual(len(forecast["holdoutDates"]), 3)
        self.assertFalse(set(forecast["trainingDates"]) & set(forecast["holdoutDates"]))
        self.assertEqual(forecast["trainingDates"] + forecast["holdoutDates"],
                         [item["date"] for item in report["daily"] if item["date"] < NOW.date().isoformat()])
        self.assertNotIn(NOW.date().isoformat(), forecast["holdoutDates"])
        # The fixed-origin naive baseline must not roll forward through holdout actuals.
        self.assertEqual(forecast["naiveMAE"], 20.0)

        changed_holdout = [dict(row) for row in rows]
        for row in changed_holdout[-3:]:
            row["actualCostMicrousd"] *= 100
        changed = build_analytics({"source": "import", "days": 20, "rows": changed_holdout}, now=NOW)["forecast"]
        self.assertEqual(changed["trainingDates"], forecast["trainingDates"])
        self.assertEqual(changed["holdoutDates"], forecast["holdoutDates"])
        self.assertNotEqual(changed["backtestMAE"], forecast["backtestMAE"])

    def test_unknown_cost_blocks_unit_economics_and_forecast_without_zero_imputation(self):
        rows = daily_rows(20)
        rows[4]["actualCostMicrousd"] = None
        rows[8]["actualCostMicrousd"] = 1_000_000
        report = build_analytics({"source": "import", "days": 20, "rows": rows}, now=NOW)
        self.assertEqual(report["quality"]["unknownCostRows"], 1)
        self.assertIsNone(report["kpis"]["costPerSuccessMicrousd"])
        self.assertEqual(report["forecast"]["status"], "blocked_incomplete_coverage")
        self.assertEqual(report["daily"][4]["unknownCostRows"], 1)
        self.assertEqual(report["anomalies"], [])

    def test_forecast_does_not_treat_pre_observation_days_as_zero_history(self):
        rows = [event(f"recent-{i}", date(2026, 9, 17 + i), cost=100 + i)
                for i in range(10)]
        report = build_analytics({"source": "import", "days": 30, "rows": rows}, now=NOW)
        self.assertEqual(report["forecast"]["status"], "insufficient_data")
        self.assertEqual(report["forecast"]["trainingDates"], [])
        self.assertEqual(report["forecast"]["holdoutDates"], [])

    def _make_db(self, path, count=4):
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE execution_attempts (attempt_id TEXT, task_id TEXT, tool_id TEXT, resource_id TEXT, started_at REAL, settled_at REAL, outcome TEXT, actual_cost_microusd INTEGER)")
            db.execute("CREATE TABLE tasks (task_id TEXT, attempts INTEGER)")
            day = NOW.date()
            for i in range(count):
                item = event(f"live-{i}", day, hour=i + 1)
                db.execute("INSERT INTO execution_attempts VALUES (?,?,?,?,?,?,?,?)",
                           (item["attemptId"], item["taskId"], item["tool"], item["resource"],
                            item["startedAt"], item["settledAt"], item["outcome"], item["actualCostMicrousd"]))
                db.execute("INSERT INTO tasks VALUES (?,1)", (item["taskId"],))

    def test_live_source_is_read_only_and_row_cap_suppresses_favorable_metrics(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.sqlite"
            self._make_db(path)
            before = path.read_bytes()
            report = build_analytics({"source": "live", "days": 7}, db_path=path,
                                     now=NOW, max_rows=2)
            after = path.read_bytes()
            self.assertEqual(before, after)
            self.assertTrue(report["quality"]["truncated"])
            self.assertTrue(report["quality"]["selectionKnownCoverage"] is False)
            self.assertIsNone(report["kpis"]["costPerSuccessMicrousd"])
            self.assertEqual(report["forecast"]["status"], "blocked_incomplete_coverage")
            self.assertLessEqual(report["quality"]["scannedRows"], 2)

    def test_missing_database_is_not_created_and_cli_source_cannot_choose_a_path(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.sqlite"
            report = build_analytics({"source": "live"}, db_path=path, now=NOW)
            self.assertFalse(path.exists())
            self.assertIn("missing", report["quality"]["message"].lower())
            self.assertFalse(report["quality"]["selectionKnownCoverage"])

    def test_live_coverage_is_checked_per_task_not_only_by_global_attempt_total(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mismatched-coverage.sqlite"
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("CREATE TABLE execution_attempts (attempt_id TEXT, task_id TEXT, tool_id TEXT, resource_id TEXT, started_at REAL, settled_at REAL, outcome TEXT, actual_cost_microusd INTEGER)")
                db.execute("CREATE TABLE tasks (task_id TEXT, attempts INTEGER)")
                db.execute("INSERT INTO tasks VALUES ('task-a',2)")
                db.execute("INSERT INTO tasks VALUES ('task-b',0)")
                for attempt, task in (("a1", "task-a"), ("b1", "task-b")):
                    item = event(attempt, NOW.date(), hour=2)
                    db.execute("INSERT INTO execution_attempts VALUES (?,?,?,?,?,?,?,?)",
                               (attempt, task, item["tool"], item["resource"], item["startedAt"],
                                item["settledAt"], item["outcome"], item["actualCostMicrousd"]))
            report = build_analytics({"source": "live", "days": 7}, db_path=path, now=NOW)
            self.assertFalse(report["quality"]["selectionKnownCoverage"])
            self.assertIsNone(report["kpis"]["costPerSuccessMicrousd"])
            self.assertEqual(report["forecast"]["status"], "blocked_incomplete_coverage")

    def test_live_coverage_rejects_orphan_attempt_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "orphan.sqlite"
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("CREATE TABLE execution_attempts (attempt_id TEXT, task_id TEXT, tool_id TEXT, resource_id TEXT, started_at REAL, settled_at REAL, outcome TEXT, actual_cost_microusd INTEGER)")
                db.execute("CREATE TABLE tasks (task_id TEXT, attempts INTEGER)")
                db.execute("INSERT INTO tasks VALUES ('known-task',0)")
                item = event("orphan", NOW.date())
                db.execute("INSERT INTO execution_attempts VALUES (?,?,?,?,?,?,?,?)",
                           (item["attemptId"], "missing-task", item["tool"], item["resource"],
                            item["startedAt"], item["settledAt"], item["outcome"], item["actualCostMicrousd"]))
            report = build_analytics({"source": "live", "days": 7}, db_path=path, now=NOW)
            self.assertFalse(report["quality"]["selectionKnownCoverage"])
            self.assertIsNone(report["kpis"]["costPerSuccessMicrousd"])

    def test_live_future_started_or_settled_events_are_invalid_and_not_observed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.sqlite"
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("CREATE TABLE execution_attempts (attempt_id TEXT, task_id TEXT, tool_id TEXT, resource_id TEXT, started_at REAL, settled_at REAL, outcome TEXT, actual_cost_microusd INTEGER)")
                db.execute("CREATE TABLE tasks (task_id TEXT, attempts INTEGER)")
                cases = [("future-start", NOW.timestamp() + 3600, NOW.timestamp() + 3660),
                         ("future-settlement", NOW.timestamp() - 3600, NOW.timestamp() + 60)]
                for attempt, started, settled in cases:
                    db.execute("INSERT INTO tasks VALUES (?,1)", (attempt,))
                    db.execute("INSERT INTO execution_attempts VALUES (?,?,?,?,?,?,?,?)",
                               (attempt, attempt, "model:alpha", "pool-a", started, settled,
                                "succeeded", 100))
            report = build_analytics({"source": "live", "days": 7}, db_path=path, now=NOW)
            self.assertEqual(report["quality"]["invalidRows"], 2)
            self.assertEqual(report["quality"]["selectedRows"], 0)
            self.assertEqual(report["latency"]["count"], 0)
            self.assertFalse(report["quality"]["selectionKnownCoverage"])
            self.assertIsNone(report["kpis"]["costPerSuccessMicrousd"])

    def test_scatter_sampling_spans_sorted_observations_instead_of_first_rows(self):
        rows = [event(f"scatter-{i}", NOW.date(), tool="model:one", hour=1,
                      duration=i + 1, cost=100 + i) for i in range(250)]
        report = build_analytics({"source": "import", "days": 2, "rows": rows}, now=NOW)
        self.assertEqual(len(report["scatter"]), 200)
        self.assertTrue(report["quality"]["scatterSampled"])
        self.assertEqual(report["scatter"][0]["latencySeconds"], 1)
        self.assertEqual(report["scatter"][-1]["latencySeconds"], 250)


if __name__ == "__main__":
    unittest.main()
