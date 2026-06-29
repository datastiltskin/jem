"""Maintainer admin — correction queue and user roles."""

from __future__ import annotations

import sqlite3
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from api.auth import oauth
from api.auth.deps import optional_user, require_maintainer
from api.auth.session import User, audit, promote_if_trusted
from api.chrome import templates
from api.deps import get_db


def create_admin_router() -> APIRouter:
    router = APIRouter(prefix="/admin", tags=["admin"])

    @router.get("/", response_class=HTMLResponse)
    def admin_home(
        request: Request,
        conn: sqlite3.Connection = Depends(get_db),
        user: Optional[User] = Depends(optional_user),
    ) -> HTMLResponse:
        pending = []
        users = []
        if user and user.is_maintainer:
            pending = [
                dict(r)
                for r in conn.execute(
                    """
                    SELECT cp.*,
                           u.display_name AS author_name,
                           u.email AS author_email,
                           u.avatar_url AS author_avatar,
                           u.profile_url AS author_profile_url,
                           u.role AS author_role,
                           u.approved_correction_count AS author_approved_count,
                           u.oauth_provider AS author_provider
                    FROM correction_proposals cp
                    JOIN users u ON u.id = cp.author_id
                    WHERE cp.status = 'pending_review'
                    ORDER BY cp.created_at ASC
                    """
                ).fetchall()
            ]
            users = [dict(r) for r in conn.execute("SELECT * FROM users ORDER BY created_at DESC LIMIT 100").fetchall()]

        return templates.TemplateResponse(
            request,
            "admin_index.html",
            {
                "user": user,
                "pending": pending,
                "users": users,
                "pending_count": len(pending),
                "linkedin_login_url": (
                    f"{oauth.public_api_prefix()}/auth/linkedin/login"
                    if oauth.linkedin_configured()
                    else None
                ),
            },
        )

    @router.post("/corrections/{proposal_id}/approve")
    def approve_correction(
        proposal_id: int,
        conn: sqlite3.Connection = Depends(get_db),
        maintainer: User = Depends(require_maintainer),
    ) -> RedirectResponse:
        row = conn.execute(
            "SELECT * FROM correction_proposals WHERE id = ?",
            (proposal_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Proposal not found")
        if row["status"] != "pending_review":
            raise HTTPException(status_code=400, detail="Not pending review")

        conn.execute(
            """
            UPDATE correction_proposals
            SET status = 'published', reviewed_by = ?, reviewed_at = datetime('now')
            WHERE id = ?
            """,
            (maintainer.id, proposal_id),
        )
        conn.execute(
            """
            UPDATE users SET approved_correction_count = approved_correction_count + 1
            WHERE id = ?
            """,
            (row["author_id"],),
        )
        promote_if_trusted(conn, row["author_id"])
        audit(
            conn,
            "approve",
            "correction_proposals",
            str(proposal_id),
            maintainer.display_name,
            {"author_id": row["author_id"]},
        )
        conn.commit()
        return RedirectResponse(url="/admin/", status_code=303)

    @router.post("/corrections/{proposal_id}/reject")
    def reject_correction(
        proposal_id: int,
        conn: sqlite3.Connection = Depends(get_db),
        maintainer: User = Depends(require_maintainer),
        reason: str = Form(""),
    ) -> RedirectResponse:
        row = conn.execute(
            "SELECT id FROM correction_proposals WHERE id = ?",
            (proposal_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Proposal not found")

        conn.execute(
            """
            UPDATE correction_proposals
            SET status = 'rejected', reviewed_by = ?, reviewed_at = datetime('now'), review_note = ?
            WHERE id = ?
            """,
            (maintainer.id, reason.strip(), proposal_id),
        )
        audit(
            conn,
            "reject",
            "correction_proposals",
            str(proposal_id),
            maintainer.display_name,
            {"reason": reason},
        )
        conn.commit()
        return RedirectResponse(url="/admin/", status_code=303)

    @router.post("/users/{user_id}/role")
    def set_user_role(
        user_id: int,
        conn: sqlite3.Connection = Depends(get_db),
        maintainer: User = Depends(require_maintainer),
        role: str = Form(...),
    ) -> RedirectResponse:
        if role not in ("new", "trusted", "expert", "maintainer"):
            raise HTTPException(status_code=400, detail="Invalid role")

        conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        audit(
            conn,
            "set_role",
            "users",
            str(user_id),
            maintainer.display_name,
            {"role": role},
        )
        conn.commit()
        return RedirectResponse(url="/admin/", status_code=303)

    return router


def mount_admin(app) -> None:
    app.include_router(create_admin_router())
