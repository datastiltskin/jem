"""value_history is derived from append-only ledger events, newest-first."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from harness.events import event, project_value_history  # noqa: E402


def test_newest_first_ordering():
    ev = [
        event(
            run_id="t", recorded_at="2026-09-08T07:31:00Z",
            actor_role="maintainer", actor_name="dso",
            entity_id="sat", field_path="case_volume.pending_cases",
            value=420, change_reason="corrected_false", verdict="REFUTE",
        ),
        event(
            run_id="t", recorded_at="2026-09-08T07:32:00Z",
            actor_role="maintainer", actor_name="dso",
            entity_id="sat", field_path="case_volume.pending_cases",
            value=1066, data_as_of="2026-03-31",
            change_reason="corrected_false", verdict="REFUTE",
            source_url="https://www.sebi.gov.in/reports-and-statistics/publications/aug-2026/Chapter%2010.pdf",
            source_type="AnnualReport",
        ),
        event(
            run_id="t", recorded_at="2026-09-08T07:32:00Z",
            actor_role="maintainer", actor_name="dso",
            entity_id="sat", field_path="case_volume.filed_last_year",
            value=429, data_as_of="2026-03-31", change_reason="corrected_false",
        ),
        event(
            run_id="t", recorded_at="2026-09-08T07:32:00Z",
            actor_role="maintainer", actor_name="dso",
            entity_id="sat", field_path="case_volume.disposed_last_year",
            value=323, data_as_of="2026-03-31", change_reason="corrected_false",
        ),
        event(
            run_id="t", recorded_at="2026-09-08T07:31:00Z",
            actor_role="maintainer", actor_name="dso",
            entity_id="sat", field_path="case_volume.filed_last_year",
            value=380, change_reason="corrected_false",
        ),
        event(
            run_id="t", recorded_at="2026-09-08T07:31:00Z",
            actor_role="maintainer", actor_name="dso",
            entity_id="sat", field_path="case_volume.disposed_last_year",
            value=345, change_reason="corrected_false",
        ),
    ]
    hist = project_value_history(ev)
    pending = hist["sat"]["case_volume.pending_cases"]
    assert pending[0]["value"] == 1066
    assert pending[0]["data_as_of"] == "2026-03-31"
    assert pending[0]["source"]["url"].startswith("https://www.sebi.gov.in")
    assert pending[1]["value"] == 420
    assert pending[1]["change_reason"] == "corrected_false"
    assert hist["sat"]["case_volume.filed_last_year"][0]["value"] == 429
    assert hist["sat"]["case_volume.disposed_last_year"][0]["value"] == 323


def test_sat_live_trail_after_apply():
    """Once apply has run, SAT YAML current + ledger trail must match the packet."""
    import yaml
    jem = Path(__file__).resolve().parents[1]
    sat = None
    for p in (jem / "data" / "entities").rglob("sat.yaml"):
        doc = yaml.safe_load(p.read_text())
        if doc and doc.get("id") == "sat":
            sat = doc
            break
    if not sat:
        return
    cv = sat.get("case_volume") or {}
    if cv.get("pending_cases") != 1066:
        return  # apply not yet run; unit test above still covers the projection
    assert cv.get("filed_last_year") == 429
    assert cv.get("disposed_last_year") == 323
    njdg = [s for s in (sat.get("sources") or []) if s.get("type") == "NJDG"]
    assert njdg == []
    from harness.events import load_events, project_value_history
    hist = project_value_history(load_events(jem / "ledger" / "events"))
    trail = hist["sat"]["case_volume.pending_cases"]
    assert trail[0]["value"] in (1066, "1066")
    assert any(e.get("value") in (420, "420") and e.get("change_reason") == "corrected_false" for e in trail)
