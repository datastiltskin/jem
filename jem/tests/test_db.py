"""SQLite foundation tests — marker: test_db."""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

JEM_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = JEM_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from build_db import SCHEMA_VERSION, apply_schema, build_db, connect, entity_count, migrate_graph  # noqa: E402
from validate_db import validate_db  # noqa: E402

REQUIRED_TABLES = [
    "entities",
    "entity_aliases",
    "entity_sources",
    "jurisdictional_scope",
    "relationships",
    "staging_records",
    "audit_log",
]


def test_schema_tables_exist(tmp_db: Path, schema_sql_path: Path) -> None:
    conn = connect(tmp_db)
    apply_schema(conn)
    tables = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    conn.close()
    for table in REQUIRED_TABLES:
        assert table in tables


def test_migrate_mini_graph(tmp_db: Path, mini_graph: dict) -> None:
    graph_path = tmp_db.parent / "mini.json"
    graph_path.write_text(json.dumps(mini_graph))
    result = build_db(graph_path, tmp_db, force=True)
    assert result["skipped"] is False
    assert result["entities"] == len(mini_graph["entities"])

    conn = connect(tmp_db)
    assert entity_count(conn) == len(mini_graph["entities"])
    row = conn.execute("SELECT entity_json FROM entities LIMIT 1").fetchone()
    assert row is not None
    json.loads(row[0])  # valid JSON
    conn.close()


def test_entity_aliases_normalized(tmp_db: Path, mini_graph: dict) -> None:
    graph_path = tmp_db.parent / "mini.json"
    graph_path.write_text(json.dumps(mini_graph))
    build_db(graph_path, tmp_db, force=True)

    conn = connect(tmp_db)
    for entity in mini_graph["entities"]:
        aliases = entity.get("aliases") or []
        if not aliases:
            continue
        count = conn.execute(
            "SELECT COUNT(*) FROM entity_aliases WHERE entity_id = ?",
            (entity["id"],),
        ).fetchone()[0]
        assert count == len([a for a in aliases if a])
    conn.close()


def test_jurisdictional_scope_normalized(tmp_db: Path, mini_graph: dict) -> None:
    graph_path = tmp_db.parent / "mini.json"
    graph_path.write_text(json.dumps(mini_graph))
    build_db(graph_path, tmp_db, force=True)

    conn = connect(tmp_db)
    for entity in mini_graph["entities"]:
        js = entity.get("jurisdiction_scope")
        if not js:
            continue
        row = conn.execute(
            "SELECT states_covered_json FROM jurisdictional_scope WHERE entity_id = ?",
            (entity["id"],),
        ).fetchone()
        assert row is not None
        assert json.loads(row[0]) == js.get("states_covered", [])
    conn.close()


def test_relationship_fk_integrity(tmp_db: Path, mini_graph: dict) -> None:
    graph_path = tmp_db.parent / "mini.json"
    graph_path.write_text(json.dumps(mini_graph))
    build_db(graph_path, tmp_db, force=True)

    errors = validate_db(tmp_db, graph_path)
    assert errors == []


def test_build_idempotent_skip(tmp_db: Path, mini_graph: dict) -> None:
    graph_path = tmp_db.parent / "mini.json"
    graph_path.write_text(json.dumps(mini_graph))
    first = build_db(graph_path, tmp_db, force=True)
    second = build_db(graph_path, tmp_db, force=False)
    assert first["skipped"] is False
    assert second["skipped"] is True


def test_schema_version_recorded(tmp_db: Path, mini_graph: dict) -> None:
    graph_path = tmp_db.parent / "mini.json"
    graph_path.write_text(json.dumps(mini_graph))
    build_db(graph_path, tmp_db, force=True)

    conn = connect(tmp_db)
    version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    conn.close()
    assert version == SCHEMA_VERSION


def test_validate_db_fails_on_empty_db(tmp_path: Path) -> None:
    empty_db = tmp_path / "empty.db"
    conn = sqlite3.connect(empty_db)
    conn.close()
    errors = validate_db(empty_db, tmp_path / "missing.json")
    assert any("not found" in e or "missing" in e for e in errors)
