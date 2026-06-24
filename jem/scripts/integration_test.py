#!/usr/bin/env python3
"""End-to-end integration test for JEM pipeline components."""

from __future__ import annotations

import json
import sys
from pathlib import Path

JEM_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(JEM_ROOT))
sys.path.insert(0, str(JEM_ROOT / "scripts"))

from agents.dedup import insert_staging, promote_to_vacancy_event
from agents.fetcher import extract_from_text, to_staging_records
from agents.monitor import detect_anomalies
from agents.summarise_staging import build_summary
from agents.verifier import verify_record
from build_db import build_db
from api.deps import connect

FIXTURE_GRAPH = JEM_ROOT / "tests" / "fixtures" / "mini_graph.json"


def run_integration(db_path: Path) -> dict:
    graph = json.loads(FIXTURE_GRAPH.read_text())
    graph_file = db_path.parent / "mini.json"
    graph_file.write_text(json.dumps(graph))
    build_db(graph_file, db_path, force=True)

    conn = connect(db_path)

    sample_items = [
        {
            "entity_name": "Armed Forces Tribunal",
            "position": "Member",
            "event_type": "vacancy",
            "event_date": "2026-03-30",
            "reference_number": "RS-Q-2026",
            "verbatim_excerpt": "11 of 34 member posts vacant nationally",
            "confidence": 0.91,
        }
    ]
    records = to_staging_records(sample_items, source_url="https://rajyasabha.nic.in/")
    staging_id, conflicts = insert_staging(conn, records[0])

    verification = verify_record(
        records[0],
        "11 of 34 member posts vacant nationally per MoS Defence reply",
        create_message=lambda system, user: json.dumps(
            {"verification_status": "confirmed", "confidence": 0.91, "flags": [], "notes": ""}
        ),
    )
    assert verification["verification_status"] == "confirmed"

    conn.execute(
        "UPDATE staging_records SET status = 'needs_review' WHERE id = ?",
        (staging_id,),
    )
    conn.commit()

    summary = build_summary(conn)
    anomalies = detect_anomalies(conn)

    conn.close()
    return {
        "entities": graph["meta"]["entity_count"],
        "staging_id": staging_id,
        "conflicts": len(conflicts),
        "verification": verification["verification_status"],
        "anomalies": len(anomalies),
        "summary_keys": list(summary.keys()),
    }


def main() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "integration.db"
        result = run_integration(db_path)
        print(json.dumps(result, indent=2))
        if result["entities"] < 1:
            print("FAIL: no entities migrated", file=sys.stderr)
            return 1
        if result["verification"] != "confirmed":
            print("FAIL: verification", file=sys.stderr)
            return 1
    print("Integration test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
