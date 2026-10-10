#!/usr/bin/env bash
# Fuzzing suite runner for ApexGraphSwarm
# Runs Python (hypothesis) and JavaScript (fast-check) property-based fuzz tests
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "=== ApexGraphSwarm Fuzzing Suite ==="
echo ""

# --- Python fuzzing ---
echo "--- Python fuzzing (hypothesis) ---"
python3 -m pytest tests/fuzzing/test_python_fuzzing.py -v --tb=short 2>&1 || {
    echo "Python fuzzing failed"
    exit 1
}
echo ""

# --- JavaScript fuzzing ---
echo "--- JavaScript fuzzing (fast-check) ---"
cd apps/web
node --import tsx --test tests/fuzzing/graph-parsers.test.ts 2>&1 || {
    echo "JavaScript fuzzing failed"
    exit 1
}
echo ""

echo "=== All fuzzing suites passed ==="
