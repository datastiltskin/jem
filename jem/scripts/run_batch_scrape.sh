#!/usr/bin/env bash
# Cron body: run the full roster scrape → gate → verify → store sweep over all entities.
# Fresh weekly sweep (re-scrapes + re-verifies everything); pass --resume manually to continue a
# crashed run. batch_scrape.py writes its own per-run ledger/digest/schedule under .claude/outputs.
# Launch (usually via launchd, scripts/com.jem.batch-scrape.plist):
#   jem/scripts/run_batch_scrape.sh >> jem/.claude/outputs/batch_cron.log 2>&1
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"        # jem/
OUTPUT_DIR="${ROOT}/.claude/outputs"
STAMP="$(date +%Y%m%d_%H%M%S)"
LOG="${OUTPUT_DIR}/batch_scrape_${STAMP}.log"
MODEL="${JEM_BATCH_MODEL:-claude-sonnet-5}"
CONCURRENCY="${JEM_BATCH_CONCURRENCY:-4}"

mkdir -p "${OUTPUT_DIR}"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $*" | tee -a "${LOG}"; }

cd "${ROOT}"
# ANTHROPIC_API_KEY comes from the gitignored .env (batch_scrape also load_dotenv()s it).
if [[ -f .env ]]; then set -a; source .env; set +a; fi

log "Batch scrape started (PID $$) model=${MODEL} concurrency=${CONCURRENCY}"
STATUS="complete"
if ! python3 scripts/batch_scrape.py --model "${MODEL}" --concurrency "${CONCURRENCY}" \
    >>"${LOG}" 2>&1; then
  STATUS="failed"
  log "WARN: batch_scrape.py exited non-zero (fail-rate threshold exceeded or crash) — see log"
fi
log "BATCH_SCRAPE_COMPLETE status=${STATUS} digest=${OUTPUT_DIR}/batch_digest_latest.md"
[[ "${STATUS}" == "complete" ]]
