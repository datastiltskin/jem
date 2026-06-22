# v1.0.0 release runbook (items 1–3)

**Audience:** maintainers running production deploy and git tag.  
**Prerequisite:** `validate.py` clean; repo-root `graph.json` is the build you intend to ship (**1,103** entities, Jun 2026 corpus).

**Canonical public demo (attribution only):** https://friedso.com/apps/jem/

**Deploy branch:** `friedso_v1` — production always serves this branch. `main` continues for active development; promote to `friedso_v1` via PR after validate + smoke test (founder merges only — see [`GOVERNANCE.md`](../../.github/GOVERNANCE.md)).

---

## 0. Preflight (run locally)

**Recommended:** checkout `friedso_v1`, then run:

```bash
git fetch origin
git checkout friedso_v1
git pull --ff-only origin friedso_v1
./jem/scripts/deploy_friedso_production.sh          # validate → derive → build → bundle
./jem/scripts/deploy_friedso_production.sh --deploy # rsync when JEM_REMOTE is set
```

Or run `./jem/scripts/deploy_prep.sh` for checks only, then ship `graph.json` + `jem/web/` per §1 below.

Maintainers with a **local copy** of `build_friedso_deploy_bundle.sh` (not in public GitHub — see `jem/scripts/MAINTAINER_SCRIPTS.md`) can build `_deploy_bundle/jem-web-*` and optional `--deploy`.

Fix any errors before upload/rsync. See [`SESSION_WORKFLOW.md`](SESSION_WORKFLOW.md) for the daily pipeline and **graph overwrite** risks.

### Promote `main` → `friedso_v1`

When `main` has changes you want on friedso.com:

```bash
gh pr create --base friedso_v1 --head main --title "deploy: promote main to friedso_v1"
# Founder: run deploy_friedso_production.sh locally on friedso_v1 after merge, then smoke §2
```

---

## 1. Deploy to production (static host)

`jem/web/public/graph.json` is a **symlink** → repo-root `graph.json`. Static hosts often do not resolve that symlink correctly unless you ship the repo layout or **copy the file**.

Set your deploy target (keep real host/user/path in your shell or private notes — **do not commit**):

```bash
export JEM_REMOTE='user@your-host.example:~/path/to/apps/jem'
export JEM_PUBLIC="${JEM_REMOTE}/public"
export JEM_PUBLIC_URL='https://your-host.example/apps/jem/'   # for smoke tests
```

### Recommended (two-step from repo root)

```bash
# 1) Ship the graph as a real file at public/graph.json
rsync -avz graph.json "${JEM_PUBLIC}/graph.json"

# 2) Ship the web app (HTML/CSS/JS; --delete drops removed assets)
rsync -avz --delete jem/web/ "${JEM_REMOTE}/"
```

### Other deploy options

| Method | Notes |
|--------|--------|
| **rsync over SSH** | Above; use `JEM_REMOTE` you control |
| **S3 / object storage** | Upload `graph.json` to `public/graph.json` + sync `jem/web/` |
| **GitHub Pages / Netlify** | Build artifacts only; ensure `public/graph.json` is a real file |
| **Local smoke** | `cd jem/web && python3 -m http.server 8080` |

### Optional: materialize locally before one rsync

```bash
cp graph.json jem/web/public/graph.json   # replaces symlink — restore symlink after deploy if needed
ln -sf ../../../graph.json jem/web/public/graph.json
```

### Do not deploy a stale or partial graph

- **Never** run `python3 jem/scripts/build.py` on a partial YAML tree without checking `meta.entity_count`.
- Use `jem/scripts/build_safe.sh` for experiments → `build/graph.staging.json` only.

---

## 2. Live smoke tests

Open **`$JEM_PUBLIC_URL`** (your deployed URL). Check:

| # | Test | Pass criteria |
|---|------|----------------|
| 1 | Page load | No console errors loading `public/graph.json` |
| 2 | Search | Type `Supreme Court` — node highlights / found |
| 3 | Appellate arcs | Default view shows appellate_chain edges |
| 4 | L0 clusters | Cluster rectangles visible (~14 clusters) |
| 5 | L3 panel | Click an entity — detail panel opens with fields |
| 6 | Timeline | Year scroller drags; entities filter by year |
| 7 | Impact bar | Shows gap / Not_Constituted counts (numbers may differ from old build) |
| 8 | State packs | Filter or navigate MH, DL, KA, TN, PY entities |
| 9 | TN districts | Focus **Madras HC** — use **+/−** to collapse/expand district lattice; collapsed shows `tn_district_courts_generic` |

If `graph.json` 404s or shows ~13 entities, the deploy did not ship the repo-root graph (see §1).

---

## 3. Tag `v1.0.0` (after smoke pass)

```bash
cd /path/to/jem/repo
git checkout friedso_v1
git status   # clean, on friedso_v1
git log -1 --oneline

git tag -a v1.0.0 -m "JEM v1.0.0 — 1,103 entities, full state/UT packs, UI refresh"

# git push origin friedso_v1
# git push origin v1.0.0
```

Record in release notes:

- **1,103** entities / **1,858** relationships in shipped `graph.json` (Jun 2026)
- Full state/UT core packs (35 codes); central tribunal bench lattice
- Summary/detail UI refresh (co-maintainer @Prajna1999); `entityConnections.js`; DC→HC edge backfill at build
- NJDG static snapshot merge (139 entities); district-level NJDG **parked** (Part 3.5.2)
- TN 38-district lattice + consolidated generic

---

## Related

- [`MASTER_CHECKLIST.md`](../../MASTER_CHECKLIST.md) §3.4  
- [`V1_DATA_RESTORE.md`](V1_DATA_RESTORE.md) — if graph was overwritten  
- [`SESSION_WORKFLOW.md`](SESSION_WORKFLOW.md) — every-session commands + overwrite warning
