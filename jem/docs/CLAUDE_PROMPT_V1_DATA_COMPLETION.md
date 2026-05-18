# Claude prompt — complete tribunal, arbitration, regulator & ministry mapping (JEM)

Use this in a fresh Claude session with the JEM repo open (`jem/` as the app root). Goal: **finish structural + funding + NJDG / report fields** for entities that are still stubs, without inventing case outcomes or judge names.

## Context you must preserve

- **Canonical paths:** entity YAML under `jem/data/entities/_generated/` (do **not** move to `subordinate_courts/` unless the maintainer approves a migration).
- **Schema:** `jem/data/schema/entity_schema.yaml` + `jem/scripts/validate.py` (`EntityModel`, `CaseVolumeModel`, `SOURCE_TYPES`).
- **Workflow after edits:** from `jem/`:  
  `python3 scripts/validate.py --strict` → `python3 scripts/derive.py` → `python3 scripts/build.py`
- **Sources:** every non-obvious fact needs a primary URL + `accessed_date`. Prefer NJDG, tribunal annual report, Gazette, statute, official ministry site.

## 1) Entity typing corrections (high value)

Several **tribunal / commission** stubs are still typed `ExecutiveBody` (e.g. `jem/data/entities/_generated/backbone/aptel.yaml`, `ncdrc.yaml`). For each:

1. Pick the correct `type` from `ENTITY_TYPES` in `validate.py` (e.g. `CentralTribunal`, `ConsumerCommission`, `RegulatoryBodyQJ`, `ArbitralInstitution`).
2. Ensure `cluster` matches (`tribunals_adr`, `consumer_redressal`, `regulatory_bodies`, `arbitration`).
3. Re-run `validate.py --strict` and fix any follow-on field requirements.

## 2) Funding → ministry / department (`funding.ministry_responsible`)

Populate **`funding.ministry_responsible`** with an **existing entity id** from the graph (snake_case), e.g.:

- `ministry_law_justice` — DoJ / MoLJ interface, many tribunals, NJDG / eCourts policy.
- `ministry_of_finance` — revenue/tax tribunals, CESTAT/CBIC-related funding lines.
- `ministry_personnel_dopt` — CAT and personnel tribunals where applicable.

**Rule:** use the **statutory “parent” ministry** that tables budget for that body in Union Budget documents, not a guess from the subject matter alone. If genuinely shared, document in `data_quality_notes` and pick the primary funder.

## 3) `case_volume` for tribunals & regulators

For each central tribunal / major regulator where public statistics exist:

- Fill `case_volume` with `source_type` in  
  `NJDG_Live | NJDG_Snapshot | DoJ_Report | Tribunal_Report | HC_Report | Estimated | AnnualReport`
- Prefer **tribunal annual report** or **NJDG** where integrated; never fabricate `pending_cases`.

## 4) Arbitration & ADR institutions

Locate `cluster: arbitration` and `type: ArbitralInstitution` (or stubs). Add:

- statutory basis, funding (often non-state), complaint / ethics pathway if structural,
- relationships: `EstablishedUnder`, `AppealableTo` / `AwardChallengedIn` where the model supports it.

## 5) State packs (non-TN / non-MH/DL/KA)

States that still use **only** `*_district_courts_generic` + principal: either

- keep as **Phase-2 light pack**, or  
- expand to full district lattice **per state** using the same pattern as `jem/scripts/bootstrap_tn_district_lattice.py` + NJDG pulls.

## 6) High Court permanent benches (do not confuse with district courts)

Several HCs sit at multiple permanent benches. Model these as **`type: HighCourtBench`**, not as `SubordinateCivilCourt`.

1. **Entity pattern:** `jem/data/entities/_generated/high_courts/benches/hc_{parent}_bench_{city}.yaml`
   - `parent_hc`: consolidated HC id (e.g. `hc_madras`)
   - `seat_city`: bench location
   - Same appointment/funding/audit blocks as parent HC where shared
2. **Relationship:** `BenchOf` (bench → parent `hc_*`), category `statutory_ref`
3. **Appellate / supervision:** districts in the bench’s territorial jurisdiction should `AppealableTo` and receive `AdministrativeSupervision` from the **bench entity**, not only from `hc_*`. Reference routing in `jem/scripts/hc_benches_config.py`.
4. **Minimum bench set to verify:** Madras (Madurai, Tiruchirappalli), Bombay (Nagpur, Aurangabad, Panaji), Allahabad (Lucknow), Calcutta (Port Blair, Jalpaiguri), Rajasthan (Jaipur), Karnataka (Dharwad), Gauhati (Kohima, Aizawl, Itanagar), Punjab & Haryana (Shimla).
5. **Do not** label a district court as “Madurai Bench of HC” — that is a separate entity from `District Court — Madurai`.

## 7) Judge strength (`judge_strength` — v2.0)

For every **court** or **court-like** entity (`ConstitutionalCourt`, `HighCourtBench`, `SubordinateCivilCourt`, `CityCivilCourt`, `SpecialCourt`, tribunals/commissions with judicial members):

```yaml
judge_strength:
  data_as_of: 'YYYY-MM-DD'
  allotted: <integer>      # sanctioned posts
  appointed: <integer>     # working judges in post
  vacancy_count: <integer>  # optional
  source_type: DoJ_Report | NJDG_Snapshot | HC_Report | ...
  source_url: https://...
  notes: optional
```

- **Allotted** = sanctioned strength (posts approved). **Appointed** = working strength (judges in post). Never invent counts; use DoJ quarterly vacancy reports, HC websites, or NJDG where available.
- If unknown, leave `allotted`/`appointed` null and keep `data_quality: partial` with a note in `data_quality_notes`.
- See `jem/docs/V2_DATA_MODEL.md`.

## 8) Output expectations

- Small **atomic commits** per cluster (e.g. `data(tribunals): type + funding for APTEL/NCDRC`).
- If a fact cannot be verified, keep `data_quality: partial` and explain in `data_quality_notes`.

When done, paste the **validation summary** (0 errors) and **graph.json** `meta.entity_count` line into the PR description.

---

## Claude Desktop wrapper (copy-paste for Claude Desktop)

Use this **in the first message** in Claude Desktop, **then** attach this entire file **or** paste from **“Context you must preserve”** through **§8 Output expectations**. Desktop has **no repo** unless you attach files.

### Before you start in Desktop

1. **Give the model the repo (minimum viable):**
   - Best: attach a **zip** with `jem/` at the expected depth, **or** add the project folder if Desktop supports it.
   - Otherwise attach at least:
     - `jem/scripts/validate.py` — **`EntityModel`**, **`CaseVolumeModel`**, **`JudgeStrengthModel`**, **`ENTITY_TYPES`** (includes **`HighCourtBench`**), **`SOURCE_TYPES`**, relationship types (e.g. **`BenchOf`**).
     - `jem/docs/V2_DATA_MODEL.md` — **`judge_strength`** field semantics.
     - `jem/scripts/hc_benches_config.py` — bench list and district→bench routing (if you touch HC benches or appellate edges).
     - Schema: `jem/data/schema/entity_schema.yaml` **or** repo-root `entity_schema.yaml`.
     - **YAML references (3):**
       - Tribunal stub: `jem/data/entities/_generated/backbone/aptel.yaml`
       - Entity with **`case_volume`**: `jem/data/entities/_generated/backbone/ncdrc.yaml`
       - HC bench example: `jem/data/entities/_generated/high_courts/benches/hc_madras_bench_madurai.yaml` (`type: HighCourtBench`, **`parent_hc`**, optional **`judge_strength`**).
2. **Tell it your branch name** (you merge locally), e.g. `data/desktop-tribunal-pass`.
3. **Optional scope line** in Message 1 if you want a narrow pass, e.g. “This pass: backbone tribunals + `ministry_responsible` only; skip §6 benches and §7 judge_strength.”

### Message 1 — paste this block first

You are editing the **JEM** (Judiciary Entity Map) repository. Application root: **`jem/`** (`jem/data/`, `jem/scripts/`, `jem/docs/`).

**Hard rules**

- Output **only valid YAML** under `jem/data/entities/` (keep **`_generated/`**; do **not** move directories).
- Do **not** invent **case outcomes**, **judge names**, **`pending_cases`**, or **`judge_strength` allotted/appointed** without a **primary URL** and matching **`sources`**, **`case_volume`**, or **`judge_strength`** citation (plus **`accessed_date`** / **`data_as_of`** where applicable).
- **`HighCourtBench`** entities live under `jem/data/entities/_generated/high_courts/benches/`; set **`parent_hc`** to the consolidated HC id (e.g. `hc_madras`). Do **not** model a permanent HC bench as a district court.
- The maintainer runs, from `jem/`:

  `python3 scripts/validate.py --strict && python3 scripts/derive.py && python3 scripts/build.py`

  Output must satisfy **`validate.py`** (**0 errors**): **`EntityModel`**, **`CaseVolumeModel`**, **`JudgeStrengthModel`**, and allowed **`SOURCE_TYPES`** / **`case_volume.source_type`** / **`judge_strength.source_type`** values.

**Task sections in the attached spec (apply all unless I narrow scope above)**

| § | Topic |
|---|--------|
| 1–5 | Tribunal typing, funding/ministries, `case_volume`, arbitration, other state packs |
| 6 | HC **permanent benches** (`HighCourtBench`, `BenchOf`, bench appellate/supervision routing) |
| 7 | **`judge_strength`** (allotted vs appointed) on courts and court-like bodies |
| 8 | Output expectations |

**Out of scope unless I explicitly allow it**

- Do **not** delete, rename, or resplit **`jem/data/entities/_generated/states/tn/tn_district_court_*.yaml`** (full TN lattice).
- Do **not** edit **`jem/data/derived/`** or hand-edit **`graph.json`** / `jem/web/public/graph.json`.
- Do **not** remove existing **`jem/data/entities/_generated/high_courts/benches/*.yaml`** unless replacing with a corrected full file.

**Deliverable format — pick one**

- **Option A (preferred):** For each created/changed file:

  `### PATH: jem/data/entities/.../file.yaml`

  then one fenced block with the **complete final file** (no `…` omissions).

- **Option B:** One **unified diff** against attached files; paths **relative to repo root**.

If you add or change **`BenchOf`** / appellate / supervision edges, also output complete files under **`jem/data/relationships/`** (same Option A/B rules).

**Also return (always)**

- Bullet list of **every file path** created or modified (entities **and** relationships).
- **“Unverified / left partial”** — fields without a primary source.

**Then:** follow **§1–§8** in `jem/docs/CLAUDE_PROMPT_V1_DATA_COMPLETION.md` (sections **“Context you must preserve”** through **“Output expectations”**).

### After Claude replies — merge locally

1. `git checkout -b <branch>` (e.g. `data/desktop-tribunal-pass`).
2. Copy YAML (and relationship files) to the **exact paths** listed, or `git apply` the diff.
3. From `jem/`: `python3 scripts/validate.py --strict` → fix Desktop output (do not weaken validation).
4. `python3 scripts/derive.py` → `python3 scripts/build.py`.
5. PR description: **validation 0 errors** + `graph.json` **`meta.entity_count`**.

**Relationships:** If benches or districts were rewired, confirm unique `id` values across `jem/data/relationships/*.yaml` and that **`BenchOf`** edges use category **`statutory_ref`** per §6.
