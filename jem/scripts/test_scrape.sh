#!/usr/bin/env bash
# Manually scrape a FEW entities to test the full scrape → gate → verify flow.
# DRY-RUN by default: results land in .claude/outputs/batch_<stamp>/{would_write,needs_review}/,
# the live data/entities tree is never touched. Pass --write to actually store to the live tree.
#
#   scripts/test_scrape.sh                       # default two entities, dry-run
#   scripts/test_scrape.sh hc_madras hc_bombay   # your two ids, dry-run
#   scripts/test_scrape.sh --write hc_madras     # store to the live tree (careful)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"        # jem/
cd "${ROOT}"

DRY="--dry-run"
IDS=()
for a in "$@"; do
  if [[ "$a" == "--write" ]]; then DRY=""; else IDS+=("$a"); fi
done
[[ ${#IDS[@]} -eq 0 ]] && IDS=(hc_madras hc_bombay)   # default two

[[ -f .env ]] && { set -a; source .env; set +a; }     # ANTHROPIC_API_KEY

echo "Testing ${#IDS[@]} entities: ${IDS[*]} ${DRY:-(LIVE WRITE)}"
exec python3 scripts/batch_scrape.py \
  --only "${IDS[@]}" \
  --concurrency "${#IDS[@]}" \
  --model "${JEM_BATCH_MODEL:-claude-sonnet-5}" \
  ${DRY}
