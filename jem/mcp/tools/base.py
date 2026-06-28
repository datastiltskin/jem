"""Shared DB helpers for MCP tools."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

JEM_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB = JEM_ROOT / "data" / "jem.db"


def get_db_path() -> Path:
    return Path(os.environ.get("JEM_DB_PATH", str(DEFAULT_DB)))


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn
