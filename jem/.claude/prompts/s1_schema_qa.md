# Session 1 — Schema QA

**Context files:**
- `CLAUDE.md`
- `jem/.claude/decisions/schema_lock.md`
- `jem/.claude/decisions/migration_rules.md`
- `jem/config/schema.sql`
- `jem/scripts/build_db.py`
- `jem/scripts/validate_db.py`

## Task

Post-build QA audit of SQLite implementation against locked schema.

1. Does `schema.sql` match every table/column in `schema_lock.md`?
2. Does `build_db.py` migrate all graph.json entity and relationship fields?
3. Are FK constraints enforced correctly?
4. Any columns that should be NOT NULL but allow NULL?
5. Missing indexes for entity lookup by id, type, cluster, state?
6. Test coverage gaps in `test_db.py`

**Output:** Issues table (severity, location, fix) + green list of correct design.
