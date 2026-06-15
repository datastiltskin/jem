# Judiciary Entity Map (India) - JEM — Master Build & Deployment Checklist
# Generated: April 25 2026
# Last full repo audit: **Jun 15 2026 (post Wave 4–5 + C26 orphan wiring complete)** — see PROGRESS & REPO AUDIT below
# Current build: **1,103 entities**, **1,855 relationships**, **~5.63 MB** `graph.json` (`validate.py` 0 errors)
# ============================================================
# HOW TO USE THIS FILE
# - Work top to bottom
# - Check each box [x] as you complete it
# - Never edit `jem/data/derived/` manually; do not hand-edit `graph.json` — rebuild via scripts
# - After ANY data change: `validate.py` → `derive.py` → `build.py` → spot-check
# - NJDG snapshot merge: `jem/scripts/merge_njdg_snapshot.py` (see Part 3.5)
# ============================================================

---

## REPO AUDIT (Jun 15 2026 — post Wave 4–5 state packs)

| Metric | Value |
|--------|--------|
| Unique entity ids in graph | **1,103** |
| Entity YAML files on disk | **1,103** (canonical) |
| Relationship files | **50** packs (**1,855** edges in `graph.json`) |
| `graph.json` size | **~5.63 MB** (5,629,019 bytes after `build.py`) |
| `validate.py` | **0 errors** (1,152 files checked) |
| `validate_graph_refs.py` | **0 broken refs**; **0 orphan entities** (no rel source/target; `--strict`) |
| `CentralTribunal` entities | **101** (principals + CESTAT×8, AFT×12, DRT×25, DRAT×6, ITAT×25, CGIT×7, EPFAT, tax stack, etc.) |
| State SERC entities | **32** under `regulatory_bodies/serc_states/` |
| `RegulatoryBodyQJ` (backbone) | trai, sebi, cci, irdai, pfrda, fssai, aera + state SERC gens |
| Funding ministry stubs | ministry_of_power, ministry_consumer_affairs, ministry_corporate_affairs, ministry_environment — **present** |
| `judge_strength` populated (allotted/appointed) | **39 / 1,103** (HC health pass Jun 2; dilution from new entities) |
| `case_volume.pending_cases` populated | **84 / 1,103** |
| HC permanent benches in graph | **13** — Madras HC has **Madurai only** (no Tiruchirappalli bench) |
| Entities with `case_volume` block in YAML | 153 |
| Entities tagged `NJDG snapshot case_volume merged` | 139 |
| State/UT packs (35 folders) | All states + UTs have core packs (SERC, RERA, SJA, SLSA, AG, CDRC, 2–10 named districts + generic); **TN 50** (38-district lattice), **MH 53**, **KA 43** |
| TN district lattice | 38 per-district courts + `tn_district_courts_generic` (collapse proxy) |
| Digital infra (C10) | e_committee_sc, nic_india, ecourts_services_generic, njdg_generic |
| Security scaffolds (C11) | crpf, cisf, state_police_generic, court_marshal_sc, sheriff_hc_generic |
| NJDG snapshot source | local `graph.json` snapshot (216 entities with `_detail.case_volume`; path not in repo) |
| Merge plan | [`jem/docs/NJDG_MERGE_PLAN.md`](jem/docs/NJDG_MERGE_PLAN.md) — 139 mergeable rows applied |

**Recent work (Jun 15 — Wave 4–5 + v1.2):** **C15–C18 state packs** — core entities for all remaining states/UTs (AP, TS, GJ, MP, BR, KL, PB, HR, OD, NE states, CG, GA, HP, JH, UK, CH, AN, LD, LA, JK, SK; PY expanded). **Per-state relationship packs** — `{st}_relationships.yaml` for all 35 state folders + `c26_backbone_orphan_relationships.yaml` + `c26_generic_orphan_relationships.yaml` (22 generic orphans wired). Entity count **668 → 1,103**; relationships **748 → 1,855**; orphans **175 → 0**.

**Prior (Jun 12 — Phase 1 batch):** M-T1 ITAT×25; M-T2–M-T6; C15 UP/WB/RJ; C10/C11. **599 → 668** entities.

**Prior (May 20):** Central tribunal + regulator + ministry batch; IIAC rename; governance graph Phase 6. Operator docs: [`V1_DATA_RESTORE.md`](jem/docs/V1_DATA_RESTORE.md) · [`V1_RELEASE_RUNBOOK.md`](jem/docs/V1_RELEASE_RUNBOOK.md) · [`ENTITY_BUILD_ROADMAP.md`](jem/docs/ENTITY_BUILD_ROADMAP.md).

---

## PROGRESS & STATUS (Jun 15 2026)

**Restore procedure:** [`jem/docs/V1_DATA_RESTORE.md`](jem/docs/V1_DATA_RESTORE.md) · **v1 release:** [`jem/docs/V1_RELEASE_RUNBOOK.md`](jem/docs/V1_RELEASE_RUNBOOK.md) · **v2 schema:** [`jem/docs/V2_DATA_MODEL.md`](jem/docs/V2_DATA_MODEL.md) · **entity roadmap:** [`jem/docs/ENTITY_BUILD_ROADMAP.md`](jem/docs/ENTITY_BUILD_ROADMAP.md)

### Done (verified this audit)

- [x] **Full YAML corpus** under `jem/data/entities/` (hand-curated + `_generated/`) — `build.py` reproduces the large graph intentionally.
- [x] **Phase 1 state packs:** MH, DL, KA, TN (38-district lattice), PY — see Part 3.
- [x] **NJDG snapshot merge (state / HC / tribunal rollups):** `merge_njdg_snapshot.py --apply` — 139 entities; see Part 3.5.
- [x] **TN collapsed + expanded district model:** `tn_district_courts_generic` + per-district YAML; map uses `districtAggregates.js` (+/− on Madras HC).
- [x] **v2 partial (data + UI):** HC bench entities, `judge_strength` blocks, district lattice collapse, IIAC (ex-NDIAC), state SCDRC/NHRC, CVC consolidation.
- [x] **Toolchain:** `validate.py`, `derive.py`, `build.py`, `generate_v1_states_bundle.py`, `merge_njdg_snapshot.py`, `bootstrap_tn_district_lattice.py`.
- [x] **CI scaffold:** `.github/workflows/validate.yml`.
- [x] **Docs:** `DATA_MODEL.md`, `CONTRIBUTING.md`, `NJDG_MERGE_PLAN.md`, `V2_DATA_MODEL.md`, `V1_DATA_RESTORE.md`, `V1_RELEASE_RUNBOOK.md`, `SESSION_WORKFLOW.md`.
- [x] **Doc cleanup (May 20):** GANTT schedule doc removed; patch-extract bundles deleted from workspace.
- [x] **Governance graph (May 20):** Central officeholders + appointment committees; NHRC/CVC/CBI consultation edges; minister vs ministry distinction; `validate_graph_refs.py` in pipeline.
- [x] **Governance score exclusions:** `derive.py` + [`jem/docs/DATA_MODEL.md`](jem/docs/DATA_MODEL.md) — PM/ministers/ministries excluded from IR/DP; `AppointmentBody` committees still scored.
- [x] **CBI Director appointment:** Lokpal Act 2013 s.4A selection committee (`selection_committee_cbi_director`); retired `dopt_dpc` entity.
- [x] **Coverage-gap session (May 20 parallel agents):** §1 central tribunals/regulators + §2 funding ministries; ExecutiveBody audit clean; §6 HC benches (Bombay–Shimla); IIAC rename; Madurai/DIAC/MCIA/tn_slsa primary-source fields.
- [x] **Batch 3 (Jun 12) — C21/C22/C23:** Defence (`court_martial_generic`), specialised regulators (FSSAI, AERA, ICADR, PCI, SEC generic, insurance ombudsman), IP stack (CGPDTM, TMR, COMPAT, IPAB abolished in-place); relationship pack + `ConsultedOn_Removal` schema.
- [x] **C04 regional benches (Jun):** CESTAT×8, AFT×11 (+ Jabalpur, Srinagar beyond original 9), DRT×25 regional + DRAT circuit wiring; AFT BenchOf + bench→SC appellate edges.
- [x] **C19 tax stack (partial):** `cit_appeals_generic`, `ao_income_tax_generic`, `jcit_appeals_generic`, `aar_income_tax`, `caar_customs`, `gstat_bench_generic` in graph; ITAT chain wired.
- [x] **C20 labour (partial):** CGIT×6 + `cgit_principal` + EPFAT + EPFO — BenchOf + MoLE funding/oversight wired (`cgit_epfat_mole_relationships.yaml`); **remaining:** ESI courts, state labour court generic.
- [x] **Tribunal completion (Jun 12):** DRAT BenchOf×5, CESTAT→HC×9, tax appellate edges in `tribunal_completion_jun2026.yaml`.
- [x] **HC numerics pass (Jun 2):** `judge_strength` on constitutional/HC entities — 40/668 populated.
- [x] **ITAT×25 per-zone benches (Jun 12 — M-T1):** `itat_*` bench entities + `itat_bench_relationships.yaml`; aggregate `rel_itat_to_high_courts_all` removed.
- [x] **UP/WB/RJ state packs (Jun 12 — C15):** core entities + named districts; relationship packs wired (bench routing).
- [x] **C10 digital infrastructure (Jun 12):** e_committee_sc, nic_india, ecourts_services_generic, njdg_generic.
- [x] **C11 security scaffolds (Jun 12):** crpf, cisf, state_police_generic, court_marshal_sc, sheriff_hc_generic.
- [x] **C20 labour scaffolds (Jun 12 — M-T4):** `state_labour_court_generic`, `esi_court_generic` (generic scaffolds; wiring pending).
- [x] **Wave 4–5 state packs (Jun 15 — C15–C18):** core packs for all 28 states + 7 UTs (35 folders); 6–10 named districts each + `*_district_courts_generic`; SERC/RERA/SJA/SLSA/AG/CDRC per MH template.
- [x] **State relationship wiring (Jun 15 — C26):** per-state `{st}_relationships.yaml` packs; orphans **175 → 0** (`c26_backbone_orphan_relationships.yaml` + `c26_generic_orphan_relationships.yaml`).

### What remains to complete the project (~1,500 entity target)

| Priority | Workstream | Gap | Best tool | Blocks deploy? |
|----------|------------|-----|-----------|----------------|
| **P0** | **v1.0.0 ship** — runbook deploy + smoke + local tag | Operator step only | Human | **Yes** — first public semver |
| **P1** | **v1.1 finish** — KA Dharwad bench verify; `board_of_revenue_generic` / `state_industrial_tribunal_generic` `state_data` | ~3 config items | **Cursor** | No |
| **P2** | **v1.2 numerics** — `judge_strength` **39/1,103**; `case_volume` **84/1,103** | ~1,000+ court-like entities | **Cursor** bulk + **Claude** field design | No |
| **P3** | **v1.4 district lattices** — 31 states at 2–10 named districts vs TN 38 / MH 36 / KA 29 | **~400 entities** → ~1,500 | **Cursor** (generator + YAML) | No |
| **P4** | **v1.5 gap registry** — GSTAT benches (gated), DRT `drt_city_n` (gated), labour/ESI wiring, 28 Board of Revenue | ~50–80 when ungated | **Claude** domain + **Cursor** YAML | No |
| **P5** | **v1.3 per-district NJDG** — TN **1/38** with `pending_cases` | Blocked on district exports | Maintainer + NJDG | No |
| **P6** | **v2.0 product** — Canvas, live `fetch_njdg.py`, Sankey, journey mode, GitHub remote | Part 4 | **Claude** architecture + **Cursor** impl | No |
| **Ongoing** | **C27 data quality** — **1,094/1,103** at `partial`; 9 `verified` | Community + reviewers | **Cursor** + sources | No |

**Critical path to structural completeness (~1,500):** P0 → P1 → P3 → P4. **Critical path to metric usefulness:** P2 + P5. **Critical path to product completeness:** P6.

### Coverage-gap thread — v1.0.0 deploy still pending; post-May growth → **VERSION ROADMAP**

> **Deploy decision (May 20, still valid):** Ship **v1.0.0** when operator runs runbook (`validate.py` 0 errors). Corpus has since grown **506 → 1,103** entities pre-deploy — acceptable to tag v1.0.0 at current head or cut from an earlier commit; remainder scheduled for **v1.1+**.

| Thread action | Status | Target release |
|---------------|--------|----------------|
| ExecutiveBody audit (mis-typed tribunal stubs) | ✅ **Done** | v1.0.0 |
| Create NCLAT, TDSAT, AFT, DRT, DRAT, RCT, IPAB | ✅ **Done** | v1.0.0 |
| Create TRAI, SEBI, CCI, IRDAI, PFRDA | ✅ **Done** | v1.0.0 |
| Create ministry_of_power, ministry_consumer_affairs, ministry_corporate_affairs, ministry_environment | ✅ **Done** | v1.0.0 |
| §6 HC bench YAML batch (non-Madras) | ✅ **Done** | v1.0.0 |
| IIAC rename (ex-NDIAC) | ✅ **Done** | v1.0.0 |
| Primary source: Madurai `created_year`, DIAC `statutory_basis`, MCIA/tn_slsa `created_year` | ✅ **Done** | v1.0.0 |
| Madras HC bench model (Madurai only; no Trichy bench) | ✅ **Done** | v1.0.0 |
| Bench routing: UP / WB / RJ | ✅ **Done** (Jun 12) | v1.0.0 |
| KA Dharwad district→bench verify | ⏸️ Deferred | **v1.1** |
| Relationship orphans (~175) — incremental wiring | ✅ **Done** (0 remain — C26 packs) | **v1.1** |
| §7 `judge_strength` bulk fill | ⏸️ Partial (39/1,103) | **v1.2** |
| §3 `case_volume` bulk fill | ⏸️ Partial (84/1,103) | **v1.2** |
| C04 DRT remaining benches (14 of 39) | ⏸️ Deferred (gated on drt.gov.in) | **v1.5** / Phase 3 |
| C20 labour court wiring (ESI, state labour courts) | ⏸️ Partial (scaffolds in graph; CGIT/EPFAT/EPFO wired) | **v1.5** |
| Per-district NJDG (TN 37/38, MH/KA bootstrap) | ⏸️ Parked | **v1.3** |
| §5 full state district lattices (core packs done; TN/MH/KA deep) | ⏸️ Core packs ✅; per-district expansion deferred | **v1.4** |
| Gap registry entities (tax/labour/defence benches) | ⏸️ Mostly done — GSTAT benches gated | **v1.5** (Part 5) |

### v1.0.0 release (operator — prepared, not yet run)

**Runbook:** [`jem/docs/V1_RELEASE_RUNBOOK.md`](jem/docs/V1_RELEASE_RUNBOOK.md) · **Preflight:** `./jem/scripts/deploy_prep.sh`

- [ ] **1. Deploy** — rsync `graph.json` + `jem/web/` (see runbook §1; symlink caveat)
- [ ] **2. Live smoke tests** — runbook §2 checklist on production URL
- [ ] **3. Tag** — `git tag -a v1.0.0` after smoke pass (push deferred to v2 — Part 4.3)

### Parked (scheduled later — do not block v1.0.0 tag)

- [ ] **District-level NJDG exports** — **v1.3** (Part 3.5.2)

### Deferred to v2.0 (product / infra — not v1.x data releases)

> **Naming:** **v1.x** = data/graph semver tags on production deploy. **v2.0** = UI + live API + GitHub (Part 4) — separate from v1.1–v1.5 below.

- [ ] **GitHub remote + CI QA** — Part 4.3 (push repo, Actions on PR, topics/description)
- [ ] **Live NJDG API** (`fetch_njdg.py`) — Part 4.2

### Still outstanding (scheduled releases — see VERSION ROADMAP)

- [ ] **v1.1** — KA Dharwad verify + generic `state_data` (orphans ✅)
- [ ] **v1.2** — `judge_strength` + `case_volume` numeric bulk fill
- [ ] **v1.3** — per-district NJDG (when exports exist)
- [ ] **v1.4** — non-TN state district lattices (Part 5.6)
- [ ] **v1.5** — gap registry entities (Part 5.1–5.5)
- [ ] **v2.0** — Canvas / Sankey / live NJDG / GitHub (Part 4.2–4.3)

---

## VERSION ROADMAP (v1.0.0 → v1.5)

Semantic data releases after **v1.0.0** deploy. Tag with `git tag -a v1.x.y` after validate + build + smoke on production URL.

| Release | Scope | Acceptance |
|---------|--------|------------|
| **v1.0.0** | Ship graph at deploy time (**1,103** entities, **1,855** rels at Jun 15 head; was 668/748 at Jun 12). | `validate.py` 0 errors; runbook deploy + smoke; local tag |
| **v1.1** | **Structural integrity** — no new external datasets required | Config matches graph; UP/WB/RJ bench edges ✅; orphans **0** ✅; KA Dharwad + generic `state_data` remain |
| **v1.2** | **Numeric coverage** — DoJ + NJDG rollups | `judge_strength` on all court-like entities; `case_volume` >> 84/1,103 |
| **v1.3** | **Per-district NJDG** — blocked on district exports | TN 38/38 + MH/KA bootstrap districts with district URLs |
| **v1.4** | **State pack expansion** | Replace 31 `*_district_courts_generic`-only states with MH/DL/KA-style packs |
| **v1.5** | **Gap registry** | Part 5.1–5.5 high-priority missing entities (CESTAT benches, CIT(A), AFT benches, etc.) |
| **v2.0** | **Product** (not data-only) | Part 4 — Canvas, `fetch_njdg.py`, Sankey, GitHub remote |

### v1.1 — structural integrity (target: first post-deploy data release)

- [x] **Madras HC bench model** — Madurai sole permanent bench; `hc_madras_bench_tiruchirappalli` removed from `hc_benches_config.py` and generators (no Trichy bench)
- [x] **Bench district routing** — `up_relationships.yaml`, `wb_relationships.yaml`, `rj_relationships.yaml` with `AppealableTo` / supervisory edges per `hc_benches_config.py` (Lucknow, Jalpaiguri, Jaipur) — **done Jun 12**
- [ ] **KA Dharwad** — verify all districts in `KA_DISTRICT_TO_BENCH` have bench edges (**29/29** named KA districts wired in `ka_relationships.yaml`; confirm `hc_benches_config.py` table matches e-Courts roster)
- [x] **Orphan wiring (finish)** — **0** orphans (`c26_generic_orphan_relationships.yaml`, Jun 15); check: `python3 jem/scripts/validate_graph_refs.py --strict`
- [x] **Housekeeping** — deleted 108 untracked `* 2.yaml` + 1 `* 2.py` macOS duplicate files (Jun 12)
- [ ] Re-run: `validate.py` → `derive.py` → `build.py` → deploy → tag `v1.1.0`

### v1.2 — numeric coverage (§3 + §7)

- [ ] Bulk **`judge_strength`** (allotted/appointed) from DoJ vacancy reports: https://doj.gov.in/report-and-committees/judicial-vacancy-reports
- [ ] Extend **`case_volume.pending_cases`** beyond 84/506 — refresh `merge_njdg_snapshot.py` when new snapshot path available
- [ ] All court-like entities: `judge_strength` block with `data_as_of` + `source_type` (nulls OK + `data_quality_notes`)
- [ ] **Audit baseline:** `judge_strength` 39/1,103 → target majority of courts; `pending_cases` 84/1,103 → target all HCs + state rollups + named districts
- [ ] Tag `v1.2.0` after smoke

### v1.3 — per-district NJDG (Part 3.5.2 — blocked on exports)

> **Do not start until district-level NJDG exports exist.** State/HC rollup merge is complete in v1.0.0.

| Scope | Count | Current | Unblock |
|-------|-------|---------|---------|
| TN per-district courts | 38 | 1 with `pending_cases` (Chennai) | TN e-Courts / NJDG district export |
| MH bootstrap districts | 26 | structural only | Per-district NJDG per `mh_district_court_*` |
| KA bootstrap districts | 19 | structural only | same |
| Other states | varies | generic rollup only | Phase with v1.4 |

- [ ] Each targeted court YAML: `pending_cases`, `filed_last_year`, `disposed_last_year` (or null + notes)
- [ ] `data_quality_notes` cites NJDG district URL + `data_as_of`
- [ ] Tag `v1.3.0`

### v1.4 — state district lattices (§5 / Part 5.6)

- [x] **Core state packs** — all 35 state/UT folders have SERC, RERA, SJA, SLSA, lokayukta, AG, CDRC, 2–10 named districts + generic (Jun 15)
- [ ] **Per-district lattice expansion** — expand beyond core packs using `bootstrap_tn_district_lattice.py` pattern + NJDG per state (TN 38/38 done; MH 36 named; KA 29 named; others 2–10 named)
- [ ] Priority deep-lattice batches: UP, WB, AP, TS, GJ, KL (high volume)
- [x] **Orphan wiring (finish)** — 0 backbone/generic orphans remain
- [ ] Tag `v1.4.0`

### v1.5 — gap registry (Part 5)

- [x] §5.1 Tax/revenue stack — **partial:** CESTAT×8, CIT(A)/JCIT(A)/AO generics, AAR/CAAR, `gstat_bench_generic`; **remaining:** GSTAT constituted benches, VAT tribunal per-state
- [x] §5.2 Labour — **partial:** CGIT×6 + principal wired (MoLE funding); EPFAT + EPFO in graph; `state_labour_court_generic` + `esi_court_generic` scaffolds; **remaining:** ESI/labour court relationship wiring
- [x] §5.3 Defence (AFT regional benches, court martial generic) — Batch 3 + prior AFT bench pass
- [x] §5.4 Regulators (FSSAI, AERA, ICADR, PCI, SEC generic, Insurance Ombudsman, PFRDA) — Batch 3 + backbone
- [x] §5.5 IP (CGPDTM, TMR, COMPAT historical; `ipab` abolished in-place) — Batch 3
- [ ] Tag `v1.5.0`

### v1.x audit commands (run before every tag)

```bash
cd jem
python3 scripts/validate.py
python3 scripts/derive.py
python3 scripts/build.py
python3 -c "
import yaml; from pathlib import Path
ids=set()
for f in Path('data/entities').rglob('*.yaml'):
    d=yaml.safe_load(f.read_text()) or {}
    if d.get('id'): ids.add(d['id'])
for x in ['nclat','iiac','hc_madras_bench_madurai']:
    print(x, 'OK' if x in ids else 'MISS')
js=cv=tot=0
for f in Path('data/entities').rglob('*.yaml'):
    d=yaml.safe_load(f.read_text()) or {}
    if not d.get('id'): continue
    tot+=1
    j=d.get('judge_strength') or {}
    if j.get('allotted') is not None or j.get('appointed') is not None: js+=1
    if (d.get('case_volume') or {}).get('pending_cases') is not None: cv+=1
print(f'entities={tot} judge_strength={js}/{tot} pending_cases={cv}/{tot}')
"
python3 scripts/validate_graph_refs.py --strict   # orphan count
```

---

## PART 1 — DOWNLOAD & FIRST DEPLOY (do today, April 25)

### 1.1 Download from Claude

Download this repository (or the packaged output that contains the layout below).
It contains everything. Structure (this repository):

  <repo root>/
  ├── .github/workflows/validate.yml    ← CI config
  ├── README.md
  ├── MASTER_CHECKLIST.md
  ├── entity_schema.yaml
  ├── graph.json
  └── jem/                                ← app + data + scripts
      ├── README.md
      ├── .gitignore
      ├── data/
      │   ├── schema/                       ← entity_schema.yaml, relationship_schema.yaml
      │   ├── entities/                     ← all entity YAML files
      │   ├── relationships/                ← all relationship YAML files
      │   └── derived/                      ← auto-generated, do not edit
      ├── docs/
      │   ├── DATA_MODEL.md
      │   ├── CONTRIBUTING.md
      │   ├── CURSOR_PHASE1_BRIEF.md        ← Cursor task brief for MH/DL/KA
      │   └── V2_SESSION_SPEC.md            ← Paste into Claude on April 27
      ├── scripts/
      │   ├── validate.py
      │   ├── derive.py
      │   ├── build.py
      │   └── requirements.txt
      └── web/
          ├── index.html
          ├── public/graph.json             ← symlink → repo-root graph.json
          ├── src/                          ← main.js, state.js, renderer.js, panel.js, timeline.js
          └── styles/main.css

- [x] Repository present in workspace *(app in `jem/`, CI at repo root)*
- [x] ~~Unzip / confirm all 49 files present~~ — **not required for v1** (corpus is 494+ YAML files; April-25 zip inventory is archival only)

---

### 1.2 Deploy v1 to production → use release runbook

**Prepared:** [`jem/docs/V1_RELEASE_RUNBOOK.md`](jem/docs/V1_RELEASE_RUNBOOK.md) §1–2 · `./jem/scripts/deploy_prep.sh`

- [ ] Complete runbook §1 (deploy) and §2 (smoke tests) — checkboxes tracked there and in §3.4 below

---

### 1.3 Push to GitHub → **moved to v2 (Part 4.3)**

GitHub remote, push, and CI verification are **v2 operator tasks** so v1.0.0 can tag from local/deploy QA without blocking on remote setup.

---

## PART 2 — CURSOR SETUP (from April 28)

### 2.1 Open project in Cursor

```bash
# In Cursor terminal:
cd jem
pip install -r scripts/requirements.txt
python scripts/validate.py     # should show: 0 errors, 0 warnings
python scripts/build.py        # should show: 147 entities, 818 KB
```

- [x] Open jem/ as Cursor project
- [x] Run validate.py — confirm clean *(May 19 2026: 0 errors, 494+ entity files)*
- [x] ~~Read docs/CURSOR_PHASE1_BRIEF.md~~ — **not required** (MH/DL/KA packs already in `_generated/`; restore file only if re-authoring from scratch)
- [x] Read docs/DATA_MODEL.md sections on structural_gap and case_volume *(also `V2_DATA_MODEL.md` for judge_strength / HC benches)*

### 2.2 Session workflow (bookmark)

- [x] **Bookmark:** [`jem/docs/SESSION_WORKFLOW.md`](jem/docs/SESSION_WORKFLOW.md) — validate → derive → build, **graph/bundle overwrite risks**, `build_safe.sh`, deploy pointer

Shortcut: `cd jem && ./scripts/safe_pipeline.sh` (does not run bundle generator)

---

## PART 3 — V1 COMPLETION: 4 STATES + 1 UT

### STATUS (Jun 15 2026): **All 35 state/UT folders** have core packs in `jem/data/entities/_generated/states/` with per-state relationship packs. Phase-1 states (MH, DL, KA, TN, PY) remain deepest; TN uses full 38-district lattice. Rebuild: `python3 jem/scripts/build.py` → **1,103 entities**.

---

### 3.1 Maharashtra (MH) — ~51 entity YAML files ✅

**Paths:** `jem/data/entities/_generated/states/mh/*.yaml` · `jem/data/relationships/mh_relationships.yaml`

#### 3.1.1 State-level regulators
- [x] `merc` — enriched; NJDG `case_volume` merged
- [x] `mh_rera`
- [x] `mh_bar_council`

#### 3.1.2 Oversight / training / ADR
- [x] `mh_lokayukta`
- [x] `mh_sja`
- [x] `mh_slsa` — NJDG merged

#### 3.1.3 Prosecution
- [x] `mh_advocate_general`

#### 3.1.4 Consumer
- [x] `mh_state_cdrc`
- [x] `mh_cdrc_mumbai` · `mh_cdrc_pune` · `mh_cdrc_nagpur` · `mh_cdrc_aurangabad`

#### 3.1.5 City civil courts
- [x] `city_civil_court_mumbai` — NJDG rollup merged *(verify ~900k pending against Bombay HC annual report)*

#### 3.1.6 District courts
- [x] Priority 10 named districts (mumbai_city, thane, pune, nashik, aurangabad, nagpur, solapur, kolhapur, nanded, amravati)
- [x] `mh_district_courts_generic` — collapsed-lattice proxy + NJDG state rollup
- [x] **+26 bootstrap districts** (`mh_district_court_jalgaon`, …) — structural YAML + HC edges; **per-district NJDG → v1.3** (Part 3.5.2)

#### 3.1.7 Special courts
- [x] `mh_special_courts`

#### 3.1.8 MH relationships
- [x] Appellate / supervisory / ADR edges in `mh_relationships.yaml`

#### 3.1.9 MH clog data (NJDG snapshot Dec 2024)
- [x] State rollup + named courts merged via `merge_njdg_snapshot.py`
- [ ] **Per-district dashboard pull** for 26 bootstrap districts — **v1.3** (Part 3.5.2)

- [x] MH validate + derive + build passes 0 errors
- [x] Committed on main
- [ ] Deploy — v1 release runbook §1–2

---

### 3.2 Delhi (DL) — ~22 entity YAML files ✅

**Paths:** `jem/data/entities/_generated/states/dl/*.yaml` · `jem/data/relationships/dl_relationships.yaml`

#### 3.2.1 Delhi-specific constitutional entity
- [x] `dl_lieutenant_governor` — NJDG merged; gap notes for LG/MHA tension remain valid

#### 3.2.2 Regulators
- [x] `derc` — enriched statutory detail + `case_volume` (verify vs DERC annual reports)
- [x] `dl_rera`

#### 3.2.3 Oversight / training / ADR
- [x] `dl_lokayukta` · `dl_sja` · `dl_slsa`

#### 3.2.4 Prosecution
- [x] `dl_advocate_general`

#### 3.2.5 Consumer
- [x] `dl_state_cdrc` + zone forums (`dl_cdrc_north`, `south`, `east`, `west`, `central`, `northwest`)

#### 3.2.6 District courts
- [x] Six named complexes (saket, tis_hazari, rohini, patiala_house, dwarka, karkardooma) — NJDG merged
- [x] `dl_district_courts_generic` — collapsed proxy + NJDG rollup

#### 3.2.7 Special courts
- [x] `dl_special_courts`

#### 3.2.8 DL relationships
- [x] `dl_relationships.yaml` (appellate, supervisory, ADR)

- [x] DL validate + derive + build passes 0 errors
- [x] Committed on main
- [ ] Deploy — v1 release runbook §1–2

---

### 3.3 Karnataka (KA) — ~43 entity YAML files ✅

**Paths:** `jem/data/entities/_generated/states/ka/*.yaml` · `jem/data/relationships/ka_relationships.yaml`

#### 3.3.1–3.3.8 (summary)
- [x] `kerc` (enriched) · `ka_rera` · `ka_lokayukta` · `ka_sja` · `ka_slsa` · `ka_advocate_general`
- [x] `ka_state_cdrc` · `ka_cdrc_bengaluru` · `city_civil_court_bangalore` (NJDG merged)
- [x] Priority 10 districts + `ka_district_courts_generic`
- [x] **+19 bootstrap districts** — structural only; **per-district NJDG → v1.3** (Part 3.5.2)
- [x] `ka_special_courts` · `ka_relationships.yaml`

- [x] KA validate + derive + build passes 0 errors
- [x] Committed on main
- [ ] Deploy — v1 release runbook §1–2

---

### 3.3a Tamil Nadu (TN) + Puducherry (PY) — ✅

**TN paths:** `jem/data/entities/_generated/states/tn/` (49 YAML) · `jem/data/relationships/tn_relationships.yaml`

- [x] Full **38-district lattice** (`tn_district_court_*`) with bench-aware appellate edges (Madras / Madurai)
- [x] **`tn_district_courts_generic`** — consolidated collapsed view (3.2M pending state rollup from NJDG)
- [x] Map collapse/expand via `jem/web/src/districtAggregates.js` + `PRINCIPAL_HC_BY_STATE_CODE.tn`
- [x] TN regulators, SLSA, SJA, CDRC, RERA, special courts — NJDG merged where in snapshot
- [ ] **37/38 districts** without per-district `pending_cases` in YAML — **v1.3** (only Chennai + generic in Dec 2024 snapshot)

**PY:** `jem/data/entities/_generated/states/py/` (6 entities) · `py_relationships.yaml` — ✅ in graph

---

### 3.6 Post–v1.0.0 data releases → **VERSION ROADMAP** (v1.1–v1.5)

> Supersedes the May 20 “Part 3.6 next build” scratch list. All deferred coverage-gap items are versioned there:
>
> | Was Part 3.6 | Now |
> |--------------|-----|
> | 3.6.1 Madras bench / config sync | **v1.1** |
> | 3.6.2 UP/WB/RJ bench routing | **v1.1** |
> | 3.6.3 `judge_strength` + `case_volume` | **v1.2** |
> | Part 3.5.2 per-district NJDG | **v1.3** |
> | §5 non-TN state lattices | **v1.4** |
> | Part 5 gap registry | **v1.5** |

---

### 3.4 V1 Completion Checklist

- [x] Run full validate: `python3 jem/scripts/validate.py` — **0 errors** (May 20 2026)
- [x] Run full build: `python3 jem/scripts/build.py` — **1,103 entities**, **~5.63 MB** `graph.json` (Jun 15)
- [x] State packs — all 35 state/UT folders in repo and graph (Jun 15)
- [x] NJDG snapshot merge applied (139 entities) — Part 3.5
- [ ] **§1 Deploy** — [`V1_RELEASE_RUNBOOK.md`](jem/docs/V1_RELEASE_RUNBOOK.md) + `deploy_prep.sh`
- [ ] **§2 Smoke tests** — same runbook (production URL)
- [ ] **§3 Tag** — `git tag -a v1.0.0` locally after smoke pass; `git push` / remote → v2 (Part 4.3)

---

## PART 3.5 — NJDG DATA (snapshot merge + parked district work)

### 3.5.1 Snapshot merge — ✅ DONE (May 19 2026)

| Item | Status |
|------|--------|
| Source snapshot | local NJDG `graph.json` export (216 entities with `_detail.case_volume`; path not in repo) |
| Tool | `jem/scripts/merge_njdg_snapshot.py` |
| Plan | [`jem/docs/NJDG_MERGE_PLAN.md`](jem/docs/NJDG_MERGE_PLAN.md) — **139** mergeable rows applied |
| Re-apply after YAML changes | `python3 jem/scripts/merge_njdg_snapshot.py --snapshot /path/to/snapshot/graph.json --apply` |
| Rebuild graph | `python3 jem/scripts/build.py` |
| ID remaps in script | `mh_district_court_mumbai` → `mh_district_court_mumbai_city`; `hc_guwahati` → `hc_gauhati` |

**Merged coverage:** all 24 mergeable HCs, DL/MH/KA/TN/PY state entities in plan, backbone tribunals/regulators, hand-curated SC/CBI/ACI/eCommittee, etc.

### 3.5.2 PARKED — District-level NJDG exports → **v1.3** ⏸️

> **Do not start until district exports exist.** State/HC rollup merge shipped in **v1.0.0**; per-district work is **v1.3**.

| Scope | Count | Current data | When un-parked |
|-------|-------|----------------|----------------|
| **TN per-district courts** | 38 nodes | 1 with `pending_cases` (Chennai); 37 placeholders | New NJDG district export or TN e-Courts district dashboard scrape |
| **TN collapsed generic** | 1 | ✅ `tn_district_courts_generic` (state rollup) | Refresh when new state snapshot available |
| **MH bootstrap districts** | 26 | `avg_disposal_days` placeholder only | Per-district NJDG for each `mh_district_court_*` slug |
| **KA bootstrap districts** | 19 | same | same |
| **Other states (v1 bundle)** | varies | principal + `*_district_courts_generic` often have rollup only | Phase 2 / community passes |

**Acceptance criteria (when un-parked):**

- [ ] Each targeted `*_district_court_*` YAML has `case_volume.pending_cases`, `filed_last_year`, `disposed_last_year` (or explicit null + `data_quality_notes`)
- [ ] `data_quality_notes` cites NJDG district URL and `data_as_of`
- [ ] Re-run `merge_njdg_snapshot.py --apply` **only if** new snapshot includes per-district `_detail.case_volume`
- [ ] `validate.py` → `build.py` → spot-check expanded TN lattice on map

**Tracking command (audit):**

```bash
python3 -c "
import yaml
from pathlib import Path
tn = Path('jem/data/entities/_generated/states/tn')
dist = list(tn.glob('tn_district_court_*.yaml'))
with_p = sum(1 for f in dist if (yaml.safe_load(f.read_text()).get('case_volume') or {}).get('pending_cases'))
print(f'TN districts with pending_cases: {with_p}/{len(dist)}')
"
```

---

## PART 4 — V2 BUILD (April 27 Claude session)

**Status (May 19 2026):** **Partial.** Data model + map UX advances below; full Canvas/Sankey/journey spec still outstanding.

**Done in repo (v2 partial):**

- [x] `jem/docs/V2_DATA_MODEL.md` — HC benches, `judge_strength`, district lattice
- [x] HC bench YAML under `jem/data/entities/_generated/high_courts/benches/`
- [x] `jem/web/src/districtAggregates.js` — collapse/expand per state; TN generic proxy
- [x] `jem/web/src/nodeShapes.js` — crescent bench shapes
- [x] `generate_v1_states_bundle.py`, `hc_benches_config.py`, `bootstrap_tn_district_lattice.py`
- [x] NJDG **static** snapshot merge (not live API) — Part 3.5

### 4.1 Preparation (do before next v2 session)

- [ ] Read docs/V2_SESSION_SPEC.md fully *(restore to `jem/docs/` if missing)*
- [ ] Open fresh Claude session for remaining v2 items
- [ ] Do NOT mix research/essay writing in build sessions

### 4.2 V2 feature checklist

#### Priority 1 — Canvas renderer
- [ ] `web/src/renderer.js` rewritten — L1/L2 on Canvas, L0 stays SVG *(still SVG — acceptable at ~500 entities)*
- [ ] D3 quadtree hit detection implemented
- [ ] Canvas arrowheads implemented
- [ ] Gap asterisk `*` renders on Canvas
- [ ] Circularity icon `⟳` renders on Canvas
- [ ] IR heat ring renders on Canvas
- [ ] Role layer rectangles render on Canvas
- [ ] Performance test: smooth pan/zoom at 142 entities
- [ ] Performance test: smooth at 500 entities (test with duplicated data if needed)

#### Priority 2 — NJDG live fetch
- [x] **Static snapshot path** — `merge_njdg_snapshot.py` + local NJDG snapshot *(May 2026)*
- [ ] **District-level exports** — **v1.3** (Part 3.5.2)
- [ ] `scripts/fetch_njdg.py` created (live API)
- [ ] Rate limiting (1 req / 2 seconds) implemented
- [ ] Cache layer (`data/cache/njdg/`) implemented
- [ ] Test: fetch live data for hc_delhi, hc_madras — confirm fields update
- [ ] build.py `--live` flag added
- [ ] Staleness indicator in graph.json meta
- [ ] `⚠ Data may be stale` UI indicator when snapshot > 90 days old

#### Priority 3 — Major litigant nodes
- [ ] entity_schema.yaml: `MajorLitigant` type, `diamond` node_shape, `litigant_tier` field
- [ ] relationship_schema.yaml: `FrequentLitigantIn` type, `major_litigant` category
- [ ] New entities: `union_of_india`, `state_govt_tn`, `state_govt_mh`, `state_govt_dl`, `state_govt_ka`, `state_govt_generic`
- [ ] Diamond rendering on Canvas
- [ ] Major Litigants lens toggle (gold, off by default)
- [ ] FrequentLitigantIn relationships from DoJ Annual Report data

#### Priority 4 — Case flow Sankey
- [ ] `web/src/sankey.js` created
- [ ] build.py: `sankey_data` object added to graph.json
- [ ] Slide-up Sankey panel in index.html
- [ ] Case Flow button in toolbar
- [ ] Sankey nodes: District → HC → SC (+ major tribunal tiers)
- [ ] Arc widths proportional to case volume

#### Priority 5 — Appointment delay pipeline
- [ ] derive.py: `appointment_health_score` formula implemented
- [ ] schema: `avg_days_vacancy_unfilled`, `vacancy_data_as_of` fields added
- [ ] data/derived/appointment_health.yaml output
- [ ] Appointment Health overlay toggle in renderer
- [ ] HC vacancy duration data from DoJ quarterly report populated for 5 HCs

#### Priority 6 — Litigant journey mode
- [ ] `web/src/journey.js` created
- [ ] Journey mode UI scaffold — breadcrumb trail, dimming, path highlight
- [ ] Journey button in toolbar
- [ ] `filing_cost_range`, `appeal_cost_range` added to schema (empty — community task)
- [ ] avg_disposal_days used as wait time proxy

#### V2 validation & deploy
- [ ] `python scripts/validate.py --strict` — 0 errors
- [ ] `python scripts/build.py`
- [ ] Graph.json size check: target <1.5 MB
- [ ] Canvas performance: open devtools, confirm <16ms render at current entity count
- [ ] Sankey displays correctly
- [ ] Journey mode breadcrumb works for District → HC → SC path
- [ ] Deploy per runbook (`JEM_REMOTE` on your static host — see `V1_RELEASE_RUNBOOK.md`)
- [ ] Tag: `git tag v2.0.0 && git push --tags`

### 4.3 GitHub & CI (moved from v1 Part 1.3)

Complete when setting up **v2** remote workflow (not required to cut local `v1.0.0` tag after production smoke tests).

- [ ] Create GitHub repo (public, CC0 data / MIT code) or attach `origin`
- [ ] Push `main` and tags: `git push -u origin main && git push origin v1.0.0`
- [ ] Confirm `.github/workflows/validate.yml` runs on PRs touching `jem/data/**` or `jem/scripts/**`
- [ ] Optional v2 CI: add `build.py` dry-run or `deploy_prep.sh` on `main` push
- [ ] Add topics: `india`, `judiciary`, `open-data`, `d3js`, `legal-tech`
- [ ] Description: "Open-source structural map of the Indian judicial ecosystem"

Existing workflow (PR only): validate `--strict` + `derive.py` in `jem/` working directory.

---

## PART 5 — GAPS REGISTRY: ALL MISSING ENTITIES

Complete task list drawn from README.md Gap Registry Section B.
Each item: entity_id to create, source URL, which Cursor session.

### 5.1 Tax / Revenue tribunal stack (high priority)

- [x] `cestat_chennai` — CESTAT Chennai bench (covers TN, KA, KE, PY, AP, TS, AN) — Jun 2026
- [x] `cestat_mumbai` — covers MH, GA
- [x] `cestat_kolkata`
- [x] `cestat_bangalore`
- [x] `cestat_ahmedabad` — covers GJ, RJ
- [x] `cestat_hyderabad` — covers TS, AP
- [x] `cestat_allahabad` — covers UP, UK
- [x] `cestat_chandigarh` — covers PB, HR, HP, JK, LA, CH
- [x] `gstat_bench_generic` — 31 planned benches, Not_Constituted scaffold — Jun 2026
- [x] `aar_income_tax` — Authority for Advance Rulings (IT) — Jun 2026
- [x] `caar_customs` — Customs Authority for Advance Rulings (reconstituted 2021)

**Tax adjudication chain (pre-ITAT):**
- [x] `cit_appeals_generic` — Commissioner of Income Tax (Appeals). Pre-ITAT appellate body. — Jun 2026
- [x] `jcit_appeals_generic` — Joint Commissioner of Income Tax (Appeals) — Jun 2026; wired → ITAT
- [x] `ao_income_tax_generic` — Assessing Officer (Income Tax). Source of all ITAT chain.

**State sales tax / VAT:**
- [x] `state_vat_tribunal_generic` — generic scaffold, ~28 states — Jun 2026 (Not_Constituted / legacy)

### 5.2 Labour / Employment (medium priority)

- [x] `cgit_delhi` — CGIT Delhi bench (principal + largest) — Jun 2026; **wired** (BenchOf + MoLE funding)
- [x] `cgit_mumbai` — CGIT Mumbai bench — **wired**
- [x] `cgit_kolkata` — **wired**
- [x] `cgit_chennai` — CGIT Chennai bench — **wired**
- [x] `cgit_chandigarh_1` · `cgit_chandigarh_2` — CGIT Chandigarh benches — **wired**
- [x] `epfo` — Employees' Provident Fund Organisation (quasi-judicial enforcement) — Jun 2026; MoLE funding wired
- [x] `epfat` — EPF Appellate Tribunal — Jun 2026; MoLE funding wired
- [x] `esi_court_generic` — Employees' State Insurance Court (generic scaffold) — Jun 2026
  Source: esic.gov.in | Statutory basis: ESI Act 1948, Section 75
- [x] `state_labour_court_generic` — state labour courts (generic scaffold) — Jun 2026 (M-T4)
  ~200 bodies nationally. Industrial Disputes Act Section 7.

### 5.3 Defence (medium priority)

- [x] `aft_chandigarh` — covers PB, HR, HP, JK, LA
- [x] `aft_lucknow` — covers UP, UK
- [x] `aft_kolkata` — covers WB, BR, JH, OD, NE states
- [x] `aft_guwahati` — covers NE states
- [x] `aft_chennai` — covers TN, KE, PY, AP, TS
- [x] `aft_kochi` — covers KE, Lakshadweep
- [x] `aft_jaipur` — covers RJ, GJ
- [x] `aft_mumbai` — covers MH, GA
- [x] `aft_hyderabad` — covers TS, AP
- [x] `court_martial_generic` — Army/Navy/Air Force court martial (generic) — Batch 3
  Source: Army Act 1950, Navy Act 1957, Air Force Act 1950
  Gap: No external appeal until AFT. Accused has no right to civilian counsel in summary CM.

### 5.4 Specialised regulators (medium priority)

- [x] `pfrda` — Pension Fund Regulatory and Development Authority (backbone entity)
- [x] `fssai` — Food Safety and Standards Authority of India — Batch 3
  Source: fssai.gov.in | Quasi-judicial functions, appellate → HC
- [x] `aera` — Airport Economic Regulatory Authority — Batch 3
  Source: aera.gov.in | Appellate → TDSAT (confirmed by SC)
- [x] `icadr` — International Centre for ADR, Delhi — Batch 3
  Source: icadr.in | GoI-funded, domestic + international arbitration
- [x] `press_council_india` — Press Council of India — Batch 3
  Source: presscouncil.nic.in | Quasi-judicial media complaints, no enforcement
- [x] `state_election_commission_generic` — 28 state SECs — Batch 3
  Source: varies by state | Distinct from ECI. Electoral dispute adjudication.
- [x] `insurance_ombudsman_generic` — Insurance Ombudsman (17 centres; Batch 3)
  Source: irdai.gov.in | Appeals from Insurance Ombudsman above Rs 50L

### 5.5 Intellectual Property (lower priority)

- [x] `ipab` — IPAB (IP Appellate Board) — Abolished 2021 (in-place upgrade, not ipab_abolished)
  Type: CentralTribunal, operational_status: Abolished, abolished_year: 2021
  Gap: Abolition without adequate transition — HC hearing IP appeals without specialist benches
  Source: The Tribunal Reforms Act 2021
- [x] `patent_controller` — Office of the Controller General of Patents, Designs and Trade Marks — Batch 3
  Source: ipindia.gov.in | created_year 1912 (office); Patents Act 1970 in statutory_basis
  Gap: Backlog in post-grant opposition proceedings
- [x] `trade_marks_registry` — Trade Marks Registry (adjudicatory on opposition, cancellation) — Batch 3
  created_year 1940 (registry); Trade Marks Act 1999 in statutory_basis
- [x] `compat` — Competition Appellate Tribunal (abolished 2017; jurisdiction → NCLAT) — Batch 3

### 5.6 State-level — all states + UTs (core packs ✅ Jun 15; deep lattices → v1.4)

Priority order based on case volume and structural significance:

**Batch A — Community (high volume states):**
- [x] Uttar Pradesh (UP) — **core pack** (22 entities, 9 named districts; full lattice → v1.4)
- [x] Andhra Pradesh (AP) — **core pack** (23 entities, 9 named districts)
- [x] Telangana (TS) — **core pack** (23 entities, 9 named districts)
- [x] Rajasthan (RJ) — **core pack** (20 entities, 7 named districts)
- [x] Madhya Pradesh (MP) — **core pack** (23 entities, 10 named districts)
- [x] Bihar (BR) — **core pack** (22 entities, 9 named districts; Patna HC vacancy documented)

**Batch B — Community (medium volume):**
- [x] West Bengal (WB) — **core pack** (23 entities, 7 named districts)
- [x] Gujarat (GJ) — **core pack** (22 entities, 9 named districts)
- [x] Odisha (OD) — **core pack** (23 entities, 9 named districts)
- [x] Kerala (KL) — **core pack** (23 entities, 9 named districts)
- [x] Punjab (PB) — **core pack** (22 entities, 9 named districts)
- [x] Haryana (HR) — **core pack** (21 entities, 9 named districts)

**Batch C — Community (smaller states):**
- [x] Jharkhand (JH) — **core pack** (19 entities, 7 named districts)
- [x] Chhattisgarh (CG) — **core pack** (19 entities, 7 named districts)
- [x] Assam (AS) — **core pack** (19 entities, 7 named districts)
- [x] Himachal Pradesh (HP) — **core pack** (20 entities, 7 named districts)
- [x] Uttarakhand (UK) — **core pack** (19 entities, 7 named districts)

**Batch D — Community (NE states + small UTs):**
- [x] Manipur (MN), Meghalaya (ML), Tripura (TR), Nagaland (NL), Mizoram (MZ), Arunachal Pradesh (AR), Sikkim (SK) — **core packs** (17–18 entities each)
- [x] Goa (GA) — **core pack** (19 entities, 7 named districts)
- [x] UTs: CH (13), AN (14), LD (13); DN/DD via PY pack
- [x] Jammu & Kashmir (JK) + Ladakh (LA) — **core packs** (19 + 14 entities)

**Core pack template (done for all states Jun 15):**
- [x] `{state}_serc` / SERC reference
- [x] `{state}_rera`
- [x] `{state}_bar_council`
- [x] `{state}_sja`
- [x] `{state}_slsa`
- [x] `{state}_lokayukta` (or Not_Constituted gap)
- [x] `{state}_advocate_general`
- [x] `{state}_state_cdrc` + 2–10 district CDRCs
- [x] `{state}_district_courts_generic` + 2–10 named district courts
- [x] `{state}_special_courts`
- [ ] Board of Revenue variation in `board_of_revenue_generic.state_data` — **pending**
- [ ] State Industrial Tribunal variation in `state_industrial_tribunal_generic.state_data` — **pending**
- [ ] **Deep lattice expansion** (38-district TN-style) — **v1.4**

### 5.7 Data quality upgrades (ongoing)

These entities are in the repo but at partial/unverified quality. Any contributor can upgrade:

- [ ] **District-level NJDG pendency** — **v1.3** (Part 3.5.2); do not duplicate state rollup into every district YAML
- [ ] All 10 northeast HCs: upgrade from `unverified` to `partial`
  Task: verify sanctioned/working strength from HC websites or DoJ data
- [ ] `state_bar_council_generic`: add enrollment count, working strength
- [ ] `district_cdrc_generic`: add per-district pendency from consumerhelpline.gov.in
- [ ] `rera_generic`: verify appellate tribunal operational status per state
- [ ] `serc_generic`: verify APTEL appeal statistics per SERC
- [ ] `gram_nyayalaya_generic`: update state-wise operational count (2025 data)
- [ ] All entities with `scores_validated: false`: domain reviewer to check derive.py output
  Command: `python3 jem/scripts/derive.py --explain {entity_id}` for each

---

## PART 6 — V3 PLANNING (post-V2, timing TBD)

Not a Cursor or Claude session task — plan only.

### 6.1 Performance infrastructure

- [ ] Chunk graph.json into cluster tiles (required at 1500+ entities)
  Plan: `graph_meta.json` (50KB, clusters + impact) + `graph_{cluster}.json` per cluster
  Loader: main.js fetches meta first, then fetches cluster chunks on zoom
- [ ] Service worker for offline caching of pre-built tiles
- [ ] CDN for graph.json delivery (CloudFlare free tier sufficient)

### 6.2 Data infrastructure

- [x] **One-time NJDG snapshot ingest** — local snapshot → entity YAML via `merge_njdg_snapshot.py` (May 2026)
- [ ] **District-level NJDG ingest pipeline** — **v1.3** until exports exist (Part 3.5.2)
- [ ] Scheduled NJDG fetch: cron on production host, weekly *(requires `fetch_njdg.py`)*
  `0 3 * * 0 cd /path/to/repo && python3 jem/scripts/fetch_njdg.py --all-hcs && python3 jem/scripts/derive.py && python3 jem/scripts/build.py && rsync …`
- [ ] Historical NJDG snapshots: store `data/cache/njdg/` in git-annex or S3
  (enables year-over-year clog trend in time scroller)
- [ ] Community contribution pipeline: GitHub Actions auto-builds on merge to main
  Requires: GitHub Actions deploy step (e.g. SSH/rsync to your host) or webhook — credentials in GitHub Secrets, not in repo

### 6.3 Remaining feature deferrals

- [ ] **Per-district NJDG metrics** — **v1.3** (Part 3.5.2)
- [ ] Year-over-year clog trend (needs 3+ NJDG snapshots)
- [ ] Time scroller annotation mode
- [ ] Funding flow Sankey (separate from case flow)
- [x] AFT/CESTAT individual bench entities (11 AFT + 8 CESTAT) — Jun 2026
- [ ] State Board of Revenue individual entities (28)
- [ ] Full appointment delay pipeline (data from DoJ quarterly reports)
- [x] COMPAT (abolished 2017) as historical entity — Batch 3
- [x] IPAB (abolished 2021) as historical entity — Batch 3 in-place upgrade
- [ ] Gram Nyayalaya per-state operational entities (Maharashtra ~450, others near zero)

### 6.4 Separate project candidates (from README)

These need their own repos. JEM's schema is a usable starting point.

- [ ] Revenue administration map (Patwari → Tehsildar → DM → Board of Revenue)
- [ ] Tax dispute chain map (AO → CIT(A) → ITAT → HC → SC)
- [ ] Military justice map (Summary CM → FGCM → AFT → SC)
- [ ] District Legal Services Authority map (650 DLSAs)
- [ ] State Vigilance / Anti-Corruption Bureau map

---

## PART 7 — MAINTENANCE SCHEDULE (recurring)

- [ ] Weekly: check NJDG for significant pendency changes (run fetch_njdg.py for HCs)
- [ ] Monthly: check DoJ quarterly vacancy report — update HC working_strength fields
- [ ] Quarterly: check SC Annual Report for SC pendency / disposal data
- [ ] Annually: update budget_figure_crore from Union Budget for ministry entities
- [ ] On SC judgment: add to amendment_history if structural change (e.g., new collegium ruling)
- [ ] On new legislation: add new entity or update operational_status (e.g., if GSTAT constituted)
- [ ] On HC appointment: update working_strength, rerun derive.py, check IR score change

---

## PART 8 — DELEGATION PLAYBOOK (Cursor vs Claude)

Use this when planning the next sessions. **Rule of thumb:** Cursor for volume and repo execution; Claude for domain judgment and architecture you cannot template.

### Strengths & weaknesses

| Dimension | **Cursor** (Agent + terminal) | **Claude** (co-maintainer / research) |
|-----------|-------------------------------|----------------------------------------|
| Bulk YAML from templates | ✅ Fast — 10–50 entities/session | ❌ Token-heavy; drifts on repetition |
| `validate.py` / `derive.py` / `build.py` loop | ✅ Native terminal + fix-on-fail | ⚠️ Possible but awkward |
| Generator scripts (`generate_v1_states_bundle.py`, lattice bootstrap) | ✅ Edit + run + diff in one session | ⚠️ Better for design review than execution |
| Relationship wiring (maintainer) | ✅ Mechanical edges from config tables | ✅ Better when appellate routing is ambiguous |
| Schema / `derive.py` formula changes | ⚠️ Can do, but easy to miss knock-on effects | ✅ Strong — read full `entity_schema.yaml` + score logic |
| Independence-risk / structural-gap reasoning | ⚠️ Shallow without sources | ✅ Strong — statute + collegium context |
| V2 architecture (Canvas, Sankey, `fetch_njdg.py`) | ✅ Implementation once spec exists | ✅ Strong — system design + API shape |
| Primary-source research (gazettes, DoJ reports) | ⚠️ Needs URLs supplied in prompt | ✅ Strong — synthesize across sources |
| GitHub issues / contributor YAML triage | ✅ Validate + merge | ⚠️ Overkill |
| Essay / Pendency Lab / external writing | ❌ Wrong tool | ✅ Keep separate — no code context |

### Recommended next sessions (in order)

| # | Session | Tool | Est. output |
|---|---------|------|-------------|
| 1 | **Ship v1.0.0** — `deploy_prep.sh` → rsync → smoke → `git tag v1.0.0` | Operator | Live map at current 1,103 entities |
| 2 | **Close v1.1** — KA Dharwad audit + `board_of_revenue_generic` / `state_industrial_tribunal_generic` `state_data` | Cursor | Tag `v1.1.0` |
| 3 | **v1.2 numerics batch A** — HC + SC `judge_strength` from DoJ vacancy report | Cursor | +26 entities with numerics |
| 4 | **v1.2 numerics batch B** — state rollup `case_volume` refresh if new NJDG snapshot available | Cursor | +50–100 entities |
| 5 | **v1.4 lattice — UP** — bootstrap full district lattice from `bootstrap_tn_district_lattice.py` pattern | Cursor | +60–70 entities |
| 6 | **v1.5 labour wiring** — ESI + state labour court edges (maintainer) | Claude brief → Cursor apply | Relationship pack |
| 7 | **v2 spec** — Canvas renderer + `fetch_njdg.py` API contract | Claude | `V2_SESSION_SPEC.md` refresh |
| 8 | **v2 impl** — Canvas hit-test + live NJDG stub | Cursor | Part 4.2 partial |

### Copy-paste prompts

**Cursor — P1 KA Dharwad close-out**
```
Audit KA district→bench routing: compare jem/scripts/hc_benches_config.py KA_DISTRICT_TO_BENCH
against jem/data/relationships/ka_relationships.yaml AppealableTo edges for all ka_district_court_*.
Fix any missing edges. Run validate.py → derive.py → build.py. Do not add relationships for other states.
```

**Cursor — P2 judge_strength HC pass**
```
Using DoJ judicial vacancy report (https://doj.gov.in/report-and-committees/judicial-vacancy-reports),
populate judge_strength (allotted, appointed, data_as_of, source in data_quality_notes) on all
ConstitutionalCourt and HighCourtBench entities missing numerics. Template: existing hc_delhi.yaml block.
Run safe_pipeline.sh. Target: all 26 constitutional/HC nodes.
```

**Cursor — P3 UP district lattice**
```
Bootstrap UP full district lattice mirroring TN: use bootstrap_tn_district_lattice.py pattern for state code up.
Create up_district_court_* YAML for all UP districts with AppealableTo → hc_allahabad or hc_allahabad_bench_lucknow
per hc_benches_config.py. Wire edges in up_relationships.yaml only. validate → derive → build.
```

**Claude — v1.5 labour relationship design**
```
JEM co-maintainer session. Design relationship pack for esi_court_generic and state_labour_court_generic:
MoLE funding, appellate to HC, state-level instantiation pattern. Output edge list (source, target, type, statutory_basis)
for maintainer to paste into labour_tribunal_relationships.yaml. No YAML files — design only.
Read jem/data/entities/_generated/backbone/esi_court_generic.yaml and C20 entries in ENTITY_BUILD_ROADMAP.md.
```

**Claude — v2 architecture**
```
Design refresh for jem/docs/V2_SESSION_SPEC.md: Canvas renderer migration plan for 1,100+ nodes,
fetch_njdg.py API contract (rate limit, cache path, build.py --live flag), and minimal Sankey data shape.
Constraints: vanilla JS, no bundler, graph.json ≤10 MB at 1,500 entities. No implementation — spec only.
```

**Cursor — contributor triage**
```
Validate YAML attached to GitHub issue [paste]. Run validate.py --entity on each file.
Fix schema errors only; do not upgrade data_quality to verified without primary URL per field.
Summarize: merge-ready / needs sources / reject.
```

### Parallelization (safe to run concurrently)

| Track A (Cursor) | Track B (Cursor) | Track C (Claude) |
|------------------|------------------|------------------|
| UP district lattice YAML | WB district lattice YAML | Labour wiring spec |
| `judge_strength` HC pass | `judge_strength` tribunal pass | v2 Canvas spec |
| CDRC drafts per state (no rels) | SERC source upgrades | GSTAT watch / gated entities |

**Never parallelize:** two agents editing the same `{st}_relationships.yaml` or `graph.json` build on one branch.

---

## PART 9 — TOKEN BUDGET RULES

To keep Claude sessions available for research writing:

| Work type | Tool | Claude session needed? |
|---|---|---|
| YAML data entry (district courts, SERCs, RERAx34) | Cursor Pro | No |
| Running validate + derive + build | Cursor terminal | No |
| Schema changes (new fields, new enum values) | Claude | Yes — brief session |
| New derived metric formula design | Claude | Yes |
| Gap analysis + independence risk reasoning | Claude | Yes |
| Blog / essay / research paper writing | Claude | Yes — separate session, no code context |
| V2 build (Canvas, NJDG API, Sankey) | Claude | Yes — April 27 full day |
| Debugging validate.py errors in Cursor | Cursor AI | No |
| Adding amendment_history entries (BNS/BNSS) | Cursor | No — mechanical |
| Verifying data quality upgrades (partial → complete) | Cursor + primary sources | No |

Rule: If a task requires domain reasoning about Indian judicial structure or new code architecture, use Claude. If it requires writing more YAML from a known template, use Cursor.

---

## SUMMARY MILESTONES

| Milestone | Entities | graph.json | Date |
|---|---|---|---|
| V1 backbone | 147 | 818 KB | April 25 ✅ |
| V1 + TN + PY | ~157 | ~946 KB | May 2026 ✅ |
| V1 + MH + DL + KA + full corpus | **494** | **~1.87 MB** | **May 19 2026 ✅** |
| NJDG snapshot merge (rollup) | 494 | ~1.87 MB | May 19 2026 ✅ |
| TN generic + 38-district lattice | 494 | ~1.87 MB | May 19 2026 ✅ |
| Central tribunal + ministry batch | **506** | **~1.86 MB** | **May 20 2026 ✅** |
| Batch 3 + C04/C19/C20 partial | **592** | **~2.94 MB** | **Jun 12 2026 ✅** |
| Tribunal completion + drt_b5 (C20 MoLE wiring) | **599** | **~3.02 MB** | **Jun 12 2026 ✅** |
| Phase 1 batch (ITAT×25, UP/WB/RJ, C10/C11, M-T1–M-T6) | **668** | **~3.34 MB** | **Jun 12 2026 ✅** |
| Wave 4–5 (all state/UT core packs + rel wiring) | **1,103** | **~5.63 MB** | **Jun 15 2026 ✅** |
| **v1.0.0** tag + production deploy | **1,103** | **~5.63 MB** | **Ready — run runbook** (not yet deployed) |
| **v1.1** structural (KA verify, generic state_data) | 1,103+ | ~5.6 MB | **Nearly done** — orphans 0 ✅ |
| **v1.2** numerics (`judge_strength`, `case_volume` bulk) | 1,103+ | ~5.6 MB | **Pending** — 39/1,103 JS, 84/1,103 CV |
| **v1.3** per-district NJDG (TN/MH/KA) | 1,103+ | ~5.6 MB | TBD (blocked on exports) |
| **v1.4** deep district lattices (beyond core packs) | ~1,300+ | ~6 MB | TBD |
| **v1.5** gap registry (Part 5 remainder) | ~1,100+ | ~5.6 MB | **Mostly done** — GSTAT/DRT sub-entities gated |
| **v2.0** product (Canvas, live NJDG, Sankey, GitHub) | ~1,100+ | ~5.6 MB | TBD |
| Gap fills (tax/labour/defence) | ~1,100 | ~5.6 MB | **Mostly done** — GSTAT/DRT sub-entities gated |
| Phase 2 (core state packs) | **1,103** | ~5.63 MB | **Done** ✅ |
| Phase 3 (district resolution to ~1,500) | ~1,500+ | chunked | **In progress** — TN/MH/KA deepest |
