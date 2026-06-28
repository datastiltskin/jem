#!/usr/bin/env bash
# Run morning data-finding + full apply chain immediately (no 06:00 sleep).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_ROOT="$(cd "${ROOT}/.." && pwd)"
OUTPUT_DIR="${ROOT}/.claude/outputs"
LOG="${OUTPUT_DIR}/morning_pipeline.log"
DATA_PROMPT="${ROOT}/.claude/prompts/gap_morning_data_finding.md"
STAMP="$(date +%Y%m%d_%H%M%S)"
DATA_OUTPUT="${OUTPUT_DIR}/gap_morning_data_finding_${STAMP}.md"
DATA_LATEST="${OUTPUT_DIR}/gap_morning_data_finding_latest.md"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S %Z')] $*" | tee -a "${LOG}"; }

cd "${ROOT}"
log "=== run_gap_pipeline_now: immediate morning completion ==="

DATA_FINDING_OK=1
if command -v claude &>/dev/null && [[ -f "${DATA_PROMPT}" ]]; then
  log "Claude morning data-finding (read-only)"
  if claude -p "$(cat "${DATA_PROMPT}")

---
IMMEDIATE RUN: $(date -Iseconds 2>/dev/null || date)
Respond with markdown only. Do not write repository files." \
    --add-dir "${REPO_ROOT}" \
    --output-format text > "${DATA_OUTPUT}" 2>>"${LOG}"; then
    log "Data-finding OK"
  else
    log "WARN: data-finding claude exit $?"
    DATA_FINDING_OK=0
  fi
  cp "${DATA_OUTPUT}" "${DATA_LATEST}"
  log "Report: ${DATA_LATEST}"
else
  log "SKIP data-finding (claude or prompt missing)"
  DATA_FINDING_OK=0
fi

log "Apply chain"
for cmd in \
  "python3 scripts/validate.py" \
  "python3 scripts/validate_graph_refs.py" \
  "python3 scripts/derive.py" \
  "python3 scripts/build.py" \
  "python3 scripts/build_db.py" \
  "python3 scripts/validate_db.py"; do
  log "→ ${cmd}"
  eval "${cmd}" >>"${LOG}" 2>&1 && log "PASS: ${cmd}" || { log "FAIL: ${cmd}"; exit 1; }
done

log "GAP_PIPELINE_NOW_COMPLETE"
echo "GAP_PIPELINE_NOW_COMPLETE"
