"""Row → JSON serializers for API responses."""

from __future__ import annotations

import json
import sqlite3
from typing import Any


def _loads(value: str | None, default: Any) -> Any:
    if value is None:
        return default
    return json.loads(value)


def entity_row_to_dict(row: sqlite3.Row, conn: sqlite3.Connection | None = None) -> dict:
    blob = _loads(row["entity_json"], {})
    unverified = _loads(row["unverified_fields_json"], [])

    result: dict[str, Any] = {
        "id": row["id"],
        "name": row["name"],
        "name_hindi": row["name_hindi"],
        "abbreviation": row["abbreviation"],
        "type": row["type"],
        "cluster": row["cluster"],
        "level_of_government": row["level_of_government"],
        "legislature_status": row["legislature_status"],
        "created_year": row["created_year"],
        "enacted_year": row["enacted_year"],
        "operational_year": row["operational_year"],
        "abolished_year": row["abolished_year"],
        "operational_status": row["operational_status"],
        "constitutional_basis": row["constitutional_basis"],
        "statutory_basis": row["statutory_basis"],
        "parent_hc": row["parent_hc"],
        "data_quality": row["data_quality"],
        "data_quality_notes": row["data_quality_notes"],
        "unverified_fields": unverified if unverified is not None else [],
        "position": row["position"],
    }
    result.update(blob)

    if conn is not None:
        aliases = [
            r["alias"]
            for r in conn.execute(
                "SELECT alias FROM entity_aliases WHERE entity_id = ? ORDER BY alias",
                (row["id"],),
            )
        ]
        result["aliases"] = aliases

        sources = [
            {
                "source_type": s["source_type"],
                "url": s["url"],
                "title": s["title"],
                "accessed_date": s["accessed_date"],
            }
            for s in conn.execute(
                """
                SELECT source_type, url, title, accessed_date
                FROM entity_sources WHERE entity_id = ? ORDER BY id
                """,
                (row["id"],),
            )
        ]
        result["sources"] = sources

        js = conn.execute(
            """
            SELECT is_all_india, is_shared_multi, shared_appointer,
                   states_covered_json, uts_covered_json, jurisdiction_types_json
            FROM jurisdictional_scope WHERE entity_id = ?
            """,
            (row["id"],),
        ).fetchone()
        if js:
            result["jurisdiction_scope"] = {
                "is_all_india": bool(js["is_all_india"]),
                "is_shared_multi": bool(js["is_shared_multi"]),
                "shared_appointer": js["shared_appointer"],
                "states_covered": _loads(js["states_covered_json"], []),
                "uts_covered": _loads(js["uts_covered_json"], []),
                "jurisdiction_types": _loads(js["jurisdiction_types_json"], []),
            }

    return result


def relationship_row_to_dict(row: sqlite3.Row) -> dict:
    blob = _loads(row["relationship_json"], {})
    result: dict[str, Any] = {
        "id": row["id"],
        "source": row["source"],
        "target": row["target"],
        "relationship_type": row["relationship_type"],
        "relationship_category": row["relationship_category"],
        "is_binding": bool(row["is_binding"]) if row["is_binding"] is not None else None,
        "is_constitutional": bool(row["is_constitutional"])
        if row["is_constitutional"] is not None
        else None,
        "year_established": row["year_established"],
        "year_abolished": row["year_abolished"],
        "data_quality": row["data_quality"],
        "contested_note": row["contested_note"],
        "notes": row["notes"],
        "statutory_basis": row["statutory_basis"],
    }
    result.update(blob)
    return result
