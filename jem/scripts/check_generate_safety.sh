#!/usr/bin/env bash
# Git safety net: list hand-maintained paths and optional diff after generate.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA="$ROOT/data"
MANIFEST="$DATA/HAND_MAINTAINED.yaml"

echo "=== JEM hand-maintained manifest ==="
if [[ -f "$MANIFEST" ]]; then
  cat "$MANIFEST"
else
  echo "WARN: missing $MANIFEST"
fi

echo ""
echo "=== Curated entity files ==="
find "$DATA/entities/_curated" -name '*.yaml' 2>/dev/null | sort || true

echo ""
echo "=== Curated relationship overlays ==="
find "$DATA/relationships/_curated" -name '*.yaml' 2>/dev/null | sort || true

if [[ "${1:-}" == "--post-generate" ]]; then
  echo ""
  echo "=== git diff (hand-maintained paths only) ==="
  git -C "$(cd "$ROOT/.." && pwd)" diff -- \
    jem/data/HAND_MAINTAINED.yaml \
    jem/data/entities/_curated \
    jem/data/relationships/_curated \
    2>/dev/null || true
  if git -C "$(cd "$ROOT/.." && pwd)" diff --quiet -- jem/data/entities/_curated jem/data/relationships/_curated 2>/dev/null; then
    echo "OK: no diff under curated trees"
  else
    echo "WARN: curated files changed — review before commit"
    exit 1
  fi
fi
