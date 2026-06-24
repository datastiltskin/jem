"""Entity search and detail endpoints."""

from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from api.deps import get_db
from api.serializers import entity_row_to_dict

router = APIRouter(prefix="/entities", tags=["entities"])


def _not_found(entity_id: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"error": {"code": "not_found", "message": f"Entity not found: {entity_id}"}},
    )


@router.get("/{entity_id}")
def get_entity(entity_id: str, conn: sqlite3.Connection = Depends(get_db)) -> dict:
    row = conn.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
    if row is None:
        raise _not_found(entity_id)
    return entity_row_to_dict(row, conn)


@router.get("")
def search_entities(
    conn: sqlite3.Connection = Depends(get_db),
    q: Optional[str] = Query(None, description="Search name, abbreviation, or alias"),
    cluster: Optional[str] = None,
    type: Optional[str] = Query(None, alias="type"),
    operational_status: Optional[str] = None,
    state: Optional[str] = Query(None, description="ISO state code in jurisdiction scope"),
    data_quality: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
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

    if cluster:
        clauses.append("e.cluster = ?")
        params.append(cluster)
    if type:
        clauses.append("e.type = ?")
        params.append(type)
    if operational_status:
        clauses.append("e.operational_status = ?")
        params.append(operational_status)
    if data_quality:
        clauses.append("e.data_quality = ?")
        params.append(data_quality)
    if state:
        clauses.append(
            """
            EXISTS (
                SELECT 1 FROM jurisdictional_scope js
                WHERE js.entity_id = e.id
                  AND js.states_covered_json LIKE ?
            )
            """
        )
        params.append(f'%"{state}"%')

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    total = conn.execute(
        f"SELECT COUNT(*) FROM entities e {where}",
        params,
    ).fetchone()[0]

    rows = conn.execute(
        f"""
        SELECT e.* FROM entities e
        {where}
        ORDER BY e.name
        LIMIT ? OFFSET ?
        """,
        [*params, limit, offset],
    ).fetchall()

    items = [entity_row_to_dict(row, conn) for row in rows]
    return {"total": total, "limit": limit, "offset": offset, "items": items}
