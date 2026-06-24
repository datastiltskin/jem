# Session 0 — Schema Audit

**Context files (repo root unless noted):**
- `CLAUDE.md`
- `entity_schema.yaml` (canonical, v1.3.0)
- `jem/data/schema/relationship_schema.yaml`
- `graph.json` (meta + entity/relationship samples)

## Task

Schema audit before any code is written.

1. Review `entity_schema.yaml` and `relationship_schema.yaml`
2. List every field missing for temporal vacancy tracking
3. List every field missing for statutory basis layer
4. List every field missing for jurisdictional scope
5. Identify naming inconsistencies across schemas
6. Identify graph.json entities with migration problems
7. Propose complete final SQLite table list with exact column names, types, constraints, and foreign keys

**Output format:** Markdown table per section.
**Do not generate code.** Generate decisions only.
This output becomes the ground truth for all subsequent sessions.
