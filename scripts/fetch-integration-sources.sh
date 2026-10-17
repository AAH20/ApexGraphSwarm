#!/usr/bin/env bash
# Check out the sibling kernel repos the integration tests import.
# These are separate repositories; .integration-sources/ is a checkout, not a
# vendored copy, so nothing here is duplicated in this repo.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$ROOT/.integration-sources"
ORG="${APEX_GH_ORG:-AAH20}"
REPOS=(
  agentic-graph-swarm-kernel
  agentic-np-hard-kernel
  graph-rag-np-hard-kernel
  mirofish-swarm-optimizer
)
mkdir -p "$DEST"
for r in "${REPOS[@]}"; do
  if [ -d "$DEST/$r/.git" ]; then
    echo "updating $r"; git -C "$DEST/$r" pull --ff-only --quiet || true
  else
    echo "cloning $r"; git clone --depth 1 --quiet "https://github.com/$ORG/$r.git" "$DEST/$r"
  fi
done
echo "integration sources ready in $DEST"
