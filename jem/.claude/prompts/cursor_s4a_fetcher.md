# CURSOR SESSION 4A — Fetcher Agent

**Attach:**
- `jem/.claude/prompts/extraction_v1.md`
- `jem/.claude/prompts/verification_v1.md`
- `jem/.claude/decisions/schema_lock.md`

## Task

Build `jem/agents/`:
- `agents/fetcher.py` — fetch sources, call Anthropic API with extraction prompt
- `agents/verifier.py` — verify staging records
- `agents/dedup.py` — per dedup spec
- `config/sources.yaml` — source URLs
- `tests/test_agents.py`

Load prompts from `.claude/prompts/`, never inline.
