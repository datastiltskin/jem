# v1.0.0 release runbook (items 1–3)

**Audience:** operator running friedso.com deploy and git tag.  
**Prerequisite:** `validate.py` clean; repo-root `graph.json` is the build you intend to ship (~500 entities, May 2026 corpus).

---

## 0. Preflight (run locally)

```bash
cd /path/to/jem/repo
./jem/scripts/deploy_prep.sh
```

Fix any errors before rsync. See [`SESSION_WORKFLOW.md`](SESSION_WORKFLOW.md) for the daily pipeline and **graph overwrite** risks.

---

## 1. Deploy to friedso.com

`jem/web/public/graph.json` is a **symlink** → repo-root `graph.json`. Static hosts often do not resolve that symlink correctly unless you ship the repo layout or **copy the file**.

### Recommended (two-step from repo root)

```bash
export JEM_REMOTE="you@friedso.com:~/path/to/site/apps/jem"
export JEM_PUBLIC="${JEM_REMOTE}/public"

# 1) Ship the graph as a real file at public/graph.json
rsync -avz graph.json "${JEM_PUBLIC}/graph.json"

# 2) Ship the web app (HTML/CSS/JS; --delete drops removed assets)
rsync -avz --delete jem/web/ "${JEM_REMOTE}/"
```

Adjust `JEM_REMOTE` to match your vhost (e.g. `https://friedso.com/apps/jem/`).

### Optional: materialize locally before one rsync

Only if you prefer a single `jem/web/` tree without relying on symlink at deploy time:

```bash
cp graph.json jem/web/public/graph.json   # replaces symlink — restore symlink after deploy if needed
ln -sf ../../../graph.json jem/web/public/graph.json
```

### Do not deploy a stale or partial graph

- **Never** run `python3 jem/scripts/build.py` on a partial YAML tree without checking `meta.entity_count`.
- Use `jem/scripts/build_safe.sh` for experiments → `build/graph.staging.json` only.

---

## 2. Live smoke tests

Open the public URL (e.g. `https://friedso.com/apps/jem/`). Check:

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
git status   # clean, on main (or release branch)
git log -1 --oneline

git tag -a v1.0.0 -m "JEM v1.0.0 — backbone + MH/DL/KA/TN/PY, NJDG rollup merge"

# Push when remote is ready (deferred to v2 for GitHub setup — see MASTER_CHECKLIST Part 4)
# git push origin main
# git push origin v1.0.0
```

Record in release notes:

- 505 entities / 512 relationships in shipped `graph.json` (May 2026 build)
- NJDG static snapshot merge (139 entities); district-level NJDG **parked** (Part 3.5.2)
- TN 38-district lattice + consolidated generic

---

## Related

- [`MASTER_CHECKLIST.md`](../../MASTER_CHECKLIST.md) §3.4  
- [`V1_DATA_RESTORE.md`](V1_DATA_RESTORE.md) — if graph was overwritten  
- [`SESSION_WORKFLOW.md`](SESSION_WORKFLOW.md) — every-session commands + overwrite warning
