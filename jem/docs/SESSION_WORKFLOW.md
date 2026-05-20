# JEM — session workflow (bookmark)

Run from repo root unless noted. **Order matters.**

---

## Standard data session

```bash
cd jem

# 1. Before editing
python3 scripts/validate.py --strict

# 2. Edit YAML under data/entities/ and data/relationships/

# 3. After editing
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py
python3 scripts/derive.py
python3 scripts/build.py          # ⚠ see overwrite warning below
python3 scripts/derive.py --clog-report   # optional spot-check

# 4. Commit (from repo root)
cd ..
git add jem/data graph.json
git commit -m "data(scope): description"
```

Shortcut (validate + derive + build, no generator):

```bash
cd jem && ./scripts/safe_pipeline.sh
```

---

## ⚠ Graph / bundle overwrite risks

| Risk | What happens | Safe practice |
|------|----------------|-----------------|
| **`build.py` without `--output`** | Writes **repo-root `graph.json`**, which `jem/web/public/graph.json` symlinks to | Only run when you intend to replace the viewer graph. Check `meta.entity_count` after build. |
| **Partial YAML corpus** | Build can shrink graph to tens of entities | Run `deploy_prep.sh` or `python3 -c "import json; print(json.load(open('graph.json'))['meta'])"` before deploy. |
| **`generate_v1_states_bundle.py`** | Regenerates large `_generated/` trees; can **overwrite** hand-edited entity YAML | Run only when intentional. Prefer targeted edits or `bootstrap_*.py` for one-off lattice work. |
| **`merge_njdg_snapshot.py --apply`** | Overwrites `case_volume` + appends NJDG source on matched entities | Idempotent for same snapshot; re-run after adding new entity YAML. |
| **`build_safe.sh`** | Writes **`build/graph.staging.json` only** — does not touch production symlink target | Use for experiments; diff staging vs root before promoting. |

**Promote staging → production:**

```bash
cd jem
./scripts/build_safe.sh
python3 -c "import json; m=json.load(open('build/graph.staging.json'))['meta']; print(m)"
# If counts look right:
cp build/graph.staging.json ../graph.json
```

**Restore after accidental clobber:** [`V1_DATA_RESTORE.md`](V1_DATA_RESTORE.md)

---

## Deploy / release (v1.0.0)

See [`V1_RELEASE_RUNBOOK.md`](V1_RELEASE_RUNBOOK.md) — preflight, rsync, smoke tests, git tag.

---

## Generators (use sparingly)

| Script | Purpose |
|--------|---------|
| `generate_v1_states_bundle.py` | Full state bundle regen — **high overwrite risk** |
| `bootstrap_tn_district_lattice.py` | TN 38 districts + generic — idempotent skips |
| `merge_njdg_snapshot.py` | NJDG snapshot → entity `case_volume` |
| `build_safe.sh` | Safe build to staging only |

Install optional git hook (blocks unsafe generator without env flag):

```bash
cd jem && ./scripts/install-git-hooks.sh
```
