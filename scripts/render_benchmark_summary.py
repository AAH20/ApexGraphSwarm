#!/usr/bin/env python3
"""Render the CI benchmark report as GitHub step-summary markdown.

Extracted from an inline `python3 -c "..."` in benchmark.yml. A YAML block scalar
preserves its indentation into the source, so every line of the embedded code began
with 12 spaces and the step died with "IndentationError: unexpected indent".
Keeping it in a real file removes the whole class of problem, and makes the script
testable on its own.
"""
from __future__ import annotations

import json
import sys

with open('reports/ci-benchmark-report.json') as f:
    report = json.load(f)

status = '✅ PASS' if report['status'] == 'pass' else '❌ FAIL'
print(f'### {status}')
print()
print('| Benchmark | Status |')
print('|-----------|--------|')
for name, result in report.get('benchmarks', {}).items():
    icon = '✅' if result['status'] == 'pass' else '❌' if result['status'] == 'fail' else '⏭️'
    print(f'| {name} | {icon} {result["status"]} |')

regressions = report.get('regressions', [])
if regressions:
    print()
    print(f'### ⚠️ {len(regressions)} Performance Regression(s)')
    print()
    for reg in regressions:
        scenario = reg.get('scenario', reg.get('benchmark', 'unknown'))
        print(f'- **{scenario}**: {reg["metric"]} {reg["changePercent"]:+.1f}% (threshold: {reg["threshold"]:+.1f}%)')
