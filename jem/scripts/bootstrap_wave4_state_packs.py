#!/usr/bin/env python3
"""Bootstrap Wave 4 core state packs (NE + CG/GA/HP/JH/UK). Idempotent — skips existing entity files."""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STATES = ROOT / "data" / "entities" / "_generated" / "states"
RELS = ROOT / "data" / "relationships"

SRC = {
    "label": "India Code — Constitution & Acts",
    "url": "https://india-code.nic.in/",
    "type": "GoIWebsite",
    "accessed_date": "2026-06-15",
}

# hc: default appellate HC; district_overrides: slug -> bench HC
WAVE4: dict[str, dict] = {
    "as": {
        "hc": "hc_gauhati",
        "districts": ["guwahati", "jorhat", "silchar", "dibrugarh", "nagaon", "tezpur"],
        "cdrc": ["guwahati", "dibrugarh", "jorhat", "silchar"],
    },
    "ar": {
        "hc": "hc_gauhati_bench_itanagar",
        "districts": ["itanagar", "naharlagun", "pasighat", "ziro", "tezu"],
        "cdrc": ["itanagar", "naharlagun", "pasighat", "tezu"],
    },
    "ml": {
        "hc": "hc_meghalaya",
        "districts": ["shillong", "tura", "jowai", "nongstoin", "baghmara"],
        "cdrc": ["shillong", "tura", "jowai", "nongstoin"],
    },
    "mn": {
        "hc": "hc_manipur",
        "districts": ["imphal", "bishnupur", "churachandpur", "ukhrul", "thoubal"],
        "cdrc": ["imphal", "bishnupur", "churachandpur", "thoubal"],
    },
    "mz": {
        "hc": "hc_gauhati_bench_aizawl",
        "districts": ["aizawl", "lunglei", "champhai", "serchhip", "kolasib"],
        "cdrc": ["aizawl", "lunglei", "champhai", "serchhip"],
    },
    "nl": {
        "hc": "hc_gauhati",
        "districts": ["kohima", "dimapur", "mokokchung", "wokha", "tuensang"],
        "cdrc": ["kohima", "dimapur", "mokokchung", "wokha"],
    },
    "tr": {
        "hc": "hc_tripura",
        "districts": ["agartala", "dharmanagar", "udaipur", "ambassa", "kailashahar"],
        "cdrc": ["agartala", "dharmanagar", "udaipur", "ambassa"],
    },
    "cg": {
        "hc": "hc_chhattisgarh",
        "districts": ["raipur", "bilaspur", "durg", "korba", "raigarh", "jagdalpur"],
        "cdrc": ["raipur", "bilaspur", "durg", "korba"],
    },
    "ga": {
        "hc": "hc_bombay_bench_panaji",
        "districts": ["north_goa", "south_goa", "panaji", "margao", "mapusa", "vasco"],
        "cdrc": ["panaji", "margao", "mapusa", "vasco"],
    },
    "hp": {
        "hc": "hc_himachal_pradesh",
        "districts": ["shimla", "dharamshala", "mandi", "solan", "kullu", "una"],
        "cdrc": ["shimla", "dharamshala", "mandi", "solan"],
    },
    "jh": {
        "hc": "hc_jharkhand",
        "districts": ["ranchi", "jamshedpur", "dhanbad", "bokaro", "hazaribagh", "deoghar"],
        "cdrc": ["ranchi", "jamshedpur", "dhanbad", "bokaro"],
    },
    "uk": {
        "hc": "hc_uttarakhand",
        "districts": ["dehradun", "nainital", "haridwar", "haldwani", "roorkee", "pauri"],
        "cdrc": ["dehradun", "nainital", "haridwar", "haldwani"],
    },
}

NAMES = {
    "as": "Assam", "ar": "Arunachal Pradesh", "ml": "Meghalaya", "mn": "Manipur",
    "mz": "Mizoram", "nl": "Nagaland", "tr": "Tripura", "cg": "Chhattisgarh",
    "ga": "Goa", "hp": "Himachal Pradesh", "jh": "Jharkhand", "uk": "Uttarakhand",
}


def write_if_missing(path: Path, doc: dict) -> bool:
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True))
    return True


def core_entity(st: str, eid: str, name: str, etype: str, cluster: str) -> dict:
    return {
        "id": eid,
        "name": name,
        "type": etype,
        "cluster": cluster,
        "level_of_government": "State",
        "jurisdiction_scope": {"states_covered": [st.upper()], "is_all_india": False},
        "created_year": 1961,
        "operational_status": "Active",
        "statutory_basis": "See data_quality_notes",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {
            "audited_by": "cag_india",
            "audit_type": "CAG_Statutory",
            "audit_report_public": True,
        },
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [dict(SRC)],
    }


def district_court(st: str, slug: str) -> dict:
    nice = slug.replace("_", " ").title()
    return {
        "id": f"{st}_district_court_{slug}",
        "name": f"District & Sessions Court — {nice}",
        "type": "SubordinateCivilCourt",
        "cluster": "subordinate_courts",
        "level_of_government": "State",
        "jurisdiction_scope": {
            "states_covered": [st.upper()],
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
        "data_quality": "partial",
        "data_quality_notes": "Pendency TBD from NJDG district dashboard.",
        "sources": [dict(SRC)],
    }


def district_cdrc(st: str, slug: str) -> dict:
    nice = slug.replace("_", " ").title()
    return {
        "id": f"{st}_cdrc_{slug}",
        "name": f"{nice} District Consumer Disputes Redressal Commission",
        "type": "ConsumerCommission",
        "cluster": "tribunals_adr",
        "level_of_government": "State",
        "jurisdiction_scope": {"states_covered": [st.upper()], "is_all_india": False},
        "created_year": 2019,
        "operational_status": "Active",
        "statutory_basis": "Consumer Protection Act 2019 — District commissions",
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {
            "audited_by": "cag_india",
            "audit_type": "CAG_Statutory",
            "audit_report_public": True,
        },
        "complaint_mechanism": {"bias_complaint_to": [], "lokpal_jurisdiction": "Not_Applicable"},
        "data_quality": "partial",
        "sources": [dict(SRC)],
    }


def rel(
    rid: str,
    source: str,
    target: str,
    rtype: str,
    category: str,
    notes: str,
    *,
    constitutional: bool = False,
) -> dict:
    d = {
        "id": rid,
        "source": source,
        "target": target,
        "relationship_type": rtype,
        "relationship_category": category,
        "is_binding": True,
        "is_constitutional": constitutional,
        "notes": notes,
        "data_quality": "partial",
        "sources": [dict(SRC)],
    }
    return d


def slsa_id(st: str) -> str:
    p = STATES / st
    if (p / f"slsa_{st}.yaml").exists():
        return f"slsa_{st}"
    if (p / f"{st}_slsa.yaml").exists():
        return f"{st}_slsa"
    return f"slsa_{st}"


def build_relationships(st: str, cfg: dict) -> list[dict]:
    hc = cfg["hc"]
    gov = f"government_{st}"
    rera = f"rera_{st}"
    serc = f"serc_{st}"
    out: list[dict] = [
        rel(f"{st}_cdrc_ncdrc", f"{st}_state_cdrc", "ncdrc", "AppealableTo", "appellate_chain", f"{st.upper()} SCDRC to NCDRC"),
        rel(f"{st}_slsa_lok", slsa_id(st), "lok_adalat_generic", "Designates", "statutory_ref", f"{st.upper()} SLSA lok adalat"),
        rel(f"{st}_fund_rera", gov, rera, "PrimaryFunder", "funding", f"{st.upper()} RERA funding"),
        rel(f"{st}_fund_serc", gov, serc, "PrimaryFunder", "funding", f"{st.upper()} SERC funding"),
        rel(f"{st}_serc_aptel", serc, "aptel", "AppealableTo", "appellate_chain", f"{st.upper()} SERC to APTEL"),
        rel(
            f"{st}_dist_principal_hc",
            f"{st}_district_court_principal",
            hc,
            "AppealableTo",
            "appellate_chain",
            f"{st.upper()} principal district to HC",
        ),
        rel(
            f"{st}_hc_super_principal",
            hc.split("_bench_")[0] if "_bench_" in hc else hc,
            f"{st}_district_court_principal",
            "AdministrativeSupervision",
            "supervisory",
            f"HC supervision {st.upper()} principal",
        ),
        rel(
            f"{st}_district_courts_generic_hc",
            f"{st}_district_courts_generic",
            hc.split("_bench_")[0] if "_bench_" in hc else hc,
            "AppealableTo",
            "appellate_chain",
            f"{st.upper()} district rollup to HC",
        ),
        rel(
            f"{st}_hc_super_district_courts_generic",
            hc.split("_bench_")[0] if "_bench_" in hc else hc,
            f"{st}_district_courts_generic",
            "AdministrativeSupervision",
            "supervisory",
            f"HC supervision {st.upper()} rollup",
        ),
        rel(
            f"{st}_sja_train",
            f"{st}_sja",
            f"{st}_district_court_principal",
            "ProvidesContinuingEducation",
            "training",
            f"{st.upper()} judicial academy training",
        ),
    ]
    parent_hc = hc.split("_bench_")[0] if "_bench_" in hc else hc
    for slug in cfg["districts"]:
        eid = f"{st}_district_court_{slug}"
        if not (STATES / st / f"{eid}.yaml").exists():
            continue
        out.append(rel(f"{st}_{slug}_hc", eid, hc, "AppealableTo", "appellate_chain", f"{st.upper()} {slug} appellate"))
        out.append(
            rel(
                f"{st}_hc_super_{slug}",
                parent_hc,
                eid,
                "AdministrativeSupervision",
                "supervisory",
                f"HC supervision {slug}",
            )
        )
    for slug in cfg["cdrc"]:
        out.append(
            rel(
                f"{st}_cdrc_{slug}_scdrc",
                f"{st}_cdrc_{slug}",
                f"{st}_state_cdrc",
                "AppealableTo",
                "appellate_chain",
                f"{slug} DCDRC to {st.upper()} SCDRC",
            )
        )
    return out


def bootstrap_state(st: str, cfg: dict) -> tuple[int, int]:
    created = 0
    sn = NAMES[st]
    core_specs = [
        (f"{st}_bar_council", f"Bar Council of {st.upper()}", "ProfessionalBody", "training_professional", "Advocates Act 1961"),
        (f"{st}_sja", f"{sn} State Judicial Academy", "TrainingBody", "training_professional", "State judicial training institute"),
        (f"{st}_advocate_general", f"Advocate General — {sn}", "ExecutiveBody", "executive_interface", "Constitution of India Article 165"),
        (f"{st}_special_courts", f"{sn} Special Courts (generic)", "SubordinateCivilCourt", "subordinate_courts", "Special courts under central/state statutes"),
    ]
    for eid, name, etype, cluster, basis in core_specs:
        doc = core_entity(st, eid, name, etype, cluster)
        doc["statutory_basis"] = basis
        if write_if_missing(STATES / st / f"{eid}.yaml", doc):
            created += 1
    for slug in cfg["districts"]:
        if write_if_missing(STATES / st / f"{st}_district_court_{slug}.yaml", district_court(st, slug)):
            created += 1
    for slug in cfg["cdrc"]:
        if write_if_missing(STATES / st / f"{st}_cdrc_{slug}.yaml", district_cdrc(st, slug)):
            created += 1
    rel_path = RELS / f"{st}_relationships.yaml"
    rel_path.write_text(yaml.dump({"relationships": build_relationships(st, cfg)}, sort_keys=False))
    return created, len(build_relationships(st, cfg))


def main() -> None:
    total_e = total_r = 0
    for st, cfg in WAVE4.items():
        e, r = bootstrap_state(st, cfg)
        print(f"{st}: +{e} entities, {r} rel edges")
        total_e += e
        total_r += r
    print(f"TOTAL: +{total_e} entity files, {len(WAVE4)} relationship packs")


if __name__ == "__main__":
    main()
