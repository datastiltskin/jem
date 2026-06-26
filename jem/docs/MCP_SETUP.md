# JEM — MCP & API setup

**Audience:** researchers and developers who want JEM data inside Cursor, Claude, Gemini, or custom agents — or who need programmatic access.

**Non-technical users:** use the **map search** at [friedso.com/apps/jem/](https://friedso.com/apps/jem/) or the hosted REST search API (when deployed). You do not need MCP configuration.

---

## Overview

JEM exposes two integration surfaces on the same FastAPI server:

| Surface | Prefix | Transport | Typical client |
|---------|--------|-----------|----------------|
| REST API | `/api/v1/` | HTTP JSON | Scripts, notebooks, map search backend, other apps |
| MCP HTTP tools | `/mcp/` | HTTP JSON (+ minimal SSE) | AI agents, custom bridges |

Both read from the same SQLite database (`data/jem.db`). No hosted LLM runs on the server.

```
graph.json  →  build_db.py  →  data/jem.db
                                    ↓
                         FastAPI (api.main:app)
                           ├── /api/v1/entities   (search + detail)
                           ├── /api/v1/relationships
                           └── /mcp/tools/*
```

---

## Local setup

### Prerequisites

- Python 3.10+ (3.10+ required for optional `mcp` package)
- Repo cloned; pipeline run at least once so `graph.json` exists at repo root

### Install and build

```bash
cd jem
pip install -r scripts/requirements-dev.txt

python scripts/validate.py
python scripts/derive.py
python scripts/build.py          # writes ../graph.json
python scripts/build_db.py       # writes data/jem.db
python scripts/validate_db.py    # optional integrity check
```

### Environment

Copy `jem/.env.example` to `jem/.env`:

| Variable | Required for | Default |
|----------|--------------|---------|
| `JEM_DB_PATH` | All API/MCP lookups | `data/jem.db` |
| `ANTHROPIC_API_KEY` | Fetcher/verifier agents only (maintainer batch jobs) | — |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | LinkedIn sign-in | — |
| `JEM_BASE_URL` | OAuth redirect base (must match uvicorn host/port) | `http://127.0.0.1:8001` |

Entity lookup via REST and MCP HTTP works **without** an Anthropic key. LinkedIn sign-in: see [`AUTH_SETUP.md`](AUTH_SETUP.md).

### Run the server

```bash
cd jem
python3 -m uvicorn api.main:app --reload --port 8000
```

| Endpoint | Purpose |
|----------|---------|
| http://localhost:8000/api/v1/health | Entity count + status |
| http://localhost:8000/docs | OpenAPI (Swagger) — try search endpoints here |

---

## REST API (recommended for scripts and search)

Base path: `/api/v1`

### Entities (search + detail)

```bash
# Detail
curl -s http://localhost:8000/api/v1/entities/supreme_court_india | jq .

# Search
curl -s 'http://localhost:8000/api/v1/entities?q=NCLT&limit=5' | jq .
```

Query parameters for search: `q`, `cluster`, `type`, `operational_status`, `state`, `data_quality`, `limit`, `offset`.

### Relationships

```bash
curl -s 'http://localhost:8000/api/v1/relationships?entity_id=aft' | jq .
```

---

## MCP HTTP tools

JEM registers four tools (see `jem/mcp/server.py`):

| Tool | Description | Key arguments |
|------|-------------|---------------|
| `get_entity` | Entity by id with data_quality flags | `entity_id` |
| `search_entities` | Search by name, cluster, type, state | `q`, `cluster`, `type`, `limit` |
| `get_relationships` | Relationships for an entity or filters | `entity_id`, `relationship_category` |
| `get_structural_gaps` | Appellate gaps, circularity, capacity | `entity_id`, `cluster` |

### List tools

```bash
curl -s http://localhost:8000/mcp/tools | jq .
```

### Call a tool

```bash
curl -s -X POST http://localhost:8000/mcp/tools/get_entity \
  -H 'Content-Type: application/json' \
  -d '{"arguments": {"entity_id": "nclt"}}' | jq .
```

Response wraps JSON in MCP-style content:

```json
{
  "content": [
    { "type": "text", "text": "{\"id\": \"nclt\", ...}" }
  ]
}
```

### SSE endpoint

`GET /mcp/sse` emits a minimal event stream announcing available tool names. It is not a full MCP stdio session; use HTTP tool calls or REST for reliable integration.

### Refusals

Tool handlers refuse queries that request legal advice, case outcomes, or judge names (see `jem/mcp/refusal.py`). Refused responses include `"refused": true`.

---

## Using JEM in Cursor, Claude, Gemini, or any LLM

### Option A — Repo context (no server)

For **data entry** or YAML edits, open the JEM repo and use [`AI_DATA_ENTRY_PROMPT.md`](AI_DATA_ENTRY_PROMPT.md) with `ROLE: contributor` or `co-maintainer`. The agent reads entity YAML directly.

### Option B — REST / MCP HTTP (live queries, your LLM tokens)

1. Run the FastAPI server locally (see above).
2. Point your LLM client at `http://localhost:8000/api/v1/` or `/mcp/tools/*`.
3. Use **your** subscription or API key in the client — JEM serves data only.

Example Cursor instruction:

```
With JEM API at http://localhost:8000, search entities for NCLT and summarize
appointment relationships. Always report data_quality and unverified_fields.
```

### Option C — MCP server config (advanced)

JEM’s MCP layer is **HTTP-mounted on FastAPI**, not a standalone stdio MCP process. Native MCP config (`mcp.json`) expects stdio or SSE from a dedicated server binary.

**Practical approaches:**

1. **HTTP via agent** — Option B (no extra config).
2. **Custom MCP bridge** — wrap `/mcp/tools/*` in a small stdio proxy.
3. **Future** — full FastMCP / SDK SSE integration is stubbed in `mount_mcp()` but not yet the primary path.

### Option D — Static `graph.json`

Upload or symlink `graph.json` into a Claude Project, ChatGPT, or NotebookLM session for offline snapshot queries (stale until you refresh the file).

---

## Example agent prompts

Structural lookup:

```
Use JEM tools to fetch entity supreme_court_india. Report data_quality,
unverified_fields, and cite source URLs from the response. Do not give legal advice.
```

Relationship trace:

```
Search JEM for "Armed Forces Tribunal", then get_relationships for entity aft.
Summarize the appellate chain only from tool output.
```

Gap analysis:

```
get_structural_gaps for entity_id=nclt. List each gap type and severity from JEM data only.
```

---

## Deployment notes (maintainers)

- **Static map** (friedso.com) ships `graph.json` + `jem/web/` — search can call the API when nginx proxies `/api/jem/`.
- **Researcher stack** needs: `jem.db` built from the same `graph.json` revision you ship, and `uvicorn` (or gunicorn) behind a reverse proxy.
- Rebuild DB after data releases: `python scripts/build_db.py --force`
- Rate-limit public REST/MCP if exposed. See [`.github/SECURITY.md`](../../.github/SECURITY.md).

---

## Tests

```bash
cd jem
pytest tests/test_mcp.py tests/test_api.py -v
```

---

## Related docs

- **Data pipeline:** [`SESSION_WORKFLOW.md`](SESSION_WORKFLOW.md)
- **Schema / DB:** `jem/.claude/decisions/schema_lock.md` · `jem/config/schema.sql`
- **AI data entry (YAML):** [`AI_DATA_ENTRY_PROMPT.md`](AI_DATA_ENTRY_PROMPT.md)
