#!/usr/bin/env python3
"""Emit ledger/derived/consensus_dashboard.json — derived, never hand-edited."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from harness.events import load_events, project_value_history  # noqa: E402
from harness.inter_model import AGRIYA_EMAIL_COMMENT  # noqa: E402

ROUND_BADGE = "PIPELINE EXERCISE — not blinded calibration"

PROMPT_LED = {
    "S_schema": "done",
    "C_tn_commercial_courts": "done",
    "K_tn_criminal_magistracy": "done",
    "N_classification_counting": "done",
    "report_publication": "done",
    "verify_trib_raters": "done",
    "inter_model_join": "done",
    "verify_trib_apply": "this-run",
    "value_history_projection": "this-run",
    "expert_packets": "this-run",
}


def _load_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    return list(csv.DictReader(path.open(encoding="utf-8")))


def _canon_result(gate: Dict[str, str]) -> str:
    outcome = gate.get("outcome") or ""
    auto = gate.get("auto_apply") or "N"
    if outcome == "agree_unsourced":
        return "conflicted" if False else "gap"
    if auto == "Y" and "SAT" in (gate.get("classification") or ""):
        return "reached canon"
    if auto == "Y" and outcome == "agree_refute_njdg":
        return "reached canon"
    if auto == "Y" and "corrected_false" in (gate.get("classification") or ""):
        return "contamination-dropped"
    if auto == "N" and outcome in ("disagree_period", "disagree_verdict", "disagree_value"):
        return "pending-expert"
    return "pending-expert" if auto == "N" else "reached canon"


def build_dashboard(jem: Path) -> Dict[str, Any]:
    consensus = _load_csv(jem / "ledger" / "suggested" / "verify_trib_01_consensus.csv")
    gate = _load_csv(jem / "ledger" / "suggested" / "decision_gate_20260908.csv")
    gate_by = {(r["entity_id"], r["field"]): r for r in gate}
    events = load_events(jem / "ledger" / "events")
    history = project_value_history(events)
    outcomes = Counter(r.get("outcome") for r in consensus)
    canon_counts = Counter()
    cards = []
    for row in consensus:
        g = gate_by.get((row["entity_id"], row["field"]), {})
        result = _canon_result(g) if g else "pending-expert"
        if result == "gap":
            result = "gap"
        canon_counts[result] += 1
        fp = {
            "pending_cases": "case_volume.pending_cases",
            "filed_last_year": "case_volume.filed_last_year",
            "disposed_last_year": "case_volume.disposed_last_year",
            "disposal_rate": "case_volume.disposal_rate",
            "avg_disposal_days": "case_volume.avg_disposal_days",
            "njdg_source_stamp": "sources.njdg",
        }.get(row["field"], row["field"])
        trail = (history.get(row["entity_id"]) or {}).get(fp) or []
        thin = (
            row.get("outcome", "").startswith("agree")
            and int(row.get("model_diversity") or 0) >= 1
            and not (row.get("prajna_value") and row.get("agriya_value")
                     and row["prajna_value"] == row["agriya_value"]
                     and row["outcome"] != "agree_unsourced")
        )
        # both agree + single primary: NJDG strip and SAT (one SEBI table)
        shared_bias = False
        if row["outcome"] in ("agree_refute_njdg", "agree_unsourced"):
            shared_bias = True
        if row["entity_id"] == "sat" and row["field"] in (
            "pending_cases", "filed_last_year", "disposed_last_year", "disposal_rate"
        ):
            shared_bias = True  # diversity 2, one primary
        cards.append({
            "entity_id": row["entity_id"],
            "field": row["field"],
            "field_path": fp,
            "prajna": {"verdict": row.get("prajna_verdict"), "value": row.get("prajna_value") or None},
            "agriya": {"verdict": row.get("agriya_verdict"), "value": row.get("agriya_value") or None},
            "reconcile_outcome": row.get("outcome"),
            "canon_result": result,
            "auto_apply": g.get("auto_apply"),
            "classification": g.get("classification"),
            "value_history": trail,
            "shared_bias_risk": "high" if shared_bias else "low",
            "contributor_signals": {
                "cell_vs_consensus": row.get("outcome"),
                "expert_status": result,
                "prajna_family_on_field": "deepseek",
                "agriya_family_on_field": "gpt",
            },
        })
    auto_applied = sum(1 for r in gate if r.get("auto_apply") == "Y")
    expert_pending = sum(1 for r in gate if r.get("auto_apply") == "N"
                         and r.get("outcome") != "agree_unsourced")
    gaps = outcomes.get("agree_unsourced", 0)
    dropped = canon_counts.get("contamination-dropped", 0)
    return {
        "generated_by": "scripts/derive.py :: consensus dashboard",
        "round_badge": ROUND_BADGE,
        "calibration_eligible": 0,
        "calibration_score": None,
        "agriya_caveats": AGRIYA_EMAIL_COMMENT,
        "prompt_led": PROMPT_LED,
        "funnel": {
            "total": len(consensus),
            "buckets": {
                "gap": outcomes.get("agree_unsourced", 0),
                "strip": outcomes.get("agree_refute_njdg", 0),
                "period": outcomes.get("disagree_period", 0),
                "verdict_split": outcomes.get("disagree_verdict", 0),
                "value_split": outcomes.get("disagree_value", 0),
            },
            "auto_applied_to_canon": auto_applied,
            "expert_pending": expert_pending,
            "dropped_as_contamination": dropped,
            "gaps_unchanged": gaps,
        },
        "canon_result_counts": dict(canon_counts),
        "cells": cards,
    }


def emit_dashboard(jem: Path) -> Path:
    payload = build_dashboard(jem)
    out = jem / "ledger" / "derived" / "consensus_dashboard.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return out
