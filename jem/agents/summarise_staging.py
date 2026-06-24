"""Build JSON summary for nightly digest prompt."""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Any

from agents.monitor import detect_anomalies


def confidence_histogram(conn: sqlite3.Connection) -> dict[str, int]:
    buckets = {"0.0-0.69": 0, "0.70-0.84": 0, "0.85-1.0": 0}
    rows = conn.execute("SELECT confidence FROM staging_records").fetchall()
    for row in rows:
        c = float(row["confidence"])
        if c < 0.7:
            buckets["0.0-0.69"] += 1
        elif c < 0.85:
            buckets["0.70-0.84"] += 1
        else:
            buckets["0.85-1.0"] += 1
    return buckets


def staging_counts(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM staging_records GROUP BY status"
    ).fetchall()
    return {row["status"]: row["cnt"] for row in rows}


def build_summary(conn: sqlite3.Connection, report_date: str | None = None) -> dict[str, Any]:
    report_date = report_date or date.today().isoformat()
    return {
        "date": report_date,
        "staging_counts": staging_counts(conn),
        "confidence_histogram": confidence_histogram(conn),
        "unresolved_conflicts": conn.execute(
            "SELECT COUNT(*) FROM data_conflicts WHERE resolved = 0"
        ).fetchone()[0],
        "anomalies": detect_anomalies(conn),
        "fetch_results": {"successes": 0, "failures": 0},
    }


def summary_json(conn: sqlite3.Connection, report_date: str | None = None) -> str:
    return json.dumps(build_summary(conn, report_date), indent=2)
