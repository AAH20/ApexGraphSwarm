"""Example 16: Analytics from live ledger database.

Read analytics directly from an existing ControlStore SQLite
database in read-only mode.
"""
from apexgraphswarm.analytics import build_analytics
from datetime import datetime, timezone
import tempfile
import sqlite3
from pathlib import Path

now = datetime(2026, 9, 27, 12, 0, tzinfo=timezone.utc)

# Create a temporary ledger database
with tempfile.TemporaryDirectory() as d:
    db_path = Path(d) / "ledger.sqlite"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
        CREATE TABLE execution_attempts(
            attempt_id TEXT, task_id TEXT, tool_id TEXT, resource_id TEXT,
            started_at REAL, settled_at REAL, outcome TEXT, actual_cost_microusd INTEGER
        );
        CREATE TABLE tasks(task_id TEXT, attempts INTEGER);
    """)
    # Insert sample data
    for i in range(10):
        conn.execute(
            "INSERT INTO execution_attempts VALUES(?,?,?,?,?,?,?,?)",
            (f"a-{i}", f"t-{i}", "model:test", "pool-a",
             1727438400 + i * 3600, 1727438400 + i * 3600 + 10,
             "succeeded" if i % 3 else "failed", 100 + i * 10),
        )
    conn.execute("INSERT INTO tasks VALUES('t-1', 2)")
    conn.commit()
    conn.close()

    # Read analytics from the live database
    result = build_analytics(
        {"source": "live", "days": 30},
        db_path=db_path,
        now=now,
    )
    print(f"Live attempts: {result['kpis']['attempts']}")
    print(f"Live succeeded: {result['kpis']['succeeded']}")
    print(f"Quality message: {result['quality']['message']}")
    print(f"Known coverage: {result['quality']['selectionKnownCoverage']}")
