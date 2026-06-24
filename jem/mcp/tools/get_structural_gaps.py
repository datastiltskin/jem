"""MCP tool: get_structural_gaps."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from mcp.refusal import is_refused_query, refusal_payload


def _extract_gaps(entity_id: str, name: str, data_quality: str, blob: dict) -> list[dict]:
    gaps_raw = blob.get("gaps")
    if not gaps_raw:
        return []

    entries: list[dict] = []
    if isinstance(gaps_raw, list):
        for item in gaps_raw:
            if isinstance(item, dict) and "gaps" in item:
                entries.extend(item["gaps"])
            elif isinstance(item, dict):
                entries.append(item)
    elif isinstance(gaps_raw, dict):
        if "gaps" in gaps_raw:
            entries.extend(gaps_raw["gaps"])
        else:
            entries.append(gaps_raw)
    return entries


def run(conn: sqlite3.Connection, arguments: dict[str, Any]) -> dict:
    entity_id = arguments.get("entity_id")
    cluster = arguments.get("cluster")
    if entity_id and is_refused_query(str(entity_id)):
        return refusal_payload()

    clauses: list[str] = []
    params: list[object] = []
    if entity_id:
        clauses.append("id = ?")
        params.append(entity_id)
    if cluster:
        clauses.append("cluster = ?")
        params.append(cluster)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"SELECT id, name, data_quality, entity_json FROM entities {where}",
        params,
    ).fetchall()

    results: list[dict] = []
    for row in rows:
        blob = json.loads(row["entity_json"] or "{}")
        gap_list = _extract_gaps(row["id"], row["name"], row["data_quality"], blob)
        if not gap_list:
            continue
        results.append(
            {
                "entity_id": row["id"],
                "entity_name": row["name"],
                "data_quality": row["data_quality"],
                "gaps": gap_list,
            }
        )

    return {"gaps": results, "count": len(results)}
