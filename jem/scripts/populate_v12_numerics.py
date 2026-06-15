#!/usr/bin/env python3
"""
Bulk attach v1.2 judge_strength stubs to court-like entity YAML.

Does not invent allotted/appointed numbers — null + DoJ_Report / HC_Report / Tribunal_Report
source_url placeholders only. Idempotent: skips entities that already have judge_strength.

Usage (from jem/):
  python3 scripts/populate_v12_numerics.py
  python3 scripts/populate_v12_numerics.py --dry-run
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ENTITIES_DIR = SCRIPT_DIR.parent / "data" / "entities"

DOJ_VACANCY_URL = (
    "https://cdnbbsr.s3waas.gov.in/s35d6646aad9bcc0be55b2c82f69750387/"
    "uploads/2025/12/202512241943014515.pdf"
)

COURT_TYPES = frozenset(
    {
        "ConstitutionalCourt",
        "HighCourtBench",
        "SubordinateCivilCourt",
        "SubordinateCriminalCourt",
        "CityCivilCourt",
        "SpecialCourt",
        "CentralTribunal",
        "StateTribunal",
        "ConsumerCommission",
    }
)

# HighCourtBench roster pages for v1.2 structure (appointed populated separately).
BENCH_ROSTER_URLS: Dict[str, str] = {
    "hc_calcutta_bench_jalpaiguri": "https://www.calcuttahighcourt.gov.in/Judges/judges",
    "hc_calcutta_bench_port_blair": "https://www.calcuttahighcourt.gov.in/Judges/judges",
    "hc_karnataka_bench_dharwad": "https://judiciary.karnataka.gov.in/",
    "hc_punjab_haryana_bench_shimla": "https://highcourtchd.gov.in/",
    "hc_rajasthan_bench_jaipur": "https://hcraj.nic.in/hcraj/index.php/judges/present-judges",
}

TRIBUNAL_REPORT_URLS: Dict[str, str] = {
    "aft": "https://aft.gov.in/",
    "cat": "https://cgat.gov.in/",
    "cestat": "https://cestat.gov.in/",
    "drt": "https://drt.gov.in/",
    "drat": "https://dfs.gov.in/financial-institutions/drat",
    "nclat": "https://nclat.gov.in/",
    "nclt": "https://nclt.gov.in/",
    "ngt": "https://greentribunal.gov.in/",
    "sat": "https://sebi.gov.in/sebiweb/home/HomeAction.html?do=recognised#",
    "ncdrc": "https://ncdrc.nic.in/",
    "itat": "https://itat.gov.in/",
    "tdsat": "https://tdsat.gov.in/",
    "aptel": "https://aptel.gov.in/",
}


def judge_strength_stub(*, source_type: str = "DoJ_Report", source_url: Optional[str] = None) -> dict:
    return {
        "data_as_of": None,
        "allotted": None,
        "appointed": None,
        "source_type": source_type,
        "source_url": source_url or "https://doj.gov.in/",
        "notes": (
            "Allotted = sanctioned posts; appointed = working judges in post. "
            "Populate from DoJ quarterly vacancy report or NJDG bench strength."
        ),
    }


def bench_judge_strength_stub(parent_hc: str, *, source_url: Optional[str] = None) -> dict:
    return {
        "data_as_of": None,
        "allotted": None,
        "appointed": None,
        "source_type": "HC_Report",
        "source_url": source_url,
        "notes": (
            f"Judges are drawn from parent HC pool ({parent_hc}). Allotted is null "
            "— sanctioned strength is set at parent HC level only. "
            "Populate appointed from official HC bench roster snapshot."
        ),
    }


def tribunal_judge_strength_stub(entity_id: str) -> dict:
    url = TRIBUNAL_REPORT_URLS.get(entity_id, "https://doj.gov.in/")
    return {
        "data_as_of": None,
        "allotted": None,
        "appointed": None,
        "source_type": "Tribunal_Report",
        "source_url": url,
        "notes": "Member/chair strength from tribunal annual report or DoJ quarterly vacancy data.",
    }


def doj_hc_judge_strength_stub() -> dict:
    return {
        "data_as_of": "2025-12-24",
        "allotted": None,
        "appointed": None,
        "source_type": "DoJ_Report",
        "source_url": DOJ_VACANCY_URL,
        "notes": "Populate allotted/appointed from DoJ quarterly vacancy report row for this court.",
    }


def _has_populated_strength(js: dict) -> bool:
    return js.get("allotted") is not None or js.get("appointed") is not None


def _merge_notes(existing: str, tag: str) -> str:
    if tag in existing:
        return existing.strip()
    return f"{existing.strip()} {tag}".strip() if existing else tag


def enrich_entity(data: dict) -> Tuple[dict, bool]:
    """Return (updated_doc, changed)."""
    eid = data.get("id") or ""
    etype = data.get("type")
    if etype not in COURT_TYPES:
        return data, False

    changed = False
    js = data.get("judge_strength")

    if etype == "HighCourtBench":
        parent = data.get("parent_hc") or "parent HC"
        roster_url = BENCH_ROSTER_URLS.get(eid)
        if js is None:
            data["judge_strength"] = bench_judge_strength_stub(parent, source_url=roster_url)
            changed = True
        elif not _has_populated_strength(js):
            merged = dict(js)
            if merged.get("source_url") is None and roster_url:
                merged["source_url"] = roster_url
            if merged.get("data_as_of") is None and merged.get("appointed") is None:
                merged.setdefault("data_as_of", None)
            if not merged.get("notes"):
                merged["notes"] = bench_judge_strength_stub(parent)["notes"]
            if merged != js:
                data["judge_strength"] = merged
                changed = True
    elif etype == "ConstitutionalCourt":
        if eid == "high_courts_all":
            if js is None:
                data["judge_strength"] = doj_hc_judge_strength_stub()
                changed = True
        elif js is None and eid.startswith("hc_"):
            data["judge_strength"] = doj_hc_judge_strength_stub()
            changed = True
    elif etype in ("CentralTribunal", "StateTribunal"):
        if js is None:
            data["judge_strength"] = tribunal_judge_strength_stub(eid)
            changed = True
        elif not _has_populated_strength(js) and js.get("source_url") in (None, ""):
            merged = dict(js)
            merged["source_url"] = TRIBUNAL_REPORT_URLS.get(eid, "https://doj.gov.in/")
            merged.setdefault("source_type", "Tribunal_Report")
            data["judge_strength"] = merged
            changed = True
    else:
        if js is None:
            data["judge_strength"] = judge_strength_stub()
            changed = True

    if changed:
        tag = "v1.2 judge_strength stub attached"
        data["data_quality_notes"] = _merge_notes(data.get("data_quality_notes") or "", tag)
        if data.get("data_quality") == "verified":
            # Never downgrade; only ensure partial if numerics are null stubs.
            pass
        elif data.get("data_quality") is None:
            data["data_quality"] = "partial"

    return data, changed


def dump_yaml(path: Path, data: dict) -> None:
    header = ""
    raw = path.read_text(encoding="utf-8")
    if raw.startswith("#"):
        first_nl = raw.find("\n")
        if first_nl != -1:
            header = raw[: first_nl + 1]
    body = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    path.write_text(header + body, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Attach v1.2 judge_strength stubs to court YAML")
    parser.add_argument("--dry-run", action="store_true", help="Report only; do not write files")
    args = parser.parse_args()

    updated: List[str] = []
    for path in sorted(ENTITIES_DIR.rglob("*.yaml")):
        if "schema" in str(path) or "_TAXONOMY" in str(path):
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict) or not data.get("id"):
            continue
        new_data, changed = enrich_entity(data)
        if changed:
            updated.append(data["id"])
            if not args.dry_run:
                dump_yaml(path, new_data)

    print(f"{'Would update' if args.dry_run else 'Updated'} {len(updated)} entity YAML file(s).")
    if updated and len(updated) <= 40:
        for eid in updated:
            print(f"  {eid}")
    elif updated:
        for eid in updated[:20]:
            print(f"  {eid}")
        print(f"  ... and {len(updated) - 20} more")


if __name__ == "__main__":
    main()
