"""Reproducible local analytics fixture; no providers, network, or production DB writes."""
from __future__ import annotations
import argparse
from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import sqlite3
import tempfile
import time
import tracemalloc
from apexgraphswarm.analytics import build_analytics


def benchmark(rows: int = 50000) -> dict:
    if not 1 <= rows <= 200000:
        raise ValueError('rows must be 1..200000')
    now = datetime(2026, 9, 27, 23, 59, 59, tzinfo=timezone.utc)
    with tempfile.TemporaryDirectory(prefix='apex-analytics-benchmark-') as directory:
        db_path = Path(directory) / 'fixture.sqlite'
        with closing(sqlite3.connect(db_path)) as db, db:
            db.execute('CREATE TABLE execution_attempts (attempt_id TEXT PRIMARY KEY,task_id TEXT,tool_id TEXT,resource_id TEXT,started_at REAL,settled_at REAL,outcome TEXT,actual_cost_microusd INTEGER)')
            db.execute('CREATE TABLE tasks (task_id TEXT PRIMARY KEY, attempts INTEGER)')
            for offset in range(0, rows, 1000):
                events = []
                tasks = []
                for i in range(offset, min(rows, offset + 1000)):
                    start = now.timestamp() - (1 + i % 28) * 86400 + i % 3600
                    events.append((f'a{i}', f't{i}', f'tool-{i%4}', f'resource-{i%12}', start, start + 1 + i%120, 'succeeded' if i%9 else 'failed', None if i%97 == 0 else 20+i%700))
                    tasks.append((f't{i}',1))
                db.executemany('INSERT INTO execution_attempts VALUES(?,?,?,?,?,?,?,?)', events)
                db.executemany('INSERT INTO tasks VALUES(?,?)', tasks)
        tracemalloc.start()
        started = time.perf_counter()
        result = build_analytics({'source':'live','days':30},db_path=db_path,now=now)
        elapsed = time.perf_counter()-started
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {'fixtureVersion':1,'python':platform.python_version(),'platform':platform.system(),
                'rows':rows,'elapsedSeconds':round(elapsed,6),'peakPythonAllocationBytes':peak,
                'selectedRows':result['quality']['selectedRows'],'truncated':result['quality']['truncated'],
                'knownCostMicrousd':result['kpis']['knownCostMicrousd'],'unknownCostRows':result['quality']['unknownCostRows'],
                'forecastStatus':result['forecast']['status'],
                'limits':['Synthetic local SQLite fixture, not a production throughput benchmark.',
                          'tracemalloc measures Python allocations, not total RSS or SQLite native memory.',
                          'Instrumentation adds overhead; wall time is machine-specific.']}

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows',type=int,default=50000)
    args=parser.parse_args()
    print(json.dumps(benchmark(args.rows),indent=2))
