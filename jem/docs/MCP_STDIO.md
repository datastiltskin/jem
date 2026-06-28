# Native MCP stdio — discussion (Jun 2026)

**Status:** Not implemented. JEM ships **HTTP MCP tools** on the FastAPI server (`/mcp/tools/*`). This note records requirements and a go/no-go for native stdio before building.

---

## What “native MCP stdio” means

Cursor, Claude Desktop, and similar clients can load an MCP server from `mcp.json` as a **child process** that speaks JSON-RPC over **stdin/stdout**:

```json
{
  "mcpServers": {
    "jem": {
      "command": "python3",
      "args": ["/path/to/jem/mcp/stdio_server.py"],
      "env": { "JEM_DB_PATH": "/path/to/jem/data/jem.db" }
    }
  }
}
```

That is different from JEM’s current model: tools are **HTTP POST** handlers on the same app as the REST API.

---

## Is MCP useful at all?

**Yes, for a narrow audience:**

| User | Best surface |
|------|----------------|
| Map browser | Static `graph.json` + in-app search — **no MCP** |
| Script / notebook | REST `/api/v1/entities?q=…` |
| AI agent (Cursor, Claude) with live DB | MCP tools or REST — **search first, then by id** |
| Maintainer YAML editing | Repo context + `AI_DATA_ENTRY_PROMPT.md` — **no server** |

MCP tools expose the same SQLite data as REST: `get_entity`, `search_entities`, `get_relationships`, `get_structural_gaps`. They refuse legal-advice / case-outcome / judge-name queries. Value is **structured, citable lookups** inside an agent session without uploading all of `graph.json`.

---

## Requirements for native stdio

| Requirement | Notes |
|-------------|--------|
| Python **3.10+** | `mcp` package (optional in `requirements-dev.txt`) |
| **`data/jem.db`** | Built from `graph.json` via `build_db.py`; ~few MB for 1,145 entities |
| **MCP Python SDK** | `FastMCP` or low-level `Server` + stdio transport |
| **Local process** | stdio runs on the **researcher’s machine**, not on friedso.com |
| **Tool handlers** | Reuse `jem/mcp/tools/*.py` (already shared with HTTP) |

**Not required on server for stdio:** uvicorn, nginx, public URL — unless you also expose HTTP MCP.

---

## Would friedso VPS (4GB RAM, 2 cores) handle it?

**Clarify where each piece runs:**

| Component | Typical host | Load on 4GB VPS |
|-----------|----------------|-----------------|
| **Static map** (`graph.json` + `jem/web/`) | friedso nginx | Low — already deployed |
| **REST + HTTP MCP** (`uvicorn`) | Optional on VPS | Low–moderate for SQLite reads; rate-limit if public |
| **Native MCP stdio** | Developer laptop / Cursor | **Zero on VPS** — subprocess on client machine |
| **Anthropic API** (fetcher agents) | External API | Not on VPS |

The VyomCloud box can run **one uvicorn worker + SQLite** for public `/api/jem/v1` and `/mcp/tools` if nginx is configured. That is unrelated to stdio.

**Risks if exposing HTTP MCP publicly:** abuse, no auth on tool endpoints today — use nginx rate limits and optional API keys before wide exposure.

**stdio on VPS** only matters if you SSH into the server and point Cursor at a remote stdio process — unusual; HTTP or REST is simpler.

---

## Options (if we build later)

1. **Keep HTTP only (current)** — agents use `curl` or REST from the same host as uvicorn. Zero new code.
2. **Local stdio server** — `mcp/stdio_server.py` using FastMCP, reads `JEM_DB_PATH`, registers same four tools. Best for Cursor `mcp.json` on maintainer machines.
3. **Stdio → HTTP bridge** — thin proxy for clients that only speak stdio but data lives on friedso — adds latency; rarely worth it.
4. **Full SDK SSE** — stub in `mount_mcp()`; Cursor’s SSE URL support varies; HTTP POST tools already work.

**Recommendation:** Ship **(2) local stdio** when a maintainer needs one-click Cursor integration; keep production on **HTTP REST/MCP** behind nginx. Do not run stdio as a systemd service on the VPS unless there is a concrete remote-SSH workflow.

---

## Related

- Setup: [`MCP_SETUP.md`](MCP_SETUP.md)
- Tests: `pytest tests/test_mcp.py`
- HTTP registry: `jem/mcp/server.py`
