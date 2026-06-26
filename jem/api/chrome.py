"""Shared JEM chrome (compact lockup toolbar) for API satellite pages."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def map_base_url() -> str:
    return os.environ.get("JEM_MAP_URL", "http://127.0.0.1:8080").rstrip("/")


def jem_toolbar_html(active: str | None = None) -> Markup:
    """Compact lockup + nav links back to the map UI."""
    map_url = map_base_url()
    about_url = f"{map_url}/#/about"

    def link(href: str, label: str, key: str) -> str:
        cls = ' class="active"' if active == key else ""
        return f'<a href="{href}"{cls}>{label}</a>'

    return Markup(
        f'<header class="jem-chrome">'
        f'<a href="{map_url}" class="jem-chrome-home" title="JEM map — overview">'
        f'<img src="/public/assets/jem-lockup.png" alt="JEM" class="jem-chrome-logo" '
        f'width="160" height="68" decoding="async"></a>'
        f'<nav class="jem-chrome-nav" aria-label="JEM site">'
        f'{link(map_url, "Map", "map")}'
        f'{link(about_url, "About", "about")}'
        f'{link("/docs", "API docs", "docs")}'
        f'{link("/portal/", "Portal", "portal")}'
        f'{link("/admin/", "Admin", "admin")}'
        f'{link("/mcp/", "MCP", "mcp")}'
        f"</nav></header>"
    )


templates.env.globals["jem_toolbar"] = jem_toolbar_html
templates.env.globals["map_url"] = map_base_url
