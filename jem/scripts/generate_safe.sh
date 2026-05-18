#!/usr/bin/env bash
# Regenerate relationship YAML only by default (avoids overwriting entity passes).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ONLY="${1:-relationships}"
echo "==> generate_v1_states_bundle.py --only $ONLY"
python3 scripts/generate_v1_states_bundle.py --only "$ONLY"
echo "==> validate --strict"
python3 scripts/validate.py --strict
