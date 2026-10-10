#!/usr/bin/env bash
set -euo pipefail

echo "=== ApexGraphSwarm Monorepo Build ==="
echo ""

# Build TypeScript packages
echo "── Building TypeScript Packages ──"
if command -v pnpm &> /dev/null; then
  pnpm build
elif command -v npm &> /dev/null; then
  npm run build
else
  echo "⚠ No package manager found, skipping TS build"
fi
echo ""

# Build Python packages
echo "── Building Python Packages ──"
if command -v python3 &> /dev/null; then
  python3 -m pip install -e . --quiet 2>&1 || echo "⚠ Python install failed"
  python3 -m pip install -e ./kernels --quiet 2>&1 || echo "⚠ Kernels install failed"
else
  echo "⚠ python3 not found, skipping Python build"
fi
echo ""

echo "=== Build Complete ==="
