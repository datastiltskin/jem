#!/usr/bin/env bash
# Daily JEM pipeline — does NOT run generate_v1_states_bundle.py (preserves hand-edited / curated YAML).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> validate --strict"
python3 scripts/validate.py --strict
echo "==> derive"
python3 scripts/derive.py
echo "==> build"
python3 scripts/build.py
echo "==> Done (safe pipeline; entities unchanged by generator)"
