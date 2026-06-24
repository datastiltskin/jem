"""Relationship query endpoints."""

from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from api.serializers import relationship_row_to_dict

router = APIRouter(tags=["relationships"])


@router.get("/relationships")
def list_relationships(
    conn: sqlite3.Connection = Depends(get_db),
    entity_id: Optional[str] = Query(None, description="Match source or target"),
    source: Optional[str] = None,
    target: Optional[str] = None,
    relationship_category: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    clauses: list[str] = []
    params: list[object] = []

    if entity_id:
        clauses.append("(source = ? OR target = ?)")
        params.extend([entity_id, entity_id])
    if source:
        clauses.append("source = ?")
        params.append(source)
    if target:
        clauses.append("target = ?")
        params.append(target)
    if relationship_category:
        clauses.append("relationship_category = ?")
        params.append(relationship_category)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    total = conn.execute(
        f"SELECT COUNT(*) FROM relationships {where}",
        params,
    ).fetchone()[0]

    rows = conn.execute(
        f"""
        SELECT * FROM relationships
        {where}
        ORDER BY id
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [relationship_row_to_dict(row) for row in rows],
    }


@router.get("/relationships/{relationship_id}")
def get_relationship(
    relationship_id: str,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    row = conn.execute(
        "SELECT * FROM relationships WHERE id = ?",
        (relationship_id,),
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "not_found",
                    "message": f"Relationship not found: {relationship_id}",
                }
            },
        )
    return relationship_row_to_dict(row)
