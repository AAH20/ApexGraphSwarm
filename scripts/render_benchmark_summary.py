#!/usr/bin/env python3
"""Render the CI benchmark report as GitHub step-summary markdown.

Extracted from an inline `python3 -c "..."` in benchmark.yml. Two defects came with
the move and are fixed here:

1. The embedded source carried the YAML block scalar's indentation into Python,
   which raised "IndentationError: unexpected indent" on every run.
2. `open()` with no `encoding=` uses the PLATFORM default -- cp1252 on Windows --
   so a report containing any non-ASCII byte would fail to read there.

The script also tolerates a partial report: a missing key is reported as unknown
rather than raising, because a summary step should never be the thing that fails a
run whose measurements it is only describing.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPORT = Path("reports/ci-benchmark-report.json")

# Defined at module level: an f-string expression part cannot contain a backslash
# before Python 3.12, so the escapes cannot live inside the f-strings below.
PASS = "\u2705"
FAIL = "\u274c"
SKIP = "\u23ed\ufe0f"
WARN = "\u26a0\ufe0f"
ICONS = {"pass": PASS, "fail": FAIL}


def main() -> int:
    if not REPORT.is_file():
        print(f"No benchmark report at {REPORT} -- nothing was measured.")
        return 0

    try:
        # encoding is explicit: the platform default is not UTF-8 on Windows.
        report = json.loads(REPORT.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        print(f"Benchmark report unreadable ({type(exc).__name__}: {exc}).")
        return 0

    status = "PASS" if report.get("status") == "pass" else "FAIL"
    print(f"### {PASS if status == 'PASS' else FAIL} {status}")
    print()
    print("| Benchmark | Status |")
    print("|-----------|--------|")
    for name, result in (report.get("benchmarks") or {}).items():
        state = (result or {}).get("status", "unknown")
        icon = ICONS.get(state, SKIP)
        print(f"| {name} | {icon} {state} |")

    regressions = report.get("regressions") or []
    if regressions:
        print()
        print(f"### {WARN} {len(regressions)} Performance Regression(s)")
        print()
        for reg in regressions:
            reg = reg or {}
            scenario = reg.get("scenario", reg.get("benchmark", "unknown"))
            metric = reg.get("metric", "unknown")
            change = reg.get("changePercent")
            threshold = reg.get("threshold")
            change_s = f"{change:+.1f}%" if isinstance(change, (int, float)) else "n/a"
            thr_s = f"{threshold:+.1f}%" if isinstance(threshold, (int, float)) else "n/a"
            print(f"- **{scenario}**: {metric} {change_s} (threshold: {thr_s})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
