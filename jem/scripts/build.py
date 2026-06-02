#!/usr/bin/env python3
"""
JEM — Build Script
Reads all validated YAML files, merges derived scores,
computes cluster aggregates and layout positions,
outputs the canonical graph at the repository root: ../graph.json (sibling of jem/).
The web app loads it via web/public/graph.json → symlink to that file.

Usage:
    python scripts/build.py
    python scripts/build.py --output /path/to/graph.json
    python scripts/build.py --no-derive    # Skip re-deriving scores
"""

import sys
import os
import json
import argparse
import yaml
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# ── Layout Engine ─────────────────────────────────────────────────────────────
# Level 0: fixed 4×4 cluster grid (see CLUSTER_GRID).
# Level 1: stable x,y per entity, distributed inside each cluster rectangle.

# Level 0: fixed 4×4 institutional tier grid (row 0 = apex, row 3 = ground).
# None marks an intentionally empty cell.
CLUSTER_GRID = (
    (
        "legislative_executive",
        "appointment_bodies",
        "constitutional_courts",
        "financing_audit",
    ),
    (
        "tribunals_adr",
        "regulatory_bodies",
        "consumer_redressal",
        "arbitration",
    ),
    (
        "subordinate_courts",
        "executive_interface",
        "security",
        "digital_infrastructure",
    ),
    (
        "training_professional",
        "people_roles",
        None,
        None,
    ),
)

CLUSTER_GRID_INDEX: Dict[str, tuple] = {}
for _row_i, _row in enumerate(CLUSTER_GRID):
    for _col_i, _cid in enumerate(_row):
        if _cid:
            CLUSTER_GRID_INDEX[_cid] = (_col_i, _row_i)

GRID_COLS = 4
GRID_ROWS = 4
CLUSTER_CELL_GAP_PX = 8

CLUSTER_COLORS = {
    "constitutional_courts":  "#1a365d",
    "subordinate_courts":     "#2c5282",
    "tribunals_adr":          "#2b6cb0",
    "arbitration":            "#3182ce",
    "regulatory_bodies":      "#4a235a",
    "consumer_redressal":     "#6b3480",
    "executive_interface":    "#742a2a",
    "digital_infrastructure": "#1a3a4a",
    "financing_audit":        "#1a3a2a",
    "training_professional":  "#1a2a3a",
    "appointment_bodies":     "#3d2b1f",
    "legislative_executive":  "#1f2d3d",
    "security":               "#6d4c41",
    "people_roles":           "#b8860b",
}

CANVAS_WIDTH = 1800
CANVAS_HEIGHT = 1200


def compute_browse_index(entities: List[Dict]) -> Dict[str, Dict[str, List[str]]]:
    """Facet groupings for Browse navigator mode."""
    clusters: Dict[str, List[str]] = {}
    types: Dict[str, List[str]] = {}
    states: Dict[str, List[str]] = {}
    for e in entities:
        eid = e.get("id")
        if not eid:
            continue
        c = e.get("cluster") or "other"
        clusters.setdefault(c, []).append(eid)
        t = e.get("type") or "Other"
        types.setdefault(t, []).append(eid)
        scope = (e.get("_detail") or {}).get("jurisdiction_scope") or e.get("jurisdiction_scope")
        if scope:
            states.setdefault(str(scope), []).append(eid)
    for bucket in (clusters, types, states):
        for key in bucket:
            bucket[key].sort()
    return {"clusters": clusters, "types": types, "states": states}


def compute_layout_positions(
    entities: List[Dict],
    cluster_positions: Dict[str, Dict],
) -> Dict[str, Dict]:
    """
    Assigns x, y coordinates to each entity for Level 1 display.
    Distributes members horizontally inside their cluster rectangle.
    """
    positions: Dict[str, Dict] = {}

    cluster_groups: Dict[str, List[Dict]] = {}
    for e in entities:
        c = e.get('cluster', 'constitutional_courts')
        cluster_groups.setdefault(c, []).append(e)

    for cluster, members in cluster_groups.items():
        box = cluster_positions.get(cluster)
        if not box:
            box = {
                'x': round(CANVAS_WIDTH / 2 - 100),
                'y': round(CANVAS_HEIGHT / 2 - 75),
                'width': 200,
                'height': 150,
            }
        n = len(members)
        if n == 0:
            continue

        margin_x = 28
        inner_left = box['x'] + margin_x
        inner_right = box['x'] + box['width'] - margin_x
        inner_w = max(1.0, inner_right - inner_left)
        cy = box['y'] + box['height'] * 0.52
        spacing = inner_w / (n + 1)

        for i, entity in enumerate(members):
            x = inner_left + spacing * (i + 1)
            y = cy + (18 if i % 2 == 0 else -18)
            positions[entity['id']] = {
                'x': round(x),
                'y': round(y),
            }

    return positions


def compute_cluster_positions(cluster_entities: Dict[str, List]) -> Dict[str, Dict]:
    """
    Level 0 cluster rectangles on a 4×4 grid.
    Each cell: width = canvas_width/4 - 20px, height = canvas_height/4 - 20px,
    with CLUSTER_CELL_GAP_PX between rectangles; grid centred on the canvas.
    """
    w_canvas = float(CANVAS_WIDTH)
    h_canvas = float(CANVAS_HEIGHT)
    rect_w = w_canvas / GRID_COLS - 20.0
    rect_h = h_canvas / GRID_ROWS - 20.0
    pitch_x = rect_w + CLUSTER_CELL_GAP_PX
    pitch_y = rect_h + CLUSTER_CELL_GAP_PX
    total_w = GRID_COLS * rect_w + (GRID_COLS - 1) * CLUSTER_CELL_GAP_PX
    total_h = GRID_ROWS * rect_h + (GRID_ROWS - 1) * CLUSTER_CELL_GAP_PX
    offset_x = (w_canvas - total_w) / 2.0
    offset_y = (h_canvas - total_h) / 2.0

    positions: Dict[str, Dict] = {}
    fallback_col, fallback_row = 2, 3  # first empty grid cell

    for cluster_id in cluster_entities.keys():
        idx = CLUSTER_GRID_INDEX.get(cluster_id)
        if idx is not None:
            col, row = idx
        else:
            col, row = fallback_col, fallback_row
        x = offset_x + col * pitch_x
        y = offset_y + row * pitch_y
        positions[cluster_id] = {
            'x': round(x),
            'y': round(y),
            'width': round(rect_w),
            'height': round(rect_h),
            'cluster_col': col,
            'cluster_row': row,
        }
    return positions


# ── Data Loading ──────────────────────────────────────────────────────────────

def load_yaml_file(path: Path) -> Optional[Any]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  WARNING: Could not load {path}: {e}")
        return None


def load_all_entities(data_dir: Path) -> List[Dict]:
    entities = []
    entities_dir = data_dir / "entities"
    roots = [entities_dir / "_generated", entities_dir]
    seen_ids: set = set()
    for root in roots:
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.yaml")):
            if "schema" in str(f) or "_TAXONOMY" in str(f) or "_curated" in str(f):
                continue
            data = load_yaml_file(f)
            if data and isinstance(data, dict) and "id" in data:
                eid = data["id"]
                if eid in seen_ids:
                    continue
                seen_ids.add(eid)
                entities.append(data)
    return entities


def load_all_relationships(data_dir: Path) -> List[Dict]:
    relationships = []
    rel_dir = data_dir / "relationships"
    if not rel_dir.exists():
        return relationships
    for f in sorted(rel_dir.glob("*.yaml")):
        data = load_yaml_file(f)
        if data and isinstance(data, dict):
            rels = data.get("relationships", [])
            if isinstance(rels, list):
                relationships.extend(rels)
    return relationships


def load_derived_scores(data_dir: Path) -> Dict[str, Dict]:
    scores_path = data_dir / "derived" / "scores.yaml"
    if not scores_path.exists():
        print("  INFO: No derived scores file found. Run scripts/derive.py first.")
        return {}
    data = load_yaml_file(scores_path)
    if data and isinstance(data, dict):
        return data.get('derived_scores', {})
    return {}


# ── Timeline Events ───────────────────────────────────────────────────────────

TIMELINE_EVENTS = [
    {"year": 1950, "label": "Constitution of India comes into force", "type": "constitutional"},
    {"year": 1958, "label": "Law Commission of India (1st)", "type": "reform"},
    {"year": 1963, "label": "CBI constituted", "type": "institutional"},
    {"year": 1976, "label": "42nd Amendment — tribunalisation", "type": "constitutional"},
    {"year": 1981, "label": "SP Gupta (First Judges Case) — executive primacy in appointments", "type": "judgment"},
    {"year": 1984, "label": "Family Courts Act", "type": "legislation"},
    {"year": 1991, "label": "ITAT established (antedated)", "type": "institutional"},
    {"year": 1993, "label": "Second Judges Case — Collegium system born", "type": "judgment"},
    {"year": 1996, "label": "Arbitration and Conciliation Act", "type": "legislation"},
    {"year": 1997, "label": "Vineet Narain — CBI 'caged parrot'", "type": "judgment"},
    {"year": 1998, "label": "Third Judges Case — Collegium expanded", "type": "judgment"},
    {"year": 1999, "label": "SC In-House Procedure for judge complaints", "type": "institutional"},
    {"year": 2002, "label": "PMLA enacted", "type": "legislation"},
    {"year": 2005, "label": "eCourts ICT Policy — e-Committee formed", "type": "digital"},
    {"year": 2010, "label": "NGT established; eCourts Phase I", "type": "institutional"},
    {"year": 2013, "label": "Lokpal and Lokayuktas Act", "type": "legislation"},
    {"year": 2014, "label": "99th Amendment — NJAC created", "type": "constitutional"},
    {"year": 2015, "label": "NJAC struck down; NCLT/NCLAT replace CLB/BIFR", "type": "judgment"},
    {"year": 2015, "label": "eCourts Phase II; A&C Amendment", "type": "digital"},
    {"year": 2016, "label": "IBC enacted — Insolvency & Bankruptcy Code", "type": "legislation"},
    {"year": 2019, "label": "ACI legislated (not constituted); J&K reorganisation", "type": "institutional"},
    {"year": 2020, "label": "Tribunals Reforms Act contested", "type": "legislation"},
    {"year": 2023, "label": "Mediation Act; BNS/BNSS/BSA replace IPC/CrPC/Evidence", "type": "legislation"},
    {"year": 2023, "label": "eCourts Phase III — ₹7210 crore; NJDG-SC launched", "type": "digital"},
    {"year": 2025, "label": "Lokpal jurisdiction over HC judges — SC stays order", "type": "judgment"},
]


# ── Impact Metrics ────────────────────────────────────────────────────────────

def compute_impact_metrics(entities: List[Dict], scores: Dict[str, Dict]) -> Dict:
    # Exclude placeholder nodes that exist only to render relationship endpoints.
    real_entities = [e for e in entities if not e.get("_placeholder")]
    high_ir = sum(1 for eid, s in scores.items()
                  if s.get('independence_risk_level') in ('high', 'severe'))

    # Appointer == funder == removal authority
    appointer_funder_same = 0
    for e in real_entities:
        appt = e.get('appointment') or {}
        funding = e.get('funding') or {}
        formally_appoints = appt.get('formally_appoints', '')
        removal = appt.get('removal_authority', '')
        ministry = funding.get('ministry_responsible', '')
        if formally_appoints and formally_appoints == removal == ministry:
            appointer_funder_same += 1

    no_public_criteria = sum(
        1 for e in real_entities
        if (e.get('appointment') or {}).get('criteria_public') == False
    )

    not_constituted = sum(
        1 for e in real_entities
        if e.get('operational_status') == 'Not_Constituted'
    )

    no_external_complaint = sum(
        1 for e in real_entities
        if not any(
            c.get('external_to_judiciary', False)
            for c in ((e.get('complaint_mechanism') or {}).get('bias_complaint_to') or [])
        )
    )

    return {
        "high_independence_risk_count": high_ir,
        "appointer_equals_funder_removal_count": appointer_funder_same,
        "no_public_appointment_criteria_count": no_public_criteria,
        "not_constituted_count": not_constituted,
        "no_external_complaint_mechanism_count": no_external_complaint,
    }


def _humanize_id(eid: str) -> str:
    return eid.replace('_', ' ').strip().title()


def add_placeholder_entities_for_relationships(entities: List[Dict], relationships: List[Dict]) -> List[Dict]:
    """
    The repo may contain relationship YAML referencing entities that are not
    present yet (data entry incomplete). The frontend cannot draw edges unless
    both endpoints exist in graph.entities.

    To preserve the "relationship map" behavior (like the inspiration app),
    we create lightweight placeholder entities for missing endpoints.
    """
    existing = {e.get("id") for e in entities if isinstance(e, dict) and e.get("id")}
    missing: Dict[str, Dict] = {}

    for r in relationships:
        s = r.get("source")
        t = r.get("target")
        for eid in (s, t):
            if not eid or eid in existing or eid in missing:
                continue
            missing[eid] = {
                "id": eid,
                "name": _humanize_id(eid),
                "name_hindi": None,
                "abbreviation": None,
                "aliases": [],
                "type": "ExecutiveBody",
                "cluster": "legislative_executive",
                "level_of_government": "Central",
                "jurisdiction_scope": {"is_all_india": True, "jurisdiction_types": []},
                "created_year": 1950,
                "abolished_year": None,
                "operational_status": "Active",
                "constitutional_basis": None,
                "statutory_basis": None,
                "appointment": None,
                "funding": None,
                "audit": None,
                "complaint_mechanism": None,
                "training": None,
                "digital_infrastructure": None,
                "structural_variations": [],
                "data_quality": "unverified",
                "data_quality_notes": "Placeholder node auto-created because relationships reference this entity id, but no entity YAML exists yet.",
                "sources": [],
                "_placeholder": True,
            }

    if missing:
        print(f"  INFO: Added {len(missing)} placeholder entities for relationship endpoints.")
        entities = entities + list(missing.values())
    return entities


# ── Main Build ────────────────────────────────────────────────────────────────

def build_graph_json(data_dir: Path, output_path: Path, no_derive: bool = False):
    print("\nJEM Build")
    print(f"{'='*50}")

    if not no_derive:
        print("\nStep 1: Running derive.py...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(data_dir.parent / "scripts" / "derive.py")],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  WARNING: derive.py had issues:\n{result.stderr}")
        else:
            print("  ✓ Scores derived")

    print("\nStep 2: Loading entities...")
    entities = load_all_entities(data_dir)
    print(f"  Loaded {len(entities)} entities")

    print("\nStep 3: Loading relationships...")
    relationships = load_all_relationships(data_dir)
    print(f"  Loaded {len(relationships)} relationships")

    # Ensure relationship endpoints exist so edges can render in the frontend.
    entities = add_placeholder_entities_for_relationships(entities, relationships)
    print(f"  Total entities after placeholders: {len(entities)}")

    print("\nStep 4: Loading derived scores...")
    scores = load_derived_scores(data_dir)
    print(f"  Loaded scores for {len(scores)} entities")

    print("\nStep 5: Merging scores into entities...")
    entity_lookup = {}
    for e in entities:
        eid = e['id']
        if eid in scores:
            e.setdefault('derived', {})
            e['derived'].update(scores[eid])
        entity_lookup[eid] = e

    print("\nStep 6: Computing cluster grid and entity layout positions...")
    cluster_entities: Dict[str, List] = {}
    for e in entities:
        c = e.get('cluster', 'constitutional_courts')
        cluster_entities.setdefault(c, []).append(e['id'])

    cluster_positions = compute_cluster_positions(cluster_entities)
    positions = compute_layout_positions(entities, cluster_positions)

    print("\nStep 7: Building cluster summaries...")
    clusters = []
    for cluster_id, member_ids in cluster_entities.items():
        members = [entity_lookup[eid] for eid in member_ids if eid in entity_lookup]
        member_scores = [scores.get(eid, {}) for eid in member_ids]
        ir_scores = [s.get('independence_risk_score', 0) for s in member_scores if s]
        avg_ir = round(sum(ir_scores) / len(ir_scores), 1) if ir_scores else 0

        not_const = sum(1 for e in members if e.get('operational_status') == 'Not_Constituted')

        clusters.append({
            "id": cluster_id,
            "name": cluster_id.replace('_', ' ').title(),
            "color": CLUSTER_COLORS.get(cluster_id, "#2d3436"),
            "entity_count": len(members),
            "avg_independence_risk": avg_ir,
            "not_constituted_count": not_const,
            "position": cluster_positions.get(
                cluster_id,
                {
                    "x": 0,
                    "y": 0,
                    "width": 200,
                    "height": 150,
                    "cluster_col": 0,
                    "cluster_row": 0,
                },
            ),
        })

    print("\nStep 8: Computing impact metrics...")
    impact = compute_impact_metrics(entities, scores)

    print("\nStep 9: Serialising entities for frontend...")
    # Strip large internal fields not needed by renderer
    frontend_entities = []
    for e in entities:
        fe = {
            "id": e.get("id"),
            "name": e.get("name"),
            "aliases": e.get("aliases", []),
            "jurisdiction_scope": e.get("jurisdiction_scope"),
            "name_hindi": e.get("name_hindi"),
            "abbreviation": e.get("abbreviation"),
            "type": e.get("type"),
            "cluster": e.get("cluster"),
            "level_of_government": e.get("level_of_government"),
            "created_year": e.get("created_year"),
            "abolished_year": e.get("abolished_year"),
            "operational_status": e.get("operational_status"),
            "constitutional_basis": e.get("constitutional_basis"),
            "statutory_basis": e.get("statutory_basis"),
            "data_quality": e.get("data_quality"),
            "data_quality_notes": e.get("data_quality_notes"),
            "derived": e.get("derived", {}),
            "funding_source": (e.get("funding") or {}).get("primary_source"),
            "funding_ministry": (e.get("funding") or {}).get("ministry_responsible"),
            "audited_by": (e.get("audit") or {}).get("audited_by"),
            "audit_report_public": (e.get("audit") or {}).get("audit_report_public"),
            "complaint_external_exists": any(
                c.get("external_to_judiciary", False)
                for c in ((e.get("complaint_mechanism") or {}).get("bias_complaint_to") or [])
            ),
            "appointment_criteria_public": (e.get("appointment") or {}).get("criteria_public"),
            "reappointment_possible": (e.get("appointment") or {}).get("reappointment_possible"),
            "sources": e.get("sources", []),
            # Full detail fields (used in Level 3 detail panel)
            "_detail": {
                "appointment": e.get("appointment"),
                "funding": e.get("funding"),
                "audit": e.get("audit"),
                "complaint_mechanism": e.get("complaint_mechanism"),
                "training": e.get("training"),
                "digital_infrastructure": e.get("digital_infrastructure"),
                "structural_variations": e.get("structural_variations", []),
                "jurisdiction_scope": e.get("jurisdiction_scope"),
                "case_volume": e.get("case_volume"),
                "judge_strength": e.get("judge_strength"),
                "parent_hc": e.get("parent_hc"),
            },
            "position": positions.get(e["id"], {"x": 0, "y": 0}),
        }
        # Gap / health fields (schema v1.3) for Gaps mode, detail panel, reports
        if e.get("gap_flag") is not None:
            fe["gap_flag"] = e.get("gap_flag")
        if e.get("gap_count") is not None:
            fe["gap_count"] = e.get("gap_count")
        gaps = e.get("gaps") or e.get("structural_gap")
        if gaps:
            fe["gaps"] = gaps if isinstance(gaps, list) else [gaps]
        if e.get("structural_exception"):
            fe["structural_exception"] = True
        if e.get("circularity_score") is not None:
            fe["circularity_score"] = e.get("circularity_score")
        if e.get("appellate_health"):
            fe["appellate_health"] = e.get("appellate_health")
        if e.get("appellate_functional") is not None:
            fe["appellate_functional"] = e.get("appellate_functional")
        if e.get("structural_health_score") is not None:
            fe["structural_health_score"] = e.get("structural_health_score")
        frontend_entities.append(fe)

    print("\nStep 10: Serialising relationships...")
    frontend_relationships = []
    for r in relationships:
        fr = {
            "id": r.get("id"),
            "source": r.get("source"),
            "target": r.get("target"),
            "relationship_type": r.get("relationship_type"),
            "relationship_category": r.get("relationship_category"),
            "is_binding": r.get("is_binding"),
            "is_constitutional": r.get("is_constitutional"),
            "year_established": r.get("year_established"),
            "year_abolished": r.get("year_abolished"),
            "data_quality": r.get("data_quality"),
            "contested_note": r.get("contested_note"),
            "notes": r.get("notes"),
            "sources": r.get("sources", []),
        }
        frontend_relationships.append(fr)

    # ── Step 10b: Backfill missing District Court → High Court edges ─────────
    # 184 subordinate-court entities exist; ~half lack an explicit AppealableTo
    # relationship in the YAML. Infer the parent HC from the state-code prefix
    # in the entity id so the graph is structurally complete. These are tagged
    # data_quality: "inferred" so they're visually distinct from curated edges.
    STATE_CODE_TO_HC = {
        "an": "hc_calcutta", "ap": "hc_andhra_pradesh", "ar": "hc_gauhati",
        "as": "hc_gauhati", "br": "hc_patna", "ch": "hc_punjab_haryana",
        "cg": "hc_chhattisgarh", "dd": "hc_bombay", "dl": "hc_delhi",
        "ga": "hc_bombay", "gj": "hc_gujarat", "hr": "hc_punjab_haryana",
        "hp": "hc_himachal_pradesh", "jk": "hc_jammu_kashmir_ladakh",
        "jh": "hc_jharkhand", "ka": "hc_karnataka", "kl": "hc_kerala",
        "la": "hc_jammu_kashmir_ladakh", "ld": "hc_kerala",
        "mp": "hc_madhya_pradesh", "mh": "hc_bombay", "mn": "hc_manipur",
        "ml": "hc_meghalaya", "mz": "hc_gauhati", "nl": "hc_gauhati",
        "or": "hc_orissa", "od": "hc_orissa", "py": "hc_madras",
        "pb": "hc_punjab_haryana", "rj": "hc_rajasthan", "sk": "hc_sikkim",
        "tn": "hc_madras", "tg": "hc_telangana", "ts": "hc_telangana",
        "tr": "hc_tripura",
        "up": "hc_allahabad", "uk": "hc_uttarakhand", "wb": "hc_calcutta",
    }
    SUBORDINATE_TYPES = {
        "SubordinateCivilCourt", "SubordinateCriminalCourt", "CityCivilCourt",
        "SpecialCourt", "FastTrackCourt", "FamilyCourt", "CommercialCourt",
        "RevenueCourt",
    }
    entity_ids = {e["id"] for e in frontend_entities}
    has_appellate_parent = set()
    for r in frontend_relationships:
        if r.get("relationship_category") == "appellate_chain":
            has_appellate_parent.add(r["source"])

    inferred = 0
    for e in frontend_entities:
        if e.get("type") not in SUBORDINATE_TYPES:
            continue
        eid = e["id"]
        if eid in has_appellate_parent:
            continue
        # Use jurisdiction_scope.states_covered first; fall back to id prefix.
        scope = (e.get("_detail") or {}).get("jurisdiction_scope") or {}
        states = scope.get("states_covered") or []
        target_hc = None
        if states:
            target_hc = STATE_CODE_TO_HC.get(states[0].lower())
        if not target_hc:
            prefix = eid.split("_", 1)[0].lower()
            target_hc = STATE_CODE_TO_HC.get(prefix)
        if not target_hc or target_hc not in entity_ids:
            continue
        frontend_relationships.append({
            "id": f"inferred_appellate_{eid}",
            "source": eid,
            "target": target_hc,
            "relationship_type": "AppealableTo",
            "relationship_category": "appellate_chain",
            "is_binding": True,
            "is_constitutional": False,
            "year_established": None,
            "year_abolished": None,
            "data_quality": "inferred",
            "contested_note": None,
            "notes": "Edge inferred at build time from entity id / state code; not present in relationships YAML",
            "sources": [],
        })
        inferred += 1
    print(f"  Backfilled {inferred} District Court → HC edges (data_quality=inferred)")

    print("\nStep 11: Building browse index...")
    browse_index = compute_browse_index(frontend_entities)

    print("\nStep 12: Assembling final graph.json...")
    graph = {
        "meta": {
            "version": "1.0.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "entity_count": len(frontend_entities),
            "relationship_count": len(frontend_relationships),
            "canvas_width": CANVAS_WIDTH,
            "canvas_height": CANVAS_HEIGHT,
            "year_range": [1950, datetime.now().year],
        },
        "impact_metrics": impact,
        "timeline_events": TIMELINE_EVENTS,
        "clusters": clusters,
        "entities": frontend_entities,
        "relationships": frontend_relationships,
        "browse_index": browse_index,
        "data_quality_legend": {
            "verified":    {"font_weight": "700", "color": "#000000", "border": "solid",  "opacity": 1.0,  "badge": None},
            "complete":    {"font_weight": "400", "color": "#000000", "border": "solid",  "opacity": 1.0,  "badge": None},
            "partial":     {"font_weight": "400", "color": "#555555", "border": "solid",  "opacity": 0.85, "badge": "?",   "italic": True},
            "unverified":  {"font_weight": "400", "color": "#999999", "border": "dashed", "opacity": 0.70, "badge": None,  "italic": True},
            "contested":   {"font_weight": "400", "color": "#c0392b", "border": "dashed", "opacity": 0.85, "badge": "⚑",  "italic": True, "underline": "dotted"},
        },
        "operational_status_legend": {
            "Active":           {"node_stroke": "solid",  "node_opacity": 1.0},
            "Not_Constituted":  {"node_stroke": "dashed", "node_opacity": 0.80, "label_style": "italic"},
            "Proposed":         {"node_stroke": "dotted", "node_opacity": 0.65, "label_style": "italic"},
            "Abolished":        {"node_stroke": "solid",  "node_opacity": 0.25, "label_style": "line-through"},
            "Merged":           {"node_stroke": "solid",  "node_opacity": 0.25, "label_style": "line-through"},
            "Suspended":        {"node_stroke": "dashed", "node_opacity": 0.60},
        },
        "relationship_colors": {
            "appointment":     "#e67e22",
            "funding":         "#27ae60",
            "appellate_chain": "#2c3e50",
            "supervisory":     "#8e44ad",
            "training":        "#16a085",
            "audit":           "#7f8c8d",
            "complaint":       "#e74c3c",
            "investigative":   "#c0392b",
            "digital":         "#2980b9",
            "security":        "#6d4c41",
            "statutory_ref":   "#bdc3c7",
        },
        "independence_risk_colors": {
            "low":      "#27ae60",
            "moderate": "#f39c12",
            "high":     "#e74c3c",
            "severe":   "#8e44ad",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(graph, f, ensure_ascii=False, indent=2, default=str)

    size_kb = output_path.stat().st_size / 1024
    print(f"\n  ✓ Written to {output_path}")
    print(f"  ✓ File size: {size_kb:.1f} KB")
    print(f"\n{'='*50}")
    print("Build complete.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JEM build")
    parser.add_argument("--output", type=str, default=None,
                        help="Output path for graph.json (default: <repo>/graph.json)")
    parser.add_argument("--no-derive", action="store_true",
                        help="Skip re-running derive.py (use existing scores)")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"

    if args.output:
        output_path = Path(args.output)
    else:
        # Repo root: …/<repository>/graph.json when this script lives in …/<repository>/jem/scripts/
        output_path = script_dir.parent.parent / "graph.json"

    build_graph_json(data_dir, output_path, no_derive=args.no_derive)
