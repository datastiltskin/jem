"""FastAPI application factory."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from api.deps import get_db
from api.routes import clusters, entities, relationships
from harness.chat import chat as harness_chat
from mcp.server import mount_mcp
from portal.app import mount_portal

API_PREFIX = "/api/v1"
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


class ChatRequest(BaseModel):
    message: str


def create_app() -> FastAPI:
    app = FastAPI(
        title="JEM Researcher API",
        version="1.0.0",
        description="Judiciary Entity Map (India) — structural data for legal researchers",
    )

    @app.get(f"{API_PREFIX}/health")
    def health(conn: sqlite3.Connection = Depends(get_db)) -> dict:
        count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        return {"status": "ok", "entity_count": count}

    @app.post(f"{API_PREFIX}/chat")
    def chat_endpoint(body: ChatRequest) -> dict:
        return harness_chat(body.message)

    @app.get("/chat")
    def chat_ui() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "chat.html")

    app.include_router(entities.router, prefix=API_PREFIX)
    app.include_router(relationships.router, prefix=API_PREFIX)
    app.include_router(clusters.router, prefix=API_PREFIX)
    mount_mcp(app)
    mount_portal(app)

    return app


app = create_app()
