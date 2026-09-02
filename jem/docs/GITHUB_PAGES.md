# GitHub Pages for the JEM orchestration dashboard

The interactive **map** stays at [friedso.com/apps/jem](https://friedso.com/apps/jem/).
That site is `jem/web/` plus `graph.json`, deployed from the `friedso_v1` production
line. It is a 6 MB canvas app. It is not what GitHub Pages should serve.

This document is how the **orchestration dashboard** — who ran, in what order,
under what permissions — becomes the GitHub repository's clickable website, so
the open-source community can follow a packet run without cloning.

Live URL after enablement: **https://datastiltskin.github.io/jem/**

## Why a separate Pages site, not `jem/web/`

| | Map (`jem/web/`) | Dashboard (`docs/`) |
|---|---|---|
| Audience | Litigants, journalists, researchers using the map | Contributors tracking a data-integrity run |
| Host | friedso.com (maintainer deploy) | github.io (GitHub Actions) |
| Payload | D3 + `graph.json` | One HTML file + diagrams |
| Changes with | entity YAML, renderer | ledger/dashboard, diagrams |

Putting the map on GitHub Pages would either duplicate friedso.com or fight it
for the `github.io/jem/` URL. Putting the dashboard there gives the repo a
page the community can bookmark, and leaves the product where it already lives.

## What we committed

```
docs/                         ← GitHub Pages root (generated; do not hand-edit)
  index.html                  ← copy of jem/ledger/dashboard/index.html
  diagrams/                   ← gif / png / mp4 / webm
  .nojekyll                   ← do not run Jekyll
  README.md
jem/ledger/dashboard/         ← source of truth
jem/scripts/harness/publish_dashboard.py
.github/workflows/pages.yml   ← deploys docs/ on push to main
```

Regenerate after changing the dashboard or the renderer:

```bash
cd jem
python3 scripts/harness/render_orchestration.py
python3 scripts/harness/publish_dashboard.py
# then commit docs/ alongside the ledger sources
```

Preview locally: `python3 -m http.server 8080 --directory docs` and open
http://127.0.0.1:8080/. Or open `docs/index.html` in a browser (the GIF/MP4
paths are relative, so `file://` works too).

## One-time maintainer steps

These cannot be done from a pull request. A repo admin does them once.

1. **Settings → Pages**
   - Source: **GitHub Actions** (not “Deploy from a branch”).
   - The first run of `GitHub Pages — orchestration dashboard` then publishes
     `docs/` to `https://datastiltskin.github.io/jem/`.
2. **Settings → General → About → Website**
   - Set to `https://datastiltskin.github.io/jem/`.
   - That is the “clickable page” next to the repo description. The README
     continues to lead with friedso.com as the map.
3. Optional fallback, if Actions Pages is blocked on a plan or permission:
   - Source: **Deploy from a branch**
   - Branch: `main` / folder: `/docs`
   - Same URL. The workflow can stay; GitHub will ignore it if the source is
     “branch”. Prefer Actions so a broken `docs/` tree fails the job instead
     of silently serving an old copy.

Until step 1 is done, `https://datastiltskin.github.io/jem/` 404s. The
dashboard is still readable from the repo:

- https://github.com/datastiltskin/jem/blob/main/docs/index.html (after merge)
- or clone and open `docs/index.html`

## What we are not doing

- Not replacing friedso.com.
- Not deploying `jem/web/` to the same Pages site. A later `/map/` subpath is
  possible (copy `jem/web/` + `graph.json` into `docs/map/`) but it is a
  product decision: two copies of a 6 MB graph to keep in sync. Out of scope
  until someone wants github.io to host a mirror of the map.
- Not auto-deploying from feature branches. Preview = this PR’s `docs/` tree
  locally, or a maintainer running **workflow_dispatch** after merge.

## Custom domain

Skip unless the project wants something like `status.friedso.com`. A `docs/CNAME`
file plus DNS would do it; that is a founder decision, not part of this wiring.
