#!/usr/bin/env bash
# Daily JEM pipeline — validate, derive, build. Does not run the bundle generator.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
echo "==> validate --strict"
python3 scripts/validate.py --strict
echo "==> validate graph refs"
python3 scripts/validate_graph_refs.py
echo "==> derive"
python3 scripts/derive.py
echo "==> build"
python3 scripts/build.py
echo "==> Done"
