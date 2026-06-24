# Session 0 — Migration Decisions

**Context files:**
- `CLAUDE.md`
- `jem/.claude/outputs/s0_schema_audit.md` (if available)
- `entity_schema.yaml`
- `graph.json`

## Task

Lock migration rules for graph.json → SQLite.

1. **Naming rules** — snake_case columns, table prefixes, FK naming
2. **FK strategy** — CASCADE vs RESTRICT per relationship type
3. **Staging vs target** — which tables are write-once vs mutable
4. **JSON blob policy** — which nested entity fields stay JSON vs normalized tables
5. **graph.json field mapping** — column per top-level entity field
6. **Idempotency** — schema_version table, rebuild semantics
7. **Indexes** — required for API query patterns

**Output format:** Numbered decisions with rationale. No SQL DDL — that goes in schema_lock.
