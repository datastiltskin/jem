#!/usr/bin/env bash
# Sleep until next 06:00 IST, then gap validation + morning data-finding (read-only),
# then apply chain from overnight_pipeline_report.md on success.
# Launch (usually via run_scheduled_gap_validation.sh on rate limit):
#   nohup jem/scripts/run_morning_gap_pipeline.sh >> jem/.claude/outputs/morning_pipeline.log 2>&1 &
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT}/.." && pwd)"
OUTPUT_DIR="${ROOT}/.claude/outputs"
LOG="${OUTPUT_DIR}/morning_pipeline.log"
SCHEDULE="${OUTPUT_DIR}/gap_validation_schedule.json"
DATA_PROMPT="${ROOT}/.claude/prompts/gap_morning_data_finding.md"
OVERNIGHT_DOC="${OUTPUT_DIR}/overnight_pipeline_report.md"
STAMP="$(date +%Y%m%d_%H%M%S)"
DATA_OUTPUT="${OUTPUT_DIR}/gap_morning_data_finding_${STAMP}.md"
DATA_LATEST="${OUTPUT_DIR}/gap_morning_data_finding_latest.md"

mkdir -p "${OUTPUT_DIR}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $*" | tee -a "${LOG}"
}

seconds_until_next_0600_ist() {
  python3 <<'PY'
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ist = ZoneInfo("Asia/Kolkata")
now = datetime.now(ist)
target = now.replace(hour=6, minute=0, second=0, microsecond=0)
if now >= target:
    target += timedelta(days=1)
print(int((target - now).total_seconds()))
PY
}

update_schedule() {
  python3 - "$@" <<'PY'
import json, sys
path = sys.argv[1]
patch = json.loads(sys.argv[2])
try:
    with open(path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}
data.update(patch)
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
}

log "Morning gap pipeline started (PID $$)"
update_schedule "${SCHEDULE}" "$(python3 -c 'import json; print(json.dumps({"morning_job_pid": '"$$"', "morning_job_status": "running"}))')"

DELAY_SEC="$(seconds_until_next_0600_ist)"
TARGET_LOCAL="$(TZ=Asia/Kolkata date -v+"${DELAY_SEC}"S '+%Y-%m-%d %H:%M:%S IST' 2>/dev/null \
  || TZ=Asia/Kolkata date -d "+${DELAY_SEC} seconds" '+%Y-%m-%d %H:%M:%S IST')"
log "Sleeping ${DELAY_SEC}s until ${TARGET_LOCAL} (next 06:00 IST)"
sleep "${DELAY_SEC}"

log "06:00 IST window — running scheduled gap validation (no delay)"
cd "${ROOT}"
VALIDATION_OK=1
if ! ./scripts/run_scheduled_gap_validation.sh 0 >>"${LOG}" 2>&1; then
  log "WARN: run_scheduled_gap_validation.sh failed — see log"
  VALIDATION_OK=0
fi

DATA_FINDING_OK=1
CLAUDE_DATA_EXIT=0
if [[ ! -f "${DATA_PROMPT}" ]]; then
  log "ERROR: data-finding prompt missing: ${DATA_PROMPT}"
  DATA_FINDING_OK=0
elif ! command -v claude &>/dev/null; then
  log "ERROR: claude CLI not found for morning data-finding"
  DATA_FINDING_OK=0
else
  log "Starting Claude morning data-finding (read-only)"
  if claude -p "$(cat "${DATA_PROMPT}")

---
MORNING DATA-FINDING RUN: $(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z')
Respond with markdown only. Do not write or edit repository files." \
    --add-dir "${REPO_ROOT}" \
    --output-format text > "${DATA_OUTPUT}" 2>>"${LOG}"; then
    CLAUDE_DATA_EXIT=0
  else
    CLAUDE_DATA_EXIT=$?
    log "WARN: morning data-finding claude exited ${CLAUDE_DATA_EXIT}"
    DATA_FINDING_OK=0
  fi
  cp "${DATA_OUTPUT}" "${DATA_LATEST}"
  log "Morning data report: ${DATA_LATEST}"
fi

APPLY_OK=1
if [[ "${VALIDATION_OK}" -eq 1 && "${DATA_FINDING_OK}" -eq 1 ]]; then
  log "Morning success — running apply chain from ${OVERNIGHT_DOC}"
  if [[ -f "${OVERNIGHT_DOC}" ]]; then
    log "--- apply chain (see overnight_pipeline_report.md) ---"
  else
    log "WARN: ${OVERNIGHT_DOC} missing — using default apply chain"
  fi
  while IFS= read -r cmd; do
    [[ -z "${cmd}" || "${cmd}" =~ ^# ]] && continue
    log "→ ${cmd}"
    if ! (cd "${ROOT}" && eval "${cmd}") >>"${LOG}" 2>&1; then
      log "FAIL: ${cmd}"
      APPLY_OK=0
    else
      log "PASS: ${cmd}"
    fi
  done <<'APPLY_CHAIN'
python3 scripts/validate.py
python3 scripts/validate_graph_refs.py
python3 scripts/derive.py
python3 scripts/build.py
python3 scripts/build_db.py
python3 scripts/validate_db.py
APPLY_CHAIN
else
  log "Skipping apply chain (validation_ok=${VALIDATION_OK} data_finding_ok=${DATA_FINDING_OK})"
  APPLY_OK=0
fi

PIPELINE_OK=$(( VALIDATION_OK && DATA_FINDING_OK && APPLY_OK ))
STATUS="complete"
if [[ "${PIPELINE_OK}" -ne 1 ]]; then
  STATUS="morning_failed"
fi

update_schedule "${SCHEDULE}" "$(python3 -c "import json; print(json.dumps({
  'morning_job_status': '${STATUS}',
  'morning_completed_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
  'morning_data_output_latest': '${DATA_LATEST}',
  'morning_claude_exit': ${CLAUDE_DATA_EXIT},
}))")"

log "MORNING_PIPELINE_COMPLETE status=${STATUS} pipeline_ok=${PIPELINE_OK}"
exit $(( PIPELINE_OK ? 0 : 1 ))
