#!/usr/bin/env python3
"""One-shot merge: Claude Phase-2 deliverables D1, D2, D4 (D3/D5 separate files)."""
from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ENT = ROOT / "data" / "entities"
SERC_DIR = ENT / "_generated" / "regulatory_bodies" / "serc_states"
STATES = ENT / "_generated" / "states"

SRC_INDIA = {
    "label": "India Code — Constitution & Acts",
    "url": "https://india-code.nic.in/",
    "type": "GoIWebsite",
    "accessed_date": "2026-06-15",
}

LOKAYUKTA: dict[str, dict] = {
    "ap": {"status": "Active", "year": 1983, "act": "Andhra Pradesh Lokayukta and Upa-Lokayuktas Act 1983", "url": "https://www.aplokayukta.ap.gov.in/", "note": "Reconstituted post-bifurcation 2014."},
    "as": {"status": "Active", "year": 1985, "act": "Assam Lokayukta Act 1985", "url": "https://assamlokayukta.gov.in/", "note": None},
    "br": {"status": "Active", "year": 1973, "act": "Bihar Lokayukta Act 1973", "url": "https://lokayukta.bih.nic.in/", "note": None},
    "cg": {"status": "Active", "year": 2001, "act": "Chhattisgarh Lokayukta Evam Up-Lokayukta Adhiniyam 2001", "url": "https://cglokayukta.gov.in/", "note": None},
    "ga": {"status": "Active", "year": 2011, "act": "Goa Lokayukta Act 2011", "url": "https://lokayuktagoa.nic.in/", "note": None},
    "gj": {"status": "Active", "year": 1986, "act": "Gujarat Lokayukta Act 1986", "url": "https://lokayuktagujarat.gov.in/", "note": None},
    "hr": {"status": "Active", "year": 2002, "act": "Haryana Lokayukta Act 2002", "url": "https://www.haryana.gov.in/lokayukta", "note": None},
    "hp": {"status": "Active", "year": 1983, "act": "Himachal Pradesh Lokayukta Act 1983", "url": "https://hplokayukta.gov.in/", "note": None},
    "jh": {"status": "Active", "year": 2001, "act": "Jharkhand Lokayukta Act 2001", "url": "https://jhlokayukta.gov.in/", "note": None},
    "kl": {"status": "Active", "year": 1999, "act": "Kerala Lokayukta Act 1999", "url": "https://lokayukta.kerala.gov.in/", "note": None},
    "mp": {"status": "Active", "year": 1981, "act": "Madhya Pradesh Lokayukta Evam Up-Lokayuktas Adhiniyam 1981", "url": "https://www.mplokayukta.gov.in/", "note": None},
    "mn": {"status": "Active", "year": 2014, "act": "Manipur Lokayukta Act 2014", "url": "https://manipur.gov.in/", "note": "DG-L1: appointment history interrupted — verify incumbent; may be Not_Constituted."},
    "ml": {"status": "Not_Constituted", "year": None, "act": "Meghalaya Lokayukta Act 2014 (passed; notification status unverified)", "url": "https://meghalaya.gov.in/", "note": "DG-L4: upgrade if Act notified."},
    "mz": {"status": "Not_Constituted", "year": None, "act": "No Lokayukta Act enacted in Mizoram as of 2025", "url": "https://mizoram.gov.in/", "note": None},
    "nl": {"status": "Not_Constituted", "year": None, "act": "No Lokayukta Act enacted in Nagaland as of 2025", "url": "https://nagaland.gov.in/", "note": None},
    "od": {"status": "Active", "year": 1995, "act": "Odisha Lokayukta Act 1995", "url": "https://lokayukta.odisha.gov.in/", "note": None},
    "pb": {"status": "Active", "year": 1995, "act": "Punjab Lokayukta Act 1995", "url": "https://lokayuktapunjab.gov.in/", "note": None},
    "rj": {"status": "Active", "year": 1973, "act": "Rajasthan Lokayukta and Upa-Lokayuktas Act 1973", "url": "https://rajlokayukta.nic.in/", "note": None},
    "sk": {"status": "Not_Constituted", "year": None, "act": "No Lokayukta Act enacted in Sikkim as of 2025", "url": "https://sikkim.gov.in/", "note": None},
    "tn": {"status": "Active", "year": 2001, "act": "Tamil Nadu Lokayukta Act 2001", "url": "https://lokayukta.tn.gov.in/", "note": "Prior graph marked Not_Constituted; upgraded per state portal — maintainer verify."},
    "ts": {"status": "Active", "year": 2018, "act": "Telangana Lokayukta Act 2018", "url": "https://www.tslokayukta.gov.in/", "note": "Post-bifurcation Act; not inherited from AP."},
    "tr": {"status": "Active", "year": 1999, "act": "Tripura Lokayukta Act 1999", "url": "https://tripura.gov.in/lokayukta", "note": "DG-L3: appointment gaps reported — verify incumbent."},
    "up": {"status": "Active", "year": 1975, "act": "Uttar Pradesh Lokayukta and Upa-Lokayuktas Act 1975", "url": "https://uplokayukta.org/", "note": None},
    "uk": {"status": "Active", "year": 2002, "act": "Uttarakhand Lokayukta Act 2002", "url": "https://lokayuktauttarakhand.gov.in/", "note": None},
    "wb": {"status": "Active", "year": 2003, "act": "West Bengal Lokayukta Act 2003 (amended 2016)", "url": "https://wb.gov.in/", "note": "DG-L2: appointment controversy — verify operational state."},
    "py": {"status": "Not_Constituted", "year": None, "act": "No Lokayukta Act for Puducherry UT as of 2025", "url": "https://py.gov.in/", "note": "UT; Central Lokpal may cover applicable functionaries."},
    "jk": {"status": "Not_Constituted", "year": None, "act": "J&K Accountability Commission dissolved 2019; no UT Lokayukta substitute constituted", "url": "https://jk.gov.in/", "note": "DG-L5: post-2019 UT accountability structure."},
    "mh": {"status": "Active", "year": 1972, "act": "Maharashtra Lokayukta and Upa-Lokayuktas Act 1971", "url": "https://lokayuktamaharashtra.gov.in/", "note": None},
    "dl": {"status": "Active", "year": 1995, "act": "Delhi Lokayukta Act 1995", "url": "https://delhilokayukta.gov.in/", "note": None},
    "ka": {"status": "Active", "year": 1984, "act": "Karnataka Lokayukta Act 1984", "url": "https://lokayukta.kar.nic.in/", "note": None},
}

SERC_ROWS = [
    ("ap", "serc_ap", "Andhra Pradesh Electricity Regulatory Commission", "APERC", "https://aperc.gov.in/", "s.82 EA 2003"),
    ("as", "serc_as", "Assam Electricity Regulatory Commission", "AERC", "https://aerc.gov.in/", "s.82 EA 2003"),
    ("br", "serc_br", "Bihar Electricity Regulatory Commission", "BERC", "https://berc.gov.in/", "s.82 EA 2003"),
    ("cg", "serc_cg", "Chhattisgarh State Electricity Regulatory Commission", "CSERC", "https://cserc.gov.in/", "s.82 EA 2003"),
    ("ga", "serc_ga", "Goa Electricity Regulatory Commission", "GERC", "https://www.gerc.gov.in/", "s.82 EA 2003"),
    ("gj", "serc_gj", "Gujarat Electricity Regulatory Commission", "GERC", "https://www.gercin.org/", "s.82 EA 2003"),
    ("hr", "serc_hr", "Haryana Electricity Regulatory Commission", "HERC", "https://www.herc.gov.in/", "s.82 EA 2003"),
    ("hp", "serc_hp", "Himachal Pradesh Electricity Regulatory Commission", "HPERC", "https://hperc.org/", "s.82 EA 2003"),
    ("jh", "serc_jh", "Jharkhand State Electricity Regulatory Commission", "JSERC", "https://www.jserc.org/", "s.82 EA 2003"),
    ("jk", "serc_jk", "J&K Electricity Regulatory Commission", "JKERC", "https://jkerc.nic.in/", "s.82 EA 2003"),
    ("kl", "serc_kl", "Kerala State Electricity Regulatory Commission", "KSERC", "https://www.kserckerala.org/", "s.82 EA 2003"),
    ("mp", "serc_mp", "Madhya Pradesh Electricity Regulatory Commission", "MPERC", "https://www.mperc.in/", "s.82 EA 2003"),
    ("mh", "serc_mh", "Maharashtra Electricity Regulatory Commission", "MERC", "https://www.mercindia.org.in/", "s.82 EA 2003"),
    ("mn", "serc_mn", "Manipur Electricity Regulatory Commission", "MERC Manipur", "https://manipurerc.nic.in/", "s.82 EA 2003"),
    ("ml", "serc_ml", "Meghalaya Electricity Regulatory Commission", "MeERC", "https://meerc.gov.in/", "s.82 EA 2003"),
    ("mz", "serc_mz", "Mizoram Electricity Regulatory Commission", "MERC Mizoram", "https://mzerc.gov.in/", "s.82 EA 2003"),
    ("nl", "serc_nl", "Nagaland Electricity Regulatory Commission", "NERC", "https://nercnagaland.gov.in/", "s.82 EA 2003"),
    ("od", "serc_od", "Odisha Electricity Regulatory Commission", "OERC", "https://www.orierc.org/", "s.82 EA 2003"),
    ("pb", "serc_pb", "Punjab State Electricity Regulatory Commission", "PSERC", "https://pserc.gov.in/", "s.82 EA 2003"),
    ("rj", "serc_rj", "Rajasthan Electricity Regulatory Commission", "RERC", "https://rerc.rajasthan.gov.in/", "s.82 EA 2003"),
    ("sk", "serc_sk", "Sikkim State Electricity Regulatory Commission", "SSERC", "https://sserc.nic.in/", "s.82 EA 2003"),
    ("tn", "serc_tn", "Tamil Nadu Electricity Regulatory Commission", "TNERC", "https://www.tnerc.gov.in/", "s.82 EA 2003"),
    ("ts", "serc_ts", "Telangana State Electricity Regulatory Commission", "TSERC", "https://tserc.gov.in/", "s.82 EA 2003"),
    ("tr", "serc_tr", "Tripura Electricity Regulatory Commission", "TERC", "https://tercl.nic.in/", "s.82 EA 2003"),
    ("uk", "serc_uk", "Uttarakhand Electricity Regulatory Commission", "UERC", "https://uerc.gov.in/", "s.82 EA 2003"),
    ("up", "serc_up", "Uttar Pradesh Electricity Regulatory Commission", "UPERC", "https://www.uperc.org/", "s.82 EA 2003"),
    ("wb", "serc_wb", "West Bengal Electricity Regulatory Commission", "WBERC", "https://www.wberc.gov.in/", "s.82 EA 2003"),
]

TRIBUNALS = [
    ("ap_vat_tribunal", "AP", "Andhra Pradesh Value Added Tax Tribunal", "hc_andhra_pradesh", "AP VAT Act 2005 s.31 (pre-GST arrears)"),
    ("ts_vat_tribunal", "TS", "Telangana Value Added Tax Tribunal", "hc_telangana", "TS VAT Act 2005 s.31"),
    ("gj_vat_tribunal", "GJ", "Gujarat Value Added Tax Tribunal", "hc_gujarat", "Gujarat VAT Act 2003 s.76"),
    ("mp_vat_tribunal", "MP", "Madhya Pradesh Value Added Tax Tribunal", "hc_madhya_pradesh", "MP VAT Act 2002 s.46"),
    ("wb_vat_tribunal", "WB", "West Bengal Value Added Tax Tribunal", "hc_calcutta", "West Bengal VAT Act 2003 s.84"),
    ("br_vat_tribunal", "BR", "Bihar Value Added Tax Tribunal", "hc_patna", "Bihar VAT Act 2005 s.45"),
    ("kl_vat_tribunal", "KL", "Kerala Value Added Tax Tribunal", "hc_kerala", "Kerala VAT Act 2003 s.55"),
    ("pb_vat_tribunal", "PB", "Punjab Value Added Tax Tribunal", "hc_punjab_haryana", "Punjab VAT Act 2005 s.62"),
    ("od_vat_tribunal", "OD", "Odisha Value Added Tax Tribunal", "hc_orissa", "Odisha VAT Act 2004 s.74"),
    ("mh_sat", "MH", "Maharashtra Administrative Tribunal", "hc_bombay", "Administrative Tribunals Act 1985 s.2(b)"),
    ("hp_sat", "HP", "Himachal Pradesh Administrative Tribunal", "hc_himachal_pradesh", "Administrative Tribunals Act 1985"),
    ("ap_sat", "AP", "Andhra Pradesh Administrative Tribunal", "hc_andhra_pradesh", "Administrative Tribunals Act 1985"),
    ("wb_sat", "WB", "West Bengal Administrative Tribunal", "hc_calcutta", "Administrative Tribunals Act 1985"),
    ("od_sat", "OD", "Odisha Administrative Tribunal", "hc_orissa", "Administrative Tribunals Act 1985"),
    ("kl_sat", "KL", "Kerala Administrative Tribunal", "hc_kerala", "Administrative Tribunals Act 1985"),
    ("jk_sat", "JK", "Jammu and Kashmir Services Tribunal", "hc_jammu_kashmir_ladakh", "J&K services tribunal framework (adapted post-2019)"),
    ("ts_sat", "TS", "Telangana Administrative Tribunal", "hc_telangana", "Administrative Tribunals Act 1985"),
    ("mh_industrial_tribunal", "MH", "Maharashtra Industrial Tribunal", "hc_bombay", "Industrial Disputes Act 1947 s.7A"),
    ("wb_industrial_tribunal", "WB", "West Bengal Industrial Tribunal", "hc_calcutta", "Industrial Disputes Act 1947 s.7A"),
    ("tn_industrial_tribunal", "TN", "Tamil Nadu Industrial Tribunal", "hc_madras", "Industrial Disputes Act 1947 s.7A"),
]


def state_name(st: str) -> str:
    return {
        "ap": "Andhra Pradesh", "as": "Assam", "br": "Bihar", "cg": "Chhattisgarh",
        "ga": "Goa", "gj": "Gujarat", "hp": "Himachal Pradesh", "hr": "Haryana",
        "jh": "Jharkhand", "jk": "Jammu and Kashmir", "kl": "Kerala", "la": "Ladakh",
        "mh": "Maharashtra", "ml": "Meghalaya", "mn": "Manipur", "mp": "Madhya Pradesh",
        "mz": "Mizoram", "nl": "Nagaland", "od": "Odisha", "pb": "Punjab",
        "py": "Puducherry", "rj": "Rajasthan", "sk": "Sikkim", "tn": "Tamil Nadu",
        "tr": "Tripura", "ts": "Telangana", "uk": "Uttarakhand", "up": "Uttar Pradesh",
        "wb": "West Bengal", "dl": "Delhi", "ka": "Karnataka",
    }.get(st, st.upper())


def lokayukta_doc(st: str, meta: dict) -> dict:
    nc = meta["status"] == "Not_Constituted"
    etype = "StatutoryBodyNotConstituted" if nc else "ExecutiveBody"
    year = meta["year"] if meta["year"] is not None else 2025
    lokpal = "Not_Applicable" if nc else "Yes"
    notes = meta["note"] or ""
    if nc:
        notes = (notes + " Body not constituted.").strip()
    doc = {
        "id": f"{st}_lokayukta",
        "name": f"{state_name(st)} Lokayukta",
        "type": etype,
        "cluster": "executive_interface",
        "level_of_government": "State",
        "jurisdiction_scope": {
            "states_covered": [st.upper()],
            "is_all_india": False,
        },
        "created_year": year,
        "operational_status": meta["status"],
        "statutory_basis": meta["act"],
        "funding": {"primary_source": "State_Consolidated_Fund"},
        "audit": {
            "audited_by": "cag_india",
            "audit_type": "CAG_Statutory",
            "audit_report_public": True,
        },
        "complaint_mechanism": {
            "bias_complaint_to": [],
            "lokpal_jurisdiction": lokpal,
        },
        "data_quality": "partial",
        "sources": [
            {"label": f"{state_name(st)} Lokayukta portal", "url": meta["url"], "type": "GoIWebsite", "accessed_date": "2026-06-15"},
            dict(SRC_INDIA),
        ],
    }
    if notes:
        doc["data_quality_notes"] = notes
    return doc


def merge_lokayukta() -> int:
    n = 0
    for st, meta in LOKAYUKTA.items():
        path = STATES / st / f"{st}_lokayukta.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = lokayukta_doc(st, meta)
        path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True))
        n += 1
    return n


def merge_serc() -> int:
    n = 0
    for _st, eid, name, abbr, url, ea in SERC_ROWS:
        path = SERC_DIR / f"{eid}.yaml"
        if not path.exists():
            continue
        doc = yaml.safe_load(path.read_text()) or {}
        doc["name"] = name
        doc["abbreviation"] = abbr
        doc["statutory_basis"] = (
            f"Electricity Act 2003, {ea} (constitution of State Electricity Regulatory Commissions); "
            "s.111 (appeals from SERC orders to APTEL)."
        )
        sources = doc.get("sources") or []
        urls = {s.get("url") for s in sources if isinstance(s, dict)}
        if url not in urls:
            sources.insert(0, {"label": f"{abbr} Official Website", "url": url, "type": "GoIWebsite", "accessed_date": "2026-06-15"})
        if SRC_INDIA["url"] not in urls:
            sources.append(dict(SRC_INDIA))
        doc["sources"] = sources
        note = doc.get("data_quality_notes") or ""
        if "Claude SERC enrichment" not in note:
            doc["data_quality_notes"] = (note + " Claude SERC enrichment Jun 2026.").strip()
        path.write_text(yaml.dump(doc, sort_keys=False, allow_unicode=True))
        n += 1
    return n


def tribunal_doc(eid: str, st_code: str, name: str, basis: str) -> dict:
    st = st_code.lower()
    return {
        "id": eid,
        "name": name,
        "type": "StateTribunal",
        "cluster": "tribunals_adr",
        "level_of_government": "State",
        "jurisdiction_scope": {
            "states_covered": [st_code],
            "is_all_india": False,
        },
        "created_year": 2003,
        "operational_status": "Active",
        "statutory_basis": basis,
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
        "data_quality": "partial",
        "data_quality_notes": "Post-GST legacy docket where applicable; HC writ/appeal wired in state_tribunal_relationships.yaml.",
        "sources": [dict(SRC_INDIA)],
    }


def merge_tribunals() -> int:
    n = 0
    for eid, st_code, name, _hc, basis in TRIBUNALS:
        st = eid.split("_")[0]
        path = STATES / st / f"{eid}.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.dump(tribunal_doc(eid, st_code, name, basis), sort_keys=False, allow_unicode=True))
        n += 1
    return n


def main() -> None:
    print(f"lokayukta: {merge_lokayukta()} files")
    print(f"serc: {merge_serc()} files")
    print(f"tribunals: {merge_tribunals()} files")


if __name__ == "__main__":
    main()
