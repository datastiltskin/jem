#!/usr/bin/env python3
"""
JEM — Score Derivation Script
Computes independence_risk_score and discretionary_power_score
for every entity from their structural data attributes.

Scores are DERIVED — not editorially assigned.
Every point is traceable to a data field.
Unvalidated scores display with "Pending review" badge in UI.

Usage:
    python scripts/derive.py
    python scripts/derive.py --entity supreme_court_india
    python scripts/derive.py --explain supreme_court_india
"""

import sys
import os
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


# ── Independence Risk Formula ─────────────────────────────────────────────────
#
# Higher score = higher structural independence risk.
# This is a STRUCTURAL indicator derived from data fields.
# It does NOT indicate actual misconduct.
# Scores are labelled "Pending community review" until validated == true.
#
# SCALE: 0–2 Low | 3–5 Moderate | 6–8 High | 9+ Severe

def compute_independence_risk(entity: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
    """
    Returns (total_score, breakdown_dict).
    Each key in breakdown_dict is a human-readable reason → point value.
    """
    score = 0
    breakdown = {}

    appt = entity.get('appointment') or {}
    funding = entity.get('funding') or {}
    audit = entity.get('audit') or {}
    complaint = entity.get('complaint_mechanism') or {}
    op_status = entity.get('operational_status', '')
    entity_type = entity.get('type', '')

    # ── Appointment factors ───────────────────────────────

    formally_appoints = appt.get('formally_appoints', '')
    nominates = appt.get('nominates', '')
    removal_authority = appt.get('removal_authority', '')
    reappoint = appt.get('reappointment_possible', False)
    criteria_public = appt.get('criteria_public', True)
    consultation_binding = appt.get('consultation_binding', False)
    removal_independent = appt.get('removal_independent_committee', False)
    removal_parliament = appt.get('removal_requires_parliament', False)

    EXECUTIVE_BODIES = [
        'central_government', 'president_india', 'governor_state',
        'ministry_law_justice', 'ministry_of_finance', 'ministry_personnel_dopt',
        'dopt_dpc', 'state_government', 'state_home_department'
    ]

    if formally_appoints in EXECUTIVE_BODIES:
        score += 3
        breakdown['Appointed directly by executive body'] = 3
    elif formally_appoints and 'collegium' in formally_appoints.lower():
        score -= 2
        breakdown['Appointed by independent collegium (deduction)'] = -2
    elif formally_appoints and 'parliament' in formally_appoints.lower():
        score -= 1
        breakdown['Appointment via Parliament process (deduction)'] = -1

    if reappoint and formally_appoints in EXECUTIVE_BODIES:
        score += 2
        breakdown['Reappointment possible by same executive authority'] = 2

    if not criteria_public:
        score += 1
        breakdown['No publicly stated appointment criteria'] = 1

    if removal_authority in EXECUTIVE_BODIES and not removal_independent and not removal_parliament:
        score += 1
        breakdown['Removal by same authority that appoints (no independent committee)'] = 1

    if removal_parliament:
        score -= 1
        breakdown['Removal requires Parliamentary process (deduction)'] = -1

    # ── Funding factors ───────────────────────────────────

    funding_source = funding.get('primary_source', '')
    funding_ministry = funding.get('ministry_responsible', '')

    if funding_source in ['Ministry_Budget'] and formally_appoints in EXECUTIVE_BODIES:
        score += 2
        breakdown['Funder == Appointing authority'] = 2

    if funding_source == 'Party_Fees':
        score -= 1
        breakdown['Funded by parties (not state) — reduces executive dependency (deduction)'] = -1

    # ── Audit factors ─────────────────────────────────────

    audit_type = audit.get('audit_type', '')
    conduct_body = audit.get('conduct_oversight_body', '')
    audit_public = audit.get('audit_report_public', False)

    if audit_type in ['None', ''] or audit_type is None:
        score += 1
        breakdown['No external financial audit'] = 1

    if not conduct_body:
        score += 1
        breakdown['No independent conduct oversight body'] = 1

    if conduct_body and conduct_body == entity.get('id', ''):
        score += 1
        breakdown['Conduct oversight body is the entity itself (self-policing)'] = 1

    if not audit_public:
        score += 1
        breakdown['Audit reports not public'] = 1

    # ── Complaint mechanism factors ───────────────────────

    complaints = complaint.get('bias_complaint_to', []) or []
    external_complaints = [c for c in complaints if c.get('external_to_judiciary', False)]
    lokpal = complaint.get('lokpal_jurisdiction', 'No')

    if not complaints:
        score += 2
        breakdown['No bias complaint mechanism exists'] = 2
    elif not external_complaints:
        score += 1
        breakdown['All complaint mechanisms are internal (no external body)'] = 1

    has_public_process = any(c.get('is_public_process', False) for c in complaints)
    if complaints and not has_public_process:
        score += 1
        breakdown['Complaint process is not public/transparent'] = 1

    has_locus = any(c.get('complainant_has_locus', False) for c in complaints)
    if complaints and not has_locus:
        score += 1
        breakdown['Complainant has no locus in the inquiry process'] = 1

    has_timeframe = any(c.get('timeframe_defined', False) for c in complaints)
    if complaints and not has_timeframe:
        score += 1
        breakdown['No defined timeframe for complaint resolution'] = 1

    if lokpal == 'No':
        score += 1
        breakdown['Lokpal has no jurisdiction'] = 1
    elif lokpal == 'Contested':
        breakdown['Lokpal jurisdiction contested — active litigation'] = 0

    # ── Constitutional basis factor ───────────────────────

    const_basis = entity.get('constitutional_basis', '')
    if const_basis:
        score -= 2
        breakdown['Constitutional basis (harder to politicise) (deduction)'] = -2

    # ── Not constituted / proposed factor ─────────────────
    # A body that is mandated but not set up represents
    # a governance gap — score the vacuum, not the entity

    if op_status == 'Not_Constituted':
        score += 3
        breakdown['Statutory body not constituted — regulatory vacuum'] = 3

    return max(0, score), breakdown


# ── Discretionary Power Formula ───────────────────────────────────────────────
#
# Higher score = more concentrated discretionary power.
# Discretionary power is not inherently bad — it is a structural fact.
# Combined with high independence risk, it is a systemic concern.
#
# SCALE: 0–2 Low | 3–5 Moderate | 6–8 High | 9+ Very High

DISCRETIONARY_INDICATORS = {
    # From type
    'ConstitutionalCourt': 4,
    'HighCourtBench': 4,
    'SubordinateCriminalCourt': 3,    # Bail, remand — wide discretion
    'SubordinateCivilCourt': 2,
    'SpecialCourt': 2,
    'CentralTribunal': 2,
    'RegulatoryBodyQJ': 3,            # Both regulates AND adjudicates
    'InvestigativeAgency': 3,         # Prosecutorial discretion
    'AppointmentBody': 4,             # Decides who becomes judge
    'ArbitralInstitution': 1,
    'AuditBody': 2,
}

EXTRA_DISCRETION_ENTITIES = {
    # Specific entities with documented extra-statutory discretion
    'supreme_court_india': 5,         # Master of Roster, PIL, suo moto, contempt
    'chief_justice_india': 5,         # Master of Roster — no codified rules
    'collegium_sc': 5,                # Entirely opaque, no statutory criteria
}

def compute_discretionary_power(entity: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
    score = 0
    breakdown = {}

    entity_id = entity.get('id', '')
    entity_type = entity.get('type', '')
    appt = entity.get('appointment') or {}
    const_basis = entity.get('constitutional_basis', '')

    # Base from entity type
    type_score = DISCRETIONARY_INDICATORS.get(entity_type, 1)
    if type_score:
        score += type_score
        breakdown[f'Base discretionary power for type {entity_type}'] = type_score

    # Entity-specific extra discretion
    extra = EXTRA_DISCRETION_ENTITIES.get(entity_id, 0)
    if extra:
        score += extra
        breakdown[f'Entity-specific documented extra-statutory discretion'] = extra

    # No publicly stated criteria for decisions
    if not appt.get('criteria_public', True):
        score += 1
        breakdown['No public criteria for key decisions'] = 1

    # Can remove others
    if appt.get('removal_authority'):
        score += 1
        breakdown['Has removal authority over other entities'] = 1

    # Controls own case listing (documented for SC/HCs via roster)
    if entity_type in ('ConstitutionalCourt', 'HighCourtBench'):
        score += 2
        breakdown['Controls own case listing and bench composition (no statutory rule)'] = 2

    # No mandatory timeline for decisions
    score += 1
    breakdown['No universal mandatory timeline for all decisions'] = 1

    return score, breakdown


# ── File Processing ───────────────────────────────────────────────────────────

def load_entity(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"  WARNING: Could not load {path}: {e}")
        return None


def derive_scores_for_all(data_dir: Path) -> Dict[str, Dict]:
    """Returns dict of entity_id -> derived scores."""
    results = {}
    entity_files = list((data_dir / "entities").rglob("*.yaml"))

    for f in sorted(entity_files):
        if 'schema' in str(f) or '_TAXONOMY' in str(f):
            continue
        entity = load_entity(f)
        if not entity:
            continue

        entity_id = entity.get('id')
        if not entity_id:
            print(f"  WARNING: No 'id' field in {f.name}")
            continue

        ir_score, ir_breakdown = compute_independence_risk(entity)
        dp_score, dp_breakdown = compute_discretionary_power(entity)

        results[entity_id] = {
            'independence_risk_score': ir_score,
            'independence_risk_breakdown': ir_breakdown,
            'independence_risk_level': classify_ir(ir_score),
            'discretionary_power_score': dp_score,
            'discretionary_power_breakdown': dp_breakdown,
            'scores_validated': entity.get('derived', {}).get('scores_validated', False) if entity.get('derived') else False
        }

    return results


def classify_ir(score: int) -> str:
    if score <= 2:
        return "low"
    elif score <= 5:
        return "moderate"
    elif score <= 8:
        return "high"
    else:
        return "severe"


def save_derived_scores(results: Dict, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump({'derived_scores': results}, f, default_flow_style=False, allow_unicode=True)
    print(f"  Saved derived scores to {output_path}")


def explain_entity(entity_id: str, data_dir: Path):
    """Print detailed explanation of scores for one entity."""
    entity_files = list((data_dir / "entities").rglob("*.yaml"))
    for f in entity_files:
        entity = load_entity(f)
        if entity and entity.get('id') == entity_id:
            ir_score, ir_bd = compute_independence_risk(entity)
            dp_score, dp_bd = compute_discretionary_power(entity)

            print(f"\n{'='*60}")
            print(f"Score Explanation: {entity.get('name', entity_id)}")
            print(f"{'='*60}")
            print(f"\nINDEPENDENCE RISK SCORE: {ir_score} ({classify_ir(ir_score).upper()})")
            print("Breakdown:")
            for reason, pts in sorted(ir_bd.items(), key=lambda x: -x[1]):
                sign = "+" if pts >= 0 else ""
                print(f"  {sign}{pts:+3d}  {reason}")

            print(f"\nDISCRETIONARY POWER SCORE: {dp_score}")
            print("Breakdown:")
            for reason, pts in sorted(dp_bd.items(), key=lambda x: -x[1]):
                print(f"  +{pts:3d}  {reason}")
            print()
            return

    print(f"Entity '{entity_id}' not found.")


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JEM score derivation")
    parser.add_argument("--explain", type=str, default=None,
                        help="Print detailed score explanation for one entity ID")
    parser.add_argument("--entity", type=str, default=None,
                        help="Derive scores for one entity only")
    args = parser.parse_args()

    script_dir = Path(__file__).parent
    data_dir = script_dir.parent / "data"
    output_path = data_dir / "derived" / "scores.yaml"

    if args.explain:
        explain_entity(args.explain, data_dir)
        sys.exit(0)

    print("\nJEM — Deriving structural scores...")
    results = derive_scores_for_all(data_dir)

    print(f"\nProcessed {len(results)} entities:")
    for eid, r in sorted(results.items()):
        ir = r['independence_risk_score']
        dp = r['discretionary_power_score']
        level = r['independence_risk_level']
        validated = "✓" if r['scores_validated'] else "⚐"
        print(f"  {validated} {eid:45s} IR={ir:2d} ({level:8s}) DP={dp:2d}")

    save_derived_scores(results, output_path)

    high_ir = [(eid, r) for eid, r in results.items() if r['independence_risk_level'] in ('high', 'severe')]
    not_constituted = [(eid, r) for eid, r in results.items() if r['independence_risk_score'] >= 3 and 'regulatory vacuum' in str(r.get('independence_risk_breakdown', {}))]

    print(f"\n--- IMPACT METRICS ---")
    print(f"  High/Severe independence risk:  {len(high_ir)} entities")
    print(f"  Not constituted (regulatory gaps): {len(not_constituted)} entities")
    print(f"\n✓ Done")
