# CURSOR SESSION 6 — Operational Monitor

**Attach:**
- `jem/.claude/prompts/digest_v1.md`
- `jem/.claude/outputs/s6_anomaly_rules.md`
- `jem/agents/`

## Task

Build:
- `jem/agents/monitor.py` — anomaly detection per rules
- `jem/agents/summarise_staging.py` — JSON summary for digest prompt
- `jem/scripts/integration_test.py` — end-to-end pipeline test
- `tests/test_integration.py`

Digest output → `data/digests/YYYY-MM-DD.md`
