"""Fetcher agent tests — marker: test_agents."""

from __future__ import annotations

import json
import sqlite3

import pytest

from agents.dedup import find_duplicates, insert_staging, names_match, promote_to_vacancy_event
from agents.fetcher import extract_from_text, to_staging_records
from agents.prompts import load_prompt
from agents.verifier import verify_record
from build_db import apply_schema, connect


def test_load_extraction_prompt() -> None:
    text = load_prompt("extraction_v1.md")
    assert "verbatim_excerpt" in text
    assert "confidence" in text


def test_extract_from_text_mock() -> None:
    sample = [
        {
            "entity_name": "High Court of Delhi",
            "position": "Judge",
            "event_type": "appointment",
            "event_date": "2026-01-15",
            "reference_number": "S.O. 1234(E)",
            "verbatim_excerpt": "appointed as Judge of the High Court of Delhi",
            "confidence": 0.95,
        }
    ]

    def mock_create(system, user):
        return json.dumps(sample)

    items = extract_from_text("gazette text", create_message=mock_create)
    assert len(items) == 1
    assert items[0]["entity_name"] == "High Court of Delhi"


def test_to_staging_records_status() -> None:
    items = [
        {
            "entity_name": "Test Tribunal",
            "event_type": "vacancy",
            "verbatim_excerpt": "one vacancy",
            "confidence": 0.9,
        }
    ]
    records = to_staging_records(items, source_url="https://example.gov.in/")
    assert records[0]["status"] == "pending"

    low = to_staging_records(
        [{**items[0], "confidence": 0.5}],
    )
    assert low[0]["status"] == "needs_review"


def test_verify_record_mock() -> None:
    staging = {
        "entity_name": "AFT",
        "event_type": "vacancy",
        "verbatim_excerpt": "one member post vacant",
        "confidence": 0.88,
    }

    def mock_create(system, user):
        return json.dumps(
            {
                "verification_status": "confirmed",
                "confidence": 0.99,
                "flags": [],
                "notes": "",
            }
        )

    result = verify_record(staging, "one member post vacant", create_message=mock_create)
    assert result["verification_status"] == "confirmed"
    assert result["confidence"] == 0.88  # never upgraded


def test_names_match() -> None:
    assert names_match("High Court of Delhi", "high court of delhi")
    assert not names_match("Supreme Court", "Delhi High Court")


def test_dedup_and_promote(staging_db) -> None:
    conn = connect(staging_db)
    record = {
        "entity_name": "Armed Forces Tribunal",
        "position": "Member",
        "event_type": "vacancy",
        "event_date": "2026-03-01",
        "reference_number": "RS-2026-001",
        "verbatim_excerpt": "one vacancy at Principal Bench",
        "confidence": 0.92,
        "source_url": "https://rajyasabha.nic.in/",
        "status": "approved",
    }
    id1, conflicts1 = insert_staging(conn, record)
    assert conflicts1 == []

    id2, conflicts2 = insert_staging(conn, record)
    assert len(conflicts2) >= 1

    event_id = promote_to_vacancy_event(conn, id1, entity_id=None, actor="expert@test")
    conn.commit()

    audit = conn.execute(
        "SELECT action, table_name FROM audit_log WHERE record_id = ?",
        (str(event_id),),
    ).fetchone()
    assert audit["action"] == "promote"

    status = conn.execute(
        "SELECT status FROM staging_records WHERE id = ?",
        (id1,),
    ).fetchone()["status"]
    assert status == "promoted"
    conn.close()
