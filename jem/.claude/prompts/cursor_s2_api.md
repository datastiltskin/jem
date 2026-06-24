# CURSOR SESSION 2 — FastAPI

**Attach:**
- `jem/.claude/outputs/s2_api_contract.md`
- `jem/.claude/decisions/schema_lock.md`
- `jem/config/schema.sql`

## Task

Build `jem/api/` FastAPI application per API contract.

- `api/main.py` — app factory, mount routes
- `api/routes/entities.py`, `api/routes/relationships.py`
- `api/deps.py` — SQLite connection dependency
- `tests/test_api.py` — pytest with TestClient, fixture DB

Expose `data_quality` and `unverified_fields` on every entity response.
