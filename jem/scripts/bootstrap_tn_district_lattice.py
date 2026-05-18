#!/usr/bin/env python3
"""
Create the full Tamil Nadu district court lattice (38 districts) under
jem/data/entities/_generated/states/tn/, remove the aggregate generic entity,
and append Madras HC appellate + supervision edges in tn_relationships.yaml.

Idempotent: skips YAML that already exists; only deletes generic once.

Usage (from jem/):
  python3 scripts/bootstrap_tn_district_lattice.py
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

from hc_benches_config import TN_DISTRICT_TO_BENCH

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
TN_DIR = DATA_DIR / "entities" / "_generated" / "states" / "tn"
REL_PATH = DATA_DIR / "relationships" / "tn_relationships.yaml"

# 38 revenue districts (2020). Slug -> display name.
TN_DISTRICTS: List[Tuple[str, str]] = [
    ("ariyalur", "Ariyalur"),
    ("chengalpattu", "Chengalpattu"),
    ("chennai", "Chennai"),
    ("coimbatore", "Coimbatore"),
    ("cuddalore", "Cuddalore"),
    ("dharmapuri", "Dharmapuri"),
    ("dindigul", "Dindigul"),
    ("erode", "Erode"),
    ("kallakurichi", "Kallakurichi"),
    ("kancheepuram", "Kancheepuram"),
    ("karur", "Karur"),
    ("kanniyakumari", "Kanniyakumari"),
    ("krishnagiri", "Krishnagiri"),
    ("madurai", "Madurai"),
    ("mayiladuthurai", "Mayiladuthurai"),
    ("nagapattinam", "Nagapattinam"),
    ("namakkal", "Namakkal"),
    ("nilgiris", "The Nilgiris"),
    ("perambalur", "Perambalur"),
    ("pudukkottai", "Pudukkottai"),
    ("ramanathapuram", "Ramanathapuram"),
    ("ranipet", "Ranipet"),
    ("salem", "Salem"),
    ("sivaganga", "Sivaganga"),
    ("tenkasi", "Tenkasi"),
    ("thanjavur", "Thanjavur"),
    ("theni", "Theni"),
    ("thoothukudi", "Thoothukudi"),
    ("tiruchirappalli", "Tiruchirappalli"),
    ("tirunelveli", "Tirunelveli"),
    ("tirupathur", "Tirupathur"),
    ("tiruppur", "Tiruppur"),
    ("tiruvallur", "Tiruvallur"),
    ("tiruvannamalai", "Tiruvannamalai"),
    ("tiruvarur", "Tiruvarur"),
    ("vellore", "Vellore"),
    ("viluppuram", "Viluppuram"),
    ("virudhunagar", "Virudhunagar"),
]

SRC = {
    "label": "India Code — Constitution & Acts",
    "url": "https://india-code.nic.in/",
    "type": "GoIWebsite",
    "accessed_date": str(date.today()),
}
NJDG = {
    "label": "National Judicial Data Grid (NJDG)",
    "url": "https://njdg.ecourts.gov.in/",
    "type": "NJDG",
    "accessed_date": str(date.today()),
}

# Madras HC snapshot / TN aggregate used ~1095 days in prior generic merge — placeholder per district.
TN_AVG_DISPOSAL_DAYS = 1095


def district_doc(slug: str, display: str) -> dict:
    eid = f"tn_district_court_{slug}"
    return {
        "id": eid,
        "name": f"District Court — {display}",
        "type": "SubordinateCivilCourt",
        "cluster": "subordinate_courts",
        "level_of_government": "State",
        "jurisdiction_scope": {
            "states_covered": ["TN"],
            "is_all_india": False,
            "jurisdiction_types": ["Civil", "Criminal"],
        },
        "created_year": 1860,
        "operational_status": "Active",
        "constitutional_basis": "Constitution of India, Articles 233–237",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {
            "audited_by": "cag_india",
            "audit_type": "CAG_Statutory",
            "audit_report_public": True,
        },
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "case_volume": {
            "data_as_of": str(date.today()),
            "avg_disposal_days": TN_AVG_DISPOSAL_DAYS,
            "source_url": "https://njdg.ecourts.gov.in/",
            "source_type": "NJDG_Snapshot",
        },
        "data_quality": "partial",
        "data_quality_notes": (
            "District-level pendency (pending_cases, filed_last_year, disposed_last_year) and judge "
            "strength to be filled from NJDG district dashboard and Madras HC / DoJ sources; avg_disposal_days "
            "is a TN-level placeholder pending district pull."
        ),
        "sources": [SRC, NJDG],
    }


def main() -> None:
    TN_DIR.mkdir(parents=True, exist_ok=True)
    created = 0
    for slug, display in TN_DISTRICTS:
        path = TN_DIR / f"tn_district_court_{slug}.yaml"
        if path.exists():
            continue
        text = yaml.dump(
            district_doc(slug, display),
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
            width=120,
        )
        path.write_text(
            "# JEM — Tamil Nadu district lattice (full set); NJDG district fields TBD per CONTRIBUTING.md\n" + text,
            encoding="utf-8",
        )
        created += 1
    print(f"TN district YAML created: {created} (skipped existing)")

    gen_path = TN_DIR / "tn_district_courts_generic.yaml"
    if gen_path.exists():
        gen_path.unlink()
        print("Removed tn_district_courts_generic.yaml")

    data = yaml.safe_load(REL_PATH.read_text(encoding="utf-8"))
    rels: List[dict] = list(data.get("relationships") or [])
    anchor = rels[0]["sources"][0] if rels and rels[0].get("sources") else SRC

    # Drop legacy single-edge + any generic-based edges
    rels = [r for r in rels if r.get("id") not in ("tn_district_hc", "tn_generic_hc")]

    existing = {r.get("id") for r in rels if isinstance(r, dict)}
    added = 0
    for slug, _ in TN_DISTRICTS:
        eid = f"tn_district_court_{slug}"
        hc_tgt = TN_DISTRICT_TO_BENCH.get(slug, "hc_madras")
        rid_a = f"tn_district_{slug}_appealable_{hc_tgt}"
        rid_s = f"tn_{hc_tgt}_supervise_{slug}"
        if rid_a not in existing:
            rels.append(
                {
                    "id": rid_a,
                    "source": eid,
                    "target": hc_tgt,
                    "relationship_type": "AppealableTo",
                    "relationship_category": "appellate_chain",
                    "is_binding": True,
                    "notes": f"District court appeals to {hc_tgt} (Madras HC / bench)",
                    "data_quality": "partial",
                    "sources": [anchor],
                }
            )
            existing.add(rid_a)
            added += 1
        if rid_s not in existing:
            rels.append(
                {
                    "id": rid_s,
                    "source": hc_tgt,
                    "target": eid,
                    "relationship_type": "AdministrativeSupervision",
                    "relationship_category": "supervisory",
                    "is_binding": True,
                    "notes": "Article 235 supervision (Madras HC)",
                    "data_quality": "partial",
                    "sources": [anchor],
                }
            )
            existing.add(rid_s)
            added += 1

    # TNSJA continuing education — representative edge to Chennai (largest docket)
    rid_train = "tn_sja_train_chennai_district"
    if rid_train not in existing:
        rels.append(
            {
                "id": rid_train,
                "source": "tn_sja",
                "target": "tn_district_court_chennai",
                "relationship_type": "ProvidesContinuingEducation",
                "relationship_category": "training",
                "is_binding": True,
                "notes": "State judicial academy serves all TN districts; representative training edge",
                "data_quality": "partial",
                "sources": [anchor],
            }
        )
        added += 1

    data["relationships"] = rels
    REL_PATH.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    print(f"tn_relationships.yaml: appended {added} relationship row(s) total after cleanup.")


if __name__ == "__main__":
    main()
