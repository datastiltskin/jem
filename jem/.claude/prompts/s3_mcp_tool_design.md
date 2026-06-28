# Session 3 — MCP Tool Design

**Context files:**
- `CLAUDE.md`
- `jem/.claude/decisions/schema_lock.md`
- `jem/.claude/outputs/s2_api_contract.md` (if available)

## Task

Design MCP tools mounted on FastAPI (SSE transport).

For each tool define:
1. Tool name and description (for LLM tool selection)
2. Input schema (JSON Schema)
3. Output schema
4. Which SQLite tables queried
5. Whether results include `data_quality` flags
6. Tools that must refuse (e.g. legal advice, case outcome prediction)

Minimum tools: `get_entity`, `search_entities`, `get_relationships`, `get_structural_gaps`.

**Output:** Tool spec table + example invocations. No implementation code.
