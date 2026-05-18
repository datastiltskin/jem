#!/usr/bin/env python3
"""
Merge NJDG-style case_volume blocks from a compiled graph.json snapshot into
entity YAML files under jem/data/entities/.

The canonical Claude export path used in older briefs was d3lem; this script
accepts any graph.json that uses the richer frontend shape with _detail.case_volume.

Usage:
  python scripts/merge_njdg_snapshot.py --snapshot /path/to/graph.json --plan report.md
  python scripts/merge_njdg_snapshot.py --snapshot /path/to/graph.json --apply
  python scripts/merge_njdg_snapshot.py --bootstrap-districts   # MH/KA missing district YAMLs + HC edges

ID remap (snapshot id -> repo entity id):
  mh_district_court_mumbai -> mh_district_court_mumbai_city
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
ENTITIES_DIR = DATA_DIR / "entities"

# Snapshot graph id -> JEM entity id
ENTITY_ID_REMAP = {
    "mh_district_court_mumbai": "mh_district_court_mumbai_city",
    # Snapshot uses legacy spelling; JEM entity id is hc_gauhati
    "hc_guwahati": "hc_gauhati",
}

NJDG_SOURCE = {
    "label": "National Judicial Data Grid (NJDG)",
    "url": "https://njdg.ecourts.gov.in/",
    "type": "NJDG",
    "accessed_date": "2024-12-01",
}


def load_snapshot(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_case_volume_by_entity(graph: dict) -> Dict[str, dict]:
    """entity_id -> case_volume dict (from _detail only; matches Claude export)."""
    out: Dict[str, dict] = {}
    for e in graph.get("entities") or []:
        eid = e.get("id")
        if not eid:
            continue
        detail = e.get("_detail") or {}
        cv = detail.get("case_volume")
        if not isinstance(cv, dict):
            continue
        out[eid] = dict(cv)
    return out


def build_entity_index() -> Dict[str, Path]:
    """entity id -> yaml path (single scan)."""
    index: Dict[str, Path] = {}
    for f in ENTITIES_DIR.rglob("*.yaml"):
        if "schema" in str(f) or "_TAXONOMY" in str(f):
            continue
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and data.get("id"):
            index[data["id"]] = f
    return index


def find_entity_yaml(entity_id: str, index: Dict[str, Path]) -> Optional[Path]:
    return index.get(entity_id)


def _strip_none(d: dict) -> dict:
    return {k: v for k, v in d.items() if v is not None}


def normalise_case_volume(raw: dict, top_level: dict) -> dict:
    """Merge _detail.case_volume with useful top-level snapshot metrics."""
    cv = _strip_none(dict(raw))
    filed = cv.get("filed_last_year")
    disposed = cv.get("disposed_last_year")
    if filed and disposed and cv.get("disposal_rate") is None:
        try:
            cv["disposal_rate"] = round(float(disposed) / float(filed), 4)
        except (TypeError, ZeroDivisionError):
            pass
    if cv.get("clog_severity") is None and top_level.get("clog_severity"):
        cv["clog_severity"] = top_level["clog_severity"]
    return cv


def snapshot_entity_top_level(graph: dict, entity_id: str) -> dict:
    for e in graph.get("entities") or []:
        if e.get("id") == entity_id:
            return e
    return {}


def merge_sources(existing: List[dict]) -> List[dict]:
    have = {(s.get("url"), s.get("label")) for s in existing if isinstance(s, dict)}
    out = list(existing)
    key = (NJDG_SOURCE["url"], NJDG_SOURCE["label"])
    if key not in have:
        out.append(dict(NJDG_SOURCE))
    return out


def dump_yaml_file(path: Path, data: dict, *, header: Optional[str] = None) -> None:
    text = yaml.dump(
        data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )
    if header:
        path.write_text(header.rstrip() + "\n" + text, encoding="utf-8")
    else:
        path.write_text(text, encoding="utf-8")


def plan_report(snapshot_path: Path, out_path: Path) -> None:
    graph = load_snapshot(snapshot_path)
    cv_map = extract_case_volume_by_entity(graph)
    index = build_entity_index()
    lines: List[str] = []
    lines.append(f"# NJDG snapshot merge plan\n")
    lines.append(f"- Snapshot: `{snapshot_path}`\n")
    lines.append(f"- Entities with `_detail.case_volume` in snapshot: **{len(cv_map)}**\n")
    lines.append("\n## Per entity\n")
    lines.append("| Snapshot id | Target id | YAML | Action |\n|---|---|---|---|\n")
    matched = 0
    for sid in sorted(cv_map.keys()):
        tid = ENTITY_ID_REMAP.get(sid, sid)
        yml = find_entity_yaml(tid, index)
        if yml:
            matched += 1
            lines.append(f"| `{sid}` | `{tid}` | `{yml.relative_to(DATA_DIR.parent)}` | merge case_volume |\n")
        else:
            lines.append(f"| `{sid}` | `{tid}` | — | **no YAML — skip** |\n")
    lines.append(f"\n## Summary\n- Mergeable (YAML exists): **{matched}**\n")
    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"Wrote plan to {out_path}")


def apply_merge(snapshot_path: Path) -> Tuple[int, List[str]]:
    graph = load_snapshot(snapshot_path)
    cv_by_snap_id = extract_case_volume_by_entity(graph)
    index = build_entity_index()
    errors: List[str] = []
    updated = 0
    for sid, raw_cv in cv_by_snap_id.items():
        tid = ENTITY_ID_REMAP.get(sid, sid)
        top = snapshot_entity_top_level(graph, sid)
        path = find_entity_yaml(tid, index)
        if not path:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except Exception as e:
            errors.append(f"{tid}: parse error {e}")
            continue
        if not isinstance(data, dict):
            errors.append(f"{tid}: not a mapping")
            continue
        cv = normalise_case_volume(raw_cv, top)
        data["case_volume"] = cv
        data["sources"] = merge_sources(data.get("sources") or [])
        notes = data.get("data_quality_notes") or ""
        tag = "NJDG snapshot case_volume merged"
        if tag not in notes:
            data["data_quality_notes"] = (notes + " " + tag).strip()
        dump_yaml_file(path, data)
        updated += 1
    return updated, errors


# --- Bootstrap missing MH / KA district courts (structural v1; pendency from NJDG when available) ---

MH_NEW_DISTRICTS: List[Tuple[str, str]] = [
    ("jalgaon", "Jalgaon"),
    ("ahmednagar", "Ahmednagar"),
    ("raigad", "Raigad"),
    ("ratnagiri", "Ratnagiri"),
    ("sindhudurg", "Sindhudurg"),
    ("satara", "Satara"),
    ("sangli", "Sangli"),
    ("latur", "Latur"),
    ("osmanabad", "Osmanabad (Dharashiv)"),
    ("beed", "Beed"),
    ("jalna", "Jalna"),
    ("parbhani", "Parbhani"),
    ("hingoli", "Hingoli"),
    ("buldhana", "Buldhana"),
    ("akola", "Akola"),
    ("washim", "Washim"),
    ("yavatmal", "Yavatmal"),
    ("wardha", "Wardha"),
    ("bhandara", "Bhandara"),
    ("gondia", "Gondia"),
    ("chandrapur", "Chandrapur"),
    ("gadchiroli", "Gadchiroli"),
    ("mumbai_suburban", "Mumbai Suburban"),
    ("palghar", "Palghar"),
    ("nandurbar", "Nandurbar"),
    ("dhule", "Dhule"),
]

KA_NEW_DISTRICTS: List[Tuple[str, str]] = [
    ("raichur", "Raichur"),
    ("bidar", "Bidar"),
    ("vijayapura", "Vijayapura"),
    ("bagalkot", "Bagalkot"),
    ("uttara_kannada", "Uttara Kannada"),
    ("udupi", "Udupi"),
    ("chikkamagaluru", "Chikkamagaluru"),
    ("hassan", "Hassan"),
    ("kodagu", "Kodagu"),
    ("mandya", "Mandya"),
    ("chamarajanagar", "Chamarajanagar"),
    ("ramanagara", "Ramanagara"),
    ("chikkaballapur", "Chikkaballapur"),
    ("kolar", "Kolar"),
    ("chitradurga", "Chitradurga"),
    ("davangere", "Davanagere"),
    ("haveri", "Haveri"),
    ("gadag", "Gadag"),
    ("yadgir", "Yadgir"),
]

MH_AVG_DISPOSAL = 1277
KA_AVG_DISPOSAL = 1095


def district_template(
    *,
    state: str,
    slug: str,
    display: str,
    avg_disposal: int,
) -> dict:
    prefix = "mh" if state == "MH" else "ka"
    eid = f"{prefix}_district_court_{slug}"
    return {
        "id": eid,
        "name": f"District Court — {display}",
        "type": "SubordinateCivilCourt",
        "cluster": "subordinate_courts",
        "level_of_government": "State",
        "jurisdiction_scope": {
            "states_covered": [state],
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
        "complaint_mechanism": {
            "bias_complaint_to": [],
            "lokpal_jurisdiction": "Not_Applicable",
        },
        "case_volume": {
            "data_as_of": str(date.today()),
            "avg_disposal_days": avg_disposal,
            "source_url": "https://njdg.ecourts.gov.in/",
            "source_type": "NJDG_Snapshot",
        },
        "data_quality": "partial",
        "data_quality_notes": (
            "District-level pendency (pending_cases, filed_last_year, disposed_last_year, judge strength) "
            "to be filled from NJDG district dashboard and HC/DoJ sources; state average disposal days used as placeholder only."
        ),
        "sources": [
            {
                "label": "India Code — Constitution & Acts",
                "url": "https://india-code.nic.in/",
                "type": "GoIWebsite",
                "accessed_date": str(date.today()),
            },
            dict(NJDG_SOURCE),
        ],
    }


def bootstrap_district_files() -> Tuple[int, int]:
    """Create missing district YAMLs. Returns (mh_created, ka_created)."""
    mh_dir = ENTITIES_DIR / "_generated" / "states" / "mh"
    ka_dir = ENTITIES_DIR / "_generated" / "states" / "ka"
    mh_dir.mkdir(parents=True, exist_ok=True)
    ka_dir.mkdir(parents=True, exist_ok=True)
    mh_n = ka_n = 0
    for slug, display in MH_NEW_DISTRICTS:
        eid = f"mh_district_court_{slug}"
        path = mh_dir / f"{eid}.yaml"
        if path.exists():
            continue
        data = district_template(state="MH", slug=slug, display=display, avg_disposal=MH_AVG_DISPOSAL)
        hdr = "# JEM generated bundle — data_quality: partial; expand sources per CONTRIBUTING.md\n"
        dump_yaml_file(path, data, header=hdr)
        mh_n += 1
    for slug, display in KA_NEW_DISTRICTS:
        eid = f"ka_district_court_{slug}"
        path = ka_dir / f"{eid}.yaml"
        if path.exists():
            continue
        data = district_template(state="KA", slug=slug, display=display, avg_disposal=KA_AVG_DISPOSAL)
        hdr = "# JEM generated bundle — data_quality: partial; expand sources per CONTRIBUTING.md\n"
        dump_yaml_file(path, data, header=hdr)
        ka_n += 1
    return mh_n, ka_n


def _append_unique_relationships(rel_path: Path, new_rels: List[dict]) -> int:
    data = yaml.safe_load(rel_path.read_text(encoding="utf-8"))
    rels = list(data.get("relationships") or [])
    existing_ids = {r.get("id") for r in rels if isinstance(r, dict)}
    added = 0
    for r in new_rels:
        rid = r.get("id")
        if not rid or rid in existing_ids:
            continue
        rels.append(dict(r))
        existing_ids.add(rid)
        added += 1
    data["relationships"] = rels
    rel_path.write_text(
        yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120),
        encoding="utf-8",
    )
    return added


def bootstrap_hc_relationships() -> Tuple[int, int]:
    """AppealableTo HC + AdministrativeSupervision for each new district court."""
    anchor = {"label": "India Code — Constitution & Acts", "url": "https://india-code.nic.in/", "type": "GoIWebsite", "accessed_date": "2026-05-14"}
    mh_path = DATA_DIR / "relationships" / "mh_relationships.yaml"
    ka_path = DATA_DIR / "relationships" / "ka_relationships.yaml"
    mh_rels = []
    for slug, _ in MH_NEW_DISTRICTS:
        eid = f"mh_district_court_{slug}"
        mh_rels.append(
            {
                "id": f"{eid}_appealable_hc_bombay",
                "source": eid,
                "target": "hc_bombay",
                "relationship_type": "AppealableTo",
                "relationship_category": "appellate_chain",
                "is_binding": True,
                "notes": "District court appeals to High Court",
                "data_quality": "partial",
                "sources": [anchor],
            }
        )
        mh_rels.append(
            {
                "id": f"hc_bombay_supervise_{eid}",
                "source": "hc_bombay",
                "target": eid,
                "relationship_type": "AdministrativeSupervision",
                "relationship_category": "supervisory",
                "is_binding": True,
                "notes": "Article 235 supervision",
                "data_quality": "partial",
                "sources": [anchor],
            }
        )
    ka_rels = []
    for slug, _ in KA_NEW_DISTRICTS:
        eid = f"ka_district_court_{slug}"
        ka_rels.append(
            {
                "id": f"{eid}_appealable_hc_karnataka",
                "source": eid,
                "target": "hc_karnataka",
                "relationship_type": "AppealableTo",
                "relationship_category": "appellate_chain",
                "is_binding": True,
                "notes": "District court appeals to High Court",
                "data_quality": "partial",
                "sources": [anchor],
            }
        )
        ka_rels.append(
            {
                "id": f"hc_karnataka_supervise_{eid}",
                "source": "hc_karnataka",
                "target": eid,
                "relationship_type": "AdministrativeSupervision",
                "relationship_category": "supervisory",
                "is_binding": True,
                "notes": "Article 235 supervision",
                "data_quality": "partial",
                "sources": [anchor],
            }
        )
    return _append_unique_relationships(mh_path, mh_rels), _append_unique_relationships(ka_path, ka_rels)


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge NJDG case_volume from graph.json into entity YAML")
    parser.add_argument("--snapshot", type=str, default=str(Path.home() / "Documents" / "jem_add1405" / "graph.json"))
    parser.add_argument("--plan", type=str, default=None, help="Write markdown plan to this path")
    parser.add_argument("--apply", action="store_true", help="Apply merges to YAML files")
    parser.add_argument("--bootstrap-districts", action="store_true", help="Create missing MH/KA district YAML + HC relationships")
    args = parser.parse_args()
    snap = Path(args.snapshot)
    if not snap.is_file():
        raise SystemExit(f"Snapshot not found: {snap}")

    if args.plan:
        plan_report(snap, Path(args.plan))

    if args.apply:
        n, errs = apply_merge(snap)
        print(f"Updated {n} entity YAML file(s) with case_volume from snapshot.")
        for e in errs[:20]:
            print("ERROR:", e)
        if len(errs) > 20:
            print(f"... and {len(errs)-20} more errors")

    if args.bootstrap_districts:
        mh_c, ka_c = bootstrap_district_files()
        mh_r, ka_r = bootstrap_hc_relationships()
        print(f"Bootstrap: created {mh_c} MH + {ka_c} KA district YAML files.")
        print(f"Bootstrap: appended {mh_r} MH + {ka_r} KA relationship rows.")

    if not args.plan and not args.apply and not args.bootstrap_districts:
        parser.print_help()


if __name__ == "__main__":
    main()
