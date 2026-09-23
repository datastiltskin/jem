#!/usr/bin/env python3
"""Expert review workbooks — plain language, legal-reviewer audience.

Writes .xlsx plus .csv fallback. Ingest columns (expert_verdict, expert_value,
expert_source_url, expert_note, org) are present now; replies come later.
"""

from __future__ import annotations

import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
from xml.sax.saxutils import escape

import yaml

_SCRIPTS = Path(__file__).resolve().parent.parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

WHAT_JEM = (
    "JEM is an open map of India's judicial and quasi-judicial institutions — "
    "structure, not case outcomes."
)
WHAT_ASKING = (
    "Please check the official-source figures below and tell us which value "
    "should stand, using the last four columns."
)
RETURN = (
    "Fill expert_verdict, expert_value, expert_source_url, expert_note. "
    "Reply-all to the requesting maintainer. Leave org as pre-filled."
)
VERDICT_CHOICES = (
    "Correct as shown / Use our-found value / Different value below / Cannot verify"
)

FIELD_PLAIN = {
    "pending_cases": "cases waiting to be decided",
    "filed_last_year": "cases filed in the reporting period",
    "disposed_last_year": "cases disposed in the reporting period",
    "disposal_rate": "share of filed cases that were disposed",
    "avg_disposal_days": "average days to dispose a case",
    "njdg_source_stamp": "whether the National Judicial Data Grid is listed as a source",
}

TRUSTBRIDGE_IDS = {"sebi", "cci", "tnerc", "merc", "pngrb", "sat", "aptel", "ifsca"}


def _inline(s: str) -> str:
    return f'<c t="inlineStr"><is><t>{escape(s or "")}</t></is></c>'


def write_xlsx(path: Path, rows: List[List[str]], header_block: List[str], columns: List[str]) -> None:
    """Minimal xlsx (inline strings) — no openpyxl required."""
    sheet_rows = []
    r = 1
    for line in header_block:
        sheet_rows.append(
            f'<row r="{r}"><c r="A{r}" t="inlineStr"><is><t>{escape(line)}</t></is></c></row>'
        )
        r += 1
    r += 1  # blank
    header_row = r
    cells = "".join(
        f'<c r="{chr(65+i)}{r}" t="inlineStr"><is><t>{escape(columns[i])}</t></is></c>'
        for i in range(len(columns))
    )
    sheet_rows.append(f'<row r="{r}">{cells}</row>')
    r += 1
    for rec in rows:
        cells = "".join(
            f'<c r="{chr(65+i)}{r}" t="inlineStr"><is><t>{escape(str(rec[i]) if i < len(rec) else "")}</t></is></c>'
            for i in range(len(columns))
        )
        sheet_rows.append(f'<row r="{r}">{cells}</row>')
        r += 1
    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="review" sheetId="1" r:id="rId1"/></sheets></workbook>'
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>'
    )
    wb_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
        '</Relationships>'
    )
    ctypes = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        '</Types>'
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ctypes)
        z.writestr("_rels/.rels", rels)
        z.writestr("xl/workbook.xml", workbook)
        z.writestr("xl/_rels/workbook.xml.rels", wb_rels)
        z.writestr("xl/worksheets/sheet1.xml", sheet)


def load_entity_index(jem: Path) -> Dict[str, dict]:
    idx = {}
    for p in (jem / "data" / "entities").rglob("*.yaml"):
        try:
            d = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        if isinstance(d, dict) and d.get("id"):
            idx[d["id"]] = d
    return idx


def _question(gate: dict) -> str:
    outcome = gate.get("outcome") or ""
    if outcome == "agree_refute_njdg":
        return (
            "Our automated checks say the National Judicial Data Grid does not "
            "cover this body. Should that Grid listing be removed as a source?"
        )
    if "SAT" in (gate.get("classification") or ""):
        return (
            "The stored figure looks unsourced. Both independent checks re-read "
            "SEBI's annual report and got the same replacement. Is that replacement correct?"
        )
    if outcome == "disagree_value":
        return (
            "Two independent checks both rejected the stored figure but proposed "
            "different replacements. Which figure (if any) is right?"
        )
    if outcome == "disagree_verdict":
        return (
            "The two independent checks disagreed on whether a replacement figure "
            "is safe to use. What should JEM show?"
        )
    if outcome == "disagree_period":
        return (
            "One check treated a later official report as a replacement; the other "
            "said it describes a different reporting period. Should we keep the "
            "current figure, switch to the later one, or show both by period?"
        )
    if outcome == "agree_unsourced":
        return "Neither check found an official document for this figure. Should we keep, blank, or replace it?"
    return "Please confirm the official figure and source."


def _found(gate: dict) -> str:
    v = gate.get("rater_found_value") or ""
    if not v:
        return "none found"
    return str(v)


def _source(gate: dict, prajna_csv_row: Optional[dict]) -> str:
    if gate.get("entity_id") == "sat" and gate.get("field") in {
        "pending_cases", "filed_last_year", "disposed_last_year", "disposal_rate"
    }:
        return "SEBI Annual Report 2025-26, Chapter 10, Table 10.35 | https://www.sebi.gov.in/reports-and-statistics/publications/aug-2026/Chapter%2010.pdf"
    if gate.get("outcome") == "agree_refute_njdg":
        return "NIC: National Judicial Data Grid (eCourts scope) | https://www.nic.gov.in/project/national-judicial-data-grid/"
    url = (prajna_csv_row or {}).get("source_url") or gate.get("source_url") or ""
    if not url:
        return "none found"
    return url


def _row(entity: dict, gate: dict, org: str, prajna: Optional[dict]) -> List[str]:
    name = entity.get("name") or gate["entity_id"]
    abbr = entity.get("abbreviation") or ""
    label = f"{name} ({abbr})" if abbr else name
    field = gate["field"]
    return [
        label,
        FIELD_PLAIN.get(field, field),
        "FY 2025-26" if gate.get("entity_id") == "sat" and field != "njdg_source_stamp" and gate.get("auto_apply") == "Y"
        else (entity.get("case_volume") or {}).get("data_as_of") or "",
        str(gate.get("stored_value") or ""),
        _found(gate),
        _source(gate, prajna),
        _question(gate),
        "",  # expert_verdict
        "",  # expert_value
        "",  # expert_source_url
        "",  # expert_note
        org,
        gate.get("entity_id") or "",
        field,
        gate.get("outcome") or "",
    ]


COLUMNS = [
    "Entity (name + abbr)", "What we measured", "Period", "Value currently in JEM",
    "What our checks found", "Primary source (title + URL, or none found)",
    "Question for you", "expert_verdict", "expert_value", "expert_source_url",
    "expert_note", "org", "entity_id", "field", "consensus_outcome",
]


def emit(jem: Path) -> Dict[str, str]:
    idx = load_entity_index(jem)
    gate = list(csv.DictReader((jem / "ledger" / "suggested" / "decision_gate_20260908.csv").open()))
    prajna_path = jem / "jem-verify-tribunals" / "out" / "deepseek__verify-trib-01__prajna__20260831_131656.csv"
    prajna_by = {}
    if prajna_path.exists():
        for r in csv.DictReader(prajna_path.open()):
            prajna_by[(r["entity_id"], r["field"])] = r

    def contested(g: dict) -> bool:
        return g.get("outcome") != "agree_unsourced"

    daksh = []
    trust = []
    for g in sorted(gate, key=lambda r: (r["entity_id"], r["field"])):
        if not contested(g):
            continue
        ent = idx.get(g["entity_id"]) or {"id": g["entity_id"], "name": g["entity_id"]}
        p = prajna_by.get((g["entity_id"], g["field"]))
        if ent.get("type") == "CentralTribunal":
            daksh.append(_row(ent, g, "daksh", p))
        if g["entity_id"] in TRUSTBRIDGE_IDS:
            trust.append(_row(ent, g, "trustbridge", p))

    # IFSCA gap row — entity exists; appellate path to SAT stays SUGGESTED.
    ifsca = idx.get("ifsca") or {"id": "ifsca", "name": "International Financial Services Centres Authority", "abbreviation": "IFSCA"}
    trust.append([
        f"{ifsca.get('name')} ({ifsca.get('abbreviation') or 'IFSCA'})",
        "whether this body belongs in JEM and whether its appeals go to SAT",
        "",
        "not yet confirmed in this verification round",
        "suggested only — no relationship written",
        "IFSCA Act 2019 (primary handle currently 404 on India Code) | confirm against live primary",
        "Please confirm IFSCA's scope and whether appeals from IFSCA orders go to SAT. Do not treat a map edge as already decided.",
        "", "", "", "",
        "trustbridge", "ifsca", "appealable_to_sat", "suggested_gap",
    ])
    # PNGRB is not in the 44 — gap row
    pngrb = idx.get("pngrb")
    if not pngrb:
        trust.append([
            "Petroleum and Natural Gas Regulatory Board (PNGRB)",
            "whether this body belongs in this review pack",
            "",
            "not in JEM's verify-trib-01 roster",
            "none found in this round",
            "none found",
            "PNGRB was named for this review but has no row in the current 44-body verification set. Should we add it to a later pass?",
            "", "", "", "",
            "trustbridge", "pngrb", "roster", "suggested_gap",
        ])

    header = [WHAT_JEM, WHAT_ASKING, RETURN, f"expert_verdict choices: {VERDICT_CHOICES}"]
    out_dir = jem / "ledger" / "expert_packets"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for slug, rows, org in (
        ("expert_review_DAKSH_tribunals_20260908", daksh, "daksh"),
        ("expert_review_TrustBridge_20260908", trust, "trustbridge"),
    ):
        xlsx = out_dir / f"{slug}.xlsx"
        csvp = out_dir / f"{slug}.csv"
        write_xlsx(xlsx, rows, header, COLUMNS)
        with csvp.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            for line in header:
                w.writerow([line])
            w.writerow([])
            w.writerow(COLUMNS)
            w.writerows(rows)
        paths[org] = str(xlsx)
        paths[f"{org}_csv"] = str(csvp)
    return paths


def main() -> None:
    jem = Path(__file__).resolve().parent.parent.parent
    print(json.dumps(emit(jem), indent=2))


if __name__ == "__main__":
    main()
