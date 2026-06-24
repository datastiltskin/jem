"""MCP server — tool registry and SSE mount."""

from __future__ import annotations

import json
from typing import Any, Callable

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.responses import Response

from api.deps import connect, get_db_path
from mcp.tools import get_entity, get_relationships, get_structural_gaps, search_entities

ToolFn = Callable[[Any, dict], dict]

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "get_entity": {
        "description": "Retrieve a judicial entity by id with data_quality flags",
        "handler": get_entity.run,
        "input_schema": {
            "type": "object",
            "properties": {"entity_id": {"type": "string"}},
            "required": ["entity_id"],
        },
    },
    "search_entities": {
        "description": "Search entities by name, cluster, type, or state",
        "handler": search_entities.run,
        "input_schema": {
            "type": "object",
            "properties": {
                "q": {"type": "string"},
                "cluster": {"type": "string"},
                "type": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
    },
    "get_relationships": {
        "description": "List relationships for an entity or filters",
        "handler": get_relationships.run,
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string"},
                "relationship_category": {"type": "string"},
            },
        },
    },
    "get_structural_gaps": {
        "description": "Structural gaps (appellate, circularity, capacity) per entity",
        "handler": get_structural_gaps.run,
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {"type": "string"},
                "cluster": {"type": "string"},
            },
        },
    },
}


def list_tools() -> list[dict]:
    return [
        {
            "name": name,
            "description": meta["description"],
            "inputSchema": meta["input_schema"],
        }
        for name, meta in TOOL_REGISTRY.items()
    ]


def call_tool(name: str, arguments: dict | None = None) -> dict:
    if name not in TOOL_REGISTRY:
        return {"error": "unknown_tool", "message": f"Unknown tool: {name}"}
    conn = connect(get_db_path())
    try:
        return TOOL_REGISTRY[name]["handler"](conn, arguments or {})
    finally:
        conn.close()


def create_mcp_router() -> APIRouter:
    router = APIRouter(prefix="/mcp", tags=["mcp"])

    @router.get("/tools")
    def tools_list() -> dict:
        return {"tools": list_tools()}

    @router.post("/tools/{tool_name}")
    async def tools_call(tool_name: str, request: Request) -> JSONResponse:
        body = await request.json() if request.headers.get("content-type") else {}
        args = body.get("arguments", body) if isinstance(body, dict) else {}
        result = call_tool(tool_name, args)
        return JSONResponse({"content": [{"type": "text", "text": json.dumps(result)}]})

    @router.get("/sse")
    async def sse_endpoint() -> StreamingResponse:
        """Minimal SSE endpoint — announces available tools."""

        async def event_stream():
            payload = json.dumps({"tools": [t["name"] for t in list_tools()]})
            yield f"event: tools\ndata: {payload}\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    return router


def mount_mcp(app) -> None:
    """Mount MCP routes; use official SDK SSE when available."""
    router = create_mcp_router()
    app.include_router(router)

    try:
        from mcp.server.fastmcp import FastMCP  # noqa: F401 — optional SDK
    except ImportError:
        pass
