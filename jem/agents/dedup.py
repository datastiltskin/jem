"""Deduplication for staging records — never silent merge."""

from __future__ import annotations

import json
import sqlite3
from difflib import SequenceMatcher
from typing import Optional

NAME_MATCH_THRESHOLD = 0.85


def _normalize_name(name: str) -> str:
    return " ".join(name.lower().split())


def names_match(a: str, b: str) -> bool:
    return SequenceMatcher(None, _normalize_name(a), _normalize_name(b)).ratio() >= NAME_MATCH_THRESHOLD


def match_keys(record: dict) -> dict:
    return {
        "entity_name": record.get("entity_name", ""),
        "event_type": record.get("event_type", ""),
        "event_date": record.get("event_date"),
        "reference_number": record.get("reference_number"),
    }


def find_duplicates(conn: sqlite3.Connection, record: dict) -> list[sqlite3.Row]:
    """Find existing staging rows that may duplicate this record."""
    rows = conn.execute(
        """
        SELECT * FROM staging_records
        WHERE event_type = ? AND status IN ('needs_review', 'pending', 'approved')
        """,
        (record["event_type"],),
    ).fetchall()

    matches = []
    for row in rows:
        if not names_match(row["entity_name"], record["entity_name"]):
            continue
        if record.get("event_date") and row["event_date"] and row["event_date"] != record["event_date"]:
            continue
        if record.get("reference_number") and row["reference_number"]:
            if row["reference_number"] != record["reference_number"]:
                continue
        matches.append(row)
    return matches


def write_conflict(
    conn: sqlite3.Connection,
    staging_id_a: int,
    staging_id_b: Optional[int],
    conflict_type: str,
    description: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO data_conflicts (staging_id_a, staging_id_b, conflict_type, description)
        VALUES (?, ?, ?, ?)
        """,
        (staging_id_a, staging_id_b, conflict_type, description),
    )
    return cur.lastrowid


def insert_staging(conn: sqlite3.Connection, record: dict) -> tuple[int, list[int]]:
    """Insert staging record; return (new_id, conflict_ids)."""
    dupes = find_duplicates(conn, record)
    cur = conn.execute(
        """
        INSERT INTO staging_records (
            entity_name, position, event_type, event_date, reference_number,
            verbatim_excerpt, confidence, source_url, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["entity_name"],
            record.get("position"),
            record["event_type"],
            record.get("event_date"),
            record.get("reference_number"),
            record["verbatim_excerpt"],
            record["confidence"],
            record.get("source_url"),
            record.get("status", "needs_review"),
        ),
    )
    new_id = cur.lastrowid
    conflict_ids = []
    for dupe in dupes:
        cid = write_conflict(
            conn,
            new_id,
            dupe["id"],
            "duplicate_candidate",
            f"Possible duplicate of staging #{dupe['id']}: {dupe['entity_name']}",
        )
        conflict_ids.append(cid)
    return new_id, conflict_ids


def promote_to_vacancy_event(
    conn: sqlite3.Connection,
    staging_id: int,
    entity_id: Optional[str],
    actor: str = "system",
) -> int:
    """Promote approved staging record to vacancy_events with audit_log entry."""
    row = conn.execute("SELECT * FROM staging_records WHERE id = ?", (staging_id,)).fetchone()
    if row is None:
        raise ValueError(f"Staging record not found: {staging_id}")

    cur = conn.execute(
        """
        INSERT INTO vacancy_events (
            entity_id, entity_name_raw, position, event_type, event_date,
            reference_number, verbatim_excerpt, confidence, source_url,
            promoted_from_staging_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            entity_id,
            row["entity_name"],
            row["position"],
            row["event_type"],
            row["event_date"],
            row["reference_number"],
            row["verbatim_excerpt"],
            row["confidence"],
            row["source_url"],
            staging_id,
        ),
    )
    event_id = cur.lastrowid

    conn.execute(
        """
        INSERT INTO audit_log (action, table_name, record_id, actor, details_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            "promote",
            "vacancy_events",
            str(event_id),
            actor,
            json.dumps({"staging_id": staging_id, "entity_id": entity_id}),
        ),
    )
    conn.execute(
        "UPDATE staging_records SET status = ? WHERE id = ?",
        ("promoted", staging_id),
    )
    return event_id
