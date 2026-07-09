#!/usr/bin/env python3
"""
Package JEM release archives for manual Zenodo upload (split DOI workflow).

Creates two zip files under build/zenodo/:
  - jem-dataset-{version}.zip   (CC0 — YAML, graph.json, schema, repro scripts)
  - jem-software-{version}.zip  (MIT — web viewer + full pipeline scripts)

Usage (from repo root):
    python3 jem/scripts/package_zenodo_release.py --ref v1.0.0
    python3 jem/scripts/package_zenodo_release.py --ref 47e2ca4 --version 1.0.0
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DATASET_PATHS = [
    "jem/data/entities",
    "jem/data/relationships",
    "jem/data/derived/scores.yaml",
    "jem/data/schema",
    "graph.json",
    "jem/scripts/validate.py",
    "jem/scripts/validate_graph_refs.py",
    "jem/scripts/derive.py",
    "jem/scripts/build.py",
    "jem/scripts/requirements.txt",
]

SOFTWARE_PATHS = [
    "jem/web",
    "jem/scripts",
    "README.md",
]

DATASET_DOC = """# JEM dataset release {version}

**Licence:** CC0 1.0 (data) · pipeline scripts MIT (see LICENSE)

| Field | Value |
|-------|-------|
| Release | v{version} |
| Git ref | `{git_ref}` |
| Commit | `{commit}` |
| Entities | {entity_count} |
| Relationships | {relationship_count} |
| Entity schema | v0.1.0 |
| Orphan nodes (strict) | {orphan_count} |
| High/severe independence risk | {high_severe_ir} |
| Generated | {generated_at} |

## Reproduce graph.json

```bash
cd jem
pip install -r scripts/requirements.txt
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py --strict
python3 scripts/derive.py
RELEASE_VERSION={version} python3 scripts/build.py --no-derive
```

Pair with **jem-software-{version}.zip** (separate Zenodo record, MIT) for the interactive map viewer.
"""


def git_rev_parse(ref: str) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", f"{ref}^{{commit}}"],
        text=True,
        cwd=REPO_ROOT,
    ).strip()


def git_show_file(commit: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "show", f"{commit}:{path}"], cwd=REPO_ROOT
    )


def git_ls_files(commit: str, path: str) -> list[str]:
    """List all blob paths under path at commit (recursive for directories)."""
    out = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", commit, "--", path],
        text=True,
        cwd=REPO_ROOT,
    )
    return [line.strip() for line in out.splitlines() if line.strip()]


def git_object_type(commit: str, path: str) -> str | None:
    """Return 'blob', 'tree', or None if path missing at commit."""
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", commit, "--", path],
            text=True,
            cwd=REPO_ROOT,
        ).strip()
    except subprocess.CalledProcessError:
        return None
    if not out:
        return None
    # mode type hash\tpath  (path may contain spaces — rare here)
    parts = out.split(None, 3)
    return parts[1] if len(parts) >= 2 else None


def export_paths(commit: str, paths: list[str], dest: Path) -> list[str]:
    """Export files from git at commit. Expands directory paths recursively."""
    exported: list[str] = []
    for rel in paths:
        obj_type = git_object_type(commit, rel)
        if obj_type == "blob":
            file_paths = [rel]
        elif obj_type == "tree":
            file_paths = git_ls_files(commit, rel)
        else:
            print(f"  skip missing: {rel}", file=sys.stderr)
            continue

        if not file_paths:
            print(f"  skip empty tree: {rel}", file=sys.stderr)
            continue

        for fp in file_paths:
            target = dest / fp
            target.parent.mkdir(parents=True, exist_ok=True)
            try:
                content = git_show_file(commit, fp)
            except subprocess.CalledProcessError:
                print(f"  skip unreadable: {fp}", file=sys.stderr)
                continue
            target.write_bytes(content)
            exported.append(fp)
    return exported


def load_graph_meta(commit: str) -> dict:
    raw = git_show_file(commit, "graph.json")
    graph = json.loads(raw)
    return graph.get("meta", {}), graph


def count_orphans(graph: dict) -> int:
    entity_ids = {e["id"] for e in graph.get("entities", [])}
    rel_degree: set[str] = set()
    for rel in graph.get("relationships", []):
        rel_degree.add(rel.get("source", ""))
        rel_degree.add(rel.get("target", ""))
    rel_degree.discard("")
    return len(entity_ids - rel_degree)


def count_high_severe_ir(graph: dict) -> int:
    script_dir = Path(__file__).parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from derive import is_scores_excluded

    return sum(
        1
        for e in graph.get("entities", [])
        if e.get("derived", {}).get("independence_risk_level") in ("high", "severe")
        and not is_scores_excluded(e)
    )


def make_zip(source_dir: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(source_dir))


def main() -> int:
    parser = argparse.ArgumentParser(description="Package JEM for Zenodo (split DOIs)")
    parser.add_argument("--ref", default="v1.0.0", help="Git tag or commit (default: v1.0.0)")
    parser.add_argument("--version", default=None, help="Release version label (default: strip v from ref)")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: build/zenodo)")
    args = parser.parse_args()

    version = (args.version or args.ref).lstrip("v")
    commit = git_rev_parse(args.ref)
    out_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "build" / "zenodo"
    out_dir.mkdir(parents=True, exist_ok=True)

    meta, graph = load_graph_meta(commit)
    orphans = count_orphans(graph)
    high_severe = count_high_severe_ir(graph)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    release_doc = DATASET_DOC.format(
        version=version,
        git_ref=args.ref,
        commit=commit[:12],
        entity_count=meta.get("entity_count", "?"),
        relationship_count=meta.get("relationship_count", "?"),
        orphan_count=orphans,
        high_severe_ir=high_severe,
        generated_at=generated_at,
    )

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Dataset bundle
        ds_root = tmp_path / f"jem-dataset-{version}"
        ds_exported = export_paths(commit, DATASET_PATHS, ds_root)
        (ds_root / "DATA_LICENSE.txt").write_text(
            "Judiciary Entity Map (India) — entity and relationship data\n"
            "Licence: CC0 1.0 Universal (public domain)\n"
            "https://creativecommons.org/publicdomain/zero/1.0/\n",
            encoding="utf-8",
        )
        (ds_root / "SOFTWARE_LICENSE.txt").write_text(
            "Pipeline scripts in jem/scripts/ included for reproducibility\n"
            "Licence: MIT (see repository LICENSE at time of release)\n",
            encoding="utf-8",
        )
        print(f"  dataset files: {len(ds_exported)}")
        (ds_root / "RELEASE.md").write_text(release_doc, encoding="utf-8")
        ds_zip = out_dir / f"jem-dataset-{version}.zip"
        make_zip(ds_root, ds_zip)
        print(f"✓ {ds_zip} ({ds_zip.stat().st_size // 1024} KB)")

        # Software bundle
        sw_root = tmp_path / f"jem-software-{version}"
        sw_exported = export_paths(commit, SOFTWARE_PATHS, sw_root)
        (sw_root / "LICENSE").write_text(
            "MIT License\n\n"
            "Copyright (c) 2026 JEM maintainers\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy\n"
            "of this software and associated documentation files (the \"Software\"), to deal\n"
            "in the Software without restriction, including without limitation the rights\n"
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell\n"
            "copies of the Software, and to permit persons to whom the Software is\n"
            "furnished to do so, subject to the following conditions:\n\n"
            "The above copyright notice and this permission notice shall be included in all\n"
            "copies or substantial portions of the Software.\n\n"
            "THE SOFTWARE IS PROVIDED \"AS IS\", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR\n"
            "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,\n"
            "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE\n"
            "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER\n"
            "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,\n"
            "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE\n"
            "SOFTWARE.\n",
            encoding="utf-8",
        )
        print(f"  software files: {len(sw_exported)}")
        (sw_root / "RELEASE.md").write_text(
            f"# JEM software release {version}\n\n"
            f"MIT licence. Interactive map viewer (`jem/web/`) and pipeline scripts.\n"
            f"Git ref: `{args.ref}` ({commit[:12]})\n\n"
            f"Pair with **jem-dataset-{version}.zip** (separate Zenodo record, CC0).\n",
            encoding="utf-8",
        )
        sw_zip = out_dir / f"jem-software-{version}.zip"
        make_zip(sw_root, sw_zip)
        print(f"✓ {sw_zip} ({sw_zip.stat().st_size // 1024} KB)")

    manifest = {
        "version": version,
        "git_ref": args.ref,
        "commit": commit,
        "entity_count": meta.get("entity_count"),
        "relationship_count": meta.get("relationship_count"),
        "orphan_count_strict": orphans,
        "high_severe_independence_risk": high_severe,
        "entity_schema": "0.1.0",
        "packages": {
            "dataset": ds_zip.name,
            "software": sw_zip.name,
        },
        "generated_at": generated_at,
    }
    manifest_path = out_dir / f"release-manifest-{version}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"✓ {manifest_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
