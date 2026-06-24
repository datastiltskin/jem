#!/usr/bin/env python3
"""Migrate graph.json into SQLite per schema_lock.md."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

SCHEMA_VERSION = 1

JEM_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB = JEM_ROOT / "data" / "jem.db"
DEFAULT_GRAPH = JEM_ROOT.parent / "graph.json"
SCHEMA_SQL = JEM_ROOT / "config" / "schema.sql"

ENTITY_SCALAR_KEYS = {
    "id",
    "name",
    "name_hindi",
    "abbreviation",
    "type",
    "cluster",
    "level_of_government",
    "legislature_status",
    "created_year",
    "enacted_year",
    "operational_year",
    "abolished_year",
    "operational_status",
    "constitutional_basis",
    "statutory_basis",
    "parent_hc",
    "data_quality",
    "data_quality_notes",
}

ENTITY_NORMALIZED_KEYS = {"aliases", "sources", "jurisdiction_scope", "unverified_fields"}

REL_SCALAR_KEYS = {
    "id",
    "source",
    "target",
    "relationship_type",
    "relationship_category",
    "is_binding",
    "is_constitutional",
    "year_established",
    "year_abolished",
    "data_quality",
    "contested_note",
    "notes",
    "statutory_basis",
}


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def apply_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL.read_text())
    conn.commit()


def drop_all(conn: sqlite3.Connection) -> None:
    tables = [
        "data_conflicts",
        "audit_log",
        "staging_records",
        "vacancy_events",
        "relationships",
        "statutory_basis_records",
        "jurisdictional_scope",
        "entity_sources",
        "entity_aliases",
        "entities",
        "schema_version",
    ]
    for table in tables:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()


def get_schema_version(conn: sqlite3.Connection) -> int | None:
    try:
        row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
        return row[0] if row and row[0] is not None else None
    except sqlite3.OperationalError:
        return None


def entity_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM entities").fetchone()[0]


def should_skip(conn: sqlite3.Connection, expected_entities: int, force: bool) -> bool:
    if force:
        return False
    version = get_schema_version(conn)
    if version != SCHEMA_VERSION:
        return False
    return entity_count(conn) == expected_entities


def _bool_to_int(value) -> int | None:
    if value is None:
        return None
    return 1 if value else 0


def _json_dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def migrate_entity(conn: sqlite3.Connection, entity: dict) -> None:
    entity_id = entity["id"]
    unverified = entity.get("unverified_fields")
    unverified_json = _json_dumps(unverified) if unverified is not None else None

    blob = {
        k: v
        for k, v in entity.items()
        if k not in ENTITY_SCALAR_KEYS
        and k not in ENTITY_NORMALIZED_KEYS
        and not (k == "position" and isinstance(v, dict))
    }
    # graph.json uses position for canvas coords; schema position is officeholder role (string)
    position_val = entity.get("position")
    position_col = position_val if isinstance(position_val, str) else None
    if isinstance(position_val, dict):
        blob["canvas_position"] = position_val

    conn.execute(
        """
        INSERT OR REPLACE INTO entities (
            id, name, name_hindi, abbreviation, type, cluster, level_of_government,
            legislature_status, created_year, enacted_year, operational_year, abolished_year,
            operational_status, constitutional_basis, statutory_basis, parent_hc,
            data_quality, data_quality_notes, unverified_fields_json, position, entity_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity_id,
            entity["name"],
            entity.get("name_hindi"),
            entity.get("abbreviation"),
            entity["type"],
            entity["cluster"],
            entity["level_of_government"],
            entity.get("legislature_status"),
            entity["created_year"],
            entity.get("enacted_year"),
            entity.get("operational_year"),
            entity.get("abolished_year"),
            entity["operational_status"],
            entity.get("constitutional_basis"),
            entity.get("statutory_basis"),
            entity.get("parent_hc"),
            entity["data_quality"],
            entity.get("data_quality_notes"),
            unverified_json,
            position_col,
            _json_dumps(blob),
        ),
    )

    conn.execute("DELETE FROM entity_aliases WHERE entity_id = ?", (entity_id,))
    for alias in entity.get("aliases") or []:
        if alias:
            conn.execute(
                "INSERT OR IGNORE INTO entity_aliases (entity_id, alias) VALUES (?, ?)",
                (entity_id, alias),
            )

    conn.execute("DELETE FROM entity_sources WHERE entity_id = ?", (entity_id,))
    for src in entity.get("sources") or []:
        if isinstance(src, dict):
            conn.execute(
                """
                INSERT INTO entity_sources (entity_id, source_type, url, title, accessed_date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    entity_id,
                    src.get("type") or src.get("source_type"),
                    src.get("url"),
                    src.get("title"),
                    src.get("accessed_date") or src.get("date"),
                ),
            )
        elif isinstance(src, str):
            conn.execute(
                "INSERT INTO entity_sources (entity_id, url) VALUES (?, ?)",
                (entity_id, src),
            )

    js = entity.get("jurisdiction_scope")
    if js and isinstance(js, dict):
        conn.execute(
            """
            INSERT OR REPLACE INTO jurisdictional_scope (
                entity_id, is_all_india, is_shared_multi, shared_appointer,
                states_covered_json, uts_covered_json, jurisdiction_types_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_id,
                _bool_to_int(js.get("is_all_india")) or 0,
                _bool_to_int(js.get("is_shared_multi")) or 0,
                js.get("shared_appointer"),
                _json_dumps(js.get("states_covered") or []),
                _json_dumps(js.get("uts_covered") or []),
                _json_dumps(js.get("jurisdiction_types") or []),
            ),
        )
    else:
        conn.execute("DELETE FROM jurisdictional_scope WHERE entity_id = ?", (entity_id,))

    conn.execute("DELETE FROM statutory_basis_records WHERE entity_id = ?", (entity_id,))
    for basis_type, field in (
        ("constitutional", entity.get("constitutional_basis")),
        ("statutory", entity.get("statutory_basis")),
    ):
        if field:
            conn.execute(
                """
                INSERT INTO statutory_basis_records (entity_id, basis_type, citation)
                VALUES (?, ?, ?)
                """,
                (entity_id, basis_type, field),
            )


def migrate_relationship(conn: sqlite3.Connection, rel: dict, entity_ids: set[str]) -> list[str]:
    warnings: list[str] = []
    if rel["source"] not in entity_ids:
        warnings.append(f"relationship {rel['id']}: missing source {rel['source']}")
        return warnings
    if rel["target"] not in entity_ids:
        warnings.append(f"relationship {rel['id']}: missing target {rel['target']}")
        return warnings

    blob = {k: v for k, v in rel.items() if k not in REL_SCALAR_KEYS}

    conn.execute(
        """
        INSERT OR REPLACE INTO relationships (
            id, source, target, relationship_type, relationship_category,
            is_binding, is_constitutional, year_established, year_abolished,
            data_quality, contested_note, notes, statutory_basis, relationship_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            rel["id"],
            rel["source"],
            rel["target"],
            rel["relationship_type"],
            rel["relationship_category"],
            _bool_to_int(rel.get("is_binding")),
            _bool_to_int(rel.get("is_constitutional")),
            rel.get("year_established"),
            rel.get("year_abolished"),
            rel.get("data_quality"),
            rel.get("contested_note"),
            rel.get("notes"),
            rel.get("statutory_basis"),
            _json_dumps(blob),
        ),
    )
    return warnings


def migrate_graph(conn: sqlite3.Connection, graph: dict) -> list[str]:
    warnings: list[str] = []
    entities = graph.get("entities") or []
    relationships = graph.get("relationships") or []
    entity_ids = {e["id"] for e in entities}

    for entity in entities:
        migrate_entity(conn, entity)

    for rel in relationships:
        warnings.extend(migrate_relationship(conn, rel, entity_ids))

    conn.execute(
        "INSERT OR REPLACE INTO schema_version (version, description) VALUES (?, ?)",
        (SCHEMA_VERSION, "graph.json migration"),
    )
    conn.commit()
    return warnings


def build_db(graph_path: Path, db_path: Path, force: bool = False) -> dict:
    graph = json.loads(graph_path.read_text())
    expected = graph.get("meta", {}).get("entity_count", len(graph.get("entities", [])))

    if db_path.exists():
        conn = connect(db_path)
        if should_skip(conn, expected, force):
            count = entity_count(conn)
            conn.close()
            return {"skipped": True, "entities": count, "db": str(db_path)}
        conn.close()

    conn = connect(db_path)
    if force or get_schema_version(conn) is None:
        drop_all(conn)
    apply_schema(conn)

    if not force and entity_count(conn) == expected and get_schema_version(conn) == SCHEMA_VERSION:
        conn.close()
        return {"skipped": True, "entities": expected, "db": str(db_path)}

    if not force and entity_count(conn) != expected:
        for table in (
            "data_conflicts",
            "entity_aliases",
            "entity_sources",
            "jurisdictional_scope",
            "statutory_basis_records",
            "relationships",
            "entities",
        ):
            conn.execute(f"DELETE FROM {table}")
        conn.commit()

    warnings = migrate_graph(conn, graph)
    count = entity_count(conn)
    conn.close()

    return {
        "skipped": False,
        "entities": count,
        "relationships": len(graph.get("relationships", [])),
        "warnings": warnings,
        "db": str(db_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Migrate graph.json to SQLite")
    parser.add_argument("--graph", type=Path, default=DEFAULT_GRAPH)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--force", action="store_true", help="Drop and rebuild database")
    args = parser.parse_args()

    if not args.graph.exists():
        print(f"ERROR: graph not found: {args.graph}", file=sys.stderr)
        return 1
    if not SCHEMA_SQL.exists():
        print(f"ERROR: schema not found: {SCHEMA_SQL}", file=sys.stderr)
        return 1

    result = build_db(args.graph, args.db, force=args.force)
    if result.get("skipped"):
        print(f"Skipped — DB up to date ({result['entities']} entities): {result['db']}")
    else:
        print(f"Built {result['entities']} entities → {result['db']}")
        for w in result.get("warnings") or []:
            print(f"WARN: {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
