#!/usr/bin/env bash
# Production deploy for https://friedso.com/apps/jem/
#
# Always run from the friedso_v1 branch (the deploy line). main may move ahead;
# friedso_v1 is what production serves after validate + smoke test.
#
# Usage (from repo root):
#   ./jem/scripts/deploy_friedso_production.sh
#   ./jem/scripts/deploy_friedso_production.sh --deploy
#   ./jem/scripts/deploy_friedso_production.sh --both          # prod + staging + friedso repo copy
#   JEM_REMOTE='user@host:~/path/to/apps/jem' ./jem/scripts/deploy_friedso_production.sh --deploy
#
# --both defaults (override with env):
#   JEM_REMOTE_PROD=root@157.10.98.182:/srv/friedso/prod/web/site/apps/jem
#   JEM_REMOTE_STAGE=root@157.10.98.182:/srv/friedso/stage/web/site/apps/jem
#   FRIEDSO_JEM_DIR=../friedso/web/site/apps/jem  (relative to jem repo root)
# Promote main → friedso_v1 (founder merges PR after local smoke on a branch):
#   git fetch origin
#   gh pr create --base friedso_v1 --head main --title "deploy: promote main to friedso_v1"
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JEM_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_ROOT="$(cd "${JEM_ROOT}/.." && pwd)"
GRAPH="${REPO_ROOT}/graph.json"
DEPLOY_BRANCH="${JEM_DEPLOY_BRANCH:-friedso_v1}"
MIN_ENTITIES=400
DO_DEPLOY=0
DEPLOY_BOTH=0
BUNDLE_NAME=""
JEM_REMOTE_PROD="${JEM_REMOTE_PROD:-root@157.10.98.182:/srv/friedso/prod/web/site/apps/jem}"
JEM_REMOTE_STAGE="${JEM_REMOTE_STAGE:-root@157.10.98.182:/srv/friedso/stage/web/site/apps/jem}"
FRIEDSO_JEM_DIR="${FRIEDSO_JEM_DIR:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --deploy) DO_DEPLOY=1; shift ;;
    --both) DEPLOY_BOTH=1; DO_DEPLOY=1; shift ;;
    --branch)
      DEPLOY_BRANCH="$2"
      shift 2
      ;;
    --name)
      BUNDLE_NAME="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
  esac
done

cd "${REPO_ROOT}"

echo "==> Ensure deploy branch (${DEPLOY_BRANCH})"
git fetch origin "${DEPLOY_BRANCH}" 2>/dev/null || git fetch origin

CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if [[ "${CURRENT}" != "${DEPLOY_BRANCH}" ]]; then
  if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "ERROR: working tree dirty; commit or stash before switching to ${DEPLOY_BRANCH}" >&2
    exit 1
  fi
  git checkout "${DEPLOY_BRANCH}"
fi

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "origin/${DEPLOY_BRANCH}" 2>/dev/null || echo "")"
if [[ -n "${REMOTE_SHA}" && "${LOCAL_SHA}" != "${REMOTE_SHA}" ]]; then
  echo "ERROR: local ${DEPLOY_BRANCH} (${LOCAL_SHA:0:7}) != origin/${DEPLOY_BRANCH} (${REMOTE_SHA:0:7})" >&2
  echo "Run: git pull --ff-only origin ${DEPLOY_BRANCH}" >&2
  exit 1
fi

if [[ -z "${BUNDLE_NAME}" ]]; then
  BUNDLE_NAME="jem-web-$(date +%Y%m%d-%H%M%S)"
fi
BUNDLE_DIR="${REPO_ROOT}/_deploy_bundle/${BUNDLE_NAME}"

echo "==> JEM production bundle: ${BUNDLE_DIR}"
echo "==> Branch: ${DEPLOY_BRANCH} @ $(git rev-parse --short HEAD)"
echo "==> Pipeline (validate → derive → build)"
cd "${JEM_ROOT}"
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py
python3 scripts/derive.py
python3 scripts/build.py

if [[ ! -f "${GRAPH}" ]]; then
  echo "ERROR: missing ${GRAPH}" >&2
  exit 1
fi

COUNT="$(python3 -c "import json; print(json.load(open('${GRAPH}'))['meta'].get('entity_count', 0))")"
RELS="$(python3 -c "import json; print(json.load(open('${GRAPH}'))['meta'].get('relationship_count', 0))")"
if [[ "${COUNT}" -lt "${MIN_ENTITIES}" ]]; then
  echo "ERROR: entity_count ${COUNT} < ${MIN_ENTITIES} — aborting bundle" >&2
  exit 1
fi

GIT_SHA="$(git rev-parse --short HEAD)"
GIT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

rm -rf "${BUNDLE_DIR}"
mkdir -p "${BUNDLE_DIR}/public"

echo "==> Copy web app (exclude symlink public/graph.json)"
rsync -a \
  --exclude 'public/graph.json' \
  "${JEM_ROOT}/web/" "${BUNDLE_DIR}/"

echo "==> Materialize graph.json → public/graph.json"
cp -f "${GRAPH}" "${BUNDLE_DIR}/public/graph.json"

cat > "${BUNDLE_DIR}/DEPLOY_README.txt" <<EOF
JEM production deploy bundle
Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)
Git: ${GIT_BRANCH} @ ${GIT_SHA}
graph.json: entity_count=${COUNT} relationship_count=${RELS}

Deploy branch: ${DEPLOY_BRANCH} (https://friedso.com/apps/jem/)

--- rsync (set JEM_REMOTE in your shell; do not commit) ---

  export JEM_REMOTE='user@your-host:~/path/to/apps/jem'
  export JEM_PUBLIC="\${JEM_REMOTE}/public"

  rsync -avz public/graph.json "\${JEM_PUBLIC}/graph.json"
  rsync -avz --delete --exclude 'public/graph.json' ./ "\${JEM_REMOTE}/"

--- smoke test ---

  export JEM_PUBLIC_URL='https://friedso.com/apps/jem/'
  See jem/docs/V1_RELEASE_RUNBOOK.md §2
EOF

python3 -c "
import json
from pathlib import Path
g = json.loads(Path('${GRAPH}').read_text())
manifest = {
  'built_at': '$(date -u +%Y-%m-%dT%H:%M:%SZ)',
  'git_sha': '${GIT_SHA}',
  'git_branch': '${GIT_BRANCH}',
  'deploy_branch': '${DEPLOY_BRANCH}',
  'entity_count': g.get('meta', {}).get('entity_count'),
  'relationship_count': g.get('meta', {}).get('relationship_count'),
  'graph_version': g.get('meta', {}).get('version'),
}
Path('${BUNDLE_DIR}/bundle_manifest.json').write_text(json.dumps(manifest, indent=2))
"

cat > "${REPO_ROOT}/_deploy_bundle/LATEST.txt" <<EOF
${BUNDLE_NAME}
${BUNDLE_DIR}
branch=${DEPLOY_BRANCH}
entities=${COUNT}
EOF

echo ""
echo "OK: bundle ready at"
echo "  ${BUNDLE_DIR}"
echo "  branch=${DEPLOY_BRANCH} entities=${COUNT} relationships=${RELS}"
echo ""
echo "Next: smoke test per jem/docs/V1_RELEASE_RUNBOOK.md §2"
echo "      export JEM_PUBLIC_URL='https://friedso.com/apps/jem/'"
echo ""

deploy_to_remote() {
  local remote="$1"
  local label="$2"
  local public="${remote%/}/public"
  echo "==> rsync to ${label}: ${remote}"
  rsync -avz "${BUNDLE_DIR}/public/graph.json" "${public}/graph.json"
  rsync -avz --delete \
    --exclude 'public/graph.json' \
    "${BUNDLE_DIR}/" "${remote%/}/"
  echo "OK: deployed to ${label} (${remote})"
}

sync_friedso_repo_copy() {
  local target="${FRIEDSO_JEM_DIR:-${REPO_ROOT}/../friedso/web/site/apps/jem}"
  if [[ ! -d "$(dirname "${target}")" ]]; then
    echo "WARN: friedso apps dir missing — skip local repo sync (${target})" >&2
    return 0
  fi
  echo "==> sync bundle → friedso repo (${target})"
  rsync -avz --delete \
    --exclude 'public/graph.json' \
    "${BUNDLE_DIR}/" "${target}/"
  rsync -avz "${BUNDLE_DIR}/public/graph.json" "${target}/public/graph.json"
  echo "OK: friedso repo copy updated at ${target}"
}

if [[ "${DO_DEPLOY}" -eq 1 ]]; then
  if [[ "${DEPLOY_BOTH}" -eq 1 ]]; then
    sync_friedso_repo_copy
    deploy_to_remote "${JEM_REMOTE_PROD}" "production"
    deploy_to_remote "${JEM_REMOTE_STAGE}" "staging"
    echo ""
    echo "Smoke tests:"
    echo "  Production: https://friedso.com/apps/jem/"
    echo "  Staging:    https://staging.friedso.com/apps/jem/"
  else
    if [[ -z "${JEM_REMOTE:-}" ]]; then
      echo "ERROR: --deploy requires JEM_REMOTE (or use --both for prod+staging defaults)" >&2
      exit 1
    fi
    deploy_to_remote "${JEM_REMOTE}" "remote"
    echo "Run smoke tests at \${JEM_PUBLIC_URL:-https://friedso.com/apps/jem/}"
  fi
fi
