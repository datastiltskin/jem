#!/usr/bin/env python3
"""Apply pending schema migrations to jem.db."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

JEM_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = JEM_ROOT / "data" / "jem.db"
SCHEMA_V2 = JEM_ROOT / "config" / "schema_v2.sql"
SCHEMA_V3 = JEM_ROOT / "config" / "schema_v3.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def current_version(conn: sqlite3.Connection) -> int:
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return int(row[0] or 0)
    except sqlite3.OperationalError:
        return 0


def apply_v2(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_V2.read_text())
    conn.commit()


def apply_v3(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_V3.read_text())
    conn.commit()


def migrate(db_path: Path) -> list[str]:
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")

    conn = connect(db_path)
    applied: list[str] = []
    version = current_version(conn)

    if version < 1:
        raise RuntimeError(
            f"schema_version is {version}; run build_db.py first to create v1 schema"
        )

    if version < 2:
        apply_v2(conn)
        applied.append("v2: users, correction_proposals, sessions, mcp_tokens")

    if version < 3:
        apply_v3(conn)
        applied.append("v3: insight_requests telemetry")

    conn.close()
    return applied


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply JEM SQLite schema migrations")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="Path to jem.db")
    args = parser.parse_args()

    try:
        applied = migrate(args.db)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if applied:
        for item in applied:
            print(f"Applied {item}")
    else:
        print("No migrations pending")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
