"""MCP tool: get_relationships."""

from __future__ import annotations

import sqlite3
from typing import Any

from api.serializers import relationship_row_to_dict
from mcp.refusal import is_refused_query, refusal_payload


def run(conn: sqlite3.Connection, arguments: dict[str, Any]) -> dict:
    for key in ("entity_id", "source", "target", "relationship_category"):
        val = arguments.get(key)
        if val and is_refused_query(str(val)):
            return refusal_payload()

    clauses: list[str] = []
    params: list[object] = []

    entity_id = arguments.get("entity_id")
    if entity_id:
        clauses.append("(source = ? OR target = ?)")
        params.extend([entity_id, entity_id])
    for key in ("source", "target", "relationship_category"):
        val = arguments.get(key)
        if val:
            clauses.append(f"{key} = ?")
            params.append(val)

    limit = min(int(arguments.get("limit", 20)), 100)
    offset = int(arguments.get("offset", 0))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    total = conn.execute(f"SELECT COUNT(*) FROM relationships {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM relationships {where} ORDER BY id LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [relationship_row_to_dict(row) for row in rows],
    }
