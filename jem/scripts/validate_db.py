#!/usr/bin/env python3
"""Validate SQLite database against schema_lock.md expectations."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

JEM_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = JEM_ROOT / "data" / "jem.db"
DEFAULT_GRAPH = JEM_ROOT.parent / "graph.json"
SCHEMA_VERSION = 3

REQUIRED_TABLES = {
    "schema_version",
    "entities",
    "entity_aliases",
    "entity_sources",
    "jurisdictional_scope",
    "statutory_basis_records",
    "relationships",
    "vacancy_events",
    "staging_records",
    "audit_log",
    "data_conflicts",
    "users",
    "sessions",
    "correction_proposals",
    "correction_votes",
    "mcp_tokens",
    "insight_requests",
}

ENTITIES_REQUIRED_COLUMNS = {
    "id",
    "name",
    "type",
    "cluster",
    "level_of_government",
    "created_year",
    "operational_status",
    "data_quality",
    "entity_json",
}


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def validate_db(db_path: Path, graph_path: Path) -> list[str]:
    errors: list[str] = []

    if not db_path.exists():
        return [f"database not found: {db_path}"]

    conn = connect(db_path)

    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    missing_tables = REQUIRED_TABLES - tables
    if missing_tables:
        errors.append(f"missing tables: {sorted(missing_tables)}")

    if "entities" in tables:
        cols = {row[1] for row in conn.execute("PRAGMA table_info(entities)")}
        missing_cols = ENTITIES_REQUIRED_COLUMNS - cols
        if missing_cols:
            errors.append(f"entities missing columns: {sorted(missing_cols)}")
    else:
        conn.close()
        return errors

    try:
        version_row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        if not version_row or version_row[0] != SCHEMA_VERSION:
            errors.append(f"schema_version expected {SCHEMA_VERSION}, got {version_row}")
    except sqlite3.OperationalError:
        errors.append("schema_version table missing or unreadable")

    entity_count = conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]
    if graph_path.exists():
        graph = json.loads(graph_path.read_text())
        expected = graph.get("meta", {}).get("entity_count", len(graph.get("entities", [])))
        if entity_count < expected:
            errors.append(f"entity count {entity_count} < graph meta {expected}")

    orphan_aliases = conn.execute(
        """
        SELECT COUNT(*) FROM entity_aliases a
        LEFT JOIN entities e ON a.entity_id = e.id
        WHERE e.id IS NULL
        """
    ).fetchone()[0]
    if orphan_aliases:
        errors.append(f"orphan entity_aliases: {orphan_aliases}")

    orphan_rels = conn.execute(
        """
        SELECT COUNT(*) FROM relationships r
        LEFT JOIN entities s ON r.source = s.id
        LEFT JOIN entities t ON r.target = t.id
        WHERE s.id IS NULL OR t.id IS NULL
        """
    ).fetchone()[0]
    if orphan_rels:
        errors.append(f"orphan relationships (FK violation): {orphan_rels}")

    null_names = conn.execute(
        "SELECT COUNT(*) FROM entities WHERE name IS NULL OR name = ''"
    ).fetchone()[0]
    if null_names:
        errors.append(f"entities with empty name: {null_names}")

    conn.close()
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate jem.db schema and integrity")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    args = parser.parse_args()

    errors = validate_db(args.db, args.graph)
    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1

    print(f"OK: {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
