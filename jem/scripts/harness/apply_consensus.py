#!/usr/bin/env python3
"""Apply verify-trib-01 consensus to the ledger, then to canon — gated.

Prints the decision-gate table BEFORE any YAML write. Auto-applies only
unambiguous rows. Ambiguous rows go to ledger/suggested/, not canon.

Usage (from jem/):
    python3 scripts/harness/apply_consensus.py --gate-only
    python3 scripts/harness/apply_consensus.py --apply
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import yaml

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from harness.events import append_events, event  # noqa: E402
from harness.inter_model import AGRIYA_EMAIL_COMMENT  # noqa: E402

SEBI_AR = (
    "https://www.sebi.gov.in/reports-and-statistics/publications/"
    "aug-2026/Chapter%2010.pdf"
)
SAT_PROMOTE = {
    "pending_cases": ("1066", "2026-03-31"),
    "filed_last_year": ("429", "2026-03-31"),
    "disposed_last_year": ("323", "2026-03-31"),
    "disposal_rate": ("0.7529", "2026-03-31"),
}
LADDER_42 = {42, 420, 4200, 42000, 420000}
VOLUME_FIELDS = {
    "pending_cases", "filed_last_year", "disposed_last_year",
    "disposal_rate", "avg_disposal_days",
}
RUN_ID = "verify-trib-01-apply-20260908"
PROMPT_VERSION = "apply-consensus-verify-trib-01-v1"
FIELD_PATH = {
    "pending_cases": "case_volume.pending_cases",
    "filed_last_year": "case_volume.filed_last_year",
    "disposed_last_year": "case_volume.disposed_last_year",
    "disposal_rate": "case_volume.disposal_rate",
    "avg_disposal_days": "case_volume.avg_disposal_days",
    "njdg_source_stamp": "sources.njdg",
}


def jem_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def is_homepage(url: Optional[str]) -> bool:
    if not url or not str(url).strip():
        return True
    path = urlparse(str(url).strip()).path
    return path in ("", "/")


def _as_number(raw: Any) -> Optional[float]:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return float(str(raw).replace(",", "").strip())
    except ValueError:
        return None


def stored_contaminated(field: str, stored: Any, source_url: Optional[str]) -> bool:
    """Homepage / 42-ladder / 365-day / round-thousand tells. NGT dashboard is not this."""
    if field == "njdg_source_stamp":
        return False
    num = _as_number(stored)
    if num is None:
        return False
    if field == "avg_disposal_days" and num == 365:
        return True
    if num in LADDER_42 or int(num) in LADDER_42:
        return True
    if field in VOLUME_FIELDS and is_homepage(source_url):
        return True
    if is_homepage(source_url) and num >= 1000 and num == int(num) and int(num) % 1000 == 0:
        return True
    return False


def index_entities(data_dir: Path) -> Dict[str, Path]:
    idx: Dict[str, Path] = {}
    for path in data_dir.joinpath("entities").rglob("*.yaml"):
        if "schema" in path.name:
            continue
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if isinstance(doc, dict) and doc.get("id"):
            idx[doc["id"]] = path
    return idx


def load_yaml(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@dataclass
class GateRow:
    entity_id: str
    entity_name: str
    field: str
    stored_value: Optional[str]
    stored_provenance: str
    rater_found_value: Optional[str]
    classification: str
    auto_apply: str
    outcome: str
    reason: str
    yaml_path: str = ""
    source_url: Optional[str] = None
    entity_type: str = ""
    abbreviation: str = ""


def rater_found(row: Dict[str, str]) -> Optional[str]:
    if row.get("entity_id") == "sat" and row.get("field") in SAT_PROMOTE:
        return SAT_PROMOTE[row["field"]][0]
    p, a = row.get("prajna_value") or "", row.get("agriya_value") or ""
    if p and a and p == a:
        return p
    if p and not a:
        return p
    if a and not p:
        return a
    if p and a and p != a:
        return f"SPLIT p={p} a={a}"
    return None


def classify_gate(row: Dict[str, str], entity: Dict[str, Any], path: Path) -> GateRow:
    cv = entity.get("case_volume") or {}
    field = row["field"]
    stored = row.get("stored_value") or ""
    outcome = row["outcome"]
    url = cv.get("source_url")
    contaminated = stored_contaminated(field, stored, url)
    provenance = "contaminated (homepage / 42-ladder / round-thousand)" if contaminated else (
        "sourced (document URL or specific as_of)" if not is_homepage(url) else "unsourced / homepage"
    )
    if field == "njdg_source_stamp":
        provenance = "NJDG stamp on a non-eCourts body"

    found = rater_found(row)
    auto = "N"
    classification = outcome

    if outcome == "agree_refute_njdg":
        classification = "source_corrected — strip NJDG"
        auto = "Y"
    elif outcome == "agree_unsourced":
        classification = "gap — both UNSOURCED; no canon change"
        auto = "N"
    elif outcome in ("disagree_verdict", "disagree_value"):
        classification = "expert-pending — rater split; no auto-write"
        auto = "N"
    elif outcome == "disagree_period":
        if row["entity_id"] == "sat" and field in SAT_PROMOTE:
            classification = (
                "SAT FY25-26 — both raters re-derived SEBI AR; "
                "stored is fabricated → corrected_false + promote"
            )
            auto = "Y"
            provenance = "contaminated (42-ladder + homepage)"
        elif contaminated:
            classification = (
                "stored contaminated → corrected_false (null); "
                "replacement is single-rater → suggested/"
            )
            auto = "Y"
        else:
            classification = (
                "stored looks primary-sourced for its period — keep current; "
                "newer figure → suggested/ (superseded_newer_period if expert agrees)"
            )
            auto = "N"
            provenance = "sourced (document URL; keep for its period)"

    return GateRow(
        entity_id=row["entity_id"],
        entity_name=entity.get("name") or row["entity_id"],
        field=field,
        stored_value=stored or None,
        stored_provenance=provenance,
        rater_found_value=found,
        classification=classification,
        auto_apply=auto,
        outcome=outcome,
        reason=row.get("reason") or "",
        yaml_path=str(path),
        source_url=url,
        entity_type=entity.get("type") or "",
        abbreviation=entity.get("abbreviation") or "",
    )


def build_gate(jem: Path) -> List[GateRow]:
    consensus = jem / "ledger" / "suggested" / "verify_trib_01_consensus.csv"
    rows = list(csv.DictReader(consensus.open(encoding="utf-8")))
    idx = index_entities(jem / "data")
    gates: List[GateRow] = []
    for row in rows:
        path = idx[row["entity_id"]]
        gates.append(classify_gate(row, load_yaml(path), path))
    return gates


def print_gate(gates: List[GateRow]) -> None:
    print("\n=== DECISION-GATE (before any canon write) ===")
    print(
        f"{'entity':18} {'field':20} {'stored':12} {'prov':14} "
        f"{'found':16} {'apply':5} classification"
    )
    print("-" * 140)
    for g in gates:
        prov = "contaminated" if "contaminated" in g.stored_provenance else (
            "NJDG" if "NJDG" in g.stored_provenance else (
                "sourced" if g.stored_provenance.startswith("sourced") else "unsourced"
            )
        )
        print(
            f"{g.entity_id:18} {g.field:20} {str(g.stored_value or ''):12} "
            f"{prov:14} {str(g.rater_found_value or ''):16} {g.auto_apply:5} {g.classification}"
        )
    y = sum(1 for g in gates if g.auto_apply == "Y")
    n = sum(1 for g in gates if g.auto_apply == "N")
    print(f"\n{len(gates)} cells  auto-apply Y={y}  hold N={n}")
    print("Agriya caveat:", AGRIYA_EMAIL_COMMENT[:160], "...")


def write_gate_csv(path: Path, gates: List[GateRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "entity_id", "entity_name", "field", "stored_value", "stored_provenance",
        "rater_found_value", "classification", "auto_apply", "outcome", "reason",
        "yaml_path", "source_url", "entity_type", "abbreviation",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for g in gates:
            w.writerow(asdict(g))


# ── YAML surgery (preserve structural_gap / block scalars) ────────────────────

_NJDG_ITEM = re.compile(
    r"(?m)^- label:.*\n(?:  .*\n)*?  type: NJDG\n(?:  .*\n)*?(?=^[-a-zA-Z]|\Z)",
)


def strip_njdg_sources(text: str) -> Tuple[str, int]:
    new, n = _NJDG_ITEM.subn("", text)
    # collapse leftover blank lines in sources
    new = re.sub(r"\n{3,}", "\n\n", new)
    return new, n


def _set_key_in_block(text: str, block: str, key: str, value: Any) -> str:
    pat = re.compile(
        rf"(?m)^({re.escape(block)}:\n(?:  .*\n)*?  {re.escape(key)}: )(.*)$"
    )
    rendered = "null" if value is None else str(value)
    if value is None:
        rendered = "null"
    elif isinstance(value, str):
        if re.match(r"^\d{4}-\d{2}-\d{2}", value) or "://" in value or " " in value:
            rendered = json.dumps(value)
        else:
            rendered = value
    else:
        rendered = str(value)
    if pat.search(text):
        return pat.sub(rf"\g<1>{rendered}", text, count=1)
    # insert the key at the start of the block
    insert = f"{block}:\n  {key}: {rendered}\n"
    return re.sub(rf"(?m)^{re.escape(block)}:\n", insert, text, count=1)


def set_case_volume(text: str, updates: Dict[str, Any]) -> str:
    if "case_volume:" not in text:
        block = "case_volume:\n" + "".join(
            f"  {k}: {('null' if v is None else v)}\n" for k, v in updates.items()
        )
        return text.rstrip() + "\n" + block
    out = text
    for key, value in updates.items():
        out = _set_key_in_block(out, "case_volume", key, value)
    return out


def append_unverified(text: str, field_path: str, note: str) -> str:
    item = f"- field: {field_path}\n  note: {json.dumps(note)}\n"
    if re.search(r"(?m)^unverified_fields:\s*$", text):
        return re.sub(
            r"(?m)^unverified_fields:\s*\n",
            f"unverified_fields:\n{item}",
            text,
            count=1,
        )
    if re.search(r"(?m)^unverified_fields:", text):
        return re.sub(
            r"(?m)^unverified_fields:\n",
            f"unverified_fields:\n{item}",
            text,
            count=1,
        )
    # insert before case_volume if present, else at EOF
    if re.search(r"(?m)^case_volume:", text):
        return re.sub(
            r"(?m)^case_volume:",
            f"unverified_fields:\n{item}case_volume:",
            text,
            count=1,
        )
    return text.rstrip() + f"\nunverified_fields:\n{item}"


def append_dq_note(text: str, line: str) -> str:
    """Append a short note without breaking quoted or folded scalars."""
    if line in text:
        return text
    m = re.search(r"(?m)^data_quality_notes:\s*(.*)$", text)
    if not m:
        return re.sub(
            r"(?m)^data_quality:\s*.*$",
            lambda mm: mm.group(0) + f"\ndata_quality_notes: {json.dumps(line)}",
            text,
            count=1,
        )
    rest = m.group(1).strip()
    # Folded / literal / quoted / already-complex: skip (unverified_fields carries the note).
    if rest.startswith((">", "|", '"', "'", "{")):
        return text
    merged = (rest.strip(" '\"") + " | " + line).strip()
    return text[: m.start()] + f"data_quality_notes: {json.dumps(merged)}" + text[m.end() :]


def coerce_partial(text: str) -> str:
    return re.sub(
        r"(?m)^data_quality:\s*(verified|complete)\s*$",
        "data_quality: partial",
        text,
        count=1,
    )


def dump_yaml_file(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


# ── apply ────────────────────────────────────────────────────────────────────

def _num_or_str(raw: Optional[str]) -> Any:
    if raw is None or raw == "":
        return None
    n = _as_number(raw)
    if n is None:
        return raw
    if n == int(n) and abs(n) >= 1:
        return int(n)
    return n


def apply(jem: Path, gates: List[GateRow], consensus_rows: List[Dict[str, str]]) -> Dict[str, Any]:
    events_path = jem / "ledger" / "events" / f"{RUN_ID}.jsonl"
    pending_path = jem / "ledger" / "suggested" / "verify_trib_01_expert_pending.csv"
    changed: Dict[str, List[str]] = {}
    events: List[Dict[str, Any]] = []
    pending: List[Dict[str, str]] = []

    # Capture event for every consensus row (the 140).
    t0 = "2026-09-08T07:30:00Z"
    for row, gate in zip(consensus_rows, gates):
        events.append(event(
            run_id=RUN_ID,
            recorded_at=t0,
            actor_role="maintainer",
            actor_name="dso",
            model=None,
            prompt_version=PROMPT_VERSION,
            entity_id=row["entity_id"],
            field_path=FIELD_PATH[row["field"]],
            data_as_of=None,
            value=row.get("stored_value") or None,
            verdict=(
                "UNSOURCED" if row["outcome"] == "agree_unsourced"
                else "REFUTE" if "refute" in row["outcome"] or row["outcome"].startswith("disagree")
                else None
            ),
            change_reason="initial",
            notes=(
                f"consensus={row['outcome']} prajna={row['prajna_verdict']}/"
                f"{row.get('prajna_value') or ''} agriya={row['agriya_verdict']}/"
                f"{row.get('agriya_value') or ''} auto_apply={gate.auto_apply}"
            ),
            extra={"consensus_outcome": row["outcome"], "auto_apply": gate.auto_apply},
        ))

    t1 = "2026-09-08T07:31:00Z"
    t2 = "2026-09-08T07:32:00Z"

    # Group YAML mutations per file
    by_entity: Dict[str, List[Tuple[GateRow, Dict[str, str]]]] = {}
    for row, gate in zip(consensus_rows, gates):
        by_entity.setdefault(gate.entity_id, []).append((gate, row))

    for eid, items in by_entity.items():
        path = Path(items[0][0].yaml_path)
        doc = load_yaml(path)
        file_changes: List[str] = []

        def _note(line: str) -> None:
            existing = doc.get("data_quality_notes") or ""
            if line in str(existing):
                return
            doc["data_quality_notes"] = (str(existing).rstrip() + " | " + line).strip(" |")

        def _unverified(field_path: str, note: str) -> None:
            uv = list(doc.get("unverified_fields") or [])
            if any(isinstance(x, dict) and x.get("field") == field_path for x in uv):
                return
            uv.append({"field": field_path, "note": note})
            doc["unverified_fields"] = uv

        def _partial() -> None:
            if doc.get("data_quality") in ("verified", "complete"):
                doc["data_quality"] = "partial"

        for gate, row in items:
            field = row["field"]
            fp = FIELD_PATH[field]

            if gate.outcome == "agree_unsourced":
                continue

            if gate.outcome in ("disagree_verdict", "disagree_value"):
                pending.append({
                    "entity_id": eid,
                    "field": field,
                    "stored_value": row.get("stored_value") or "",
                    "prajna": f"{row['prajna_verdict']}:{row.get('prajna_value') or ''}",
                    "agriya": f"{row['agriya_verdict']}:{row.get('agriya_value') or ''}",
                    "status": "expert-pending",
                    "reason": gate.classification,
                })
                continue

            if gate.outcome == "agree_refute_njdg":
                before = len(doc.get("sources") or [])
                doc["sources"] = [
                    s for s in (doc.get("sources") or [])
                    if not (isinstance(s, dict) and s.get("type") == "NJDG")
                ]
                n = before - len(doc.get("sources") or [])
                if n:
                    file_changes.append(f"strip NJDG x{n}")
                events.append(event(
                    run_id=RUN_ID, recorded_at=t1,
                    actor_role="maintainer", actor_name="dso",
                    prompt_version=PROMPT_VERSION, entity_id=eid, field_path=fp,
                    value="absent", verdict="REFUTE",
                    change_reason="source_corrected",
                    source_type="GoIWebsite",
                    source_url="https://www.nic.gov.in/project/national-judicial-data-grid/",
                    notes="NJDG source stamp stripped — body is not eCourts.",
                ))
                _partial()
                _note("verify-trib-01: NJDG source stamp stripped (non-eCourts body).")
                cv = doc.get("case_volume") or {}
                cv_url = cv.get("source_url")
                cv_type = str(cv.get("source_type") or "")
                if cv and (is_homepage(cv_url) or cv_type.startswith("NJDG")) and eid != "sat":
                    hold_fields = {
                        g.field for g, _r in items
                        if g.auto_apply == "N" and g.field in VOLUME_FIELDS
                    }
                    for vf in ("pending_cases", "filed_last_year", "disposed_last_year",
                               "disposal_rate", "avg_disposal_days"):
                        if vf in hold_fields or cv.get(vf) is None:
                            continue
                        cv[vf] = None
                        _unverified(
                            f"case_volume.{vf}",
                            "Figure withdrawn: no surviving primary after NJDG strip.",
                        )
                        events.append(event(
                            run_id=RUN_ID, recorded_at=t1,
                            actor_role="maintainer", actor_name="dso",
                            prompt_version=PROMPT_VERSION, entity_id=eid,
                            field_path=f"case_volume.{vf}",
                            value=None, verdict="UNSOURCED",
                            change_reason="corrected_false",
                            notes="Nulled after NJDG strip — no surviving primary.",
                        ))
                        file_changes.append(f"null case_volume.{vf}")
                    doc["case_volume"] = cv
                continue

            if gate.outcome == "disagree_period" and gate.auto_apply == "Y" and eid == "sat" and field in SAT_PROMOTE:
                new_val, as_of = SAT_PROMOTE[field]
                events.append(event(
                    run_id=RUN_ID, recorded_at=t1,
                    actor_role="maintainer", actor_name="dso",
                    prompt_version=PROMPT_VERSION, entity_id="sat", field_path=fp,
                    data_as_of="2024-12-01", value=_num_or_str(row.get("stored_value")),
                    verdict="REFUTE", change_reason="corrected_false",
                    source_type="AnnualReport", source_url="https://satweb.sat.gov.in/",
                    notes="Fabricated / 42-ladder homepage snapshot withdrawn.",
                ))
                events.append(event(
                    run_id=RUN_ID, recorded_at=t2,
                    actor_role="maintainer", actor_name="dso",
                    prompt_version=PROMPT_VERSION, entity_id="sat", field_path=fp,
                    data_as_of=as_of, value=_num_or_str(new_val),
                    verdict="REFUTE", change_reason="corrected_false",
                    source_type="AnnualReport", source_url=SEBI_AR,
                    accessed_date="2026-09-08",
                    notes="Promoted: both raters re-derived SEBI AR 2025-26 Table 10.35. Pipeline exercise, not blinded calibration.",
                ))
                cv = doc.setdefault("case_volume", {})
                cv[field] = _num_or_str(new_val)
                cv["data_as_of"] = as_of
                cv["source_type"] = "AnnualReport"
                cv["source_url"] = SEBI_AR
                file_changes.append(f"promote sat {field}={new_val}")
                continue

            if gate.outcome == "disagree_period" and gate.auto_apply == "Y":
                events.append(event(
                    run_id=RUN_ID, recorded_at=t1,
                    actor_role="maintainer", actor_name="dso",
                    prompt_version=PROMPT_VERSION, entity_id=eid, field_path=fp,
                    data_as_of="2024-12-01", value=_num_or_str(row.get("stored_value")),
                    verdict="REFUTE", change_reason="corrected_false",
                    source_url=gate.source_url, source_type="AnnualReport",
                    notes="Stored figure withdrawn as contamination (homepage / 42-ladder / round-thousand).",
                ))
                cv = doc.setdefault("case_volume", {})
                cv[field] = None
                _unverified(
                    fp,
                    "Stored figure withdrawn as unsourced contamination; replacement is single-rater and sits in suggested/.",
                )
                _partial()
                _note(f"verify-trib-01: {field} nulled (contamination); replacement held for expert review.")
                file_changes.append(f"null {field}")
                pending.append({
                    "entity_id": eid,
                    "field": field,
                    "stored_value": row.get("stored_value") or "",
                    "prajna": f"{row['prajna_verdict']}:{row.get('prajna_value') or ''}",
                    "agriya": f"{row['agriya_verdict']}:{row.get('agriya_value') or ''}",
                    "status": "expert-pending",
                    "reason": "single-rater replacement after contamination null",
                })
                continue

            if gate.outcome == "disagree_period" and gate.auto_apply == "N":
                events.append(event(
                    run_id=RUN_ID, recorded_at=t1,
                    actor_role="maintainer", actor_name="dso",
                    prompt_version=PROMPT_VERSION, entity_id=eid, field_path=fp,
                    data_as_of=None, value=_num_or_str(row.get("prajna_value")),
                    verdict="REFUTE", change_reason="superseded_newer_period",
                    notes="Newer-period figure held — stored value looks primary-sourced for its own period.",
                ))
                pending.append({
                    "entity_id": eid,
                    "field": field,
                    "stored_value": row.get("stored_value") or "",
                    "prajna": f"{row['prajna_verdict']}:{row.get('prajna_value') or ''}",
                    "agriya": f"{row['agriya_verdict']}:{row.get('agriya_value') or ''}",
                    "status": "expert-pending",
                    "reason": gate.classification,
                })

        if file_changes:
            path.write_text(
                yaml.dump(doc, default_flow_style=False, allow_unicode=True,
                          sort_keys=False, width=88),
                encoding="utf-8",
            )
            changed[str(path.relative_to(jem))] = file_changes

    n_events = append_events(events_path, events)
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    with pending_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=[
            "entity_id", "field", "stored_value", "prajna", "agriya", "status", "reason",
        ])
        w.writeheader()
        w.writerows(pending)

    return {
        "events_written": n_events,
        "events_path": str(events_path),
        "canon_files_changed": sorted(changed),
        "changes": changed,
        "pending_path": str(pending_path),
        "pending_n": len(pending),
    }


def load_consensus(jem: Path) -> List[Dict[str, str]]:
    path = jem / "ledger" / "suggested" / "verify_trib_01_consensus.csv"
    return list(csv.DictReader(path.open(encoding="utf-8")))


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Gated apply of verify-trib-01 consensus")
    ap.add_argument("--jem-root", type=Path, default=None)
    ap.add_argument("--gate-only", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    jem = args.jem_root or jem_root()
    gates = build_gate(jem)
    write_gate_csv(jem / "ledger" / "suggested" / "decision_gate_20260908.csv", gates)
    print_gate(gates)
    if args.gate_only and not args.apply:
        return
    if not args.apply:
        print("\n(pass --apply to write ledger events + unambiguous canon; --gate-only to stop here)")
        return
    result = apply(jem, gates, load_consensus(jem))
    print("\n=== APPLY RESULT ===")
    print(json.dumps({k: v for k, v in result.items() if k != "changes"}, indent=2))
    print("canon files:")
    for p, ch in result["changes"].items():
        print(f"  {p}: {', '.join(ch)}")


if __name__ == "__main__":
    main()
