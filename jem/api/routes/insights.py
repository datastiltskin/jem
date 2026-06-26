"""Insight request telemetry — unanswered smart-search questions from the public map."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.deps import get_db

router = APIRouter(prefix="/insights", tags=["insights"])

INSIGHT_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,79}$")
MAX_DISTINCT_REQUESTS = 1000


class InsightRequestCreate(BaseModel):
    insight_id: str = Field(min_length=2, max_length=80)
    title: str = Field(min_length=3, max_length=500)
    query_text: Optional[str] = Field(default=None, max_length=500)


class InsightRequestItem(BaseModel):
    insight_id: str
    title: str
    request_count: int
    last_requested_at: str


class InsightRequestListResponse(BaseModel):
    items: list[InsightRequestItem]
    total: int


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _enforce_cap(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) FROM insight_requests").fetchone()
    excess = int(row[0]) - MAX_DISTINCT_REQUESTS
    if excess <= 0:
        return
    conn.execute(
        """
        DELETE FROM insight_requests
        WHERE id IN (
            SELECT id FROM insight_requests
            ORDER BY last_requested_at ASC, id ASC
            LIMIT ?
        )
        """,
        (excess,),
    )


@router.post("/requests")
def record_insight_request(
    body: InsightRequestCreate,
    conn: sqlite3.Connection = Depends(get_db),
) -> dict:
    insight_id = body.insight_id.strip().lower()
    if not INSIGHT_ID_RE.match(insight_id):
        raise HTTPException(status_code=400, detail="invalid insight_id")

    title = body.title.strip()
    query_text = body.query_text.strip() if body.query_text else None
    now = _iso_now()

    conn.execute(
        """
        INSERT INTO insight_requests (
            insight_id, title, query_text, request_count, first_requested_at, last_requested_at
        ) VALUES (?, ?, ?, 1, ?, ?)
        ON CONFLICT(insight_id) DO UPDATE SET
            request_count = request_count + 1,
            last_requested_at = excluded.last_requested_at,
            title = excluded.title,
            query_text = COALESCE(excluded.query_text, insight_requests.query_text)
        """,
        (insight_id, title, query_text, now, now),
    )
    _enforce_cap(conn)
    conn.commit()

    row = conn.execute(
        "SELECT request_count FROM insight_requests WHERE insight_id = ?",
        (insight_id,),
    ).fetchone()
    return {"ok": True, "insight_id": insight_id, "request_count": int(row[0])}


@router.get("/requests", response_model=InsightRequestListResponse)
def list_insight_requests(
    limit: int = Query(default=8, ge=1, le=50),
    conn: sqlite3.Connection = Depends(get_db),
) -> InsightRequestListResponse:
    total = int(conn.execute("SELECT COUNT(*) FROM insight_requests").fetchone()[0])
    rows = conn.execute(
        """
        SELECT insight_id, title, request_count, last_requested_at
        FROM insight_requests
        ORDER BY last_requested_at DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items = [
        InsightRequestItem(
            insight_id=row[0],
            title=row[1],
            request_count=int(row[2]),
            last_requested_at=row[3],
        )
        for row in rows
    ]
    return InsightRequestListResponse(items=items, total=total)
