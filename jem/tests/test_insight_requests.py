"""Insight request telemetry API tests."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def _apply_v3(db_path: Path) -> None:
    schema = Path(__file__).resolve().parent.parent / "config" / "schema_v3.sql"
    conn = sqlite3.connect(db_path)
    conn.executescript(schema.read_text())
    conn.commit()
    conn.close()


def test_record_and_list_insight_requests(api_client, fixture_db: Path) -> None:
    _apply_v3(fixture_db)

    resp = api_client.post(
        "/api/v1/insights/requests",
        json={
            "insight_id": "avg_days_vacancy_unfilled",
            "title": "Longest average days a vacancy stayed unfilled",
            "query_text": "vacancy days",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["request_count"] == 1

    resp2 = api_client.post(
        "/api/v1/insights/requests",
        json={
            "insight_id": "avg_days_vacancy_unfilled",
            "title": "Longest average days a vacancy stayed unfilled",
        },
    )
    assert resp2.json()["request_count"] == 2

    listed = api_client.get("/api/v1/insights/requests", params={"limit": 5})
    assert listed.status_code == 200
    data = listed.json()
    assert data["total"] == 1
    assert data["items"][0]["insight_id"] == "avg_days_vacancy_unfilled"
    assert data["items"][0]["request_count"] == 2


def test_reject_invalid_insight_id(api_client, fixture_db: Path) -> None:
    _apply_v3(fixture_db)
    resp = api_client.post(
        "/api/v1/insights/requests",
        json={"insight_id": "BAD ID!", "title": "Some question"},
    )
    assert resp.status_code == 400
