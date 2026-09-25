#!/usr/bin/env python3
"""
Inter-model consensus — rung 2 of the four-rung ladder:

    intra-run (harness/reconcile.py) → inter-model raters (this file)
                                     → gold set → expert adjudication

Deterministic: no LLM. Joins two (or more) independent rater CSVs on
(entity_id, field), measures agreement × diversity, and writes an append-only
ledger. Nothing here edits canonical YAML or graph.json.

This sample is for pipeline exercise and human review. It does not promote.
See ledger/comments/agriya_20260906_handoff.md for why the Codex arm is
not calibration-eligible.

Agriya handoff (email to Divya and Prajna, 2026-09-06) — recorded as a
comment, not as a protocol waiver:

    Thanks for sending these details, and apologies for the delay! I have
    pushed a branch containing the Codex verifier output (I ran it again
    today after realising I messed something up in the prompt). Please note
    that I have not verified it in detail myself beyond a cursory look, but
    it covers all 44 entities and 140 claims, with the CSV, metadata,
    six-point summary, and primary-source archive included. I hope you find
    some of it useful, and please let me know whenever you would like me to
    run something again. You can use it to exercise the consensus pipeline.
    This run may not be eligible for blinded calibration IMO, because the
    setup file exposed Prajna's summary, and some required model/settings
    metadata was unavailable (some of those limitations are documented).
    I used the newly released GPT-6 Astra at Ultra effort for this pass.
    Branch: https://github.com/datastiltskin/jem/tree/verifier/codex/jem/jem-verify-tribunals
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from harness.reconcile import MIN_DIVERSITY_ABOVE_PARTIAL, model_diversity  # noqa: E402

CONFIRM, REFUTE, UNSOURCED, NA = "CONFIRM", "REFUTE", "UNSOURCED", "NA"
VERDICTS = {CONFIRM, REFUTE, UNSOURCED, NA}

AGREE_UNSOURCED = "agree_unsourced"
AGREE_REFUTE_SAME_VALUE = "agree_refute_same_value"
AGREE_REFUTE_NJDG = "agree_refute_njdg"
AGREE_CONFIRM = "agree_confirm"
AGREE_NA = "agree_na"
DISAGREE_PERIOD = "disagree_period"
DISAGREE_VERDICT = "disagree_verdict"
DISAGREE_VALUE = "disagree_value"
MISSING_RATER = "missing_rater"

# Family map: two runs of one family count once.
FAMILY_OF = {
    "deepseek": "deepseek",
    "deepseek-v4-flash": "deepseek",
    "codex": "gpt",
    "gpt": "gpt",
    "gpt-6": "gpt",
    "gpt-5.6-codex": "gpt",
}

NJDG_FIELD = "njdg_source_stamp"

DEFAULT_PRAJNA = (
    "jem-verify-tribunals/out/"
    "deepseek__verify-trib-01__prajna__20260831_131656.csv"
)
DEFAULT_AGRIYA = (
    "jem-verify-tribunals/out/"
    "codex__verify-trib-01__agriya__20260906_042259.csv"
)


def _jem_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@dataclass
class RaterRow:
    rater: str
    model: str
    family: str
    entity_id: str
    field: str
    verdict: str
    current_value: Optional[str] = None
    verified_value: Optional[str] = None
    verified_as_of: Optional[str] = None
    source_url: Optional[str] = None
    anomaly_flags: str = ""
    notes: str = ""
    njdg_stamp_valid: Optional[str] = None
    calibration_eligible: bool = True

    @property
    def key(self) -> Tuple[str, str]:
        return (self.entity_id, self.field)


@dataclass
class CellConsensus:
    entity_id: str
    field: str
    outcome: str
    prajna_verdict: Optional[str]
    agriya_verdict: Optional[str]
    prajna_value: Optional[str]
    agriya_value: Optional[str]
    stored_value: Optional[str]
    model_diversity: int
    families: List[str]
    calibration_eligible: bool
    promotes_to_canon: bool
    expert_queue: bool
    reason: str
    sources: List[str] = field(default_factory=list)


def family_of(model: str) -> str:
    key = (model or "").strip().lower()
    if key in FAMILY_OF:
        return FAMILY_OF[key]
    if "deepseek" in key:
        return "deepseek"
    if "gpt" in key or "codex" in key:
        return "gpt"
    return key or "unknown"


def load_meta(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _norm_verdict(raw: str) -> str:
    v = (raw or "").strip().upper()
    return v if v in VERDICTS else UNSOURCED


def _norm_value(raw: Any) -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip()
    if s == "":
        return None
    compact = s.replace(",", "").replace(" ", "")
    try:
        number = float(compact)
    except ValueError:
        return s.lower()
    if number.is_integer():
        return str(int(number))
    return f"{number:.4f}".rstrip("0").rstrip(".")


def _recommends_strip_njdg(row: Optional[RaterRow]) -> bool:
    if row is None:
        return False
    if row.verdict == REFUTE:
        return True
    if (row.njdg_stamp_valid or "").upper() == "FALSE":
        return True
    return "recommend strip" in (row.notes or "").lower()


def _has_period_flag(row: Optional[RaterRow]) -> bool:
    if row is None:
        return False
    blob = f"{row.anomaly_flags} {row.notes}".lower()
    return "period_mismatch" in blob or "different_period" in blob


def load_rater_csv(path: Path, *, rater: str, model: str,
                   calibration_eligible: bool = True) -> Dict[Tuple[str, str], RaterRow]:
    family = family_of(model)
    rows: Dict[Tuple[str, str], RaterRow] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for rec in reader:
            row = RaterRow(
                rater=rater,
                model=model,
                family=family,
                entity_id=(rec.get("entity_id") or "").strip(),
                field=(rec.get("field") or "").strip(),
                verdict=_norm_verdict(rec.get("verdict") or ""),
                current_value=_norm_value(rec.get("current_value")),
                verified_value=_norm_value(rec.get("verified_value")),
                verified_as_of=(rec.get("verified_as_of") or "").strip() or None,
                source_url=(rec.get("source_url") or "").strip() or None,
                anomaly_flags=rec.get("anomaly_flags") or "",
                notes=rec.get("notes") or "",
                njdg_stamp_valid=(rec.get("njdg_stamp_valid") or "").strip() or None,
                calibration_eligible=calibration_eligible,
            )
            if row.entity_id and row.field:
                rows[row.key] = row
    return rows


def classify(prajna: Optional[RaterRow], agriya: Optional[RaterRow]) -> CellConsensus:
    """Merge two rater cells. Pure function of the rows + eligibility flags."""
    entity_id = (prajna or agriya).entity_id  # type: ignore[union-attr]
    field_name = (prajna or agriya).field     # type: ignore[union-attr]
    stored = (prajna or agriya).current_value  # type: ignore[union-attr]
    families = [r.family for r in (prajna, agriya) if r is not None]
    diversity = model_diversity(families)
    eligible = all(r.calibration_eligible for r in (prajna, agriya) if r is not None)
    sources = [r.source_url for r in (prajna, agriya) if r and r.source_url]
    pv = prajna.verdict if prajna else None
    av = agriya.verdict if agriya else None
    pval = prajna.verified_value if prajna else None
    aval = agriya.verified_value if agriya else None

    def _cell(outcome: str, reason: str, expert: bool) -> CellConsensus:
        return CellConsensus(
            entity_id=entity_id,
            field=field_name,
            outcome=outcome,
            prajna_verdict=pv,
            agriya_verdict=av,
            prajna_value=pval,
            agriya_value=aval,
            stored_value=stored,
            model_diversity=diversity,
            families=sorted(set(families)),
            calibration_eligible=eligible,
            # Inter-model agreement is evidence for an expert, not a write.
            # This sample also carries Agriya's calibration_eligible=false.
            promotes_to_canon=False,
            expert_queue=expert,
            reason=reason,
            sources=sources,
        )

    if prajna is None or agriya is None:
        return _cell(MISSING_RATER, "one rater has no row for this cell", True)

    if field_name == NJDG_FIELD and _recommends_strip_njdg(prajna) and _recommends_strip_njdg(agriya):
        return _cell(
            AGREE_REFUTE_NJDG,
            "both raters recommend stripping the NJDG source stamp "
            "(REFUTE, njdg_stamp_valid=FALSE, or explicit strip note)",
            False,
        )

    if pv == av == UNSOURCED:
        return _cell(AGREE_UNSOURCED, "both raters found no matching-period primary", False)

    if pv == av == NA:
        return _cell(AGREE_NA, "both raters marked NA", False)

    if pv == av == CONFIRM:
        return _cell(AGREE_CONFIRM, "both raters confirmed the stored value", False)

    if pv == av == REFUTE:
        if pval is not None and pval == aval:
            return _cell(
                AGREE_REFUTE_SAME_VALUE,
                "both raters refute the stored value and propose the same replacement",
                True,  # period / apply decision still sits with the maintainer
            )
        return _cell(
            DISAGREE_VALUE,
            "both refute but proposed replacements differ",
            True,
        )

    # The SAT-shaped case: one rater treats a later-period primary as a
    # replacement; the other records the same primary as period_mismatch.
    if {pv, av} == {REFUTE, UNSOURCED} and (
        _has_period_flag(prajna) or _has_period_flag(agriya)
    ):
        return _cell(
            DISAGREE_PERIOD,
            "one rater replaces from a later-period primary; the other "
            "keeps the stored snapshot as UNSOURCED (period_mismatch)",
            True,
        )

    return _cell(
        DISAGREE_VERDICT,
        f"verdicts differ: prajna={pv} agriya={av}",
        True,
    )


def consensus_table(
    prajna_rows: Dict[Tuple[str, str], RaterRow],
    agriya_rows: Dict[Tuple[str, str], RaterRow],
) -> List[CellConsensus]:
    keys = sorted(set(prajna_rows) | set(agriya_rows))
    return [classify(prajna_rows.get(k), agriya_rows.get(k)) for k in keys]


def summarise(cells: Iterable[CellConsensus]) -> Dict[str, Any]:
    cells = list(cells)
    counts = Counter(c.outcome for c in cells)
    return {
        "cells": len(cells),
        "outcomes": dict(counts),
        "expert_queue": sum(1 for c in cells if c.expert_queue),
        "promotes_to_canon": sum(1 for c in cells if c.promotes_to_canon),
        "calibration_eligible_cells": sum(1 for c in cells if c.calibration_eligible),
        "max_diversity": max((c.model_diversity for c in cells), default=0),
        "min_diversity_above_partial": MIN_DIVERSITY_ABOVE_PARTIAL,
    }


def write_ledger(path: Path, cells: List[CellConsensus], *,
                 batch_id: str, comments: Optional[List[str]] = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with path.open("w", encoding="utf-8") as fh:
        if comments:
            # jsonl has no comment syntax; the first record is a comment envelope.
            fh.write(json.dumps({
                "record_type": "comment",
                "batch_id": batch_id,
                "comments": comments,
                "timestamp_utc": ts,
            }, ensure_ascii=False) + "\n")
        for cell in cells:
            rec = {
                "record_type": "cell",
                "batch_id": batch_id,
                "entity_id": cell.entity_id,
                "field": cell.field,
                "track": "inter-model",
                "outcome": cell.outcome,
                "prajna": {"verdict": cell.prajna_verdict, "verified_value": cell.prajna_value},
                "agriya": {"verdict": cell.agriya_verdict, "verified_value": cell.agriya_value},
                "stored_value": cell.stored_value,
                "reconcile": {
                    "label": cell.outcome,
                    "model_diversity": cell.model_diversity,
                    "families": cell.families,
                    "calibration_eligible": cell.calibration_eligible,
                    "promotes_to_canon": cell.promotes_to_canon,
                    "expert_queue": cell.expert_queue,
                    "reason": cell.reason,
                },
                "sources": cell.sources,
                "timestamp_utc": ts,
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return path


def write_csv(path: Path, cells: List[CellConsensus]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "entity_id", "field", "outcome", "expert_queue", "promotes_to_canon",
        "calibration_eligible", "model_diversity",
        "prajna_verdict", "prajna_value", "agriya_verdict", "agriya_value",
        "stored_value", "reason",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for cell in cells:
            writer.writerow({
                "entity_id": cell.entity_id,
                "field": cell.field,
                "outcome": cell.outcome,
                "expert_queue": cell.expert_queue,
                "promotes_to_canon": cell.promotes_to_canon,
                "calibration_eligible": cell.calibration_eligible,
                "model_diversity": cell.model_diversity,
                "prajna_verdict": cell.prajna_verdict,
                "prajna_value": cell.prajna_value,
                "agriya_verdict": cell.agriya_verdict,
                "agriya_value": cell.agriya_value,
                "stored_value": cell.stored_value,
                "reason": cell.reason,
            })
    return path


AGRIYA_EMAIL_COMMENT = (
    "Agriya email 2026-09-06 to Divya and Prajna: Codex verifier output on "
    "verifier/codex covers 44 entities / 140 claims (CSV, metadata, six-point "
    "summary, primary-source archive). Use it to exercise the consensus "
    "pipeline. Not eligible for blinded calibration: setup file exposed "
    "Prajna's summary; some model/settings metadata unavailable. Model: "
    "GPT-6 Astra at Ultra effort. Branch: "
    "https://github.com/datastiltskin/jem/tree/verifier/codex/jem/jem-verify-tribunals"
)


def run(jem_root: Optional[Path] = None,
        prajna_csv: Optional[Path] = None,
        agriya_csv: Optional[Path] = None,
        write_artifacts: bool = True) -> Dict[str, Any]:
    root = jem_root or _jem_root()
    prajna_path = Path(prajna_csv) if prajna_csv else root / DEFAULT_PRAJNA
    agriya_path = Path(agriya_csv) if agriya_csv else root / DEFAULT_AGRIYA
    prajna_meta = load_meta(prajna_path.with_suffix(".meta.json"))
    agriya_meta = load_meta(agriya_path.with_suffix(".meta.json"))

    prajna_rows = load_rater_csv(
        prajna_path,
        rater="prajna",
        model=prajna_meta.get("model") or "deepseek",
        calibration_eligible=prajna_meta.get("calibration_eligible", True),
    )
    agriya_rows = load_rater_csv(
        agriya_path,
        rater="agriya",
        model=agriya_meta.get("model") or "codex",
        calibration_eligible=bool(agriya_meta.get("calibration_eligible", False)),
    )
    cells = consensus_table(prajna_rows, agriya_rows)
    summary = summarise(cells)
    summary["prajna_rows"] = len(prajna_rows)
    summary["agriya_rows"] = len(agriya_rows)
    summary["prajna_csv"] = str(prajna_path)
    summary["agriya_csv"] = str(agriya_path)
    summary["agriya_calibration_eligible"] = agriya_meta.get("calibration_eligible")
    summary["comment"] = AGRIYA_EMAIL_COMMENT

    artifacts: Dict[str, str] = {}
    if write_artifacts:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        ledger = root / "ledger" / "runs" / f"inter-model__verify-trib-01__dso__{ts}.jsonl"
        table = root / "ledger" / "suggested" / "verify_trib_01_consensus.csv"
        write_ledger(
            ledger, cells,
            batch_id="verify-trib-01",
            comments=[AGRIYA_EMAIL_COMMENT],
        )
        write_csv(table, cells)
        artifacts["ledger"] = str(ledger)
        artifacts["csv"] = str(table)
    summary["artifacts"] = artifacts
    return summary


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(
        description="Inter-model consensus over Prajna + Agriya verify-trib CSVs")
    ap.add_argument("--jem-root", type=Path, default=None)
    ap.add_argument("--prajna", type=Path, default=None)
    ap.add_argument("--agriya", type=Path, default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="print the summary, do not write ledger artifacts")
    args = ap.parse_args()
    summary = run(
        jem_root=args.jem_root,
        prajna_csv=args.prajna,
        agriya_csv=args.agriya,
        write_artifacts=not args.dry_run,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
