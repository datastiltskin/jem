"""Regression tests for the inter-model consensus rung."""

import csv
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from harness.inter_model import (  # noqa: E402
    AGREE_REFUTE_NJDG, AGREE_REFUTE_SAME_VALUE, AGREE_UNSOURCED,
    DISAGREE_PERIOD, DISAGREE_VERDICT, MISSING_RATER,
    RaterRow, classify, consensus_table, family_of, load_rater_csv,
    run, summarise,
)


def _row(rater, model, entity, field, verdict, value=None, flags="",
         current="420", eligible=True):
    return RaterRow(
        rater=rater, model=model, family=family_of(model),
        entity_id=entity, field=field, verdict=verdict,
        current_value=current, verified_value=value,
        anomaly_flags=flags, calibration_eligible=eligible,
    )


def test_two_model_families_count_as_diversity_two():
    cell = classify(
        _row("prajna", "deepseek", "sat", "pending_cases", "REFUTE", "1066"),
        _row("agriya", "codex", "sat", "pending_cases", "REFUTE", "1066"),
    )
    assert cell.model_diversity == 2
    assert set(cell.families) == {"deepseek", "gpt"}


def test_agree_refute_same_value_stays_off_canon():
    cell = classify(
        _row("prajna", "deepseek", "cestat", "pending_cases", "REFUTE", "72179"),
        _row("agriya", "codex", "cestat", "pending_cases", "REFUTE", "72179"),
    )
    assert cell.outcome == AGREE_REFUTE_SAME_VALUE
    assert cell.promotes_to_canon is False
    assert cell.expert_queue is True


def test_sat_period_mismatch_is_disagree_period():
    cell = classify(
        _row("prajna", "deepseek", "sat", "pending_cases", "REFUTE", "1066"),
        _row("agriya", "codex", "sat", "pending_cases", "UNSOURCED",
             flags="period_mismatch|anchor_verified_different_period"),
    )
    assert cell.outcome == DISAGREE_PERIOD
    assert cell.expert_queue is True
    assert cell.promotes_to_canon is False


def test_njdg_strip_agreement():
    cell = classify(
        _row("prajna", "deepseek", "sat", "njdg_source_stamp", "REFUTE", "absent"),
        _row("agriya", "codex", "sat", "njdg_source_stamp", "REFUTE", "absent"),
    )
    assert cell.outcome == AGREE_REFUTE_NJDG
    assert cell.expert_queue is False
    assert cell.promotes_to_canon is False


def test_njdg_strip_agreement_across_verdict_labels():
    """Prajna often marks the stamp UNSOURCED + FALSE; Agriya REFUTEs it."""
    prajna = _row("prajna", "deepseek", "sat", "njdg_source_stamp", "UNSOURCED")
    prajna.njdg_stamp_valid = "FALSE"
    prajna.notes = "recommend strip NJDG source"
    agriya = _row("agriya", "codex", "sat", "njdg_source_stamp", "REFUTE", "absent")
    cell = classify(prajna, agriya)
    assert cell.outcome == AGREE_REFUTE_NJDG


def test_both_unsourced_is_a_kept_gap():
    cell = classify(
        _row("prajna", "deepseek", "merc", "pending_cases", "UNSOURCED"),
        _row("agriya", "codex", "merc", "pending_cases", "UNSOURCED"),
    )
    assert cell.outcome == AGREE_UNSOURCED
    assert cell.expert_queue is False


def test_plain_verdict_disagreement():
    cell = classify(
        _row("prajna", "deepseek", "ngt", "pending_cases", "REFUTE", "5890"),
        _row("agriya", "codex", "ngt", "pending_cases", "UNSOURCED"),
    )
    assert cell.outcome == DISAGREE_VERDICT
    assert cell.expert_queue is True


def test_missing_rater_is_queued():
    cell = classify(
        _row("prajna", "deepseek", "x", "pending_cases", "UNSOURCED"),
        None,
    )
    assert cell.outcome == MISSING_RATER
    assert cell.expert_queue is True


def test_ineligible_arm_flags_the_cell(tmp_path):
    header = [
        "entity_id", "type", "field", "current_value", "verdict",
        "verified_value", "anomaly_flags", "notes",
    ]
    prajna = tmp_path / "p.csv"
    agriya = tmp_path / "a.csv"
    for path, verdict, value, flags in (
        (prajna, "REFUTE", "1066", ""),
        (agriya, "UNSOURCED", "", "period_mismatch"),
    ):
        with path.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=header)
            w.writeheader()
            w.writerow({
                "entity_id": "sat", "type": "CentralTribunal",
                "field": "pending_cases", "current_value": "420",
                "verdict": verdict, "verified_value": value,
                "anomaly_flags": flags, "notes": "",
            })
    (tmp_path / "a.meta.json").write_text(json.dumps({
        "model": "codex", "calibration_eligible": False,
    }))
    (tmp_path / "p.meta.json").write_text(json.dumps({
        "model": "deepseek", "calibration_eligible": True,
    }))

    rows_p = load_rater_csv(prajna, rater="prajna", model="deepseek",
                            calibration_eligible=True)
    rows_a = load_rater_csv(agriya, rater="agriya", model="codex",
                            calibration_eligible=False)
    cells = consensus_table(rows_p, rows_a)
    assert len(cells) == 1
    assert cells[0].outcome == DISAGREE_PERIOD
    assert cells[0].calibration_eligible is False
    assert summarise(cells)["promotes_to_canon"] == 0


def test_live_tables_join_140_cells():
    """The merged rater tables must be the same 140-claim roster."""
    jem = Path(__file__).resolve().parent.parent
    prajna = jem / "jem-verify-tribunals/out/deepseek__verify-trib-01__prajna__20260831_131656.csv"
    agriya = jem / "jem-verify-tribunals/out/codex__verify-trib-01__agriya__20260906_042259.csv"
    if not prajna.exists() or not agriya.exists():
        pytest.skip("rater CSVs not present")
    summary = run(jem_root=jem, prajna_csv=prajna, agriya_csv=agriya,
                  write_artifacts=False)
    assert summary["cells"] == 140
    assert summary["prajna_rows"] == 140
    assert summary["agriya_rows"] == 140
    assert summary["promotes_to_canon"] == 0
    assert summary["agriya_calibration_eligible"] is False
    assert "SAT" in summary["comment"] or "Astra" in summary["comment"]
