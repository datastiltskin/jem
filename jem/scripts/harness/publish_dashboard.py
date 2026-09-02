#!/usr/bin/env python3
"""
Publish the orchestration dashboard to repo-root docs/ for GitHub Pages.

Source of truth stays in jem/ledger/dashboard/ (next to the run record).
This copies it to docs/ with asset paths rewritten so the Pages site is a
self-contained static tree:

    docs/index.html
    docs/diagrams/orchestration.gif|.png|.mp4|.webm
    docs/.nojekyll

Usage (from jem/):
    python3 scripts/harness/render_orchestration.py
    python3 scripts/harness/publish_dashboard.py
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ASSET_NAMES = (
    "orchestration.gif",
    "orchestration.png",
    "orchestration.mp4",
    "orchestration.webm",
)


def publish(repo_root: Path) -> Path:
    src_html = repo_root / "jem" / "ledger" / "dashboard" / "index.html"
    src_diagrams = repo_root / "jem" / "ledger" / "diagrams"
    dest = repo_root / "docs"
    dest_diagrams = dest / "diagrams"

    if not src_html.is_file():
        raise SystemExit(f"missing dashboard: {src_html}")

    dest.mkdir(parents=True, exist_ok=True)
    dest_diagrams.mkdir(parents=True, exist_ok=True)

    html = src_html.read_text(encoding="utf-8")
    html = html.replace("../diagrams/", "diagrams/")
    # Pages is a project site at /jem/; keep relative asset URLs.
    dest.joinpath("index.html").write_text(html, encoding="utf-8")
    dest.joinpath(".nojekyll").write_text("", encoding="utf-8")

    copied = []
    for name in ASSET_NAMES:
        src = src_diagrams / name
        if src.is_file():
            shutil.copy2(src, dest_diagrams / name)
            copied.append(name)

    readme = dest / "README.md"
    readme.write_text(
        "# JEM GitHub Pages site\n\n"
        "This folder is the published **orchestration dashboard** — the "
        "repository's clickable community page, not the interactive map.\n\n"
        "- Live (after Pages is enabled): https://datastiltskin.github.io/jem/\n"
        "- Map (product): https://friedso.com/apps/jem/\n"
        "- Source HTML: `jem/ledger/dashboard/index.html`\n"
        "- How to enable / regenerate: `jem/docs/GITHUB_PAGES.md`\n\n"
        "Regenerate with:\n\n"
        "```bash\n"
        "cd jem\n"
        "python3 scripts/harness/render_orchestration.py\n"
        "python3 scripts/harness/publish_dashboard.py\n"
        "```\n",
        encoding="utf-8",
    )
    print(f"  wrote {dest / 'index.html'}")
    print(f"  copied {len(copied)} diagram assets → {dest_diagrams}")
    return dest


def main():
    ap = argparse.ArgumentParser(description="Publish dashboard to docs/ for GitHub Pages")
    ap.add_argument("--repo-root", default=None)
    args = ap.parse_args()
    here = Path(__file__).resolve()
    repo_root = Path(args.repo_root) if args.repo_root else here.parents[3]
    publish(repo_root)


if __name__ == "__main__":
    main()
