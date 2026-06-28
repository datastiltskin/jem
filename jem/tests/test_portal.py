"""Expert portal tests — marker: test_portal."""

from __future__ import annotations

import sqlite3

from build_db import apply_schema, connect


def _seed_staging(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        """
        INSERT INTO staging_records (
            entity_name, position, event_type, event_date, reference_number,
            verbatim_excerpt, confidence, source_url, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "Armed Forces Tribunal",
            "Member",
            "vacancy",
            "2026-03-01",
            "RS-2026-001",
            "one vacancy at Principal Bench",
            0.72,
            "https://rajyasabha.nic.in/",
            "needs_review",
        ),
    )
    conn.commit()
    return cur.lastrowid


def test_portal_queue_empty(api_client) -> None:
    resp = api_client.get("/portal/api/queue")
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


def test_portal_review_page(api_client, fixture_db) -> None:
    conn = connect(fixture_db)
    _seed_staging(conn)
    conn.close()

    resp = api_client.get("/portal/")
    assert resp.status_code == 200
    assert "Armed Forces Tribunal" in resp.text
    assert "needs_review" not in resp.text or "awaiting review" in resp.text


def test_portal_approve_creates_audit(api_client, fixture_db) -> None:
    conn = connect(fixture_db)
    staging_id = _seed_staging(conn)
    conn.close()

    resp = api_client.post(
        f"/portal/staging/{staging_id}/approve",
        data={"actor": "expert@test", "entity_id": "aft"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    conn = connect(fixture_db)
    status = conn.execute(
        "SELECT status FROM staging_records WHERE id = ?",
        (staging_id,),
    ).fetchone()["status"]
    assert status == "promoted"

    audit = conn.execute(
        "SELECT action, actor FROM audit_log WHERE table_name = 'staging_records' AND record_id = ?",
        (str(staging_id),),
    ).fetchone()
    assert audit["action"] == "approve"
    assert audit["actor"] == "expert@test"

    events = conn.execute(
        "SELECT COUNT(*) FROM vacancy_events WHERE promoted_from_staging_id = ?",
        (staging_id,),
    ).fetchone()[0]
    assert events == 1
    conn.close()


def test_portal_reject_creates_audit(api_client, fixture_db) -> None:
    conn = connect(fixture_db)
    staging_id = _seed_staging(conn)
    conn.close()

    resp = api_client.post(
        f"/portal/staging/{staging_id}/reject",
        data={"actor": "expert@test", "reason": "bad excerpt"},
        follow_redirects=False,
    )
    assert resp.status_code == 303

    conn = connect(fixture_db)
    status = conn.execute(
        "SELECT status FROM staging_records WHERE id = ?",
        (staging_id,),
    ).fetchone()["status"]
    assert status == "rejected"

    audit = conn.execute(
        "SELECT action FROM audit_log WHERE action = 'reject' AND record_id = ?",
        (str(staging_id),),
    ).fetchone()
    assert audit is not None
    conn.close()
