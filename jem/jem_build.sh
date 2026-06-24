#!/usr/bin/env bash
# jem_build.sh — JEM build orchestration harness
# Usage: ./jem_build.sh [session_number] [--dry-run]
#
# Run from jem/ directory.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

SESSION="${1:-0}"
DRY_RUN=""
if [[ "${2:-}" == "--dry-run" ]] || [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  if [[ "${1:-}" == "--dry-run" ]]; then
    SESSION="${2:-0}"
  fi
fi

CLAUDE_DIR=".claude"
OUTPUTS="${CLAUDE_DIR}/outputs"
PROMPTS="${CLAUDE_DIR}/prompts"
DECISIONS="${CLAUDE_DIR}/decisions"
LOG="${CLAUDE_DIR}/build_log.md"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

mkdir -p "${OUTPUTS}" "${DECISIONS}" "${PROMPTS}"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG}"
}

gate() {
  if [[ -n "${DRY_RUN}" ]]; then
    log "[DRY RUN] GATE auto-pass: $1"
    return 0
  fi
  echo ""
  echo "━━━ GATE: $1 ━━━"
  echo "Review output above. Continue? (y/n)"
  read -r confirm
  if [[ "${confirm}" != "y" ]]; then
    log "GATE FAILED: $1 — build halted"
    exit 1
  fi
}

check_prereqs() {
  local need_pytest="${1:-0}"
  if [[ -z "${DRY_RUN}" ]] && ! command -v claude &>/dev/null; then
    echo "ERROR: claude CLI not found. Install Claude Code CLI." >&2
    exit 1
  fi
  if [[ "${need_pytest}" == "1" ]] && ! command -v pytest &>/dev/null; then
    echo "ERROR: pytest not found. Run: pip install -r scripts/requirements-dev.txt" >&2
    exit 1
  fi
}

claude_reason() {
  local task=$1
  local prompt_file="${PROMPTS}/${task}.md"
  local output_file="${OUTPUTS}/${task}.md"

  if [[ ! -f "${prompt_file}" ]]; then
    echo "ERROR: prompt not found: ${prompt_file}" >&2
    exit 1
  fi

  log "Claude CLI: ${task}"
  if [[ -n "${DRY_RUN}" ]]; then
    log "[DRY RUN] Would call: claude -p <${prompt_file}> > ${output_file}"
    return 0
  fi

  claude -p "$(cat "${prompt_file}")

Respond with markdown only. Do not write files.
Read context files named in the prompt header (CLAUDE.md, graph.json, etc.)." \
    --add-dir "${REPO_ROOT}" \
    --allowedTools "Read,Grep,Glob" \
    --output-format text > "${output_file}"

  log "Output written: ${output_file}"
}

lock_decision() {
  local src="${OUTPUTS}/$1.md"
  local dest="${DECISIONS}/$2"
  if [[ -n "${DRY_RUN}" ]]; then
    log "[DRY RUN] Would lock: ${src} → ${dest}"
    return 0
  fi
  if [[ ! -f "${src}" ]]; then
    echo "ERROR: output not found: ${src}" >&2
    exit 1
  fi
  if [[ -f "${dest}" ]]; then
    local versioned="${dest%.md}_$(date +%Y%m%d_%H%M%S).md"
    log "Decision exists; writing versioned copy: ${versioned}"
    cp "${src}" "${versioned}"
  else
    cp "${src}" "${dest}"
    log "Locked: ${dest}"
  fi
}

run_tests() {
  local marker=$1
  log "Running tests: ${marker}"
  if [[ -n "${DRY_RUN}" ]]; then
    log "[DRY RUN] Would run: pytest tests/ -k ${marker} -v --tb=short"
    return 0
  fi
  pytest tests/ -k "${marker}" -v --tb=short 2>&1 | tee -a "${LOG}"
  if [[ ${PIPESTATUS[0]} -ne 0 ]]; then
    log "TESTS FAILED: ${marker}"
    gate "Tests failed for ${marker} — fix before continuing"
  fi
}

cursor_gate() {
  local prompt_file=$1
  echo ""
  echo "━━━ CURSOR GATE ━━━"
  echo "Open Cursor Composer. Attach context files listed in:"
  echo "  ${PROMPTS}/${prompt_file}"
  echo ""
  if [[ -f "${PROMPTS}/${prompt_file}" ]]; then
    cat "${PROMPTS}/${prompt_file}"
  fi
  echo ""
  gate "Cursor build complete for ${prompt_file}"
}

# ── SESSION ROUTER ─────────────────────────────────────────

case "${SESSION}" in

"0")
  check_prereqs
  log "SESSION 0: Schema Lock"
  claude_reason "s0_schema_audit"
  gate "Schema audit complete — review ${OUTPUTS}/s0_schema_audit.md"
  claude_reason "s0_migration_decisions"
  gate "Migration decisions locked — review ${OUTPUTS}/s0_migration_decisions.md"
  lock_decision "s0_schema_audit" "schema_lock.md"
  lock_decision "s0_migration_decisions" "migration_rules.md"
  log "SESSION 0 COMPLETE — update CLAUDE.md session status"
  ;;

"1")
  check_prereqs 1
  log "SESSION 1: SQLite Foundation"
  if [[ ! -f "${DECISIONS}/schema_lock.md" ]]; then
    echo "ERROR: Run session 0 first — ${DECISIONS}/schema_lock.md missing" >&2
    exit 1
  fi
  cursor_gate "cursor_s1_sqlite"
  if [[ -z "${DRY_RUN}" ]]; then
    python scripts/build_db.py
    python scripts/validate_db.py
  else
    log "[DRY RUN] Would run build_db.py and validate_db.py"
  fi
  run_tests "test_db"
  claude_reason "s1_schema_qa"
  gate "Schema QA reviewed — ${OUTPUTS}/s1_schema_qa.md"
  log "SESSION 1 COMPLETE"
  ;;

"2")
  check_prereqs 1
  log "SESSION 2: FastAPI"
  claude_reason "s2_api_contract"
  gate "API contract reviewed — ${OUTPUTS}/s2_api_contract.md"
  cursor_gate "cursor_s2_api"
  run_tests "test_api"
  log "SESSION 2 COMPLETE"
  ;;

"3")
  check_prereqs 1
  log "SESSION 3: MCP Server"
  claude_reason "s3_mcp_tool_design"
  gate "MCP tool spec reviewed — ${OUTPUTS}/s3_mcp_tool_design.md"
  cursor_gate "cursor_s3_mcp"
  run_tests "test_mcp"
  log "SESSION 3 COMPLETE"
  ;;

"4a")
  check_prereqs 1
  log "SESSION 4A: Fetcher Agent"
  claude_reason "s4a_extraction_prompt"
  gate "CRITICAL: Review extraction prompt — ${OUTPUTS}/s4a_extraction_prompt.md"
  lock_decision "s4a_extraction_prompt" "../prompts/extraction_v1.md"
  # extraction goes to prompts/ not decisions/
  if [[ -f "${OUTPUTS}/s4a_extraction_prompt.md" && -z "${DRY_RUN}" ]]; then
    cp "${OUTPUTS}/s4a_extraction_prompt.md" "${PROMPTS}/extraction_v1.md"
  fi
  claude_reason "s4a_verification_prompt"
  gate "Review verification prompt — ${OUTPUTS}/s4a_verification_prompt.md"
  if [[ -f "${OUTPUTS}/s4a_verification_prompt.md" && -z "${DRY_RUN}" ]]; then
    cp "${OUTPUTS}/s4a_verification_prompt.md" "${PROMPTS}/verification_v1.md"
  fi
  claude_reason "s4a_dedup_spec"
  gate "Review dedup spec — ${OUTPUTS}/s4a_dedup_spec.md"
  cursor_gate "cursor_s4a_fetcher"
  run_tests "test_agents"
  log "SESSION 4A COMPLETE"
  ;;

"4b")
  check_prereqs 1
  log "SESSION 4B: Expert Portal"
  cursor_gate "cursor_s4b_portal"
  run_tests "test_portal"
  log "SESSION 4B COMPLETE"
  ;;

"5")
  check_prereqs 1
  log "SESSION 5: Harness + Chat UI"
  claude_reason "s5_system_prompt"
  gate "CRITICAL: Review harness system prompt — ${OUTPUTS}/s5_system_prompt.md"
  if [[ -f "${OUTPUTS}/s5_system_prompt.md" && -z "${DRY_RUN}" ]]; then
    cp "${OUTPUTS}/s5_system_prompt.md" "harness/system_prompt.txt"
  fi
  claude_reason "s5_test_pairs"
  if [[ -f "${OUTPUTS}/s5_test_pairs.md" && -z "${DRY_RUN}" ]]; then
    cp "${OUTPUTS}/s5_test_pairs.md" "tests/fixtures/harness_test_pairs.md"
  fi
  gate "Review test pairs — ${OUTPUTS}/s5_test_pairs.md"
  cursor_gate "cursor_s5_harness"
  run_tests "test_harness"
  log "SESSION 5 COMPLETE"
  ;;

"6")
  check_prereqs 1
  log "SESSION 6: Operational Monitor Harness"
  claude_reason "s6_anomaly_rules"
  claude_reason "s6_digest_prompt"
  if [[ -f "${OUTPUTS}/s6_digest_prompt.md" && -z "${DRY_RUN}" ]]; then
    cp "${OUTPUTS}/s6_digest_prompt.md" "${PROMPTS}/digest_v1.md"
  fi
  gate "Review digest prompt — ${OUTPUTS}/s6_digest_prompt.md"
  cursor_gate "cursor_s6_monitor"
  run_tests "test_integration"
  log "SESSION 6 COMPLETE"
  ;;

"qa")
  check_prereqs 1
  log "FULL QA RUN"
  claude_reason "qa_full_audit"
  run_tests "test_"
  if [[ -z "${DRY_RUN}" ]]; then
    python scripts/validate_db.py
  fi
  log "QA COMPLETE — review ${OUTPUTS}/qa_full_audit.md"
  ;;

*)
  echo "Usage: ./jem_build.sh [0|1|2|3|4a|4b|5|6|qa] [--dry-run]"
  exit 1
  ;;
esac
