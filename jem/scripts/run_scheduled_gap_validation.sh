#!/usr/bin/env bash
# Scheduled Claude CLI validation layer for gap/tribunal data (read-only report).
# Usage:
#   ./scripts/run_scheduled_gap_validation.sh          # run now
#   ./scripts/run_scheduled_gap_validation.sh 4500     # sleep 4500s then run (~20:45 IST from 19:30)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT}/.." && pwd)"
cd "${ROOT}"

DELAY_SEC="${1:-0}"
PROMPT_FILE="${ROOT}/.claude/prompts/gap_data_validation_layer.md"
OUTPUT_DIR="${ROOT}/.claude/outputs"
STAMP="$(date +%Y%m%d_%H%M%S)"
OUTPUT="${OUTPUT_DIR}/gap_data_validation_${STAMP}.md"
LATEST="${OUTPUT_DIR}/gap_data_validation_latest.md"
SCHEDULE="${OUTPUT_DIR}/gap_validation_schedule.json"
LOG="${OUTPUT_DIR}/gap_validation_scheduled.log"
MORNING_SCRIPT="${ROOT}/scripts/run_morning_gap_pipeline.sh"

mkdir -p "${OUTPUT_DIR}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG}"
}

is_rate_limited() {
  local exit_code="${1:-0}"
  local _grep_targets=()
  [[ -f "${LOG}" ]] && _grep_targets+=("${LOG}")
  [[ -f "${OUTPUT}" ]] && _grep_targets+=("${OUTPUT}")
  ((${#_grep_targets[@]})) || return 1
  if ! grep -qiE 'session[[:space:]_-]*limit|rate[[:space:]_-]*limit|resets?' "${_grep_targets[@]}" 2>/dev/null; then
    return 1
  fi
  if [[ "${exit_code}" -ne 0 ]]; then
    return 0
  fi
  if grep -qiE 'session[[:space:]_-]*limit|rate[[:space:]_-]*limit' "${_grep_targets[@]}" 2>/dev/null; then
    return 0
  fi
  return 1
}

morning_job_pending() {
  python3 - "${SCHEDULE}" <<'PY'
import json, os, sys
path = sys.argv[1]
try:
    with open(path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    sys.exit(1)
pid = data.get("morning_job_pid")
if not pid:
    sys.exit(1)
try:
    os.kill(int(pid), 0)
except (OSError, ValueError):
    sys.exit(1)
sys.exit(0)
PY
}

spawn_morning_pipeline() {
  if morning_job_pending; then
    local existing_pid
    existing_pid="$(python3 -c "import json; print(json.load(open('${SCHEDULE}')).get('morning_job_pid',''))" 2>/dev/null || true)"
    log "Morning gap pipeline already scheduled (PID ${existing_pid}) — not spawning duplicate"
    return 0
  fi
  if [[ ! -x "${MORNING_SCRIPT}" ]]; then
    log "ERROR: morning script missing or not executable: ${MORNING_SCRIPT}"
    return 1
  fi
  nohup "${MORNING_SCRIPT}" >>"${OUTPUT_DIR}/morning_pipeline.log" 2>&1 &
  local morning_pid=$!
  log "Spawned morning gap pipeline PID ${morning_pid} (nohup → morning_pipeline.log)"
  python3 - "${SCHEDULE}" "${morning_pid}" <<'PY'
import json, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

path, pid = sys.argv[1], int(sys.argv[2])
try:
    with open(path) as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    data = {}

ist = ZoneInfo("Asia/Kolkata")
now = datetime.now(ist)
target = now.replace(hour=6, minute=0, second=0, microsecond=0)
if now >= target:
    target += timedelta(days=1)

data["morning_job_pid"] = pid
data["morning_job_status"] = "pending"
data["morning_scheduled_at"] = datetime.now(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")
data["morning_planned_at_local"] = target.strftime("%Y-%m-%d %H:%M:%S IST")

with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY
  echo "${morning_pid}"
}

if [[ ! -f "${PROMPT_FILE}" ]]; then
  echo "ERROR: prompt not found: ${PROMPT_FILE}" >&2
  exit 1
fi

SCHEDULED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
if [[ "${DELAY_SEC}" -gt 0 ]]; then
  if date -v+1S >/dev/null 2>&1; then
    RUN_AT="$(date -v+"${DELAY_SEC}"S '+%Y-%m-%d %H:%M:%S %Z')"
  else
    RUN_AT="$(date -d "+${DELAY_SEC} seconds" '+%Y-%m-%d %H:%M:%S %Z')"
  fi
else
  RUN_AT="$(date '+%Y-%m-%d %H:%M:%S %Z')"
fi

python3 - "${SCHEDULE}" "${SCHEDULED_AT}" "${DELAY_SEC}" "${RUN_AT}" "${LATEST}" "${LOG}" <<'PYINIT'
import json, os, sys
path, scheduled_at, delay, run_at, latest, log = sys.argv[1:7]
preserve = {}
try:
    with open(path) as f:
        old = json.load(f)
    pid = old.get("morning_job_pid")
    if pid:
        try:
            os.kill(int(pid), 0)
            for k in (
                "morning_job_pid", "morning_job_status", "morning_scheduled_at",
                "morning_planned_at_local",
            ):
                if k in old:
                    preserve[k] = old[k]
        except (OSError, ValueError):
            pass
except (FileNotFoundError, json.JSONDecodeError):
    pass
data = {
    "scheduled_at": scheduled_at,
    "delay_seconds": int(delay),
    "planned_run_at_local": run_at,
    "prompt": "gap_data_validation_layer.md",
    "output_latest": latest,
    "log": log,
    "status": "pending",
    **preserve,
}
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PYINIT

if [[ "${DELAY_SEC}" -gt 0 ]]; then
  log "Gap validation scheduled in ${DELAY_SEC}s (target: ${RUN_AT})"
  sleep "${DELAY_SEC}"
fi

if ! command -v claude &>/dev/null; then
  log "ERROR: claude CLI not found (install Claude Code CLI)"
  python3 - "${SCHEDULE}" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
d["status"] = "failed_cli_missing"
with open(sys.argv[1], "w") as f:
    json.dump(d, f, indent=2)
    f.write("\n")
PY
  exit 1
fi

log "Starting Claude CLI validation layer"
if claude -p "$(cat "${PROMPT_FILE}")

---
VALIDATION RUN: $(date -Iseconds 2>/dev/null || date '+%Y-%m-%dT%H:%M:%S%z')
Respond with markdown only. Do not write or edit repository files." \
  --add-dir "${REPO_ROOT}" \
  --output-format text > "${OUTPUT}" 2>>"${LOG}"; then
  CLAUDE_EXIT=0
else
  CLAUDE_EXIT=$?
  log "WARN: claude exited ${CLAUDE_EXIT} (see log for session/rate limit or API error)"
fi

cp "${OUTPUT}" "${LATEST}"
log "Report written: ${OUTPUT}"
log "Latest symlink copy: ${LATEST}"

RATE_LIMITED=0
MORNING_PID=""
if is_rate_limited "${CLAUDE_EXIT}"; then
  RATE_LIMITED=1
  log "Detected Claude session/rate limit in log (exit ${CLAUDE_EXIT})"
  MORNING_PID="$(spawn_morning_pipeline || true)"
fi

VALIDATE_EXIT=0
GRAPH_EXIT=0
if python3 scripts/validate.py >>"${LOG}" 2>&1; then
  log "validate.py: PASS"
else
  VALIDATE_EXIT=$?
  log "validate.py: FAIL (exit ${VALIDATE_EXIT})"
fi
if python3 scripts/validate_graph_refs.py >>"${LOG}" 2>&1; then
  log "validate_graph_refs.py: PASS"
else
  GRAPH_EXIT=$?
  log "validate_graph_refs.py: FAIL (exit ${GRAPH_EXIT})"
fi

STATUS="complete"
if [[ "${RATE_LIMITED}" -eq 1 ]]; then
  STATUS="claude_rate_limited"
elif [[ "${CLAUDE_EXIT}" -ne 0 ]]; then
  STATUS="claude_failed"
elif [[ "${VALIDATE_EXIT}" -ne 0 || "${GRAPH_EXIT}" -ne 0 ]]; then
  STATUS="pipeline_failed"
fi

COMPLETED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
python3 - "${SCHEDULE}" <<PY
import json
path = "${SCHEDULE}"
with open(path) as f:
    data = json.load(f)
data.update({
    "completed_at": "${COMPLETED_AT}",
    "output": "${OUTPUT}",
    "status": "${STATUS}",
    "claude_exit": ${CLAUDE_EXIT},
    "validate_exit": ${VALIDATE_EXIT},
    "graph_refs_exit": ${GRAPH_EXIT},
    "rate_limit_detected": ${RATE_LIMITED},
})
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

log "GAP_VALIDATION_COMPLETE status=${STATUS} report=${LATEST}"
if [[ -n "${MORNING_PID}" ]]; then
  log "Morning job PID ${MORNING_PID}"
  echo "GAP_VALIDATION_COMPLETE status=${STATUS} path=${LATEST} morning_job_pid=${MORNING_PID}"
else
  echo "GAP_VALIDATION_COMPLETE status=${STATUS} path=${LATEST}"
fi

exit $(( CLAUDE_EXIT != 0 ? CLAUDE_EXIT : (VALIDATE_EXIT != 0 ? VALIDATE_EXIT : GRAPH_EXIT) ))
