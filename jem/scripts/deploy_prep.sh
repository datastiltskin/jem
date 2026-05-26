#!/usr/bin/env bash
# Pre-deploy checks for v1.0.0 — run from repo root or jem/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JEM_ROOT="${REPO_ROOT}/jem"
GRAPH="${REPO_ROOT}/graph.json"
PUBLIC_LINK="${JEM_ROOT}/web/public/graph.json"
MIN_ENTITIES=400

cd "${JEM_ROOT}"

echo "==> validate --strict"
python3 scripts/validate.py --strict

echo "==> validate graph refs"
python3 scripts/validate_graph_refs.py

if [[ ! -f "${GRAPH}" ]]; then
  echo "ERROR: missing ${GRAPH}" >&2
  exit 1
fi

COUNT="$(python3 -c "import json; print(json.load(open('${GRAPH}'))['meta'].get('entity_count', 0))")"
RELS="$(python3 -c "import json; print(json.load(open('${GRAPH}'))['meta'].get('relationship_count', 0))")"
SIZE="$(wc -c < "${GRAPH}" | tr -d ' ')"

echo "==> graph.json meta.entity_count=${COUNT} relationship_count=${RELS} size=${SIZE} bytes"

if [[ "${COUNT}" -lt "${MIN_ENTITIES}" ]]; then
  echo "ERROR: entity_count ${COUNT} < ${MIN_ENTITIES} — likely partial build; see docs/V1_DATA_RESTORE.md" >&2
  exit 1
fi

PLACEHOLDERS="$(python3 -c "
import json
g=json.load(open('${GRAPH}'))
print(sum(1 for e in g.get('entities',[]) if e.get('_placeholder')))
")"
if [[ "${PLACEHOLDERS}" != "0" ]]; then
  echo "WARN: graph contains ${PLACEHOLDERS} _placeholder entities"
fi

if [[ -L "${PUBLIC_LINK}" ]]; then
  TARGET="$(readlink "${PUBLIC_LINK}")"
  echo "==> web/public/graph.json -> ${TARGET} (symlink OK)"
elif [[ -f "${PUBLIC_LINK}" ]]; then
  echo "==> web/public/graph.json is a regular file (not symlink)"
else
  echo "WARN: missing ${PUBLIC_LINK}"
fi

echo ""
echo "Deploy (set JEM_REMOTE to your host — do not commit real values):"
echo "  export JEM_REMOTE='user@your-host.example:~/path/to/apps/jem'"
echo "  export JEM_PUBLIC_URL='https://your-host.example/apps/jem/'"
echo "  rsync -avz ${GRAPH} \"\${JEM_REMOTE}/public/graph.json\""
echo "  rsync -avz --delete ${JEM_ROOT}/web/ \"\${JEM_REMOTE}/\""
echo ""
echo "Smoke tests + tag: jem/docs/V1_RELEASE_RUNBOOK.md"
echo "Canonical demo (attribution): https://friedso.com/apps/jem/"
echo "OK: preflight passed"
