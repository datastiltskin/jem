"""Correction proposals API — public read, authenticated write."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from api.auth.deps import optional_user, require_user
from api.auth.session import User, audit, promote_if_trusted
from api.deps import get_db

router = APIRouter(prefix="/corrections", tags=["corrections"])

NEW_USER_DAILY_LIMIT = 3
SCOPE_RE = re.compile(r"^(entity:[a-z0-9_]+|overview)$")


class CorrectionCreate(BaseModel):
    scope: str = Field(min_length=3, max_length=120)
    body: str = Field(min_length=1, max_length=2000)
    source_url: str = Field(min_length=8, max_length=2048)


class CorrectionItem(BaseModel):
    id: int
    scope: str
    entity_id: str | None
    body: str
    source_url: str
    status: str
    author_name: str
    author_avatar: str | None
    created_at: str
    vote_count: int
    user_voted: bool
    pending_for_viewer: bool = False


class CorrectionListResponse(BaseModel):
    items: list[CorrectionItem]
    total: int


def _parse_entity_id(scope: str) -> str | None:
    if scope.startswith("entity:"):
        return scope.split(":", 1)[1]
    return None


def _iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _count_today(conn: sqlite3.Connection, user_id: int) -> int:
    row = conn.execute(
        """
        SELECT COUNT(*) FROM correction_proposals
        WHERE author_id = ? AND date(created_at) = date('now')
        """,
        (user_id,),
    ).fetchone()
    return int(row[0])


def _serialize_row(row: sqlite3.Row, viewer: Optional[User], voted_ids: set[int]) -> CorrectionItem:
    status = row["status"]
    author_id = row["author_id"]
    pending_for_viewer = (
        status == "pending_review"
        and viewer is not None
        and viewer.id == author_id
        and not viewer.is_maintainer
    )
    return CorrectionItem(
        id=row["id"],
        scope=row["scope"],
        entity_id=row["entity_id"],
        body=row["body"],
        source_url=row["source_url"],
        status=status,
        author_name=row["display_name"],
        author_avatar=row["avatar_url"],
        created_at=row["created_at"],
        vote_count=row["vote_count"],
        user_voted=row["id"] in voted_ids,
        pending_for_viewer=pending_for_viewer,
    )


@router.get("", response_model=CorrectionListResponse)
def list_corrections(
    scope: str = Query(..., min_length=3),
    conn: sqlite3.Connection = Depends(get_db),
    viewer: Optional[User] = Depends(optional_user),
) -> CorrectionListResponse:
    if not SCOPE_RE.match(scope):
        raise HTTPException(status_code=400, detail="Invalid scope format")

    params: list = [scope]
    where = "cp.scope = ? AND cp.status = 'published'"

    if viewer and viewer.is_maintainer:
        where = "cp.scope = ? AND cp.status IN ('published', 'pending_review')"
    elif viewer:
        where = (
            "cp.scope = ? AND (cp.status = 'published' "
            "OR (cp.status = 'pending_review' AND cp.author_id = ?))"
        )
        params.append(viewer.id)

    rows = conn.execute(
        f"""
        SELECT cp.*, u.display_name, u.avatar_url,
               (SELECT COUNT(*) FROM correction_votes cv WHERE cv.proposal_id = cp.id) AS vote_count
        FROM correction_proposals cp
        JOIN users u ON u.id = cp.author_id
        WHERE {where}
        ORDER BY cp.created_at DESC
        """,
        params,
    ).fetchall()

    voted_ids: set[int] = set()
    if viewer:
        votes = conn.execute(
            "SELECT proposal_id FROM correction_votes WHERE user_id = ?",
            (viewer.id,),
        ).fetchall()
        voted_ids = {r["proposal_id"] for r in votes}

    items = [_serialize_row(r, viewer, voted_ids) for r in rows]
    return CorrectionListResponse(items=items, total=len(items))


@router.post("", response_model=CorrectionItem, status_code=201)
def create_correction(
    body: CorrectionCreate,
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(require_user),
) -> CorrectionItem:
    if not SCOPE_RE.match(body.scope):
        raise HTTPException(status_code=400, detail="Invalid scope format")

    entity_id = _parse_entity_id(body.scope)
    if entity_id:
        exists = conn.execute("SELECT 1 FROM entities WHERE id = ?", (entity_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=400, detail=f"Unknown entity: {entity_id}")

    if user.role == "new":
        if _count_today(conn, user.id) >= NEW_USER_DAILY_LIMIT:
            raise HTTPException(status_code=429, detail="Daily limit reached for new users (3/day)")

    status = "pending_review" if user.role == "new" else "published"

    cur = conn.execute(
        """
        INSERT INTO correction_proposals (scope, entity_id, body, source_url, status, author_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (body.scope, entity_id, body.body.strip(), str(body.source_url).strip(), status, user.id),
    )
    proposal_id = cur.lastrowid
    audit(
        conn,
        "create",
        "correction_proposals",
        str(proposal_id),
        user.display_name,
        {"scope": body.scope, "status": status},
    )
    conn.commit()

    row = conn.execute(
        """
        SELECT cp.*, u.display_name, u.avatar_url, 0 AS vote_count
        FROM correction_proposals cp
        JOIN users u ON u.id = cp.author_id
        WHERE cp.id = ?
        """,
        (proposal_id,),
    ).fetchone()
    assert row is not None
    return _serialize_row(row, user, set())


@router.post("/{proposal_id}/vote")
def vote_correction(
    proposal_id: int,
    conn: sqlite3.Connection = Depends(get_db),
    user: User = Depends(require_user),
) -> dict:
    if not user.can_vote:
        raise HTTPException(status_code=403, detail="Trusted account required to vote")

    row = conn.execute(
        "SELECT id, status FROM correction_proposals WHERE id = ?",
        (proposal_id,),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Proposal not found")
    if row["status"] != "published":
        raise HTTPException(status_code=400, detail="Can only vote on published proposals")

    existing = conn.execute(
        "SELECT 1 FROM correction_votes WHERE user_id = ? AND proposal_id = ?",
        (user.id, proposal_id),
    ).fetchone()

    if existing:
        conn.execute(
            "DELETE FROM correction_votes WHERE user_id = ? AND proposal_id = ?",
            (user.id, proposal_id),
        )
        voted = False
    else:
        conn.execute(
            "INSERT INTO correction_votes (user_id, proposal_id) VALUES (?, ?)",
            (user.id, proposal_id),
        )
        voted = True

    count = conn.execute(
        "SELECT COUNT(*) FROM correction_votes WHERE proposal_id = ?",
        (proposal_id,),
    ).fetchone()[0]
    conn.commit()
    return {"proposal_id": proposal_id, "voted": voted, "vote_count": count}
