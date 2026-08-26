#!/usr/bin/env python3
"""Build config/roster.yaml — the entity list the batch scraper (scripts/batch_scrape.py) walks.

The roster is the enumeration of every entity currently materialized under
data/entities/_generated/**. There is no separate manifest in this repo; the generated tree IS
the authoritative list, so this globs it and records the identity + on-disk path of each entity.

To GROW the corpus toward the ~1,500 target you must first materialize the missing entities with
the existing (idempotent) generators — e.g. `python scripts/generate_v1_states_bundle.py` and the
`scripts/bootstrap_*` state/district packs — then re-run this script. Those generators own the
logic for what net-new entities exist; this script deliberately does not duplicate it.

    python scripts/build_roster.py            # write config/roster.yaml + print counts
"""
from __future__ import annotations
import sys
from pathlib import Path
import yaml

JEM = Path(__file__).resolve().parents[1]
GENERATED = JEM / "data" / "entities" / "_generated"
ROSTER = JEM / "config" / "roster.yaml"
TARGET = 1500                                   # aspirational full-corpus size, for the shortfall log


def _state_of(path: Path, entity: dict) -> str:
    """states/<code>/ dir wins; else first states_covered, lowercased; else '' (central)."""
    parts = path.relative_to(GENERATED).parts
    if parts[0] == "states" and len(parts) > 1:
        return parts[0 + 1].lower()
    covered = (entity.get("jurisdiction_scope") or {}).get("states_covered") or []
    return str(covered[0]).lower() if covered else ""


def build() -> list[dict]:
    rows = []
    for path in sorted(GENERATED.rglob("*.yaml")):
        entity = yaml.safe_load(path.read_text()) or {}
        entity = entity.get("entity", entity)   # some files may nest under `entity:`
        eid = entity.get("id")
        if not eid:
            print(f"  skip (no id): {path.relative_to(JEM)}", file=sys.stderr)
            continue
        rows.append({
            "id": eid,
            "name": entity.get("name"),
            "type": entity.get("type"),
            "cluster": entity.get("cluster"),
            "state": _state_of(path, entity),
            "path": str(path.relative_to(JEM)),  # write-back target, relative to jem/
            "seed_url": None,
            "status": "existing",
        })
    return rows


def _dedup(rows: list[dict]) -> list[dict]:
    """One row per id. A duplicate id is a real data conflict (e.g. an entity modeled two
    different ways) — surface every colliding path, and keep the canonical cluster-dir copy over
    a states/ stub so the roster is stable. Never resolves the conflict silently in the data."""
    by_id: dict[str, list[dict]] = {}
    for r in rows:
        by_id.setdefault(r["id"], []).append(r)
    out = []
    for eid, group in by_id.items():
        if len(group) > 1:
            paths = [g["path"] for g in group]
            group.sort(key=lambda g: ("/states/" in g["path"], g["path"]))  # non-states first
            print(f"CONFLICT: id '{eid}' in {len(group)} files: {paths} — keeping "
                  f"{group[0]['path']}", file=sys.stderr)
        out.append(group[0])
    return out


def main() -> int:
    rows = _dedup(build())

    ROSTER.parent.mkdir(parents=True, exist_ok=True)
    ROSTER.write_text(yaml.safe_dump({"entities": rows}, sort_keys=False, allow_unicode=True))
    print(f"Wrote {len(rows)} entities → {ROSTER.relative_to(JEM)}")
    if len(rows) < TARGET:
        print(f"NOTE: {TARGET - len(rows)} short of the ~{TARGET} target. Materialize net-new "
              f"entities with the generators (generate_v1_states_bundle.py / bootstrap_*), then "
              f"re-run this script.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
