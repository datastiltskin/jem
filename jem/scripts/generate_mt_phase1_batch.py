#!/usr/bin/env python3
"""One-off generator: M-T1..M-T6 + Phase 1 (Jun 2026). Run from jem/."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ENT = ROOT / "data" / "entities" / "_generated"
REL = ROOT / "data" / "relationships"
SRC = {
    "label": "India Code — Constitution & Acts",
    "url": "https://india-code.nic.in/",
    "type": "GoIWebsite",
    "accessed_date": "2026-06-12",
}
DOJ_HC = {
    "label": "DoJ — High Courts of India",
    "url": "https://doj.gov.in/high-courts/",
    "type": "GoIWebsite",
    "accessed_date": "2026-06-12",
}


def W(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(data, sort_keys=False, allow_unicode=True, width=120))


def rel(rid, src, tgt, rtype, cat, notes, binding=True, constitutional=False):
    return {
        "id": rid,
        "source": src,
        "target": tgt,
        "relationship_type": rtype,
        "relationship_category": cat,
        "is_binding": binding,
        "is_constitutional": constitutional,
        "notes": notes,
        "data_quality": "partial",
        "sources": [SRC],
    }


# ── M-T1: ITAT benches ───────────────────────────────────────────────────────

ITAT_BENCHES = [
    ("itat_delhi", "Delhi", "hc_delhi", ["DL"], []),
    ("itat_mumbai", "Mumbai", "hc_bombay", ["MH"], []),
    ("itat_ahmedabad", "Ahmedabad", "hc_gujarat", ["GJ"], []),
    ("itat_bangalore", "Bangalore", "hc_karnataka", ["KA"], []),
    ("itat_chennai", "Chennai", "hc_madras", ["TN"], []),
    ("itat_hyderabad", "Hyderabad", "hc_telangana", ["TS"], ["hc_andhra_pradesh"]),
    ("itat_kolkata", "Kolkata", "hc_calcutta", ["WB"], []),
    ("itat_pune", "Pune", "hc_bombay", ["MH"], []),
    ("itat_nagpur", "Nagpur", "hc_bombay", ["MH"], []),
    ("itat_jaipur", "Jaipur", "hc_rajasthan", ["RJ"], []),
    ("itat_chandigarh", "Chandigarh", "hc_punjab_haryana", ["CH", "PB", "HR"], []),
    ("itat_allahabad", "Allahabad", "hc_allahabad", ["UP"], []),
    ("itat_lucknow", "Lucknow", "hc_allahabad", ["UP"], []),
    ("itat_guwahati", "Guwahati", "hc_gauhati", ["AS", "AR", "NL", "MZ"], []),
    ("itat_cuttack", "Cuttack", "hc_orissa", ["OD"], []),
    ("itat_amritsar", "Amritsar", "hc_punjab_haryana", ["PB"], []),
    ("itat_visakhapatnam", "Visakhapatnam", "hc_andhra_pradesh", ["AP"], []),
    ("itat_ranchi", "Ranchi", "hc_jharkhand", ["JH"], []),
    ("itat_jodhpur", "Jodhpur", "hc_rajasthan", ["RJ"], []),
    ("itat_indore", "Indore", "hc_madhya_pradesh", ["MP"], []),
    ("itat_bhopal", "Bhopal", "hc_madhya_pradesh", ["MP"], []),
    ("itat_aurangabad", "Aurangabad", "hc_bombay", ["MH"], []),
    ("itat_kochi", "Kochi", "hc_kerala", ["KL"], []),
    ("itat_thiruvananthapuram", "Thiruvananthapuram", "hc_kerala", ["KL", "LD"], []),
    ("itat_patna", "Patna", "hc_patna", ["BR"], []),
]


def itat_bench_doc(eid: str, city: str, states: list, uts: list) -> dict:
    return {
        "id": eid,
        "name": f"Income Tax Appellate Tribunal — {city} Bench",
        "abbreviation": f"ITAT {city}",
        "aliases": [f"ITAT Bench {city}"],
        "type": "CentralTribunal",
        "cluster": "tribunals_adr",
        "level_of_government": "Central",
        "created_year": 1941,
        "operational_status": "Active",
        "statutory_basis": "Income Tax Act 1961 s.252 — ITAT benches constituted by Central Government",
        "appointment": {
            "nominates": "central_government",
            "formally_appoints": "central_government",
            "consulted": ["supreme_court_india"],
            "consultation_binding": False,
            "criteria_public": True,
            "tenure": "4 years or age 70 — Tribunals Reforms Act 2021",
            "reappointment_possible": False,
            "removal_authority": "central_government",
            "removal_requires_parliament": False,
            "removal_independent_committee": True,
        },
        "funding": {
            "primary_source": "Consolidated_Fund_India",
            "ministry_responsible": "ministry_of_finance",
        },
        "audit": {
            "audited_by": "cag_india",
            "audit_type": "CAG_Statutory",
            "audit_report_public": True,
        },
        "complaint_mechanism": {
            "bias_complaint_to": [],
            "lokpal_jurisdiction": "No",
            "lokpal_jurisdiction_note": "ITAT members — tribunal member Lokpal treatment",
        },
        "jurisdiction_scope": {
            "states_covered": states,
            "uts_covered": uts,
            "is_all_india": False,
            "jurisdiction_types": ["income_tax_appeals"],
        },
        "data_quality": "partial",
        "data_quality_notes": (
            f"ITAT {city} bench. Appeal on substantial question of law to HC per IT Act s.260A. "
            "Zone jurisdiction per CBDT/ITAT bench allocation — verify at itat.gov.in."
        ),
        "sources": [
            {
                "label": "Income Tax Act 1961 s.252–260A",
                "url": "https://www.india-code.nic.in/CodeofActs/1961/1961_43.pdf",
                "type": "CentralAct",
                "accessed_date": "2026-06-12",
            },
            {
                "label": "ITAT official website",
                "url": "https://itat.gov.in",
                "type": "GoIWebsite",
                "accessed_date": "2026-06-12",
            },
        ],
    }


def generate_itat() -> list:
    rels = []
    bench_dir = ENT / "backbone"
    for eid, city, hc, states, extra_hcs in ITAT_BENCHES:
        uts = [s for s in states if s in {"DL", "CH", "LD", "PY", "AN", "LA", "JK", "DD", "DN"}]
        st = [s for s in states if s not in uts]
        W(bench_dir / f"{eid}.yaml", itat_bench_doc(eid, city, st, uts))
        rels.append(rel(f"rel_{eid}_benchof_itat", eid, "itat", "BenchOf", "statutory_ref", f"ITAT {city} bench"))
        rels.append(
            rel(
                f"rel_{eid}_to_{hc}",
                eid,
                hc,
                "AppealableTo",
                "appellate_chain",
                f"ITAT {city} → HC on question of law (IT Act s.260A)",
            )
        )
        for eh in extra_hcs:
            rels.append(
                rel(
                    f"rel_{eid}_to_{eh}",
                    eid,
                    eh,
                    "AppealableTo",
                    "appellate_chain",
                    f"ITAT {city} — dual HC jurisdiction post-bifurcation",
                )
            )
    return rels


# ── M-T2: DRT aliases ────────────────────────────────────────────────────────

DRT_BENCH_ALIASES = {
    "drt_chennai": (3, ["DRT-II Chennai", "DRT-III Chennai"]),
    "drt_hyderabad": (3, ["DRT-III Hyderabad"]),
    "drt_chandigarh": (2, ["DRT-III Chandigarh"]),
    "drt_ahmedabad": (2, ["DRT-III Ahmedabad"]),
    "drt_mumbai": (3, ["DRT-I Mumbai", "DRT-II Mumbai", "DRT-III Mumbai"]),
    "drt_delhi": (3, ["DRT-I Delhi", "DRT-II Delhi", "DRT-III Delhi"]),
    "drt_kolkata": (3, ["DRT-I Kolkata", "DRT-II Kolkata", "DRT-III Kolkata"]),
    "drt_bengaluru": (2, ["DRT-II Bengaluru", "DRT-III Bengaluru"]),
}


def patch_drt_aliases() -> None:
    for fname, (count, add_aliases) in DRT_BENCH_ALIASES.items():
        path = ENT / "backbone" / f"{fname}.yaml"
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text())
        aliases = list(data.get("aliases") or [])
        for a in add_aliases:
            if a not in aliases:
                aliases.append(a)
        data["aliases"] = aliases
        note = (
            f"Option B rollup: {count} physical DRT(s) at this location (DRT-I/II/III) "
            "rolled into single city entity per MoF composition table; see drt.etribunals.gov.in."
        )
        existing = (data.get("data_quality_notes") or "").strip()
        if "Option B rollup" not in existing:
            data["data_quality_notes"] = (existing + "\n" + note).strip() if existing else note
        W(path, data)


# ── M-T4: state labour court ─────────────────────────────────────────────────

def generate_state_labour_court() -> None:
    W(
        ENT / "backbone" / "state_labour_court_generic.yaml",
        {
            "id": "state_labour_court_generic",
            "name": "State Labour Court — Generic",
            "abbreviation": "SLC",
            "type": "StateTribunal",
            "cluster": "tribunals_adr",
            "level_of_government": "State",
            "created_year": 1947,
            "operational_status": "Active",
            "statutory_basis": "Industrial Disputes Act 1947 s.7 — State Government labour courts",
            "appointment": {
                "formally_appoints": "governor_state",
                "removal_authority": "governor_state",
            },
            "funding": {"primary_source": "State_Consolidated_Fund"},
            "audit": {"audited_by": "cag_india", "audit_type": "CAG_Performance", "audit_report_public": True},
            "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Contested"},
            "data_quality": "partial",
            "data_quality_notes": (
                "Generic scaffold. IRC 2020 notified but not in force as of Jun 2026; IDA 1947 remains operative."
            ),
            "sources": [SRC],
        },
    )


# ── M-T5: CESTAT quality ───────────────────────────────────────────────────────

def patch_cestat_quality() -> None:
    extra_source = {
        "label": "CESTAT official website — bench listing",
        "url": "https://cestat.gov.in",
        "type": "GoIWebsite",
        "accessed_date": "2026-06-12",
    }
    for path in (ENT / "backbone").glob("cestat_*.yaml"):
        data = yaml.safe_load(path.read_text())
        sources = data.get("sources") or []
        if not any(s.get("url", "").startswith("https://cestat.gov.in") for s in sources):
            sources.append(extra_source)
        data["sources"] = sources
        notes = (data.get("data_quality_notes") or "").strip()
        if "Quality pass Jun 2026" not in notes:
            data["data_quality_notes"] = (
                notes + "\nQuality pass Jun 2026: jurisdiction from Registrar Notifications 01–03/2015; cestat.gov.in source added."
            ).strip()
        W(path, data)


# ── M-T3 / M-T6 patches ───────────────────────────────────────────────────────

def patch_gstat_m6() -> None:
    gstat = yaml.safe_load((ENT / "backbone" / "gstat.yaml").read_text())
    notes = gstat.get("data_quality_notes", "")
    if "M-T3 watch Jun 2026" not in notes:
        gstat["data_quality_notes"] = (
            notes + "\nM-T3 watch Jun 2026: still Not_Constituted; monitor egazette.gov.in and CBIC for bench notifications."
        ).strip()
    W(ENT / "backbone" / "gstat.yaml", gstat)

    aft = yaml.safe_load((ENT / "backbone" / "aft_srinagar.yaml").read_text())
    notes = aft.get("data_quality_notes", "")
    if "M-T6 review Jun 2026" not in notes:
        aft["data_quality_notes"] = (
            notes + "\nM-T6 review Jun 2026: no post-2019 Ladakh gazette found; LA remains provisional in uts_covered."
        ).strip()
    W(ENT / "backbone" / "aft_srinagar.yaml", aft)

    itat = yaml.safe_load((ENT / "backbone" / "itat.yaml").read_text())
    zone_table = (
        "ITAT bench → HC mapping (IT Act s.260A, Jun 2026): Delhi→hc_delhi; Mumbai/Pune/Nagpur/Aurangabad→hc_bombay; "
        "Chennai→hc_madras; Kolkata→hc_calcutta; Ahmedabad→hc_gujarat; Hyderabad→hc_telangana+hc_andhra_pradesh; "
        "Visakhapatnam→hc_andhra_pradesh; Bangalore→hc_karnataka; Allahabad/Lucknow→hc_allahabad; "
        "Chandigarh/Amritsar→hc_punjab_haryana; Guwahati→hc_gauhati; Patna→hc_patna; Ranchi→hc_jharkhand; "
        "Bhopal/Indore→hc_madhya_pradesh; Jaipur/Jodhpur→hc_rajasthan; Cuttack→hc_orissa; Kochi/Trivandrum→hc_kerala. "
        "Per-bench entities itat_* wired in itat_bench_relationships.yaml."
    )
    notes = itat.get("data_quality_notes", "")
    if "ITAT bench → HC mapping" not in notes:
        itat["data_quality_notes"] = (notes + "\n" + zone_table).strip()
    W(ENT / "backbone" / "itat.yaml", itat)


# ── P1-A: digital infrastructure ─────────────────────────────────────────────

def generate_p1a() -> None:
    digital = [
        (
            "e_committee_sc",
            "e-Committee of the Supreme Court of India",
            "ExecutiveBody",
            "digital_infrastructure",
            2004,
            "Supreme Court e-Committee — digitisation and e-Courts policy coordination",
        ),
        (
            "nic_india",
            "National Informatics Centre (NIC)",
            "ExecutiveBody",
            "digital_infrastructure",
            1976,
            "Ministry of Electronics and IT — national e-Governance infrastructure",
        ),
        (
            "ecourts_services_generic",
            "e-Courts Services (Generic)",
            "ExecutiveBody",
            "digital_infrastructure",
            2007,
            "e-Courts Phase I–III — case information system under e-Committee/DIS",
        ),
        (
            "njdg_generic",
            "National Judicial Data Grid (Generic)",
            "ExecutiveBody",
            "digital_infrastructure",
            2015,
            "NJDG — national pendency dashboard under e-Committee",
        ),
    ]
    for eid, name, etype, cluster, year, basis in digital:
        W(
            ENT / "backbone" / f"{eid}.yaml",
            {
                "id": eid,
                "name": name,
                "type": etype,
                "cluster": cluster,
                "level_of_government": "Central",
                "jurisdiction_scope": {"is_all_india": True, "jurisdiction_types": ["digital_infrastructure"]},
                "created_year": year,
                "operational_status": "Active",
                "statutory_basis": basis,
                "funding": {"primary_source": "Consolidated_Fund_India", "ministry_responsible": "department_of_justice"},
                "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
                "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
                "data_quality": "partial",
                "sources": [
                    SRC,
                    {
                        "label": "e-Committee / NJDG",
                        "url": "https://njdg.ecourts.gov.in/",
                        "type": "NJDG",
                        "accessed_date": "2026-06-12",
                    },
                ],
            },
        )


# ── P1-B: security bodies ────────────────────────────────────────────────────

def generate_p1b() -> None:
    security = [
        ("crpf", "Central Reserve Police Force", "Central armed police — court security and law and order"),
        ("cisf", "Central Industrial Security Force", "Central armed police — airport and PSU security"),
        ("state_police_generic", "State Police (Generic)", "State police forces under respective Police Acts"),
        ("court_marshal_sc", "Supreme Court — Court Martial Appellate Jurisdiction", "SC original/appellate jurisdiction over court martial before AFT Act 2007; writ review"),
        ("sheriff_hc_generic", "High Court Sheriff (Generic)", "Sheriff offices attached to High Courts for process service"),
    ]
    for eid, name, basis in security:
        W(
            ENT / "backbone" / f"{eid}.yaml",
            {
                "id": eid,
                "name": name,
                "type": "SecurityBody",
                "cluster": "executive_interface",
                "level_of_government": "Central" if eid in {"crpf", "cisf", "court_marshal_sc"} else "State",
                "jurisdiction_scope": {"is_all_india": True},
                "created_year": 1950,
                "operational_status": "Active",
                "statutory_basis": basis,
                "funding": {"primary_source": "Consolidated_Fund_India"},
                "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
                "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Contested"},
                "data_quality": "partial",
                "sources": [SRC],
            },
        )


# ── P1-C/D/E: state packs ────────────────────────────────────────────────────

STATE_PACKS = {
    "up": {
        "code": "UP",
        "hc": "hc_allahabad",
        "gov": "government_up",
        "rera_name": "Uttar Pradesh Real Estate Regulatory Authority (UP-RERA)",
        "districts": [
            ("lucknow", "Lucknow"),
            ("prayagraj", "Prayagraj"),
            ("ghaziabad", "Ghaziabad"),
            ("agra", "Agra"),
            ("meerut", "Meerut"),
            ("gorakhpur", "Gorakhpur"),
            ("bareilly", "Bareilly"),
        ],
        "bench_routes": {"up_district_court_varanasi": "hc_allahabad_bench_lucknow"},
    },
    "wb": {
        "code": "WB",
        "hc": "hc_calcutta",
        "gov": "government_wb",
        "rera_name": "West Bengal Real Estate Regulatory Authority (WB-RERA)",
        "districts": [
            ("kolkata", "Kolkata"),
            ("howrah", "Howrah"),
            ("darjeeling", "Darjeeling"),
            ("murshidabad", "Murshidabad"),
            ("nadia", "Nadia"),
        ],
        "bench_routes": {"wb_district_court_asansol": "hc_calcutta_bench_jalpaiguri"},
    },
    "rj": {
        "code": "RJ",
        "hc": "hc_rajasthan",
        "gov": "government_rj",
        "rera_name": "Rajasthan Real Estate Regulatory Authority (RERA Rajasthan)",
        "districts": [
            ("jodhpur", "Jodhpur"),
            ("udaipur", "Udaipur"),
            ("kota", "Kota"),
            ("ajmer", "Ajmer"),
            ("bikaner", "Bikaner"),
        ],
        "bench_routes": {"rj_district_court_jaipur": "hc_rajasthan_bench_jaipur"},
    },
}


def district_court(eid: str, name: str, state: str) -> dict:
    return {
        "id": eid,
        "name": name,
        "type": "SubordinateCivilCourt",
        "cluster": "subordinate_courts",
        "level_of_government": "State",
        "jurisdiction_scope": {"states_covered": [state], "is_all_india": False, "jurisdiction_types": ["Civil", "Criminal"]},
        "created_year": 1860,
        "operational_status": "Active",
        "constitutional_basis": "Constitution of India, Articles 233–237",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def state_pack_entity(st: str, code: str, kind: str) -> dict:
    templates = {
        "rera": {
            "id": f"{st}_rera",
            "name": STATE_PACKS[st]["rera_name"],
            "type": "RegulatoryBodyQJ",
            "cluster": "regulatory_bodies",
            "statutory_basis": "Real Estate (Regulation and Development) Act 2016 — state rules",
        },
        "bar_council": {
            "id": f"{st}_bar_council",
            "name": f"Bar Council of {STATE_PACKS[st]['code']}",
            "type": "ProfessionalBody",
            "cluster": "training_professional",
            "statutory_basis": "Advocates Act 1961",
        },
        "sja": {
            "id": f"{st}_sja",
            "name": f"State Judicial Academy — {STATE_PACKS[st]['code']}",
            "type": "TrainingBody",
            "cluster": "training_professional",
            "statutory_basis": "State judicial academy statutes / High Court administrative setup",
        },
        "lokayukta": {
            "id": f"{st}_lokayukta",
            "name": f"Lokayukta — {STATE_PACKS[st]['code']}",
            "type": "ExecutiveBody",
            "cluster": "executive_interface",
            "statutory_basis": f"{STATE_PACKS[st]['code']} Lokayukta Act",
        },
        "advocate_general": {
            "id": f"{st}_advocate_general",
            "name": f"Advocate General — {STATE_PACKS[st]['code']}",
            "type": "ExecutiveBody",
            "cluster": "executive_interface",
            "statutory_basis": "Constitution of India Article 165",
        },
        "special_courts": {
            "id": f"{st}_special_courts",
            "name": f"{STATE_PACKS[st]['code']} — Special courts pool (PMLA / POCSO / NIA / SC-ST)",
            "type": "SpecialCourt",
            "cluster": "subordinate_courts",
            "statutory_basis": "Special statutes — aggregated node",
        },
    }
    base = templates[kind]
    return {
        **base,
        "level_of_government": "State",
        "jurisdiction_scope": {"states_covered": [code], "is_all_india": False},
        "created_year": 2017 if kind == "rera" else 1961,
        "operational_status": "Active",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {"audited_by": "cag_india", "audit_type": "CAG_Statutory", "audit_report_public": True},
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable" if kind != "lokayukta" else "Yes"},
        "data_quality": "partial",
        "sources": [SRC],
    }


def generate_state_packs() -> dict[str, list]:
    all_rels: dict[str, list] = {}
    for st, cfg in STATE_PACKS.items():
        base = ENT / "states" / st
        for kind in ("rera", "bar_council", "sja", "lokayukta", "advocate_general", "special_courts"):
            W(base / f"{state_pack_entity(st, cfg['code'], kind)['id']}.yaml", state_pack_entity(st, cfg["code"], kind))
        for slug, dname in cfg["districts"]:
            eid = f"{st}_district_court_{slug}"
            W(base / f"{eid}.yaml", district_court(eid, f"District & Sessions Court — {dname}", cfg["code"]))

        rels = []
        rels.append(rel(f"{st}_cdrc_ncdrc", f"{st}_state_cdrc", "ncdrc", "AppealableTo", "appellate_chain", f"{cfg['code']} SCDRC to NCDRC"))
        rels.append(rel(f"{st}_slsa_lok", f"slsa_{st}", "lok_adalat_generic", "Designates", "statutory_ref", f"{cfg['code']} SLSA lok adalat"))
        rels.append(rel(f"{st}_fund_rera", cfg["gov"], f"{st}_rera", "PrimaryFunder", "funding", f"{cfg['code']} RERA funding"))
        pr_id = f"{st}_district_court_principal"
        rels.append(rel(f"{st}_dist_principal_hc", pr_id, cfg["hc"], "AppealableTo", "appellate_chain", f"{cfg['code']} principal district to HC"))
        rels.append(rel(f"{st}_hc_super_principal", cfg["hc"], pr_id, "AdministrativeSupervision", "supervisory", f"HC supervision {cfg['code']} principal"))
        for slug, _ in cfg["districts"]:
            eid = f"{st}_district_court_{slug}"
            bench = cfg["bench_routes"].get(eid, cfg["hc"])
            rels.append(rel(f"{st}_{slug}_hc", eid, bench, "AppealableTo", "appellate_chain", f"{cfg['code']} {slug} district appellate"))
            rels.append(rel(f"{st}_hc_super_{slug}", cfg["hc"], eid, "AdministrativeSupervision", "supervisory", f"HC supervision {slug}"))
        for dist_id, bench_id in cfg["bench_routes"].items():
            if dist_id not in {f"{st}_district_court_{s}" for s, _ in cfg["districts"]}:
                rels.append(rel(f"{st}_{dist_id}_hc", dist_id, bench_id, "AppealableTo", "appellate_chain", f"{cfg['code']} bench routing"))
                rels.append(rel(f"{st}_hc_super_{dist_id}", cfg["hc"], dist_id, "AdministrativeSupervision", "supervisory", f"HC supervision {dist_id}"))
        all_rels[st] = rels
    return all_rels


# ── P1-G: NE HC quality ──────────────────────────────────────────────────────

NE_HCS = [
    "hc_gauhati",
    "hc_manipur",
    "hc_meghalaya",
    "hc_tripura",
    "hc_mizoram",
    "hc_sikkim",
    "hc_arunachal_pradesh",
]


def patch_ne_hcs() -> None:
    for hid in NE_HCS:
        path = ENT / "high_courts" / f"{hid}.yaml"
        if not path.exists():
            continue
        data = yaml.safe_load(path.read_text())
        sources = data.get("sources") or []
        if not any("doj.gov.in/high-courts" in s.get("url", "") for s in sources):
            sources.append(DOJ_HC)
        data["sources"] = sources
        notes = (data.get("data_quality_notes") or "").strip()
        if "P1-G NE quality pass Jun 2026" not in notes:
            data["data_quality_notes"] = (notes + "\nP1-G NE quality pass Jun 2026: DoJ HC listing source added.").strip()
        W(path, data)


def remove_aggregate_itat_edge() -> None:
    path = REL / "tribunal_completion_jun2026.yaml"
    text = path.read_text()
    text = re.sub(
        r"\n  - id: rel_itat_to_high_courts_all\n.*?(?=\n  - id:|\n  # ═|$)",
        "\n",
        text,
        flags=re.DOTALL,
    )
    path.write_text(text)


def main() -> None:
    itat_rels = generate_itat()
    W(REL / "itat_bench_relationships.yaml", {"relationships": itat_rels})
    remove_aggregate_itat_edge()
    patch_drt_aliases()
    generate_state_labour_court()
    patch_cestat_quality()
    patch_gstat_m6()
    generate_p1a()
    generate_p1b()
    pack_rels = generate_state_packs()
    for st, rels in pack_rels.items():
        W(REL / f"{st}_relationships.yaml", {"relationships": rels})
    patch_ne_hcs()
    print("Generated M-T1..M-T6 + Phase 1 batch")


if __name__ == "__main__":
    main()
