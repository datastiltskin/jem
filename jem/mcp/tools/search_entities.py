"""MCP tool: search_entities."""

from __future__ import annotations

import sqlite3
from typing import Any, Optional

from api.serializers import entity_row_to_dict
from mcp.refusal import is_refused_query, refusal_payload


def run(conn: sqlite3.Connection, arguments: dict[str, Any]) -> dict:
    q = arguments.get("q")
    if q and is_refused_query(str(q)):
        return refusal_payload()

    clauses: list[str] = []
    params: list[object] = []

    if q:
        clauses.append(
            """
            (e.name LIKE ? OR e.abbreviation LIKE ?
             OR EXISTS (
                SELECT 1 FROM entity_aliases ea
                WHERE ea.entity_id = e.id AND ea.alias LIKE ?
             ))
            """
        )
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern])

    for key, col in (
        ("cluster", "e.cluster"),
        ("type", "e.type"),
        ("operational_status", "e.operational_status"),
        ("data_quality", "e.data_quality"),
    ):
        val = arguments.get(key)
        if val:
            clauses.append(f"{col} = ?")
            params.append(val)

    state = arguments.get("state")
    if state:
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM jurisdictional_scope js
                WHERE js.entity_id = e.id AND js.states_covered_json LIKE ?
            )
            """
        )
        params.append(f'%"{state}"%')

    limit = min(int(arguments.get("limit", 10)), 50)
    offset = int(arguments.get("offset", 0))
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    total = conn.execute(f"SELECT COUNT(*) FROM entities e {where}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT e.* FROM entities e {where} ORDER BY e.name LIMIT ? OFFSET ?",
        [*params, limit, offset],
    ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [entity_row_to_dict(row, conn) for row in rows],
    }
