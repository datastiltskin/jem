#!/usr/bin/env python3
"""
Emit JEM v1 state/regulatory YAML (25 HCs, MH/DL/KA/TN/PY packs, light states/UTs, RERA, SERC, backbone stubs).
Run from repo:  python jem/scripts/generate_v1_states_bundle.py
Idempotent: overwrites files under jem/data/entities/_generated/ and relationship YAML under jem/data/relationships/.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml

from hc_benches_config import (
    HC_BENCHES_DEF,
    KA_DISTRICT_TO_BENCH,
    MH_DISTRICT_TO_BENCH,
    RJ_DISTRICT_TO_BENCH,
    TN_DISTRICT_TO_BENCH,
    UP_DISTRICT_TO_BENCH,
    WB_DISTRICT_TO_BENCH,
)

ROOT = Path(__file__).resolve().parents[1]  # jem/
ENT = ROOT / "data" / "entities" / "_generated"
REL = ROOT / "data" / "relationships"
SEEDS_ENT = ROOT / "data" / "seeds" / "entities"
SEEDS_REL = ROOT / "data" / "seeds" / "relationships"

SRC = {
    "label": "India Code — Constitution & Acts",
    "url": "https://india-code.nic.in/",
    "type": "GoIWebsite",
    "accessed_date": "2026-05-13",
}
SRC_SC = {
    "label": "Supreme Court of India",
    "url": "https://main.sci.gov.in/",
    "type": "GoIWebsite",
    "accessed_date": "2026-05-13",
}

# Tamil Nadu — 38 revenue districts (full lattice; no aggregate generic court).
TN_DISTRICT_LATTICE: list[tuple[str, str]] = [
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


_WRITE_ENTITIES = True


def _seed_entity_path(generated_path: Path) -> Path:
    return SEEDS_ENT / generated_path.relative_to(ENT)


def W(path: Path, doc: dict) -> None:
    if not _WRITE_ENTITIES:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    seed = _seed_entity_path(path)
    if seed.is_file():
        shutil.copy2(seed, path)
        return
    with open(path, "w", encoding="utf-8") as f:
        f.write("# JEM generated bundle — data_quality: partial; expand sources per CONTRIBUTING.md\n")
        yaml.safe_dump(doc, f, sort_keys=False, allow_unicode=True, default_flow_style=False)


def stub_exec(
    eid: str,
    name: str,
    cluster: str = "legislative_executive",
    level: str = "Central",
    year: int = 1950,
) -> dict:
    return {
        "id": eid,
        "name": name,
        "type": "ExecutiveBody",
        "cluster": cluster,
        "level_of_government": level,
        "jurisdiction_scope": {"is_all_india": level == "Central"},
        "created_year": year,
        "operational_status": "Active",
        "data_quality": "partial",
        "data_quality_notes": "Stub for graph connectivity; verify appointment/funding against primary sources.",
        "sources": [SRC],
    }


def stub_appointment(eid: str, name: str) -> dict:
    return {
        "id": eid,
        "name": name,
        "type": "AppointmentBody",
        "cluster": "appointment_bodies",
        "level_of_government": "Central",
        "jurisdiction_scope": {"is_all_india": True},
        "created_year": 1950,
        "operational_status": "Active",
        "data_quality": "partial",
        "data_quality_notes": "Stub; collegium composition per constitutional practice.",
        "sources": [SRC, SRC_SC],
    }


def judge_strength_stub() -> dict:
    """v2.0 placeholder — allotted (sanctioned) / appointed (working) from DoJ or NJDG."""
    return {
        "data_as_of": None,
        "allotted": None,
        "appointed": None,
        "source_type": "DoJ_Report",
        "source_url": "https://doj.gov.in/",
        "notes": "Allotted = sanctioned posts; appointed = working judges in post. Populate from DoJ quarterly vacancy report or NJDG bench strength.",
    }


def bench_judge_strength_stub(parent_hc: str) -> dict:
    """HighCourtBench — sanctioned strength lives on parent HC only."""
    return {
        "allotted": None,
        "appointed": None,
        "source_type": "HC_Report",
        "notes": (
            f"Judges are drawn from parent HC pool ({parent_hc}). Allotted is null "
            "— sanctioned strength is set at parent HC level only."
        ),
    }


def with_court_judge_strength(doc: dict) -> dict:
    """Attach judge_strength to court / court-like entities."""
    t = doc.get("type")
    if t in (
        "ConstitutionalCourt",
        "HighCourtBench",
        "SubordinateCivilCourt",
        "SubordinateCriminalCourt",
        "CityCivilCourt",
        "SpecialCourt",
        "CentralTribunal",
        "StateTribunal",
        "ConsumerCommission",
    ):
        doc = {**doc, "judge_strength": judge_strength_stub()}
    return doc


def hc(
    eid: str,
    name: str,
    states: list[str],
    gov_level: str = "State",
    created_year: int = 1948,
) -> dict:
    doc = {
        "id": eid,
        "name": name,
        "abbreviation": eid.replace("hc_", "").upper()[:4],
        "type": "ConstitutionalCourt",
        "cluster": "constitutional_courts",
        "level_of_government": gov_level,
        "jurisdiction_scope": {
            "states_covered": [s for s in states if s not in {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}],
            "uts_covered": [s for s in states if s in {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}],
            "is_all_india": False,
            "jurisdiction_types": ["Original", "Appellate", "Writ"],
        },
        "created_year": created_year,
        "operational_status": "Active",
        "constitutional_basis": "Constitution of India, Chapter VI — High Courts in the States",
        "statutory_basis": None,
        "appointment": {
            "nominates": "collegium_hc_appointment",
            "recommends": "collegium_hc_appointment",
            "consulted": ["governor_state"],
            "consultation_binding": True,
            "formally_appoints": "president_india",
            "criteria_public": False,
            "tenure": "Until age 62 (Article 217)",
            "reappointment_possible": False,
            "removal_authority": "president_india",
            "removal_requires_parliament": True,
            "removal_independent_committee": False,
        },
        "funding": {
            "primary_source": "State_Consolidated_Fund",
            "ministry_responsible": None,
            "budget_figure_crore": None,
            "budget_year": None,
        },
        "audit": {
            "audited_by": "cag_india",
            "audit_type": "CAG_Statutory",
            "audit_report_public": True,
            "conduct_oversight_body": None,
        },
        "complaint_mechanism": {
            "bias_complaint_to": [],
            "lokpal_jurisdiction": "Not_Applicable",
        },
        "training": {
            "trained_by": [],
            "induction_training": False,
            "continuing_education": True,
            "training_mandatory": False,
        },
        "digital_infrastructure": {
            "system_used": ["eCourts_Portal", "NJDG"],
            "digital_variant": "NIC_Standard",
            "integrated_with_njdg": True,
        },
        "structural_variations": [],
        "data_quality": "partial",
        "data_quality_notes": "Pending NJDG-backed pendency and judge_strength fields per bench.",
        "sources": [SRC, SRC_SC],
    }
    return with_court_judge_strength(doc)


def hc_bench(
    eid: str,
    name: str,
    parent_hc: str,
    seat_city: str,
    states: list[str],
    created_year: int = 1948,
) -> dict:
    """Permanent bench of a High Court (distinct from district courts in the same city)."""
    base = hc(eid, name, states, "State", created_year)
    doc = {k: v for k, v in base.items() if k != "judge_strength"}
    doc["type"] = "HighCourtBench"
    doc["parent_hc"] = parent_hc
    doc["seat_city"] = seat_city
    doc["data_quality_notes"] = (
        f"Permanent bench at {seat_city}; parent {parent_hc}. "
        "Populate case_volume from HC website / NJDG; bench judge_strength uses HC_Report stub."
    )
    doc["judge_strength"] = bench_judge_strength_stub(parent_hc)
    return doc


def regulatory_state(
    eid: str,
    name: str,
    state: str,
    year: int,
    statute: str,
) -> dict:
    uts = {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}
    lvl = "UT" if state in uts else "State"
    return {
        "id": eid,
        "name": name,
        "type": "RegulatoryBodyQJ",
        "cluster": "regulatory_bodies",
        "level_of_government": lvl,
        "jurisdiction_scope": (
            {"uts_covered": [state], "is_all_india": False, "jurisdiction_types": ["Civil"]}
            if state in uts
            else {"states_covered": [state], "is_all_india": False, "jurisdiction_types": ["Civil"]}
        ),
        "created_year": year,
        "operational_status": "Active",
        "statutory_basis": statute,
        "funding": {
            "primary_source": "State_Consolidated_Fund",
            "ministry_responsible": None,
        },
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def consumer_comm(eid: str, name: str, state: str, level_gov: str) -> dict:
    ut_codes = {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}
    js = (
        {"uts_covered": [state], "is_all_india": False}
        if state in ut_codes
        else {"states_covered": [state] if state != "IN" else [], "is_all_india": state == "IN"}
    )
    return {
        "id": eid,
        "name": name,
        "type": "ConsumerCommission",
        "cluster": "tribunals_adr",
        "level_of_government": level_gov,
        "jurisdiction_scope": js,
        "created_year": 2019,
        "operational_status": "Active",
        "statutory_basis": "Consumer Protection Act 2019 — State / District commissions",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def district_court(eid: str, name: str, state: str) -> dict:
    ut_codes = {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}
    lvl = "UT" if state in ut_codes else "State"
    js = (
        {"uts_covered": [state], "is_all_india": False, "jurisdiction_types": ["Civil", "Criminal"]}
        if state in ut_codes
        else {"states_covered": [state], "is_all_india": False, "jurisdiction_types": ["Civil", "Criminal"]}
    )
    doc = {
        "id": eid,
        "name": name,
        "type": "SubordinateCivilCourt",
        "cluster": "subordinate_courts",
        "level_of_government": lvl,
        "jurisdiction_scope": js,
        "created_year": 1860,
        "operational_status": "Active",
        "constitutional_basis": "Constitution of India, Articles 233–237",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "data_quality_notes": "Pendency and judge_strength TBD from NJDG district dashboard.",
        "sources": [SRC],
    }
    return with_court_judge_strength(doc)


def city_civil(eid: str, name: str, state: str) -> dict:
    d = district_court(eid, name, state)
    d["type"] = "CityCivilCourt"
    d["statutory_basis"] = "State enactments / Letters Patent — city civil court jurisdictions"
    return d


def special_courts_bundle(eid: str, name: str, state: str) -> dict:
    d = district_court(eid, name, state)
    d["type"] = "SpecialCourt"
    d["statutory_basis"] = "PMLA, POCSO, NIA, SC/ST Acts — special court pools (aggregated node)"
    return d


def slsa(eid: str, name: str, state: str) -> dict:
    ut_codes = {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}
    lvl = "UT" if state in ut_codes else "State"
    js = (
        {"uts_covered": [state], "is_all_india": False, "jurisdiction_types": ["Civil"]}
        if state in ut_codes
        else {"states_covered": [state], "is_all_india": False, "jurisdiction_types": ["Civil"]}
    )
    return {
        "id": eid,
        "name": name,
        "type": "ADRBody",
        "cluster": "tribunals_adr",
        "level_of_government": lvl,
        "jurisdiction_scope": js,
        "created_year": 1995,
        "operational_status": "Active",
        "statutory_basis": "Legal Services Authorities Act 1987",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def training_body(eid: str, name: str, state: str) -> dict:
    return {
        "id": eid,
        "name": name,
        "type": "TrainingBody",
        "cluster": "training_professional",
        "level_of_government": "UT" if state == "DL" else "State",
        "jurisdiction_scope": {"states_covered": [state], "is_all_india": False},
        "created_year": 1992,
        "operational_status": "Active",
        "statutory_basis": "State judicial academy statutes / rules",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def prosecution(eid: str, name: str, state: str) -> dict:
    ut_codes = {"DL", "PY"}
    lvl = "UT" if state in ut_codes else "State"
    js = (
        {"uts_covered": [state], "is_all_india": False}
        if state in ut_codes
        else {"states_covered": [state], "is_all_india": False}
    )
    return {
        "id": eid,
        "name": name,
        "type": "ProsecutionBody",
        "cluster": "executive_interface",
        "level_of_government": lvl,
        "jurisdiction_scope": js,
        "created_year": 1950,
        "operational_status": "Active",
        "statutory_basis": "CrPC / state prosecution service rules (high-level stub)",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def lokayukta(eid: str, name: str, state: str, gap: bool) -> dict:
    ut_codes = {"DL", "PY"}
    lvl = "UT" if state in ut_codes else "State"
    js = (
        {"uts_covered": [state], "is_all_india": False}
        if state in ut_codes
        else {"states_covered": [state], "is_all_india": False}
    )
    return {
        "id": eid,
        "name": name,
        "type": "ExecutiveBody",
        "cluster": "executive_interface",
        "level_of_government": lvl,
        "jurisdiction_scope": js,
        "created_year": 1971 if state == "MH" else 1984 if state == "KA" else 1995,
        "operational_status": "Active",
        "statutory_basis": "State Lokayukta / Lokpal interface statutes (stub)",
        "structural_variations": (
            [
                {
                    "variation_id": f"{eid}_appointment_delay",
                    "description": "Document appointment delays post-2019 from official sources when available.",
                    "applicable_to": [state],
                    "source": "State Lokayukta portal — verify dates",
                    "independence_risk_note": "Executive interface risk pending review",
                }
            ]
            if gap
            else []
        ),
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Yes"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def bar_council(eid: str, name: str, states: list[str]) -> dict:
    return {
        "id": eid,
        "name": name,
        "type": "ProfessionalBody",
        "cluster": "training_professional",
        "level_of_government": "Shared_MultiState" if len(states) > 1 else "State",
        "jurisdiction_scope": {"states_covered": states, "is_all_india": False},
        "created_year": 1961,
        "operational_status": "Active",
        "statutory_basis": "Advocates Act 1961 — Bar Council of India / State Bar Councils",
        "funding": {"primary_source": "Party_Fees"},
        "audit": {"audit_type": "Internal", "audit_report_public": False},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [SRC],
    }


# ── Pan-India: 25 High Courts, state→HC map, light packs ─────────────────────

HIGH_COURTS_DEF = [
    ("hc_allahabad", "High Court of Judicature at Allahabad", ["UP"], "State", 1869),
    ("hc_andhra_pradesh", "High Court of Andhra Pradesh", ["AP"], "State", 2019),
    ("hc_bombay", "High Court of Bombay", ["MH", "GA", "DD", "DN"], "Shared_MultiState", 1862),
    ("hc_calcutta", "High Court at Calcutta", ["WB", "AN"], "Shared_MultiState", 1862),
    ("hc_chhattisgarh", "High Court of Chhattisgarh", ["CG"], "State", 2000),
    ("hc_delhi", "High Court of Delhi", ["DL"], "UT", 1966),
    ("hc_gauhati", "High Court of Gauhati", ["AS", "AR", "NL", "MZ"], "Shared_MultiState", 1948),
    ("hc_gujarat", "High Court of Gujarat", ["GJ"], "State", 1960),
    ("hc_himachal_pradesh", "High Court of Himachal Pradesh", ["HP"], "State", 1971),
    ("hc_jammu_kashmir_ladakh", "High Court of Jammu & Kashmir and Ladakh", ["JK", "LA"], "Shared_MultiState", 1928),
    ("hc_jharkhand", "High Court of Jharkhand", ["JH"], "State", 2000),
    ("hc_karnataka", "High Court of Karnataka", ["KA"], "State", 1956),
    ("hc_kerala", "High Court of Kerala", ["KL", "LD"], "Shared_MultiState", 1956),
    ("hc_madhya_pradesh", "High Court of Madhya Pradesh", ["MP"], "State", 1956),
    ("hc_madras", "High Court of Judicature at Madras", ["TN", "PY"], "Shared_MultiState", 1862),
    ("hc_manipur", "High Court of Manipur", ["MN"], "State", 2013),
    ("hc_meghalaya", "High Court of Meghalaya", ["ML"], "State", 2013),
    ("hc_orissa", "High Court of Orissa", ["OD"], "State", 1948),
    ("hc_patna", "High Court of Judicature at Patna", ["BR"], "State", 1916),
    ("hc_punjab_haryana", "High Court of Punjab and Haryana", ["PB", "HR", "CH"], "Shared_MultiState", 1947),
    ("hc_rajasthan", "High Court of Judicature for Rajasthan", ["RJ"], "State", 1949),
    ("hc_sikkim", "High Court of Sikkim", ["SK"], "State", 1975),
    ("hc_telangana", "High Court for the State of Telangana", ["TS"], "State", 2014),
    ("hc_tripura", "High Court of Tripura", ["TR"], "State", 2013),
    ("hc_uttarakhand", "High Court of Uttarakhand", ["UK"], "State", 2000),
]

STATE_TO_HC_ID = {
    "AP": "hc_andhra_pradesh",
    "AR": "hc_gauhati",
    "AS": "hc_gauhati",
    "BR": "hc_patna",
    "CG": "hc_chhattisgarh",
    "GA": "hc_bombay",
    "GJ": "hc_gujarat",
    "HR": "hc_punjab_haryana",
    "HP": "hc_himachal_pradesh",
    "JK": "hc_jammu_kashmir_ladakh",
    "JH": "hc_jharkhand",
    "KA": "hc_karnataka",
    "KL": "hc_kerala",
    "MP": "hc_madhya_pradesh",
    "MH": "hc_bombay",
    "MN": "hc_manipur",
    "ML": "hc_meghalaya",
    "MZ": "hc_gauhati",
    "NL": "hc_gauhati",
    "OD": "hc_orissa",
    "PB": "hc_punjab_haryana",
    "RJ": "hc_rajasthan",
    "SK": "hc_sikkim",
    "TN": "hc_madras",
    "TS": "hc_telangana",
    "TR": "hc_tripura",
    "UP": "hc_allahabad",
    "UK": "hc_uttarakhand",
    "WB": "hc_calcutta",
    "DL": "hc_delhi",
    "PY": "hc_madras",
    "AN": "hc_calcutta",
    "CH": "hc_punjab_haryana",
    "LD": "hc_kerala",
    "LA": "hc_jammu_kashmir_ladakh",
    "DD": "hc_bombay",
    "DN": "hc_bombay",
}

GOVERNMENT_IDS = {
    "MH": "government_maharashtra",
    "DL": "government_nct_delhi",
    "KA": "government_karnataka",
    "TN": "government_tamilnadu",
}

STATES_28 = [
    "AP", "AR", "AS", "BR", "CG", "GA", "GJ", "HR", "HP", "JK", "JH", "KA", "KL", "MP", "MH",
    "MN", "ML", "MZ", "NL", "OD", "PB", "RJ", "SK", "TN", "TS", "TR", "UP", "UK", "WB",
]

UT_EXTRA = ["AN", "CH", "LD", "LA"]

SECOND_DISTRICT = {
    "UP": ("up_district_court_varanasi", "District Court — Varanasi"),
    "BR": ("br_district_court_bhagalpur", "District Court — Bhagalpur"),
    "WB": ("wb_district_court_asansol", "District Court — Asansol"),
    "MP": ("mp_district_court_indore", "District Court — Indore"),
    "RJ": ("rj_district_court_jaipur", "District Court — Jaipur"),
    "GJ": ("gj_district_court_vadodara", "District Court — Vadodara"),
    "TS": ("ts_district_court_warangal", "District Court — Warangal"),
    "AP": ("ap_district_court_vijayawada", "District Court — Vijayawada"),
    "AS": ("as_district_court_dibrugarh", "District Court — Dibrugarh"),
}

GOVERNMENT_LONG_NAMES = {
    "AP": "Government of Andhra Pradesh",
    "AR": "Government of Arunachal Pradesh",
    "AS": "Government of Assam",
    "BR": "Government of Bihar",
    "CG": "Government of Chhattisgarh",
    "GA": "Government of Goa",
    "GJ": "Government of Gujarat",
    "HR": "Government of Haryana",
    "HP": "Government of Himachal Pradesh",
    "JK": "Government of Jammu and Kashmir",
    "JH": "Government of Jharkhand",
    "KL": "Government of Kerala",
    "MP": "Government of Madhya Pradesh",
    "MH": "Government of Maharashtra",
    "MN": "Government of Manipur",
    "ML": "Government of Meghalaya",
    "MZ": "Government of Mizoram",
    "NL": "Government of Nagaland",
    "OD": "Government of Odisha",
    "PB": "Government of Punjab",
    "RJ": "Government of Rajasthan",
    "SK": "Government of Sikkim",
    "TN": "Government of Tamil Nadu",
    "TS": "Government of Telangana",
    "TR": "Government of Tripura",
    "UP": "Government of Uttar Pradesh",
    "UK": "Government of Uttarakhand",
    "WB": "Government of West Bengal",
    "DL": "Government of National Capital Territory of Delhi",
    "KA": "Government of Karnataka",
    "AN": "Government of Andaman and Nicobar Islands",
    "CH": "Government of Chandigarh",
    "LD": "Government of Lakshadweep",
    "LA": "Government of Ladakh",
}


def govt_doc(code: str) -> dict:
    uts = {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}
    gid = GOVERNMENT_IDS.get(code, f"government_{code.lower()}")
    lvl = "UT" if code in uts else "State"
    js = (
        {"uts_covered": [code], "is_all_india": False}
        if code in uts
        else {"states_covered": [code], "is_all_india": False}
    )
    return {
        **stub_exec(gid, GOVERNMENT_LONG_NAMES[code], "legislative_executive", lvl),
        "jurisdiction_scope": js,
    }


def emit_light_state_pack(ent: Path, code: str, hc_id: str, national_rels: list) -> None:
    """Principal + generic districts, SCDRC, SLSA; appellate edges (not for MH/DL/KA/TN — those have rich packs)."""
    st = code.lower()
    gid = GOVERNMENT_IDS.get(code, f"government_{st}")
    gov_dir = ent / "governments"
    gov_dir.mkdir(parents=True, exist_ok=True)
    W(gov_dir / f"{gid}.yaml", govt_doc(code))

    base = ent / "states" / st
    ut_codes = {"DL", "PY", "AN", "CH", "LD", "LA", "DD", "DN"}
    cdrc_lvl = "UT" if code in ut_codes else "State"
    W(
        base / f"{st}_state_cdrc.yaml",
        consumer_comm(f"{st}_state_cdrc", f"State Consumer Disputes Redressal Commission — {code}", code, cdrc_lvl),
    )
    W(base / f"slsa_{st}.yaml", slsa(f"slsa_{st}", f"State Legal Services Authority — {code}", code))
    pr_id = f"{st}_district_court_principal"
    W(base / f"{pr_id}.yaml", district_court(pr_id, f"District & Sessions Court — {code} (principal bench)", code))
    W(
        base / f"{st}_district_courts_generic.yaml",
        district_court(f"{st}_district_courts_generic", f"District Courts — {code} (remaining districts)", code),
    )
    if code in SECOND_DISTRICT:
        sid, sname = SECOND_DISTRICT[code]
        W(base / f"{sid}.yaml", district_court(sid, sname, code))

    national_rels.append(
        rel(f"{st}_cdrc_ncdrc", f"{st}_state_cdrc", "ncdrc", "AppealableTo", "appellate_chain", f"{code} SCDRC to NCDRC"),
    )
    national_rels.append(
        rel(f"{st}_dist_app", pr_id, hc_id, "AppealableTo", "appellate_chain", f"{code} district appeals to HC"),
    )
    national_rels.append(
        rel(f"{st}_hc_super", hc_id, pr_id, "AdministrativeSupervision", "supervisory", f"HC supervision {code}"),
    )
    national_rels.append(
        rel(f"{st}_slsa_lok", f"slsa_{st}", "lok_adalat_generic", "Designates", "statutory_ref", f"{code} SLSA lok adalat"),
    )
    national_rels.append(
        rel(f"{st}_fund_cdrc", gid, f"{st}_state_cdrc", "PrimaryFunder", "funding", f"{code} funds SCDRC"),
    )
    rera_entity = "tn_rera" if code == "TN" else (f"rera_{st}" if code not in ("MH", "DL", "KA") else None)
    if rera_entity == f"rera_{st}" and not (ent / "regulatory_bodies" / "rera_states" / f"rera_{st}.yaml").exists():
        rera_entity = None
    if rera_entity:
        national_rels.append(
            rel(f"{st}_rera_hc", rera_entity, hc_id, "AppealableTo", "appellate_chain", f"{code} RERA appeals to HC (stub)"),
        )
        national_rels.append(rel(f"{st}_fund_rera", gid, rera_entity, "PrimaryFunder", "funding", f"{code} funds RERA"))
    if code not in ("MH", "DL", "KA", "TN"):
        serc_id = f"serc_{st}"
        if (ent / "regulatory_bodies" / "serc_states" / f"{serc_id}.yaml").exists():
            national_rels.append(
                rel(f"{st}_serc_aptel", serc_id, "aptel", "AppealableTo", "appellate_chain", f"{code} SERC to APTEL"),
            )
            national_rels.append(rel(f"{st}_fund_serc", gid, serc_id, "PrimaryFunder", "funding", f"{code} funds SERC"))
    if code in SECOND_DISTRICT:
        sid, _ = SECOND_DISTRICT[code]
        slug2 = sid.split("_court_")[-1] if "_court_" in sid else ""
        hc_tgt2 = district_appellate_target(sid, slug2, hc_id)
        national_rels.append(
            rel(f"{st}_dist2_app", sid, hc_tgt2, "AppealableTo", "appellate_chain", f"{code} second district appeals to HC/bench"),
        )
        national_rels.append(
            rel(f"{st}_hc_super2", hc_tgt2, sid, "AdministrativeSupervision", "supervisory", f"HC/bench supervision {code}"),
        )


def madras_bench_of_rel(bench_id: str, parent_hc: str) -> dict:
    """Enriched BenchOf for Madras permanent benches (Track D / §6)."""
    notes = {
        "hc_madras_bench_madurai": (
            "Madurai Bench is the sole permanent bench of the Madras High Court (est. 2004), "
            "constituted under the Madras High Court (Establishment of a Permanent Bench at "
            "Madurai) Order, 2004. Exercises full HC jurisdiction for 10 southern TN districts "
            "per hc_benches_config.py TN_DISTRICT_TO_BENCH. No permanent bench at Tiruchirappalli. "
            "Central/northern TN districts appeal to hc_madras principal seat. TN district routing "
            "in tn_relationships.yaml."
        ),
    }
    return {
        "id": f"{bench_id}_bench_of_{parent_hc}",
        "source": bench_id,
        "target": parent_hc,
        "relationship_type": "BenchOf",
        "relationship_category": "statutory_ref",
        "is_binding": True,
        "notes": notes[bench_id],
        "data_quality": "partial",
        "sources": [
            {
                "label": "India Code — Constitution & Acts",
                "url": "https://india-code.nic.in/",
                "type": "GoIWebsite",
                "accessed_date": "2026-05-13",
            },
            {
                "label": "Constitution of India, Article 214",
                "url": "https://india-code.nic.in/",
                "type": "Constitution",
                "accessed_date": "2026-05-18",
            },
        ],
    }


def district_appellate_target(eid: str, slug: str, default_hc: str) -> str:
    """Resolve HC or HC bench for district appellate/supervision edges."""
    if slug and slug in TN_DISTRICT_TO_BENCH:
        return TN_DISTRICT_TO_BENCH[slug]
    if eid in MH_DISTRICT_TO_BENCH:
        return MH_DISTRICT_TO_BENCH[eid]
    if eid in KA_DISTRICT_TO_BENCH:
        return KA_DISTRICT_TO_BENCH[eid]
    if eid in UP_DISTRICT_TO_BENCH:
        return UP_DISTRICT_TO_BENCH[eid]
    if eid in WB_DISTRICT_TO_BENCH:
        return WB_DISTRICT_TO_BENCH[eid]
    if eid in RJ_DISTRICT_TO_BENCH:
        return RJ_DISTRICT_TO_BENCH[eid]
    return default_hc


def emit_hc_benches(ent: Path, bench_rels: list) -> None:
    """Write permanent HC bench entities and BenchOf / HC→SC edges."""
    bench_dir = ent / "high_courts" / "benches"
    bench_dir.mkdir(parents=True, exist_ok=True)
    parent_states: dict[str, list[str]] = {eid: sts for eid, _, sts, _, _ in HIGH_COURTS_DEF}

    for bench_id, bench_name, parent_hc, seat_city in HC_BENCHES_DEF:
        states = parent_states.get(parent_hc, [])
        W(bench_dir / f"{bench_id}.yaml", hc_bench(bench_id, bench_name, parent_hc, seat_city, states))
        if bench_id == "hc_madras_bench_madurai":
            bench_rels.append(madras_bench_of_rel(bench_id, parent_hc))
        else:
            bench_rels.append(
                rel(
                    f"{bench_id}_bench_of_{parent_hc}",
                    bench_id,
                    parent_hc,
                    "BenchOf",
                    "statutory_ref",
                    f"Permanent bench at {seat_city} — part of {parent_hc}",
                )
            )

    for eid, _, sts, _, _ in HIGH_COURTS_DEF:
        bench_rels.append(
            rel(
                f"{eid}_appealable_sc",
                eid,
                "supreme_court_india",
                "AppealableTo",
                "appellate_chain",
                "High Court appeals / SLP to Supreme Court (Article 136)",
            )
        )


def rel(rel_id: str, src: str, tgt: str, rtype: str, cat: str, notes: str) -> dict:
    return {
        "id": rel_id,
        "source": src,
        "target": tgt,
        "relationship_type": rtype,
        "relationship_category": cat,
        "is_binding": True,
        "notes": notes,
        "data_quality": "partial",
        "sources": [SRC],
    }


ADR_SRC_NDIAC_ACT = {
    "label": "New Delhi International Arbitration Centre Act 2019 — India Code",
    "url": "https://india-code.nic.in/acts-detail/MjMyMDM=",
    "type": "CentralAct",
    "accessed_date": "2026-05-18",
}
ADR_SRC_LSA_ACT = {
    "label": "Legal Services Authorities Act 1987 — India Code",
    "url": "https://india-code.nic.in/acts-detail/NzI2",
    "type": "CentralAct",
    "accessed_date": "2026-05-18",
}
ADR_SRC_AC_ACT = {
    "label": "Arbitration and Conciliation Act 1996 — India Code",
    "url": "https://india-code.nic.in/acts-detail/MTA4NDE=",
    "type": "CentralAct",
    "accessed_date": "2026-05-18",
}


def adr_rel(
    rel_id: str,
    src: str,
    tgt: str,
    rtype: str,
    cat: str,
    notes: str,
    sources: list[dict],
) -> dict:
    return {
        "id": rel_id,
        "source": src,
        "target": tgt,
        "relationship_type": rtype,
        "relationship_category": cat,
        "is_binding": True,
        "notes": notes,
        "data_quality": "partial",
        "sources": sources,
    }


def adr_arbitration_relationships() -> list[dict]:
    """Track E (§4) — NDIAC, MCIA, DIAC, NALSA, tn_slsa, lok_adalat_generic."""
    return [
        adr_rel(
            "moflj_funds_ndiac",
            "ministry_law_justice",
            "ndiac",
            "PrimaryFunder",
            "funding",
            (
                "Ministry of Law and Justice provides Central Government grants to NDIAC "
                "under NDIAC Act 2019 s.25(1)(a). Transitional arrangement pending "
                "self-sustaining fee model."
            ),
            [ADR_SRC_NDIAC_ACT],
        ),
        adr_rel(
            "moflj_funds_nalsa",
            "ministry_law_justice",
            "nalsa",
            "PrimaryFunder",
            "funding",
            (
                "Ministry of Law and Justice provides Central Government grants to the "
                "National Legal Aid Fund (NALSA) under LSA Act 1987 s.17(1)(a). "
                "NALSA in turn grants funds to State Legal Services Authorities."
            ),
            [ADR_SRC_LSA_ACT],
        ),
        adr_rel(
            "ndiac_award_challenged_hc_delhi",
            "ndiac",
            "hc_delhi",
            "AwardChallengedIn",
            "appellate_chain",
            (
                "Awards from NDIAC arbitration proceedings challenged under Arbitration "
                "and Conciliation Act 1996 s.34. NDIAC seat is New Delhi; Delhi High "
                "Court is the competent court under A&C Act s.2(1)(e)(i). Appeals from "
                "s.34 orders lie to HC Division Bench under s.37."
            ),
            [ADR_SRC_AC_ACT],
        ),
        adr_rel(
            "mcia_award_challenged_hc_bombay",
            "mcia",
            "hc_bombay",
            "AwardChallengedIn",
            "appellate_chain",
            (
                "Awards from MCIA arbitration proceedings challenged under A&C Act 1996 "
                "s.34. Default seat is Mumbai; Bombay High Court is typically the "
                "competent court. Seat is party-determined and may vary per arbitration "
                "agreement — this edge models the default/typical case."
            ),
            [ADR_SRC_AC_ACT],
        ),
        adr_rel(
            "diac_award_challenged_hc_delhi",
            "diac",
            "hc_delhi",
            "AwardChallengedIn",
            "appellate_chain",
            (
                "Awards from DIAC arbitration proceedings challenged under A&C Act 1996 "
                "s.34 in Delhi High Court. DIAC is administered by Delhi HC itself — "
                "s.34 challenge venue is Delhi HC by both seat and administration."
            ),
            [ADR_SRC_AC_ACT],
        ),
        adr_rel(
            "nalsa_designates_lok_adalat",
            "nalsa",
            "lok_adalat_generic",
            "Designates",
            "statutory_ref",
            (
                "NALSA organises Lok Adalats at national level under LSA Act 1987 s.19. "
                "State and District Legal Services Authorities organise Lok Adalats at "
                "state/district level within NALSA's policy framework (see state packs, "
                "e.g. tn_relationships.yaml tn_slsa_adr)."
            ),
            [ADR_SRC_LSA_ACT],
        ),
        adr_rel(
            "tn_slsa_reports_nalsa",
            "tn_slsa",
            "nalsa",
            "ReportsTo",
            "supervisory",
            (
                "State Legal Services Authorities function under NALSA's supervisory "
                "control (LSA Act 1987 s.6(8)). TN SLSA reports to NALSA on policy, "
                "accounts, and receives NALSA grants through this channel."
            ),
            [ADR_SRC_LSA_ACT],
        ),
    ]


def parse_generate_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Emit JEM v1 entity/relationship YAML")
    p.add_argument(
        "--only",
        choices=("all", "backbone", "hc-benches", "state-packs", "light-states", "relationships"),
        default="all",
        help="all = full bundle; relationships = relationship YAML only (no entity writes). "
        "Other slice names are reserved.",
    )
    return p.parse_args()


def main() -> None:
    global _WRITE_ENTITIES
    args = parse_generate_args()
    only = args.only
    _WRITE_ENTITIES = only != "relationships"

    ENT.mkdir(parents=True, exist_ok=True)

    if only not in ("all", "relationships"):
        raise SystemExit(
            f"--only {only!r} is reserved for a future refactor. "
            "Use --only all (default) or --only relationships (regen rel YAML only, no entity writes)."
        )

    for sid in ("government_maharashtra", "government_nct_delhi", "government_karnataka", "government_tamilnadu"):
        stale = ENT / "backbone" / f"{sid}.yaml"
        if stale.exists():
            stale.unlink()
    # ── Backbone (appointment graph + SC/CBI/ACI refs) ─────────────────
    backbone = ENT / "backbone"
    stubs = [
        stub_appointment("collegium_sc", "Supreme Court Collegium"),
        stub_appointment("collegium_hc_appointment", "High Court Collegium (aggregate)"),
        stub_exec("president_india", "President of India", "legislative_executive", "Central"),
        stub_exec("parliament_both_houses", "Parliament of India (Lok Sabha + Rajya Sabha)", "legislative_executive", "Central"),
        stub_exec("central_government", "Union of India — Central Government", "legislative_executive", "Central"),
        stub_exec("chief_justice_india", "Chief Justice of India (office)", "constitutional_courts", "Central"),
        stub_exec("ministry_of_finance", "Ministry of Finance", "financing_audit", "Central"),
        stub_exec("ministry_law_justice", "Ministry of Law and Justice", "legislative_executive", "Central"),
        stub_exec("department_of_justice", "Department of Justice", "legislative_executive", "Central"),
        stub_exec("ministry_personnel_dopt", "Ministry of Personnel, Public Grievances and Pensions (DoPT)", "legislative_executive", "Central"),
        stub_exec("cag_india", "Comptroller and Auditor General of India", "financing_audit", "Central"),
        stub_exec("in_house_procedure_sc", "Supreme Court In-House Procedure", "constitutional_courts", "Central"),
        stub_exec("national_judicial_academy", "National Judicial Academy", "training_professional", "Central"),
        stub_exec("central_vigilance_commission", "Central Vigilance Commission", "executive_interface", "Central"),
        stub_exec("high_court_competent", "High Court (competent for CBI jurisdiction)", "constitutional_courts", "Central"),
        stub_exec("governor_state", "Governors — State aggregate (Article 154 / 163 interface)", "legislative_executive", "State"),
        stub_exec("state_public_service_commission", "State Public Service Commissions (aggregate)", "appointment_bodies", "State"),
        {
            "id": "national_judicial_appointments_commission",
            "name": "National Judicial Appointments Commission",
            "type": "AppointmentBody",
            "cluster": "appointment_bodies",
            "level_of_government": "Central",
            "jurisdiction_scope": {"is_all_india": True},
            "created_year": 2014,
            "abolished_year": 2015,
            "operational_status": "Abolished",
            "data_quality": "partial",
            "data_quality_notes": "Abolished by SC in 2015; retained for historical appointment edges.",
            "sources": [SRC, SRC_SC],
        },
        {
            **stub_exec("district_courts", "District Courts (India — aggregate)", "subordinate_courts", "Shared_MultiState"),
            "type": "SubordinateCivilCourt",
            "cluster": "subordinate_courts",
        },
        {
            **stub_exec("subordinate_civil_courts", "Subordinate civil courts (aggregate — CJ/JM)", "subordinate_courts", "Shared_MultiState"),
            "type": "SubordinateCivilCourt",
            "cluster": "subordinate_courts",
        },
        {
            **stub_exec("high_courts_all", "High Courts of India (aggregate)", "constitutional_courts", "Shared_MultiState"),
            "type": "ConstitutionalCourt",
            "cluster": "constitutional_courts",
            "jurisdiction_scope": {"is_all_india": True, "jurisdiction_types": ["Appellate", "Writ"]},
        },
        stub_exec("ncdrc", "National Consumer Disputes Redressal Commission", "consumer_redressal", "Central"),
        stub_exec("aptel", "Appellate Tribunal for Electricity", "tribunals_adr", "Central"),
        {
            **stub_exec("lok_adalat_generic", "Lok Adalat (generic)", "tribunals_adr", "Shared_MultiState"),
            "type": "ADRBody",
            "cluster": "tribunals_adr",
        },
    ]
    for doc in stubs:
        W(backbone / f"{doc['id']}.yaml", doc)

    # High courts (25) + permanent benches + HC→SC appellate backbone
    hc_dir = ENT / "high_courts"
    bench_rels: list = []
    for eid, name, sts, lvl, y in HIGH_COURTS_DEF:
        W(hc_dir / f"{eid}.yaml", hc(eid, name, sts, lvl, y))
    emit_hc_benches(ENT, bench_rels)

    gov_dir = ENT / "governments"
    gov_dir.mkdir(parents=True, exist_ok=True)
    for sid, sname in [
        ("government_maharashtra", "Government of Maharashtra"),
        ("government_nct_delhi", "Government of National Capital Territory of Delhi"),
        ("government_karnataka", "Government of Karnataka"),
        ("government_tamilnadu", "Government of Tamil Nadu"),
    ]:
        W(gov_dir / f"{sid}.yaml", stub_exec(sid, sname, "legislative_executive", "State"))

    # ── MH pack ───────────────────────────────────────────────────────
    mh = ENT / "states" / "mh"
    mh_docs = [
        regulatory_state("merc", "Maharashtra Electricity Regulatory Commission", "MH", 1999, "Electricity Act 2003 — State Commission (MERc)"),
        regulatory_state("mh_rera", "Maharashtra Real Estate Regulatory Authority (MahaRERA)", "MH", 2017, "Real Estate (Regulation and Development) Act 2016 — Maharashtra rules"),
        bar_council("mh_bar_council", "Bar Council of Maharashtra and Goa", ["MH", "GA"]),
        lokayukta("mh_lokayukta", "Maharashtra Lokayukta", "MH", True),
        training_body("mh_sja", "Maharashtra State Judicial Academy", "MH"),
        slsa("mh_slsa", "Maharashtra State Legal Services Authority", "MH"),
        prosecution("mh_advocate_general", "Advocate General — Maharashtra", "MH"),
        consumer_comm("mh_state_cdrc", "Maharashtra State Consumer Disputes Redressal Commission", "MH", "State"),
        consumer_comm("mh_cdrc_mumbai", "Mumbai District Consumer Disputes Redressal Commission", "MH", "State"),
        consumer_comm("mh_cdrc_pune", "Pune District Consumer Disputes Redressal Commission", "MH", "State"),
        consumer_comm("mh_cdrc_nagpur", "Nagpur District Consumer Disputes Redressal Commission", "MH", "State"),
        consumer_comm("mh_cdrc_aurangabad", "Aurangabad District Consumer Disputes Redressal Commission", "MH", "State"),
        city_civil("city_civil_court_mumbai", "City Civil Court — Mumbai", "MH"),
        district_court("mh_district_court_mumbai_city", "District Court — Mumbai City", "MH"),
        district_court("mh_district_court_thane", "District Court — Thane", "MH"),
        district_court("mh_district_court_pune", "District Court — Pune", "MH"),
        district_court("mh_district_court_nashik", "District Court — Nashik", "MH"),
        district_court("mh_district_court_aurangabad", "District Court — Aurangabad (Chhatrapati Sambhajinagar)", "MH"),
        district_court("mh_district_court_nagpur", "District Court — Nagpur", "MH"),
        district_court("mh_district_court_solapur", "District Court — Solapur", "MH"),
        district_court("mh_district_court_kolhapur", "District Court — Kolhapur", "MH"),
        district_court("mh_district_court_nanded", "District Court — Nanded", "MH"),
        district_court("mh_district_court_amravati", "District Court — Amravati", "MH"),
        district_court("mh_district_courts_generic", "District Courts — Maharashtra (remaining districts)", "MH"),
        special_courts_bundle("mh_special_courts", "Maharashtra — Special courts pool (PMLA / POCSO / NIA / SC-ST / CBI)", "MH"),
    ]
    for doc in mh_docs:
        W(mh / f"{doc['id']}.yaml", doc)

    # ── DL pack ───────────────────────────────────────────────────────
    dl = ENT / "states" / "dl"
    dl_docs = [
        {
            **stub_exec("dl_lieutenant_governor", "Lieutenant Governor — National Capital Territory of Delhi", "legislative_executive", "UT"),
            "jurisdiction_scope": {"uts_covered": ["DL"], "is_all_india": False},
            "type": "ExecutiveBody",
            "cluster": "legislative_executive",
            "constitutional_basis": "Article 239AA — Union territory of Delhi",
        },
        regulatory_state("derc", "Delhi Electricity Regulatory Commission", "DL", 2001, "Electricity Act 2003 — DERC"),
        regulatory_state("dl_rera", "Delhi Real Estate Regulatory Authority", "DL", 2017, "RERA 2016 — Delhi"),
        lokayukta("dl_lokayukta", "Delhi Lokayukta", "DL", True),
        training_body("dl_sja", "Delhi Judicial Academy", "DL"),
        slsa("dl_slsa", "Delhi State Legal Services Authority (DSLSA)", "DL"),
        prosecution("dl_advocate_general", "Advocate General — NCT of Delhi", "DL"),
        consumer_comm("dl_state_cdrc", "Delhi State Consumer Disputes Redressal Commission", "DL", "UT"),
        consumer_comm("dl_cdrc_north", "North Delhi District Consumer Forum", "DL", "UT"),
        consumer_comm("dl_cdrc_south", "South Delhi District Consumer Forum", "DL", "UT"),
        consumer_comm("dl_cdrc_east", "East Delhi District Consumer Forum", "DL", "UT"),
        consumer_comm("dl_cdrc_west", "West Delhi District Consumer Forum", "DL", "UT"),
        consumer_comm("dl_cdrc_central", "Central Delhi District Consumer Forum", "DL", "UT"),
        consumer_comm("dl_cdrc_northwest", "North West Delhi District Consumer Forum", "DL", "UT"),
        district_court("dl_district_court_saket", "District Court — Saket", "DL"),
        district_court("dl_district_court_tis_hazari", "District Court — Tis Hazari", "DL"),
        district_court("dl_district_court_rohini", "District Court — Rohini", "DL"),
        district_court("dl_district_court_patiala_house", "District Court — Patiala House", "DL"),
        district_court("dl_district_court_dwarka", "District Court — Dwarka", "DL"),
        district_court("dl_district_court_karkardooma", "District Court — Karkardooma", "DL"),
        district_court("dl_district_courts_generic", "District Courts — Delhi (remaining districts)", "DL"),
        special_courts_bundle("dl_special_courts", "Delhi — Special courts pool (PMLA / POCSO / NIA / ACB)", "DL"),
    ]
    for doc in dl_docs:
        W(dl / f"{doc['id']}.yaml", doc)

    # ── KA pack ───────────────────────────────────────────────────────
    ka = ENT / "states" / "ka"
    ka_docs = [
        regulatory_state("kerc", "Karnataka Electricity Regulatory Commission", "KA", 1999, "Electricity Act 2003 — KERC"),
        regulatory_state("ka_rera", "Karnataka Real Estate Regulatory Authority (K-RERA)", "KA", 2017, "RERA 2016 — Karnataka"),
        lokayukta("ka_lokayukta", "Karnataka Lokayukta", "KA", True),
        training_body("ka_sja", "Karnataka State Judicial Academy", "KA"),
        slsa("ka_slsa", "Karnataka State Legal Services Authority", "KA"),
        prosecution("ka_advocate_general", "Advocate General — Karnataka", "KA"),
        consumer_comm("ka_state_cdrc", "Karnataka State Consumer Disputes Redressal Commission", "KA", "State"),
        consumer_comm("ka_cdrc_bengaluru", "Bengaluru Urban District Consumer Forum", "KA", "State"),
        consumer_comm("ka_cdrc_mysuru", "Mysuru District Consumer Forum", "KA", "State"),
        consumer_comm("ka_cdrc_hubballi", "Hubballi-Dharwad District Consumer Forum", "KA", "State"),
        consumer_comm("ka_cdrc_mangaluru", "Mangaluru District Consumer Forum", "KA", "State"),
        city_civil("city_civil_court_bangalore", "City Civil Court — Bengaluru", "KA"),
        district_court("ka_district_court_bengaluru_urban", "District Court — Bengaluru Urban", "KA"),
        district_court("ka_district_court_bengaluru_rural", "District Court — Bengaluru Rural", "KA"),
        district_court("ka_district_court_mysuru", "District Court — Mysuru", "KA"),
        district_court("ka_district_court_belagavi", "District Court — Belagavi", "KA"),
        district_court("ka_district_court_kalaburagi", "District Court — Kalaburagi", "KA"),
        district_court("ka_district_court_dharwad", "District Court — Dharwad", "KA"),
        district_court("ka_district_court_tumkuru", "District Court — Tumakuru", "KA"),
        district_court("ka_district_court_shivamogga", "District Court — Shivamogga", "KA"),
        district_court("ka_district_court_mangaluru", "District Court — Mangaluru", "KA"),
        district_court("ka_district_court_ballari", "District Court — Ballari", "KA"),
        district_court("ka_district_courts_generic", "District Courts — Karnataka (remaining districts)", "KA"),
        special_courts_bundle("ka_special_courts", "Karnataka — Special courts pool (PMLA / POCSO / NIA / SC-ST / CBI)", "KA"),
    ]
    for doc in ka_docs:
        W(ka / f"{doc['id']}.yaml", doc)

    # Fix ka_lokayukta structural variation for KA amendment (checklist)
    ka_lok = ka / "ka_lokayukta.yaml"
    doc = yaml.safe_load(ka_lok.read_text(encoding="utf-8"))
    doc.setdefault("structural_variations", []).append(
        {
            "variation_id": "ka_lokayukta_independence_2023",
            "description": "2023 amendment context — verify independence impact from primary materials.",
            "applicable_to": ["KA"],
            "source": "Rajamohan Reddy v State of Karnataka (2023) — cite official neutral citation when verified",
            "independence_risk_note": "Policy conflict risk — pending domain review",
        }
    )
    W(ka_lok, doc)

    # ── RERA ×34 (one YAML per code) ─────────────────────────────────
    # 34 jurisdictions excluding MH/DL/KA (dedicated RERA) and TN (`tn_rera` file)
    rera_codes = [
        "AP",
        "AR",
        "AS",
        "BR",
        "CG",
        "GA",
        "GJ",
        "HR",
        "HP",
        "JK",
        "JH",
        "KL",
        "MP",
        "MN",
        "ML",
        "MZ",
        "NL",
        "OD",
        "PB",
        "RJ",
        "SK",
        "TS",
        "TR",
        "UP",
        "UK",
        "WB",
        "PY",
        "CH",
        "AN",
        "LD",
        "LA",
        "DN",
        "DD",
    ]
    rdir = ENT / "regulatory_bodies" / "rera_states"
    for code in rera_codes:
        W(
            rdir / f"rera_{code.lower()}.yaml",
            regulatory_state(
                f"rera_{code.lower()}",
                f"Real Estate Regulatory Authority — {code}",
                code if code != "DL" else "DL",
                2017,
                "Real Estate (Regulation and Development) Act 2016 — state/UT RERA",
            ),
        )

    # ── SERC ×28 (states only; DL/PY often joint — still emit stubs) ───
    # SERC per state; skip MH/DL/KA (MERc/DERC/KERC); skip TN (`tnerc` in TN pack)
    serc_states = [
        "AP",
        "AR",
        "AS",
        "BR",
        "CG",
        "GA",
        "GJ",
        "HR",
        "HP",
        "JK",
        "JH",
        "KL",
        "MP",
        "MN",
        "ML",
        "MZ",
        "NL",
        "OD",
        "PB",
        "RJ",
        "SK",
        "TS",
        "TR",
        "UP",
        "UK",
        "WB",
    ]
    sdir = ENT / "regulatory_bodies" / "serc_states"
    for code in serc_states:
        if code in ("MH", "DL", "KA"):
            continue  # MERC / DERC / KERC are the electricity regulators for these jurisdictions
        W(
            sdir / f"serc_{code.lower()}.yaml",
            regulatory_state(
                f"serc_{code.lower()}",
                f"State Electricity Regulatory Commission — {code}",
                code,
                1999,
                "Electricity Act 2003 — State Electricity Regulatory Commission",
            ),
        )

    tn = ENT / "states" / "tn"
    tn_docs = [
        regulatory_state("tnerc", "Tamil Nadu Electricity Regulatory Commission (TNERC)", "TN", 1999, "Electricity Act 2003 — TNERC"),
        regulatory_state("tn_rera", "Tamil Nadu Real Estate Regulatory Authority", "TN", 2017, "RERA 2016 — Tamil Nadu"),
        bar_council("tn_bar_council", "Bar Council of Tamil Nadu and Puducherry", ["TN", "PY"]),
        lokayukta("tn_lokayukta", "Tamil Nadu Lokayukta (not constituted — verify from official sources)", "TN", False),
        training_body("tn_sja", "Tamil Nadu State Judicial Academy", "TN"),
        slsa("tn_slsa", "Tamil Nadu State Legal Services Authority", "TN"),
        prosecution("tn_advocate_general", "Advocate General — Tamil Nadu", "TN"),
        consumer_comm("tn_state_cdrc", "Tamil Nadu State Consumer Disputes Redressal Commission", "TN", "State"),
        consumer_comm("tn_cdrc_chennai", "Chennai District Consumer Forum", "TN", "State"),
        special_courts_bundle("tn_special_courts", "Tamil Nadu — Special courts pool", "TN"),
    ]
    for slug, dname in TN_DISTRICT_LATTICE:
        tn_docs.append(district_court(f"tn_district_court_{slug}", f"District Court — {dname}", "TN"))
    tn_docs.append(
        district_court(
            "tn_district_courts_generic",
            "District Courts — Tamil Nadu (consolidated)",
            "TN",
        )
    )
    for doc in tn_docs:
        W(tn / f"{doc['id']}.yaml", doc)

    py = ENT / "states" / "py"
    py_lg = {
        **stub_exec("py_lieutenant_governor", "Lieutenant Governor — Puducherry", "legislative_executive", "UT"),
        "jurisdiction_scope": {"uts_covered": ["PY"], "is_all_india": False},
    }
    W(py / "py_lieutenant_governor.yaml", py_lg)
    W(py / "py_advocate_general.yaml", prosecution("py_advocate_general", "Advocate General — Puducherry", "PY"))
    W(py / "py_district_courts.yaml", district_court("py_district_courts", "District Courts — Puducherry (aggregate)", "PY"))
    W(py / "py_slsa.yaml", slsa("py_slsa", "Puducherry State Legal Services Authority", "PY"))
    W(py / "py_cdrc.yaml", consumer_comm("py_cdrc", "Puducherry Consumer Disputes Redressal Commission", "PY", "UT"))
    py_lok = lokayukta("py_lokayukta", "Puducherry Lokayukta (verify status)", "PY", True)
    py_lok["operational_status"] = "Not_Constituted"
    W(py / "py_lokayukta.yaml", py_lok)

    tn_lok_path = tn / "tn_lokayukta.yaml"
    tnl = yaml.safe_load(tn_lok_path.read_text(encoding="utf-8"))
    tnl["operational_status"] = "Not_Constituted"
    W(tn_lok_path, tnl)

    tn_rels = [
        rel("tn_tnerc_aptel", "tnerc", "aptel", "AppealableTo", "appellate_chain", "TNERC appeals to APTEL"),
        rel("tn_cdrc_ncdrc", "tn_state_cdrc", "ncdrc", "AppealableTo", "appellate_chain", "TN SCDRC appeals to NCDRC"),
        rel("tn_rera_hc", "tn_rera", "hc_madras", "AppealableTo", "appellate_chain", "RERA appeals to HC (stub)"),
        rel("tn_slsa_adr", "tn_slsa", "lok_adalat_generic", "Designates", "statutory_ref", "TN SLSA lok adalat"),
        rel("tn_fund_rera", "government_tamilnadu", "tn_rera", "PrimaryFunder", "funding", "State funding"),
        rel("tn_sja_train_chennai_district", "tn_sja", "tn_district_court_chennai", "ProvidesContinuingEducation", "training", "State judicial academy serves all TN districts; representative edge"),
        rel(
            "tn_district_courts_generic_appealable_hc_madras",
            "tn_district_courts_generic",
            "hc_madras",
            "AppealableTo",
            "appellate_chain",
            "Consolidated TN district lattice — appeals to Madras HC (collapsed view)",
        ),
        rel(
            "hc_madras_supervise_tn_district_courts_generic",
            "hc_madras",
            "tn_district_courts_generic",
            "AdministrativeSupervision",
            "supervisory",
            "Article 235 supervision — consolidated TN district courts (collapsed view)",
        ),
    ]
    for slug, _ in TN_DISTRICT_LATTICE:
        eid = f"tn_district_court_{slug}"
        hc_tgt = district_appellate_target(eid, slug, "hc_madras")
        tn_rels.append(
            rel(
                f"tn_district_{slug}_appealable_{hc_tgt}",
                eid,
                hc_tgt,
                "AppealableTo",
                "appellate_chain",
                f"District court appeals to {hc_tgt} (Madras HC / bench)",
            )
        )
        tn_rels.append(
            rel(
                f"tn_{hc_tgt}_supervise_{slug}",
                hc_tgt,
                eid,
                "AdministrativeSupervision",
                "supervisory",
                "Article 235 supervision (Madras HC / bench)",
            )
        )
    py_rels = [
        rel("py_cdrc_ncdrc", "py_cdrc", "ncdrc", "AppealableTo", "appellate_chain", "PY CDRC appeals to NCDRC"),
        rel("py_district_hc", "py_district_courts", "hc_madras", "AppealableTo", "appellate_chain", "PY appeals to Madras HC"),
        rel("py_slsa_adr", "py_slsa", "lok_adalat_generic", "Designates", "statutory_ref", "PY SLSA"),
    ]

    mh_rels = [
        rel("mh_merc_aptel", "merc", "aptel", "AppealableTo", "appellate_chain", "Electricity appeals to APTEL"),
        rel("mh_cdrc_ncdrc", "mh_state_cdrc", "ncdrc", "AppealableTo", "appellate_chain", "State CDRC appeals to NCDRC"),
        rel("mh_city_civil_hc", "city_civil_court_mumbai", "hc_bombay", "AppealableTo", "appellate_chain", "City civil appeals to Bombay HC"),
        rel("mh_district_hc", "mh_district_court_mumbai_city", "hc_bombay", "AppealableTo", "appellate_chain", "District court appeals to HC (principal seat)"),
        rel("mh_supervise", "hc_bombay", "mh_district_court_mumbai_city", "AdministrativeSupervision", "supervisory", "Article 235 supervision (representative edge)"),
        rel("mh_fund_merc", "government_maharashtra", "merc", "PrimaryFunder", "funding", "State government funding"),
        rel("mh_fund_rera", "government_maharashtra", "mh_rera", "PrimaryFunder", "funding", "State government funding"),
        rel("mh_sja_train", "mh_sja", "mh_district_court_pune", "ProvidesContinuingEducation", "training", "Judicial academy training"),
        rel("mh_slsa_adr", "mh_slsa", "lok_adalat_generic", "Designates", "statutory_ref", "SLSA lok adalat interface"),
    ]
    for dist_eid, bench_id in MH_DISTRICT_TO_BENCH.items():
        mh_rels.append(
            rel(f"mh_{dist_eid}_appealable_{bench_id}", dist_eid, bench_id, "AppealableTo", "appellate_chain", "District appeals to HC bench"),
        )
        mh_rels.append(
            rel(f"mh_{bench_id}_supervise_{dist_eid}", bench_id, dist_eid, "AdministrativeSupervision", "supervisory", "Article 235 (bench)"),
        )
    dl_rels = [
        rel("dl_derc_aptel", "derc", "aptel", "AppealableTo", "appellate_chain", "Electricity appeals to APTEL"),
        rel("dl_cdrc_ncdrc", "dl_state_cdrc", "ncdrc", "AppealableTo", "appellate_chain", "State CDRC appeals to NCDRC"),
        rel("dl_district_hc", "dl_district_court_saket", "hc_delhi", "AppealableTo", "appellate_chain", "District appeals to Delhi HC"),
        rel("dl_supervise", "hc_delhi", "dl_district_court_saket", "AdministrativeSupervision", "supervisory", "Article 235 supervision (representative edge)"),
        rel("dl_fund_derc", "government_nct_delhi", "derc", "PrimaryFunder", "funding", "NCT funding"),
        rel("dl_fund_rera", "government_nct_delhi", "dl_rera", "PrimaryFunder", "funding", "NCT funding"),
        rel("dl_sja_train", "dl_sja", "dl_district_court_dwarka", "ProvidesContinuingEducation", "training", "Judicial academy"),
        rel("dl_slsa_adr", "dl_slsa", "lok_adalat_generic", "Designates", "statutory_ref", "DSLSA lok adalat"),
        rel("dl_lg_tension", "dl_lieutenant_governor", "government_nct_delhi", "PolicyOversight", "statutory_ref", "LG vs elected government tension (stub arc)"),
    ]
    ka_rels = [
        rel("ka_kerc_aptel", "kerc", "aptel", "AppealableTo", "appellate_chain", "Electricity appeals to APTEL"),
        rel("ka_cdrc_ncdrc", "ka_state_cdrc", "ncdrc", "AppealableTo", "appellate_chain", "State CDRC appeals to NCDRC"),
        rel("ka_city_civil_hc", "city_civil_court_bangalore", "hc_karnataka", "AppealableTo", "appellate_chain", "City civil appeals to Karnataka HC"),
        rel("ka_district_hc", "ka_district_court_bengaluru_urban", "hc_karnataka", "AppealableTo", "appellate_chain", "District appeals to HC"),
        rel("ka_supervise", "hc_karnataka", "ka_district_court_bengaluru_urban", "AdministrativeSupervision", "supervisory", "Article 235 supervision (representative edge)"),
        rel("ka_fund_kerc", "government_karnataka", "kerc", "PrimaryFunder", "funding", "State funding"),
        rel("ka_fund_rera", "government_karnataka", "ka_rera", "PrimaryFunder", "funding", "State funding"),
        rel("ka_sja_train", "ka_sja", "ka_district_court_mysuru", "ProvidesContinuingEducation", "training", "Judicial academy"),
        rel("ka_slsa_adr", "ka_slsa", "lok_adalat_generic", "Designates", "statutory_ref", "KAR SLSA lok adalat"),
    ]
    for dist_eid, bench_id in KA_DISTRICT_TO_BENCH.items():
        ka_rels.append(
            rel(f"ka_{dist_eid}_appealable_{bench_id}", dist_eid, bench_id, "AppealableTo", "appellate_chain", "District appeals to Dharwad bench"),
        )
        ka_rels.append(
            rel(f"ka_{bench_id}_supervise_{dist_eid}", bench_id, dist_eid, "AdministrativeSupervision", "supervisory", "Article 235 (Dharwad bench)"),
        )

    def dump_rels(name: str, items: list, header: str | None = None) -> None:
        p = REL / name
        with open(p, "w", encoding="utf-8") as f:
            f.write(header or "# JEM generated relationships — data_quality: partial\n")
            yaml.safe_dump({"relationships": items}, f, sort_keys=False, allow_unicode=True)

    national_rels: list = list(bench_rels)
    skip_light = {"MH", "DL", "KA", "TN", "PY"}
    for code in STATES_28:
        if code in skip_light:
            continue
        emit_light_state_pack(ENT, code, STATE_TO_HC_ID[code], national_rels)
    for code in UT_EXTRA:
        emit_light_state_pack(ENT, code, STATE_TO_HC_ID[code], national_rels)

    # Second-district stubs routed to HC benches where applicable
    for dist_eid, bench_id in {**UP_DISTRICT_TO_BENCH, **WB_DISTRICT_TO_BENCH, **RJ_DISTRICT_TO_BENCH}.items():
        national_rels.append(
            rel(f"nat_{dist_eid}_appealable_{bench_id}", dist_eid, bench_id, "AppealableTo", "appellate_chain", "Second district appeals to HC bench"),
        )
        national_rels.append(
            rel(f"nat_{bench_id}_supervise_{dist_eid}", bench_id, dist_eid, "AdministrativeSupervision", "supervisory", "Article 235 (bench)"),
        )

    dump_rels("national_state_chains.yaml", national_rels)
    dump_rels("mh_relationships.yaml", mh_rels)
    dump_rels("dl_relationships.yaml", dl_rels)
    dump_rels("ka_relationships.yaml", ka_rels)
    dump_rels("tn_relationships.yaml", tn_rels)
    dump_rels("py_relationships.yaml", py_rels)
    for rel_name in (
        "adr_arbitration_relationships.yaml",
        "central_tribunal_regulator_relationships.yaml",
    ):
        rel_seed = SEEDS_REL / rel_name
        if rel_seed.is_file():
            shutil.copy2(rel_seed, REL / rel_name)

    adr_seed = SEEDS_REL / "adr_arbitration_relationships.yaml"
    if not adr_seed.is_file():
        dump_rels(
            "adr_arbitration_relationships.yaml",
            adr_arbitration_relationships(),
            header=(
                "# JEM relationships — ADR & Arbitration cluster (backbone)\n"
                "# Track E (§4) — generated by generate_v1_states_bundle.py\n"
                "# EstablishedUnder → statute deferred until act entities exist in graph.\n"
            ),
        )

    print(
        f"Wrote entities under {ENT} and relationships "
        "(mh/dl/ka/tn/py, national_state_chains, adr_arbitration)"
    )


if __name__ == "__main__":
    main()
