"""Expert portal — staging review queue with audit trail."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from agents.dedup import promote_to_vacancy_event
from api.deps import connect, get_db, get_db_path

PORTAL_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(PORTAL_DIR))


def _audit(
    conn: sqlite3.Connection,
    action: str,
    table_name: str,
    record_id: str,
    actor: str,
    details: dict,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_log (action, table_name, record_id, actor, details_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (action, table_name, record_id, actor, json.dumps(details)),
    )


def create_portal_router() -> APIRouter:
    router = APIRouter(prefix="/portal", tags=["portal"])

    @router.get("/", response_class=HTMLResponse)
    def review_queue(request: Request, conn: sqlite3.Connection = Depends(get_db)) -> HTMLResponse:
        rows = conn.execute(
            """
            SELECT id, entity_name, position, event_type, event_date,
                   reference_number, verbatim_excerpt, confidence, source_url,
                   status, fetched_at
            FROM staging_records
            WHERE status = 'needs_review'
            ORDER BY fetched_at DESC
            """
        ).fetchall()
        items = [dict(row) for row in rows]
        return templates.TemplateResponse(
            request,
            "index.html",
            {"items": items, "count": len(items)},
        )

    @router.get("/api/queue")
    def api_queue(conn: sqlite3.Connection = Depends(get_db)) -> dict:
        rows = conn.execute(
            "SELECT * FROM staging_records WHERE status = 'needs_review' ORDER BY fetched_at DESC"
        ).fetchall()
        return {"items": [dict(r) for r in rows], "count": len(rows)}

    @router.post("/staging/{staging_id}/approve")
    def approve_staging(
        staging_id: int,
        conn: sqlite3.Connection = Depends(get_db),
        actor: str = Form("expert"),
        entity_id: Optional[str] = Form(None),
    ):
        row = conn.execute(
            "SELECT * FROM staging_records WHERE id = ?",
            (staging_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Staging record not found")
        if row["status"] != "needs_review":
            raise HTTPException(status_code=400, detail=f"Cannot approve status: {row['status']}")

        promote_to_vacancy_event(conn, staging_id, entity_id=entity_id, actor=actor)
        _audit(
            conn,
            "approve",
            "staging_records",
            str(staging_id),
            actor,
            {"entity_id": entity_id, "action": "approved_and_promoted"},
        )
        conn.commit()
        return RedirectResponse(url="/portal/", status_code=303)

    @router.post("/staging/{staging_id}/reject")
    def reject_staging(
        staging_id: int,
        conn: sqlite3.Connection = Depends(get_db),
        actor: str = Form("expert"),
        reason: str = Form(""),
    ):
        row = conn.execute(
            "SELECT * FROM staging_records WHERE id = ?",
            (staging_id,),
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Staging record not found")

        conn.execute(
            "UPDATE staging_records SET status = ? WHERE id = ?",
            ("rejected", staging_id),
        )
        _audit(
            conn,
            "reject",
            "staging_records",
            str(staging_id),
            actor,
            {"reason": reason},
        )
        conn.commit()
        return RedirectResponse(url="/portal/", status_code=303)

    return router


def mount_portal(app) -> None:
    app.include_router(create_portal_router())
