"""FastAPI dependencies — SQLite connection per request."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Generator
from pathlib import Path

from fastapi import Depends

JEM_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = JEM_ROOT / "data" / "jem.db"


def get_db_path() -> Path:
    return Path(os.environ.get("JEM_DB_PATH", str(DEFAULT_DB)))


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def get_db(db_path: Path = Depends(get_db_path)) -> Generator[sqlite3.Connection, None, None]:
    conn = connect(db_path)
    try:
        yield conn
    finally:
        conn.close()
