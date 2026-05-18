#!/usr/bin/env bash
# Regenerate with safety checks. Default: relationship YAML only (no entity overwrite).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
ONLY="${1:-relationships}"
FORCE="${FORCE:-}"

echo "==> Pre-check"
bash scripts/check_generate_safety.sh

OPTS=(--only "$ONLY")
if [[ "$FORCE" == "1" ]]; then
  OPTS+=(--force)
fi

echo "==> generate_v1_states_bundle.py ${OPTS[*]}"
python3 scripts/generate_v1_states_bundle.py "${OPTS[@]}"

echo "==> Post-check"
bash scripts/check_generate_safety.sh --post-generate

echo "==> validate --strict"
python3 scripts/validate.py --strict

echo "==> Done"
