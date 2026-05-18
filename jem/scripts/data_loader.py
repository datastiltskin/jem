"""
Shared JEM data paths: _generated vs _curated merge, hand-maintained manifest.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml

HAND_MAINTAINED_MARKER = "jem: hand-maintained"
GENERATED_HEADER = "JEM generated bundle"
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR.parent / "data"
ENTITIES_DIR = DATA_DIR / "entities"
GENERATED_ENTITIES = ENTITIES_DIR / "_generated"
CURATED_ENTITIES = ENTITIES_DIR / "_curated"
RELATIONSHIPS_DIR = DATA_DIR / "relationships"
CURATED_RELATIONSHIPS = RELATIONSHIPS_DIR / "_curated"
HAND_MAINTAINED_FILE = DATA_DIR / "HAND_MAINTAINED.yaml"


def load_yaml(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_hand_maintained_manifest() -> dict:
    if not HAND_MAINTAINED_FILE.exists():
        return {"entities": [], "relationships": [], "entity_ids": []}
    data = load_yaml(HAND_MAINTAINED_FILE) or {}
    return {
        "entities": list(data.get("entities") or []),
        "relationships": list(data.get("relationships") or []),
        "entity_ids": list(data.get("entity_ids") or []),
    }


def hand_maintained_entity_ids() -> Set[str]:
    return set(load_hand_maintained_manifest()["entity_ids"])


def hand_maintained_paths() -> Set[Path]:
    """Absolute paths listed in HAND_MAINTAINED.yaml."""
    manifest = load_hand_maintained_manifest()
    out: Set[Path] = set()
    for rel in manifest["entities"] + manifest["relationships"]:
        out.add((DATA_DIR / rel).resolve())
    return out


def is_hand_maintained_file(path: Path) -> bool:
    path = path.resolve()
    if path in hand_maintained_paths():
        return True
    if CURATED_ENTITIES in path.parents or CURATED_RELATIONSHIPS in path.parents:
        return True
    if not path.is_file():
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            first = f.readline()
            second = f.readline()
        return HAND_MAINTAINED_MARKER in first or HAND_MAINTAINED_MARKER in second
    except OSError:
        return False


def curated_entity_path(entity_id: str, subpath: Optional[str] = None) -> Path:
    """Path under _curated for an entity id (flat lookup via rglob if subpath omitted)."""
    if subpath:
        return CURATED_ENTITIES / subpath
    matches = list(CURATED_ENTITIES.rglob(f"{entity_id}.yaml"))
    return matches[0] if matches else CURATED_ENTITIES / f"{entity_id}.yaml"


def entity_id_for_generated_path(path: Path) -> Optional[str]:
    """Read entity id from a YAML file if present."""
    try:
        data = load_yaml(path)
        if isinstance(data, dict) and data.get("id"):
            return str(data["id"])
    except Exception:
        pass
    return None


def should_skip_generated_write(target: Path, entity_id: Optional[str] = None) -> bool:
    """True if generator must not overwrite this path."""
    target = target.resolve()
    if is_hand_maintained_file(target):
        return True
    if entity_id and entity_id in hand_maintained_entity_ids():
        if curated_entity_path(entity_id).exists():
            return True
    rel = None
    try:
        rel = target.relative_to(GENERATED_ENTITIES)
        curated = (CURATED_ENTITIES / rel).resolve()
        if curated.exists():
            return True
    except ValueError:
        pass
    return False


def iter_entity_yaml_paths() -> List[Path]:
    """All entity YAML paths to validate on disk (_generated + _curated, no duplicates)."""
    paths: List[Path] = []
    curated_rels: Set[str] = set()
    if CURATED_ENTITIES.exists():
        for f in sorted(CURATED_ENTITIES.rglob("*.yaml")):
            paths.append(f)
            try:
                curated_rels.add(str(f.relative_to(CURATED_ENTITIES)))
            except ValueError:
                pass
    if GENERATED_ENTITIES.exists():
        for f in sorted(GENERATED_ENTITIES.rglob("*.yaml")):
            try:
                rel = str(f.relative_to(GENERATED_ENTITIES))
            except ValueError:
                rel = ""
            if rel in curated_rels:
                continue
            paths.append(f)
    return paths


def iter_relationship_yaml_paths() -> List[Path]:
    paths: List[Path] = []
    if RELATIONSHIPS_DIR.exists():
        for f in sorted(RELATIONSHIPS_DIR.glob("*.yaml")):
            paths.append(f)
    if CURATED_RELATIONSHIPS.exists():
        for f in sorted(CURATED_RELATIONSHIPS.glob("*.yaml")):
            paths.append(f)
    return paths


def load_entities_merged(data_dir: Path | None = None) -> List[Dict]:
    """Load entities: _generated base, _curated overrides by id."""
    base = data_dir or DATA_DIR
    gen = base / "entities" / "_generated"
    cur = base / "entities" / "_curated"
    by_id: Dict[str, Dict] = {}
    order: List[str] = []

    def ingest(root: Path) -> None:
        if not root.exists():
            return
        for f in sorted(root.rglob("*.yaml")):
            if "schema" in str(f) or "_TAXONOMY" in str(f):
                continue
            data = load_yaml(f)
            if not isinstance(data, dict) or not data.get("id"):
                continue
            eid = data["id"]
            if eid not in by_id:
                order.append(eid)
            by_id[eid] = data

    ingest(gen)
    ingest(cur)
    return [by_id[i] for i in order]


def load_relationships_merged(data_dir: Path | None = None) -> List[Dict]:
    """Load relationships from top-level YAML + _curated overlays (later wins by id)."""
    base = data_dir or DATA_DIR
    rel_dir = base / "relationships"
    cur_dir = rel_dir / "_curated"
    by_id: Dict[str, Dict] = {}
    order: List[str] = []

    def ingest_file(f: Path) -> None:
        data = load_yaml(f)
        if not isinstance(data, dict):
            return
        rels = data.get("relationships") or []
        if not isinstance(rels, list):
            return
        for rel in rels:
            if not isinstance(rel, dict) or not rel.get("id"):
                continue
            rid = rel["id"]
            if rid not in by_id:
                order.append(rid)
            by_id[rid] = rel

    if rel_dir.exists():
        for f in sorted(rel_dir.glob("*.yaml")):
            ingest_file(f)
    if cur_dir.exists():
        for f in sorted(cur_dir.glob("*.yaml")):
            ingest_file(f)
    return [by_id[i] for i in order]


def check_duplicate_entity_ids() -> List[str]:
    """Errors if same id appears in both trees at different paths (should not happen)."""
    errors: List[str] = []
    gen_ids: Dict[str, Path] = {}
    if GENERATED_ENTITIES.exists():
        for f in GENERATED_ENTITIES.rglob("*.yaml"):
            eid = entity_id_for_generated_path(f)
            if eid:
                gen_ids[eid] = f
    if CURATED_ENTITIES.exists():
        for f in CURATED_ENTITIES.rglob("*.yaml"):
            eid = entity_id_for_generated_path(f)
            if eid and eid in gen_ids:
                errors.append(
                    f"Duplicate entity id '{eid}': generated {gen_ids[eid]} and curated {f}"
                )
    return errors
