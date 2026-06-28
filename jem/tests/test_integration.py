"""Integration tests — marker: test_integration."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from agents.dedup import insert_staging
from agents.monitor import detect_anomalies
from agents.summarise_staging import build_summary
from build_db import apply_schema, connect

JEM_ROOT = Path(__file__).resolve().parent.parent


def test_monitor_detects_backlog(staging_db) -> None:
    conn = connect(staging_db)
    for i in range(55):
        conn.execute(
            """
            INSERT INTO staging_records (
                entity_name, event_type, verbatim_excerpt, confidence, status
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (f"Entity {i}", "vacancy", f"excerpt {i}", 0.6, "needs_review"),
        )
    conn.commit()

    anomalies = detect_anomalies(conn)
    rules = {a["rule"] for a in anomalies}
    assert "staging_backlog" in rules
    conn.close()


def test_summarise_staging(staging_db) -> None:
    conn = connect(staging_db)
    conn.execute(
        """
        INSERT INTO staging_records (
            entity_name, event_type, verbatim_excerpt, confidence, status
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ("AFT", "vacancy", "one vacancy", 0.9, "needs_review"),
    )
    conn.commit()

    summary = build_summary(conn, report_date="2026-06-24")
    assert summary["date"] == "2026-06-24"
    assert "needs_review" in summary["staging_counts"]
    assert "anomalies" in summary
    conn.close()


def test_integration_script() -> None:
    result = subprocess.run(
        [sys.executable, str(JEM_ROOT / "scripts" / "integration_test.py")],
        capture_output=True,
        text=True,
        cwd=str(JEM_ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert "Integration test passed" in result.stdout


def test_digest_prompt_exists() -> None:
    path = JEM_ROOT / ".claude" / "prompts" / "digest_v1.md"
    assert path.exists()
    assert "Executive summary" in path.read_text()
