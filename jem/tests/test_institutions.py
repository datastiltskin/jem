#!/usr/bin/env python3
"""Institution-level consistency checks (L4 partial gate).

Complements validate_graph_refs.py (L1) by checking config ↔ entity ↔ routing sync.
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


def bench_yaml_ids() -> set[str]:
    bench_dir = ENTITIES / "_generated" / "high_courts" / "benches"
    if not bench_dir.exists():
        return set()
    return {f.stem for f in bench_dir.glob("*.yaml")}


def hc_bench_entities(entities: dict[str, dict]) -> set[str]:
    return {eid for eid, d in entities.items() if d.get("type") == "HighCourtBench"}


def district_appeals(rel_file: str, prefix: str) -> dict[str, str]:
    path = REL / rel_file
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    out: dict[str, str] = {}
    for rel in data.get("relationships") or []:
        if rel.get("relationship_type") != "AppealableTo":
            continue
        src = rel.get("source") or ""
        if not src.startswith(prefix):
            continue
        slug = src.replace(prefix, "")
        out[slug] = rel.get("target") or ""
    return out


def test_hc_benches_config_matches_disk_and_graph():
    config_ids = {b[0] for b in HC_BENCHES_DEF}
    disk_ids = bench_yaml_ids()
    entities = load_entities()
    graph_ids = hc_bench_entities(entities)

    assert config_ids == disk_ids, f"config vs disk: extra config={config_ids - disk_ids} extra disk={disk_ids - config_ids}"
    assert config_ids == graph_ids, (
        f"config vs graph: extra config={config_ids - graph_ids} extra graph={graph_ids - config_ids}"
    )


def test_no_phantom_trichy_bench():
    entities = load_entities()
    assert "hc_madras_bench_tiruchirappalli" not in entities
    config_ids = {b[0] for b in HC_BENCHES_DEF}
    assert "hc_madras_bench_tiruchirappalli" not in config_ids


def test_tn_district_routing_matches_relationships():
    rel_map = district_appeals("tn_relationships.yaml", "tn_district_court_")
    for slug, cfg_target in TN_DISTRICT_TO_BENCH.items():
        rel_target = rel_map.get(slug)
        assert rel_target == cfg_target, f"TN {slug}: config={cfg_target} rel={rel_target}"


def test_mh_district_routing_matches_relationships():
    entities = load_entities()
    for eid, cfg_target in MH_DISTRICT_TO_BENCH.items():
        assert eid in entities, f"MH district entity missing: {eid}"
        assert cfg_target in entities, f"MH bench target missing: {cfg_target}"


def test_ka_up_wb_rj_routing_targets_exist():
    entities = load_entities()
    for name, mapping in [
        ("KA", KA_DISTRICT_TO_BENCH),
        ("UP", UP_DISTRICT_TO_BENCH),
        ("WB", WB_DISTRICT_TO_BENCH),
        ("RJ", RJ_DISTRICT_TO_BENCH),
    ]:
        for eid, bench_id in mapping.items():
            assert eid in entities, f"{name} district missing: {eid}"
            assert bench_id in entities, f"{name} bench missing: {bench_id}"


def test_hc_benches_have_parent_hc():
    entities = load_entities()
    for eid in hc_bench_entities(entities):
        parent = entities[eid].get("parent_hc")
        assert parent, f"{eid} missing parent_hc"
        assert parent in entities, f"{eid} parent_hc {parent} not in graph"
