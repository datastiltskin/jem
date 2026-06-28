# CURSOR SESSION 1 — SQLite Foundation

**Attach these context files in Composer:**
- `jem/.claude/decisions/schema_lock.md`
- `jem/.claude/decisions/migration_rules.md`
- `graph.json`

## Task

Build SQLite foundation per locked schema.

### Create files

1. **`jem/config/schema.sql`** — DDL matching `schema_lock.md` exactly
2. **`jem/scripts/build_db.py`** — migrate `graph.json` → `data/jem.db`
   - WAL mode, foreign keys ON
   - `--graph PATH`, `--db PATH`, `--force` flags
   - Idempotent: skip if schema_version matches unless `--force`
   - Never default to test fixture paths
3. **`jem/scripts/validate_db.py`** — assert schema + FK integrity + entity count
   - `--db PATH` flag
   - Exit 0 on pass, 1 on fail
4. **`jem/tests/test_db.py`** — pytest using `tests/fixtures/mini_graph.json`
5. **`jem/scripts/requirements-dev.txt`** — `pytest>=8.0`

### Rules

- Follow `schema_lock.md` column names exactly
- Store nested objects (jurisdiction_scope, appointment, funding, derived, etc.) in `entity_json` TEXT column as JSON
- Normalize: aliases → `entity_aliases`, sources → `entity_sources`
- Run from `jem/`: `python scripts/build_db.py && python scripts/validate_db.py && pytest tests/ -k test_db -v`
