#!/usr/bin/env python3
"""
JEM — Graph reference validation
Ensures relationship endpoints and entity cross-references point at real entity ids.

Usage:
    python3 scripts/validate_graph_refs.py
    python3 scripts/validate_graph_refs.py --strict   # also warn on orphan entities (optional)

Exit code 0 = all references resolve. Exit code 1 = dangling references found.
"""

from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

ID_LIKE = re.compile(r"^[a-z][a-z0-9_]*$")

# Entity YAML fields that hold a single entity id reference
SINGLE_REF_PATHS = [
    ("parent_hc", None),
    ("appointment", "formally_appoints"),
    ("appointment", "nominates"),
    ("appointment", "recommends"),
    ("appointment", "removal_authority"),
    ("funding", "ministry_responsible"),
    ("audit", "audited_by"),
    ("audit", "conduct_oversight_body"),
]

LIST_REF_PATHS = [
    ("appointment", "consulted"),
    ("complaint_mechanism", "bias_complaint_to", "body"),
]


def load_yaml(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def collect_entity_ids(data_dir: Path) -> Tuple[Set[str], Dict[str, Path]]:
    ids: Set[str] = set()
    paths: Dict[str, Path] = {}
    for root in (data_dir / "entities" / "_generated", data_dir / "entities"):
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.yaml")):
            if "schema" in str(f):
                continue
            data = load_yaml(f)
            eid = data.get("id")
            if eid:
                ids.add(eid)
                paths[eid] = f
    return ids, paths


def collect_relationship_refs(data_dir: Path) -> Dict[str, List[str]]:
    """ref_id -> list of 'file:rel_id (source|target)' locations."""
    refs: Dict[str, List[str]] = defaultdict(list)
    rel_dir = data_dir / "relationships"
    if not rel_dir.exists():
        return refs
    for rf in sorted(rel_dir.glob("*.yaml")):
        data = load_yaml(rf)
        for rel in data.get("relationships") or []:
            if not isinstance(rel, dict):
                continue
            rid = rel.get("id", "?")
            for field in ("source", "target"):
                val = rel.get(field)
                if isinstance(val, str) and val:
                    refs[val].append(f"{rf.name}:{rid} ({field})")
    return refs


def collect_entity_field_refs(data_dir: Path) -> Dict[str, List[str]]:
    refs: Dict[str, List[str]] = defaultdict(list)
    for root in (data_dir / "entities" / "_generated", data_dir / "entities"):
        if not root.exists():
            continue
        for f in sorted(root.rglob("*.yaml")):
            if "schema" in str(f):
                continue
            data = load_yaml(f)
            eid = data.get("id", f.name)
            rel = f.relative_to(data_dir.parent)

            ph = data.get("parent_hc")
            if isinstance(ph, str) and ph:
                refs[ph].append(f"{rel} parent_hc (entity {eid})")

            for section, key in [
                ("appointment", "formally_appoints"),
                ("appointment", "nominates"),
                ("appointment", "recommends"),
                ("appointment", "removal_authority"),
                ("funding", "ministry_responsible"),
                ("audit", "audited_by"),
                ("audit", "conduct_oversight_body"),
            ]:
                block = data.get(section) or {}
                if isinstance(block, dict):
                    val = block.get(key)
                    if isinstance(val, str) and val and ID_LIKE.match(val):
                        refs[val].append(f"{rel} {section}.{key} (entity {eid})")

            appt = data.get("appointment") or {}
            if isinstance(appt, dict):
                for x in appt.get("consulted") or []:
                    if isinstance(x, str) and ID_LIKE.match(x):
                        refs[x].append(f"{rel} appointment.consulted (entity {eid})")

            cm = data.get("complaint_mechanism") or {}
            for item in cm.get("bias_complaint_to") or []:
                if isinstance(item, dict):
                    b = item.get("body")
                    if isinstance(b, str) and b:
                        refs[b].append(f"{rel} complaint_mechanism.body (entity {eid})")

    return refs


def run(data_dir: Path, strict: bool = False) -> bool:
    entity_ids, _ = collect_entity_ids(data_dir)
    rel_refs = collect_relationship_refs(data_dir)
    field_refs = collect_entity_field_refs(data_dir)

    rel_missing = {k: v for k, v in rel_refs.items() if k not in entity_ids}
    field_missing = {k: v for k, v in field_refs.items() if k not in entity_ids}

    # Relationship endpoints used in degree calculation
    rel_degree: Set[str] = set(rel_refs.keys())
    orphans = entity_ids - rel_degree if strict else set()

    print(f"\nGraph reference check")
    print(f"  Entity ids:              {len(entity_ids)}")
    print(f"  Relationship endpoints:  {len(rel_refs)} unique")
    print(f"  Entity field refs:       {len(field_refs)} unique")

    ok = True
    if rel_missing:
        ok = False
        print(f"\n✗ Dangling relationship endpoints ({len(rel_missing)}):")
        for eid in sorted(rel_missing):
            print(f"  {eid}")
            for loc in rel_missing[eid][:3]:
                print(f"    - {loc}")

    if field_missing:
        ok = False
        print(f"\n✗ Dangling entity field references ({len(field_missing)}):")
        for eid in sorted(field_missing):
            print(f"  {eid}")
            for loc in field_missing[eid][:2]:
                print(f"    - {loc}")

    if strict and orphans:
        print(f"\n⚠ Orphan entities (no relationship source/target): {len(orphans)}")
        for eid in sorted(list(orphans))[:20]:
            print(f"  {eid}")
        if len(orphans) > 20:
            print(f"  ... +{len(orphans) - 20} more (informational only)")

    if ok:
        print("\n✓ All graph references resolve to entity ids")
    else:
        print("\n✗ Graph reference validation FAILED")

    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate JEM entity id cross-references")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Also report entities never used as relationship endpoints (informational)",
    )
    args = parser.parse_args()
    data_dir = Path(__file__).parent.parent / "data"
    import sys

    sys.exit(0 if run(data_dir, strict=args.strict) else 1)


if __name__ == "__main__":
    main()
