# Session 2 — API Contract

**Context files:**
- `CLAUDE.md`
- `jem/.claude/decisions/schema_lock.md`
- `graph.json` (sample entities)

## Task

Design FastAPI HTTP contract for legal researchers.

Define:
1. Base path and versioning (`/api/v1/`)
2. Endpoints: entity by id, search, relationships, cluster summary
3. Request/response JSON schemas per endpoint
4. Pagination, filtering (cluster, type, state, operational_status)
5. `data_quality` and `unverified_fields` exposure rules — never hide unverified status
6. Error response format
7. Rate limiting recommendation for 4GB server

**Output:** OpenAPI-style markdown spec. No implementation code.
