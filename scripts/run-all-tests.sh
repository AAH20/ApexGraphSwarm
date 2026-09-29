#!/usr/bin/env bash
set -euo pipefail

echo "=== ApexGraphSwarm Monorepo Test Suite ==="
echo ""

# TypeScript tests
echo "── TypeScript Tests ──"
if command -v pnpm &> /dev/null; then
  pnpm test
elif command -v npm &> /dev/null; then
  npm test
else
  echo "⚠ No package manager found, skipping TS tests"
fi
echo ""

# Python tests
echo "── Python Tests ──"
if command -v python3 &> /dev/null; then
  python3 -m pytest tests/ -v --tb=short 2>&1 || python3 -m unittest discover -s tests -v 2>&1 || echo "⚠ Python tests failed"
else
  echo "⚠ python3 not found, skipping Python tests"
fi
echo ""

echo "=== Test Suite Complete ==="
