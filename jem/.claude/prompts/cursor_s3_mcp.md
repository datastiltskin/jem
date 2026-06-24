# CURSOR SESSION 3 — MCP Server

**Attach:**
- `jem/.claude/outputs/s3_mcp_tool_design.md`
- `jem/api/main.py`

## Task

Build `jem/mcp/` MCP server (Python SDK), SSE transport, mounted on FastAPI.

- `mcp/server.py` — tool registration
- `mcp/tools/` — one module per tool
- `tests/test_mcp.py`

Tools must refuse legal advice and case outcome queries.
