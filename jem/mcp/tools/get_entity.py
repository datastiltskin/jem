"""MCP tool: get_entity."""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from api.serializers import entity_row_to_dict
from mcp.refusal import is_refused_query, refusal_payload


def run(conn: sqlite3.Connection, arguments: dict[str, Any]) -> dict:
    entity_id = arguments.get("entity_id", "")
    if is_refused_query(str(entity_id)):
        return refusal_payload()

    row = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
    if row is None:
        return {"error": "not_found", "message": f"Entity not found: {entity_id}"}
    return entity_row_to_dict(row, conn)
