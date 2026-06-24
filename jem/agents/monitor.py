"""Operational monitor — anomaly detection."""

from __future__ import annotations

import sqlite3
from typing import Any

STAGING_BACKLOG_WARNING = 50
STAGING_BACKLOG_CRITICAL = 200
LOW_CONFIDENCE_RATE_WARNING = 0.4
UNRESOLVED_CONFLICTS_WARNING = 5


def detect_anomalies(conn: sqlite3.Connection) -> list[dict]:
    """Run all anomaly rules; return list of {rule, severity, message}."""
    anomalies: list[dict] = []

    backlog = conn.execute(
        "SELECT COUNT(*) FROM staging_records WHERE status = 'needs_review'"
    ).fetchone()[0]
    if backlog >= STAGING_BACKLOG_CRITICAL:
        anomalies.append(
            {
                "rule": "staging_backlog",
                "severity": "critical",
                "message": f"Staging backlog critical: {backlog} records in needs_review",
            }
        )
    elif backlog >= STAGING_BACKLOG_WARNING:
        anomalies.append(
            {
                "rule": "staging_backlog",
                "severity": "warning",
                "message": f"Staging backlog elevated: {backlog} records in needs_review",
            }
        )

    total = conn.execute("SELECT COUNT(*) FROM staging_records").fetchone()[0]
    if total > 0:
        low_conf = conn.execute(
            "SELECT COUNT(*) FROM staging_records WHERE confidence < 0.85"
        ).fetchone()[0]
        rate = low_conf / total
        if rate >= LOW_CONFIDENCE_RATE_WARNING:
            anomalies.append(
                {
                    "rule": "confidence_distribution",
                    "severity": "warning",
                    "message": f"Low-confidence rate {rate:.0%} ({low_conf}/{total} records below 0.85)",
                }
            )

    conflicts = conn.execute(
        "SELECT COUNT(*) FROM data_conflicts WHERE resolved = 0"
    ).fetchone()[0]
    if conflicts >= UNRESOLVED_CONFLICTS_WARNING:
        anomalies.append(
            {
                "rule": "unresolved_conflicts",
                "severity": "warning",
                "message": f"{conflicts} unresolved data conflicts",
            }
        )

    try:
        version = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        if version is None:
            anomalies.append(
                {
                    "rule": "schema_drift",
                    "severity": "critical",
                    "message": "schema_version table empty — possible schema drift",
                }
            )
    except sqlite3.OperationalError:
        anomalies.append(
            {
                "rule": "schema_drift",
                "severity": "critical",
                "message": "schema_version table missing",
            }
        )

    return anomalies
