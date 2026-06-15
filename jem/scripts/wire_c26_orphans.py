#!/usr/bin/env python3
"""C26 orphan reduction — wire state-pack, district court, CDRC, and SERC orphans."""

from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

import yaml

DATA = Path(__file__).resolve().parent.parent / "data"
REL_DIR = DATA / "relationships"
SOURCE_ANCHOR = {
    "label": "India Code — Constitution & Acts",
    "url": "https://india-code.nic.in/",
    "type": "GoIWebsite",
    "accessed_date": "2026-06-15",
}

PREFIX_GOV = {
    "an": "government_an",
    "ap": "government_ap",
    "ar": "government_ar",
    "as": "government_as",
    "br": "government_br",
    "cg": "government_cg",
    "ch": "government_ch",
    "dl": "government_nct_delhi",
    "ga": "government_ga",
    "gj": "government_gj",
    "hp": "government_hp",
    "hr": "government_hr",
    "jh": "government_jh",
    "jk": "government_jk",
    "ka": "government_karnataka",
    "kl": "government_kl",
    "la": "government_la",
    "ld": "government_ld",
    "mh": "government_maharashtra",
    "ml": "government_ml",
    "mn": "government_mn",
    "mp": "government_mp",
    "mz": "government_mz",
    "nl": "government_nl",
    "od": "government_od",
    "pb": "government_pb",
    "py": "py_lieutenant_governor",
    "rj": "government_rj",
    "sk": "government_sk",
    "tn": "government_tamilnadu",
    "tr": "government_tr",
    "ts": "government_ts",
    "uk": "government_uk",
    "up": "government_up",
    "wb": "government_wb",
}

PRINCIPAL_HC = {
    "an": "hc_calcutta_bench_port_blair",
    "ap": "hc_andhra_pradesh",
    "ar": "hc_gauhati_bench_itanagar",
    "as": "hc_gauhati",
    "br": "hc_patna",
    "cg": "hc_chhattisgarh",
    "ch": "hc_punjab_haryana",
    "dl": "hc_delhi",
    "ga": "hc_bombay_bench_panaji",
    "gj": "hc_gujarat",
    "hp": "hc_himachal_pradesh",
    "hr": "hc_punjab_haryana",
    "jh": "hc_jharkhand",
    "jk": "hc_jammu_kashmir_ladakh",
    "ka": "hc_karnataka",
    "kl": "hc_kerala",
    "la": "hc_jammu_kashmir_ladakh",
    "ld": "hc_kerala",
    "mh": "hc_bombay",
    "ml": "hc_meghalaya",
    "mn": "hc_manipur",
    "mp": "hc_madhya_pradesh",
    "mz": "hc_gauhati_bench_aizawl",
    "nl": "hc_gauhati",
    "od": "hc_orissa",
    "pb": "hc_punjab_haryana",
    "py": "hc_madras",
    "rj": "hc_rajasthan",
    "sk": "hc_sikkim",
    "tn": "hc_madras",
    "tr": "hc_tripura",
    "ts": "hc_telangana",
    "uk": "hc_uttarakhand",
    "up": "hc_allahabad",
    "wb": "hc_calcutta",
}

STATE_CDRC = {
    "dl": "dl_state_cdrc",
    "py": "py_cdrc",
}


def load_entities() -> set[str]:
    ids: set[str] = set()
    for root in (DATA / "entities" / "_generated", DATA / "entities"):
        if not root.exists():
            continue
        for f in root.rglob("*.yaml"):
            if "schema" in str(f):
                continue
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            eid = data.get("id")
            if eid:
                ids.add(eid)
    return ids


def load_existing() -> tuple[set[str], set[str]]:
    rel_ids: set[str] = set()
    connected: set[str] = set()
    for f in REL_DIR.glob("*.yaml"):
        data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for rel in data.get("relationships") or []:
            rid = rel.get("id")
            if rid:
                rel_ids.add(rid)
            connected.add(rel["source"])
            connected.add(rel["target"])
    return rel_ids, connected


def prefix_of(eid: str) -> str | None:
    m = re.match(r"^([a-z]{2})_", eid)
    return m.group(1) if m else None


def state_cdrc_for(prefix: str) -> str:
    return STATE_CDRC.get(prefix, f"{prefix}_state_cdrc")


def make_rel(
    rid: str,
    source: str,
    target: str,
    rtype: str,
    category: str,
    notes: str,
    *,
    constitutional: bool = False,
    statutory_basis: str | None = None,
) -> dict:
    rel = {
        "id": rid,
        "source": source,
        "target": target,
        "relationship_type": rtype,
        "relationship_category": category,
        "is_binding": True,
        "is_constitutional": constitutional,
        "notes": notes,
        "data_quality": "partial",
        "sources": [dict(SOURCE_ANCHOR)],
    }
    if statutory_basis:
        rel["statutory_basis"] = statutory_basis
    return rel


def generate_orphan_rels(entities: set[str], connected: set[str], existing_ids: set[str]) -> dict[str, list[dict]]:
    orphans = sorted(eid for eid in entities if eid not in connected)
    by_state: dict[str, list[dict]] = defaultdict(list)
    seen_ids = set(existing_ids)

    def add(prefix: str, rel: dict) -> None:
        if rel["id"] in seen_ids:
            return
        if rel["source"] not in entities or rel["target"] not in entities:
            print(f"SKIP missing endpoint: {rel['id']} {rel['source']} -> {rel['target']}")
            return
        seen_ids.add(rel["id"])
        by_state[prefix].append(rel)

    for eid in orphans:
        prefix = prefix_of(eid)
        if not prefix:
            continue

        if eid.endswith("_advocate_general"):
            add(
                prefix,
                make_rel(
                    f"{prefix}_gov_appoints_advocate_general",
                    "governor_state",
                    eid,
                    "FormallyAppoints",
                    "appointment",
                    "Governor appoints Advocate General (Art. 165)",
                    constitutional=True,
                    statutory_basis="Constitution of India, Article 165",
                ),
            )
            continue

        if eid.endswith("_bar_council"):
            gov = PREFIX_GOV.get(prefix)
            if gov:
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_gov_fund_bar_council",
                        gov,
                        eid,
                        "PrimaryFunder",
                        "funding",
                        "State consolidated fund support for State Bar Council",
                        statutory_basis="Advocates Act 1961",
                    ),
                )
            continue

        if eid.endswith("_lokayukta"):
            gov = PREFIX_GOV.get(prefix)
            if gov:
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_gov_fund_lokayukta",
                        gov,
                        eid,
                        "PrimaryFunder",
                        "funding",
                        "State government funds Lokayukta institution",
                    ),
                )
            continue

        if eid.endswith("_special_courts"):
            hc = PRINCIPAL_HC.get(prefix)
            if hc:
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_{eid}_appealable_{hc}",
                        eid,
                        hc,
                        "AppealableTo",
                        "appellate_chain",
                        "Special court orders appealable to High Court",
                    ),
                )
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_{hc}_supervise_{eid}",
                        hc,
                        eid,
                        "AdministrativeSupervision",
                        "supervisory",
                        "High Court administrative supervision over special courts",
                        constitutional=True,
                        statutory_basis="Constitution of India, Article 235",
                    ),
                )
            continue

        if "district_court" in eid:
            hc = PRINCIPAL_HC.get(prefix)
            if hc:
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_{eid}_appealable_{hc}",
                        eid,
                        hc,
                        "AppealableTo",
                        "appellate_chain",
                        "District court appeals to High Court",
                    ),
                )
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_{hc}_supervise_{eid}",
                        hc,
                        eid,
                        "AdministrativeSupervision",
                        "supervisory",
                        "Article 235 HC supervision over district court",
                        constitutional=True,
                        statutory_basis="Constitution of India, Article 235",
                    ),
                )
            continue

        if "cdrc" in eid and not eid.endswith("_state_cdrc") and eid not in ("py_cdrc",):
            parent = state_cdrc_for(prefix)
            if parent in entities:
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_{eid}_appealable_{parent}",
                        eid,
                        parent,
                        "AppealableTo",
                        "appellate_chain",
                        "District CDRC appeals to state commission",
                        statutory_basis="Consumer Protection Act 2019",
                    ),
                )
            continue

        if eid.startswith("serc_"):
            prefix = eid.replace("serc_", "", 1)
            gov = PREFIX_GOV.get(prefix)
            if gov:
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_fund_{eid}",
                        gov,
                        eid,
                        "PrimaryFunder",
                        "funding",
                        "State government funds electricity regulatory commission",
                        statutory_basis="Electricity Act 2003",
                    ),
                )
                add(
                    prefix,
                    make_rel(
                        f"{prefix}_{eid}_aptel",
                        eid,
                        "aptel",
                        "AppealableTo",
                        "appellate_chain",
                        "SERC orders appealable to APTEL",
                        statutory_basis="Electricity Act 2003",
                    ),
                )

    return dict(by_state)


def append_to_state_files(by_state: dict[str, list[dict]]) -> int:
    total = 0
    for prefix, rels in sorted(by_state.items()):
        if not rels:
            continue
        path = REL_DIR / f"{prefix}_relationships.yaml"
        header = ""
        existing: list[dict] = []
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if text.startswith("#"):
                header = text.splitlines()[0] + "\n"
            data = yaml.safe_load(text) or {}
            existing = data.get("relationships") or []

        existing_ids = {r.get("id") for r in existing}
        new_rels = [r for r in rels if r["id"] not in existing_ids]
        if not new_rels:
            continue

        merged = existing + new_rels
        dumped = yaml.dump(
            {"relationships": merged},
            default_flow_style=False,
            sort_keys=False,
            allow_unicode=True,
        )
        if not header:
            header = "# JEM generated relationships — data_quality: partial\n"
        path.write_text(header + dumped, encoding="utf-8")
        total += len(new_rels)
        print(f"{path.name}: +{len(new_rels)}")
    return total


def main() -> None:
    entities = load_entities()
    existing_ids, connected = load_existing()
    by_state = generate_orphan_rels(entities, connected, existing_ids)
    total = append_to_state_files(by_state)
    print(f"Added {total} relationships across {len(by_state)} state files")


if __name__ == "__main__":
    main()
