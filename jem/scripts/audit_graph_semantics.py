#!/usr/bin/env python3
"""
Semantic graph audit — config ↔ relationship routing consistency.

Exit 0 = checks pass. Exit 1 = mismatches found.
Run before release tags alongside validate_graph_refs.py --strict.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

JEM_ROOT = Path(__file__).resolve().parents[1]
DATA = JEM_ROOT / "data"
ENTITIES = DATA / "entities"
REL = DATA / "relationships"
SCRIPTS = JEM_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
from hc_benches_config import (  # noqa: E402
    HC_BENCHES_DEF,
    KA_DISTRICT_TO_BENCH,
    MH_DISTRICT_TO_BENCH,
    RJ_DISTRICT_TO_BENCH,
    TN_DISTRICT_TO_BENCH,
    UP_DISTRICT_TO_BENCH,
    WB_DISTRICT_TO_BENCH,
)

ROUTING_PACKS: list[tuple[str, dict[str, str], str, str]] = [
    ("TN", TN_DISTRICT_TO_BENCH, "tn_relationships.yaml", "tn_district_court_"),
    ("MH", MH_DISTRICT_TO_BENCH, "mh_relationships.yaml", ""),
    ("KA", KA_DISTRICT_TO_BENCH, "ka_relationships.yaml", ""),
    ("UP", UP_DISTRICT_TO_BENCH, "up_relationships.yaml", ""),
    ("WB", WB_DISTRICT_TO_BENCH, "wb_relationships.yaml", ""),
    ("RJ", RJ_DISTRICT_TO_BENCH, "rj_relationships.yaml", ""),
]

PHANTOM_BLOCKLIST = frozenset({"hc_madras_bench_tiruchirappalli", "hc_mizoram", "hc_arunachal_pradesh"})


def load_entities() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for root in (ENTITIES / "_generated", ENTITIES):
        if not root.exists():
            continue
        for f in root.rglob("*.yaml"):
            if "schema" in str(f):
                continue
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            eid = data.get("id")
            if eid:
                out[eid] = data
    return out


def district_appeals(rel_file: str, slug_prefix: str) -> dict[str, str]:
    """Return map key → appellate target. TN uses slug keys; others use full entity id."""
    path = REL / rel_file
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, str] = {}
    for rel in data.get("relationships") or []:
        if rel.get("relationship_type") != "AppealableTo":
            continue
        src = rel.get("source") or ""
        if slug_prefix:
            if not src.startswith(slug_prefix):
                continue
            key = src.replace(slug_prefix, "")
        else:
            key = src
        out[key] = rel.get("target") or ""
    return out


def main() -> int:
    entities = load_entities()
    entity_ids = set(entities)
    ok = True

    config_benches = {b[0] for b in HC_BENCHES_DEF}
    bench_dir = ENTITIES / "_generated" / "high_courts" / "benches"
    disk_benches = {f.stem for f in bench_dir.glob("*.yaml")} if bench_dir.exists() else set()
    graph_benches = {eid for eid, d in entities.items() if d.get("type") == "HighCourtBench"}

    print("Graph semantics audit")
    print(f"  Entities: {len(entity_ids)}")
    print(f"  HC_BENCHES_DEF: {len(config_benches)}")
    print(f"  Bench YAML on disk: {len(disk_benches)}")
    print(f"  HighCourtBench in graph: {len(graph_benches)}")

    if config_benches != disk_benches:
        ok = False
        print(
            f"\n✗ HC_BENCHES_DEF vs disk: "
            f"config-only={sorted(config_benches - disk_benches)} "
            f"disk-only={sorted(disk_benches - config_benches)}"
        )
    else:
        print("\n✓ HC_BENCHES_DEF matches bench YAML files")

    if config_benches != graph_benches:
        ok = False
        print(
            f"✗ HC_BENCHES_DEF vs graph: "
            f"config-only={sorted(config_benches - graph_benches)} "
            f"graph-only={sorted(graph_benches - config_benches)}"
        )
    else:
        print("✓ HC_BENCHES_DEF matches HighCourtBench entities")

    phantoms = [p for p in PHANTOM_BLOCKLIST if p in entity_ids or p in config_benches]
    if phantoms:
        ok = False
        for phantom in phantoms:
            print(f"✗ Phantom institution present: {phantom}")
    else:
        print("✓ Known phantom blocklist clean")

    for state, mapping, rel_file, slug_prefix in ROUTING_PACKS:
        if not mapping:
            continue
        rel_map = district_appeals(rel_file, slug_prefix)
        mismatches = []
        for key, cfg_target in mapping.items():
            rel_target = rel_map.get(key)
            if rel_target and rel_target != cfg_target:
                mismatches.append((key, cfg_target, rel_target))
            if cfg_target not in entity_ids:
                mismatches.append((key, f"missing target {cfg_target}", rel_target))
        if mismatches:
            ok = False
            print(f"\n✗ {state} routing mismatches ({len(mismatches)}):")
            for row in mismatches[:10]:
                print(f"    {row}")
        else:
            print(f"✓ {state} district routing consistent ({len(mapping)} entries)")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
