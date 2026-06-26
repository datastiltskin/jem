"""FastAPI application factory."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.deps import get_db
from api.routes import auth, clusters, corrections, entities, insights, relationships
from mcp.server import mount_mcp
from portal.app import mount_portal
from admin.app import mount_admin

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title="JEM Researcher API",
        version="1.0.0",
        description="Judiciary Entity Map (India) — structural data for legal researchers",
        docs_url=None,
        redoc_url=None,
    )

    cors_origins = [
        o.strip()
        for o in os.environ.get(
            "JEM_CORS_ORIGINS",
            "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8000,http://127.0.0.1:8000,http://localhost:8001,http://127.0.0.1:8001,https://friedso.com,https://www.friedso.com",
        ).split(",")
        if o.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs", status_code=302)

    @app.get("/docs", include_in_schema=False)
    def swagger_ui() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} — API",
            swagger_favicon_url="/public/assets/jem-favicon.svg",
            swagger_ui_parameters={"customCssUrl": "/public/jem-chrome.css"},
        )

    @app.get(f"{API_PREFIX}/health")
    def health(conn: sqlite3.Connection = Depends(get_db)) -> dict:
        count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
        return {"status": "ok", "entity_count": count}

    app.include_router(entities.router, prefix=API_PREFIX)
    app.include_router(relationships.router, prefix=API_PREFIX)
    app.include_router(clusters.router, prefix=API_PREFIX)
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(corrections.router, prefix=API_PREFIX)
    app.include_router(insights.router, prefix=API_PREFIX)
    mount_mcp(app)
    mount_portal(app)
    mount_admin(app)

    web_public = Path(__file__).resolve().parent.parent / "web" / "public"
    if web_public.is_dir():
        app.mount("/public", StaticFiles(directory=str(web_public)), name="web-public")

    return app


app = create_app()
