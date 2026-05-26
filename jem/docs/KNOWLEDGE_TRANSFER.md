# JEM — Knowledge Transfer Guide

**Judiciary Entity Map (India)**  
**Suggested subtitle:** *Open structural map of India's judicial ecosystem — institutional capacity, relationships, and systemic gaps*

| Field | Value |
|-------|--------|
| **Document version** | 1.0 (May 2026) |
| **Audience** | Co-maintainer (technical background); executive overview — use Cursor/Claude for deep dives |
| **Primary author** | Divya Sornaraja ([@dso6060](https://github.com/dso6060)) — data, deploy, process design |
| **Co-maintainer** | Prajna Prayas — equal on GitHub; friedso.com deploy stays with founder |
| **Live demo** | https://friedso.com/apps/jem/ (May 2026 build, ~506 entities) |
| **Current release label** | **v0.9** (pre-stabilisation; UI/data fixes in progress) |
| **Licences** | Data CC0 · Code MIT |
| **AI data-entry prompt** | [`AI_DATA_ENTRY_PROMPT.md`](AI_DATA_ENTRY_PROMPT.md) · also §20 below |

---

## 1. Purpose of this document

This guide transfers everything a **co-maintainer** needs to run the GitHub repository, review community contributions, and understand how JEM works — without requiring ownership of friedso.com hosting.

For command-level detail, see also:

- [`SESSION_WORKFLOW.md`](SESSION_WORKFLOW.md) — daily validate → derive → build
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — contributor rules
- [`DATA_MODEL.md`](DATA_MODEL.md) — score formulae
- [`MASTER_CHECKLIST.md`](../../MASTER_CHECKLIST.md) — version roadmap v0.9 → v2.0

---

## 2. Executive summary

**JEM** is an open-source **structural map** of India's judicial ecosystem. It does not record case outcomes, judge conduct, or editorial opinions. It records **how institutions are built and connected**: who appoints whom, who funds whom, appellate chains, complaint pathways, digital infrastructure, security arrangements, case-volume indicators, and documented **structural gaps** (e.g. bodies legislated but never constituted).

**Mission (operational framing):** Structural literacy that consolidates and presents the **functional or operational capacity** of judicial entities — a dashboard-oriented view of **court carrying capacity** for better administration and public understanding. Intended stakeholders include judicial administrators, litigants, journalists, the CJI's office, ministry officials, bureaucrats, researchers, and civic-tech users.

**Current state (May 2026):**

| Metric | Value |
|--------|--------|
| Entity YAML files | 506 |
| Relationships in `graph.json` | 525 |
| Built graph size | ~1.86 MB |
| `validate.py` | 0 errors (strict) |
| Live site | May 2026 build deployed |
| Git tags | **None** (no `v1.0.0` tag in git history) |
| `graph.json` meta.version | `1.0.0` (internal build label — treat publicly as **v0.9** until stabilised) |
| Data entry | Founder + Cursor/Claude sessions only |
| GitHub remote | **Not yet created** (founder will create; name TBD on call) |
| Community contributions | **Not open yet** — planned: data-quality upgrades only |

**Funding:** Personally funded to date; no grants documented. May change later.

---

## 3. What JEM is — and is not

### 3.1 In scope

- Institutional entities (courts, tribunals, regulators, ministries, appointment bodies, etc.)
- Typed relationships (appointment, funding, appellate, supervisory, audit, complaint, digital, security)
- Algorithmic **Independence Risk** and **Discretionary Power** scores (structural indicators, not conduct judgments)
- Case-volume / clog fields where sourced (NJDG snapshots, DoJ reports)
- **Gap registry** — documented shortfalls (vacancies, not constituted, circularity)
- Interactive map: semantic zoom L0–L3, timeline scroller, relationship lenses

### 3.2 Out of scope (by design)

- Case outcomes (who won/lost)
- Individual judge names or performance opinions
- Editorial commentary or political campaigning
- Revenue-administration chains, military justice depth, individual DLSAs (650+) — see README gap registry §E for sibling-project candidates

---

## 4. System architecture

### 4.1 Data flow

```
┌─────────────────────────────────────────────────────────────────┐
│  SOURCES (primary)                                               │
│  Constitution · Acts · Gazettes · SC/HC sites · DoJ · NJDG      │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  jem/data/                                                       │
│  entities/*.yaml  ·  relationships/*.yaml  ·  schema/          │
│  seeds/ (authoritative templates) → _generated/ (bundle output)  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PIPELINE (run from jem/)                                        │
│  validate.py → derive.py → build.py → graph.json (repo root)    │
│  validate_graph_refs.py (orphan / edge integrity)               │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  jem/web/  (vanilla HTML/JS/CSS — no frontend build step)       │
│  public/graph.json → symlink to ../../../graph.json             │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
                    Static host (e.g. friedso.com/apps/jem/)
```

### 4.2 Repository layout

```
<repo-root>/
├── README.md                 Project overview + gap registry
├── MASTER_CHECKLIST.md       Operator roadmap & audit log
├── graph.json                Compiled graph (built artifact)
├── .github/workflows/        CI: validate + derive on PR
└── jem/
    ├── data/                 All YAML source of truth
    ├── scripts/              validate, derive, build, generators
    ├── web/                  Frontend
    └── docs/                 This file + runbooks
```

### 4.3 Visualisation levels

| Level | View | Interaction |
|-------|------|-------------|
| L0 | Cluster constellations | Default / zoom out |
| L1 | Entity nodes, DAG layout | Zoom in / click cluster |
| L2 | Sub-entities, edge labels | Zoom further |
| L3 | Detail panel, sources, scores | Click entity |

**Font = data quality:** verified (bold) → complete → partial (grey italic) → unverified → contested (red dotted). Dashed border = `Not_Constituted`.

---

## 5. How data was collected

| Aspect | Detail |
|--------|--------|
| **Who entered data** | Project founder only, via Cursor/Claude-assisted sessions |
| **Methods** | Hand-authored YAML; seed files; generator scripts for state bundles and TN district lattice |
| **Case volume / NJDG** | Founder's **own export/scrape** of NJDG (National Judicial Data Grid) — not a third-party dataset. Merged via `merge_njdg_snapshot.py` (139 entities updated in May 2026 pass). Plan doc: `NJDG_MERGE_PLAN.md` |
| **Other numerics** | DoJ vacancy reports, HC annual reports where cited in entity `sources` |
| **Reproducibility** | All structural claims should cite `sources[]` with URLs; `data_quality` reflects confidence |

**Credentials / secrets:** None required for v0.9 static build. Live NJDG API (`fetch_njdg.py`) is planned for v2 — document keys and cron when implemented.

---

## 6. Data trust tiers (recommended mental model)

Use this when reviewing PRs or answering "how much can I trust this entity?"

| Tier | Scope | Trust level | Notes |
|------|--------|-------------|--------|
| **A — Core backbone** | SC, HCs, central tribunals, key regulators, governance wiring (May 2026 sessions) | Highest structural intent | Relationships actively wired; many fields `partial`, 9 `verified` |
| **B — Reference state packs** | MH, DL, KA, TN (38 districts), PY | Strong structure, variable numerics | TN has collapse/expand district lattice; NJDG merged where snapshot matched |
| **C — Bootstrap states** | ~31 states with `*_district_courts_generic` only | Structural scaffold | Correct *types* of bodies; not district-resolved |
| **D — Numeric overlays** | `case_volume`, `judge_strength` | Sparse | ~84/506 with `pending_cases`; ~2/506 with `judge_strength`; all `scores_validated: false` |

**Repo-wide audit (May 2026):** 506 entities — `verified`: 9, `partial`: 497, `scores_validated`: 0.

**Co-maintainer rule of thumb:** Do not treat the map as litigation-grade statistics until numerics are sourced per entity. Treat **relationship topology** in Tiers A–B as the primary v0.9 asset.

---

## 7. Validation — automated, maintainer, and community

### 7.1 Automated (every PR touching `jem/data/**` or `jem/scripts/**`)

1. **`validate.py --strict`** — Pydantic schema: required fields, enums, funding sources, etc.
2. **`derive.py`** — Recomputes Independence Risk / Discretionary Power → `data/derived/`
3. **`validate_graph_refs.py`** — Relationship endpoints exist; `--strict` for orphan trends

CI does **not** run `build.py` or deploy.

### 7.2 Maintainer validation (founder → shared with co-maintainer)

- Primary source check before `data_quality: verified`
- `derive.py --explain <entity_id>` for score sanity
- Disputed facts → `data_quality: contested` + both sources (no "resolution by opinion")
- **`derived.scores_validated: true`** only after verified data + score breakdown review

### 7.3 Community validation — options for your kickoff call

| Option | Model | Pros | Cons |
|--------|--------|------|------|
| **A — Issues only** | Contributors file issues with sources; maintainers edit YAML | Lowest risk | Slow scale |
| **B — PR: data-quality only** ✓ *recommended launch* | Community PRs limited to upgrading `partial`→`complete`/`verified`, sources, `data_quality_notes` | Scales review; no structural rewrites | Needs clear PR template |
| **C — CODEOWNERS** | `@maintainers` required on `jem/data/**` | Enforces 2-person review | Setup overhead |
| **D — Discussions → PR** | Disputes discussed in GitHub Discussions before YAML change | Good for contested facts | Needs moderation |
| **E — Domain reviewers** | Volunteer "owners" per cluster (courts, tax, labour) | Expertise depth | Hard to recruit early |

**Recommended v0.9 package:** **B + C + D**

- Public repo + `CONTRIBUTING.md` + issue templates (`data-correction`, `source-request`)
- **CODEOWNERS:** both maintainers on `jem/data/**`
- **Branch protection:** PR required, 1 approval from CODEOWNERS, CI green
- **Scope lock:** community may only submit **data-quality upgrades** (see §8); core entity/relationship additions stay maintainer-only until explicitly opened
- **Disputes:** documented escalation (Discussion → maintainer decision → `contested` flag if unresolved)

### 7.4 Known technical debt (acceptable for v0.9)

- **~139 relationship orphans** — incremental wiring scheduled v1.1+
- **0 scores community-validated** — UI shows "Pending community review" everywhere
- Missing docs referenced in older README (`ARCHITECTURE.md`, `SOURCES.md`, `ENTITY_TAXONOMY.md`) — use `DATA_MODEL.md` + this guide instead

---

## 8. Contribution model (agreed direction)

| Who | Can do |
|-----|--------|
| **Community (initial)** | Data-quality upgrades only: sources, `data_quality`, `data_quality_notes`, correcting factual fields with primary links |
| **Maintainers (you + co-maintainer)** | New entities, relationships, schema changes, generators, web UI, `derive.py` formulae, releases |
| **Founder only (for now)** | Deploy to friedso.com |

**Later expansion (explicit decision required):** new state packs, gap-registry entities, relationship bulk wiring.

---

## 9. GitHub & community launch plan

**Founder:** Divya Sornaraja · `@dso6060` · **Co-maintainer:** Prajna Prayas (add GitHub username to `CODEOWNERS` when known).

Scaffolding is in **`.github/`** (ready before first push):

| Path | Purpose |
|------|---------|
| [`CODEOWNERS`](../../.github/CODEOWNERS) | `@dso6060` on `jem/data`, scripts, web, docs |
| [`GOVERNANCE.md`](../../.github/GOVERNANCE.md) | Roles, scope, escalation |
| [`PUBLISH_CHECKLIST.md`](../../.github/PUBLISH_CHECKLIST.md) | Replace `REPO_NAME`, enable Discussions, branch protection |
| [`pull_request_template.md`](../../.github/pull_request_template.md) | PR checklist |
| [`ISSUE_TEMPLATE/`](../../.github/ISSUE_TEMPLATE/) | `data_correction`, `source_request`, `bug_report`, `contested_fact`, `expert_review` |
| [`DISCUSSION_TEMPLATE/`](../../.github/DISCUSSION_TEMPLATE/) | `data-question`, `dispute-escalation` |
| [`TEAM.md`](TEAM.md) | Placeholders: co-maintainer, legal expert, think-tank liaisons |
| [`workflows/validate.yml`](../../.github/workflows/validate.yml) | `validate.py` + `derive.py` + `validate_graph_refs.py` |

**On publish:** enable Discussions, branch protection (PR + CI + CODEOWNERS), create labels per publish checklist.

**Not in co-maintainer scope:** friedso server access, rsync, DNS.

---

## 10. Deployment (founder-operated)

Live URL: **https://friedso.com/apps/jem/**

- Deploy path documented in [`V1_RELEASE_RUNBOOK.md`](V1_RELEASE_RUNBOOK.md)
- **Critical:** ship `graph.json` as a real file at `public/graph.json` (symlinks often break on static hosts)
- Preflight: `./jem/scripts/deploy_prep.sh`
- `_deploy_bundle/` in workspace is a **local deploy archive** — not part of git narrative

**Mirrors:** Anyone may host `jem/web/` + `graph.json` statically; README should ask for attribution: *"Data from Judiciary Entity Map (JEM), https://friedso.com/apps/jem/"*

---

## 11. Versioning note: v0.9 vs build metadata

| Label | Meaning |
|-------|---------|
| **v0.9 (public)** | Current stabilisation track — UI fixes, data bugs, process hardening before calling v1.0 |
| **graph.json `meta.version: 1.0.0`** | Internal compiler label from May 20 build — consider aligning to `0.9.0` on next `build.py` run |
| **git tags** | None yet — create `v0.9.0` after co-maintainer onboarding + GitHub push |

---

## 12. Roadmap summary

| Release | Focus |
|---------|--------|
| **v0.9** (now) | Stabilise UI/data; GitHub public; contribution process |
| **v1.0** | Tag after smoke tests + agreed quality bar |
| **v1.1** | Bench routing, config sync, orphan reduction |
| **v1.2** | Bulk `judge_strength` + `case_volume` (DoJ/NJDG) |
| **v1.3** | Per-district NJDG (blocked on exports) |
| **v1.4** | Remaining state district lattices |
| **v1.5** | Gap registry entities (tax, labour, defence benches) |
| **v2.0** | Canvas renderer, live NJDG API, Sankey, litigant journey, optional CI deploy |

**Phased geography:**

- Phase 0: Central + TN + PY — done  
- Phase 1: MH, DL, KA — done  
- Phase 2–3: Other states / districts — community + maintainers (later)

---

## 13. Success metrics (targets)

| Metric | Target |
|--------|--------|
| Structural entities | ~1,500 (from ~506) |
| External contributors | 10+ with merged data-quality PRs |
| Data freshness | Monthly NJDG/DoJ refresh (post v2 API) |
| Orphan relationships | Trending down; strict ref check near zero for touched packs |
| `verified` entities | Growth from 9 → majority of Tier A/B |
| Community-validated scores | Tier A entities first |

---

## 14. Known gaps & access control

| Gap | Status / action |
|-----|------------------|
| No public GitHub yet | Founder creates; co-maintainer invited as admin |
| Contribution process | Documented here; implement templates + CODEOWNERS on create |
| CI does not build/deploy graph on merge | Maintainers run pipeline locally before release tags |
| friedso deploy | Founder only |
| Org size | 2 admins now; up to 5 members later |
| Legal disclaimer | Add to README + site footer (§15) |
| Live NJDG | Not built — static snapshots only |
| Domain experts | TBD |

---

## 15. Suggested legal disclaimer (README + site)

> **Disclaimer.** Judiciary Entity Map (India) (JEM) presents structural information about institutions and their formal relationships, derived from public sources. It does not provide legal advice, predict case outcomes, or assess individual conduct. Independence Risk and Discretionary Power scores are algorithmic indicators of *structural design*, not findings of bias or misconduct. Data may be incomplete or outdated; verify critical facts against primary sources before relying on them in litigation, policy, or journalism. Maintainers welcome corrections via GitHub with citations.

---

## 16. Licences & attribution

| Component | Licence | Attribution |
|-----------|---------|-------------|
| `jem/data/` | **CC0** | None required; courtesy link appreciated |
| `jem/scripts/`, `jem/web/` | **MIT** | Standard MIT notice in copies |

**Suggested courtesy (not required):**  
*"Structural data from [Judiciary Entity Map (JEM)](https://friedso.com/apps/jem/)."*

Optional future: `CONTRIBUTORS.md` listing merged PR authors.

---

## 17. Co-maintainer handoff checklist

- [ ] Clone repo; `cd jem && pip install -r scripts/requirements.txt`
- [ ] Run `python3 scripts/validate.py --strict` (expect 0 errors)
- [ ] Run `./scripts/safe_pipeline.sh`; confirm `graph.json` meta ~506 entities
- [ ] Open local `jem/web/` via static server; click SC, Madras HC, TN district collapse
- [ ] Read `DATA_MODEL.md` § governance exclusions + score formulae
- [ ] Read `SESSION_WORKFLOW.md` § overwrite risks (`build.py`, generators)
- [ ] Join GitHub org/repo as admin when created
- [ ] Agree on: PR scope (data-quality only), dispute escalation, v0.9.0 tag criteria
- [ ] Schedule call: repo name, issue templates, first community announcement

---

## 18. Essential commands

```bash
cd jem
pip install -r scripts/requirements.txt

# Standard session
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py
python3 scripts/derive.py
python3 scripts/build.py

# Explain one entity's scores
python3 scripts/derive.py --explain nclt

# Safe experiment (does not overwrite production graph)
./scripts/build_safe.sh
```

---

## 19. Key contacts

| Role | Contact |
|------|---------|
| Project founder / deploy | **Divya Sornaraja** · GitHub [@dso6060](https://github.com/dso6060) |
| Co-maintainer | **Prajna Prayas** · GitHub username TBD (add to `CODEOWNERS` when confirmed) |
| Domain reviewers (institutional) | [TrustBridge Rule of Law Foundation](https://trustbridge.in/) — *partnership / advisory role to be officially confirmed* |

---

## 20. Uniform AI prompt (Claude / Cursor / ChatGPT)

Everyone adding or correcting data should use the **same prompt** so YAML stays schema-safe and source-backed.

| Role | Workflow |
|------|----------|
| **Contributor** | `ROLE: contributor` → AI produces YAML drafts → you share files with maintainers (issue, PR, or email) → they validate & merge |
| **Co-maintainer** | `ROLE: co-maintainer` → AI edits repo → you run `validate.py` / `derive.py` → open PR |

**Contributors without git:** attach `.yaml` to a GitHub data-correction issue or email maintainers (Divya Sornaraja / Prajna Prayas). Do not set `verified` or `scores_validated`.

**Maintainers validating a contributor file:**

```bash
cd jem && python3 scripts/validate.py --entity path/to/submitted_file.yaml
```

### Copy-paste prompt (full)

Also maintained at [`AI_DATA_ENTRY_PROMPT.md`](AI_DATA_ENTRY_PROMPT.md). Copy from the opening ` ``` ` below through the closing fence.

```
You are helping with Judiciary Entity Map (India) — JEM, an open CC0 structural dataset of Indian courts, tribunals, regulators, and related bodies. You are working in a clone of the JEM repository.

=== REPO CONVENTIONS (do not violate) ===
• Map STRUCTURE only: appointment chains, funding, oversight, appellate paths, complaint mechanisms, operational status, case-volume fields when sourced — NOT case outcomes, NOT individual judge names, NOT editorial opinions.
• Entity IDs: permanent snake_case (e.g. hc_madras, mh_district_court_pune). Never rename an existing id.
• data_quality: use partial unless every changed fact has a primary GoI source URL; never set verified without official sources; never set derived.scores_validated (maintainers only).
• Primary sources (in order): india-code.nic.in, egazette.gov.in, main.sci.gov.in, official ministry/HC sites, doj.gov.in, NJDG/e-Courts URLs, PIB, law commission. Avoid Wikipedia and news-only citations.
• Schema: read jem/data/schema/entity_schema.yaml and jem/data/schema/relationship_schema.yaml before writing YAML.
• Templates: copy the closest existing file under jem/data/entities/ (same type/cluster/state). Match field names and nesting exactly.
• Paths: new state entities usually go under jem/data/entities/_generated/states/{state_code}/. Relationships go in jem/data/relationships/ (existing pack or new file only if maintainer-approved).
• Do NOT run generate_v1_states_bundle.py unless the user explicitly asks (high overwrite risk).
• Do NOT hand-edit jem/data/derived/ or commit graph.json unless the user is a maintainer running a release build.

=== YOUR SESSION ===
ROLE: [contributor | co-maintainer]
TASK: [one sentence — e.g. "Upgrade sources for hc_allahabad" OR "Draft YAML for Kerala SERC" OR "Fix case_volume on tn_district_court_chennai from NJDG"]
ENTITY_ID (if editing existing): [id or none]
STATE / CLUSTER (if relevant): [e.g. KL, regulatory_bodies, backbone]
PRIMARY SOURCES I HAVE: [paste URLs and access dates]

=== IF ROLE = contributor ===
1. Read the relevant existing YAML if ENTITY_ID is set; otherwise find the closest template entity.
2. Produce ONLY the YAML file(s) as deliverables — complete, valid-looking content with sources[] on every factual claim you add or change.
3. At the top of your reply, list: files to create/update (paths), entity ids touched, and a table of field | new value | source URL.
4. Tell the user to submit via GitHub "Data correction" issue or PR (data-quality scope) OR send the YAML to maintainers for validation and merge. Do NOT claim the data is merged or verified.
5. Do not add new relationship topology or new entity ids unless TASK explicitly says "draft for maintainer review" and user provided maintainer approval in chat.

=== IF ROLE = co-maintainer ===
1. Same quality rules as contributor.
2. After editing, run these commands from jem/ and report full output:
   python3 scripts/validate.py --strict
   python3 scripts/validate.py --entity <path>   # for single-file edits
   python3 scripts/validate_graph_refs.py
   python3 scripts/derive.py
   # build.py only if user wants to refresh graph.json for local preview
3. Suggest a commit message: data(scope): short description
4. Remind: friedso.com deploy is founder-only; PR needs CI green + CODEOWNERS review.

=== OUTPUT FORMAT ===
• Show complete YAML file contents in fenced blocks with path comment on first line: # jem/data/entities/...
• For relationship changes, show relationship YAML snippets with rel_* ids following rel_{source}_{type}_{target} pattern.
• If information is missing, leave fields null and explain in data_quality_notes — do not invent facts.
• If two primary sources conflict, set data_quality: contested and cite both; do not pick a winner.

=== TASK-SPECIFIC INSTRUCTIONS (user fills in) ===
[Paste any extra instructions, pasted statute text, NJDG export rows, or field-level corrections here.]

Begin by stating ROLE and TASK, listing files you will read, then produce deliverables.
```

**One-liner (Cursor):** `Follow jem/docs/AI_DATA_ENTRY_PROMPT.md; ROLE: co-maintainer; TASK: […]`

---

## 21. Origin (brief)

JEM began from the absence of a **public, machine-readable map** of how India's ~1,500 judicial and quasi-judicial bodies connect — appointment power, funding, oversight, and capacity signals — in one place. It is a **personally funded** civic/research infrastructure project, demonstrated at friedso.com, with the intent to move to a **standalone public GitHub** repository that others can fork, mirror, and improve under CC0/MIT.

---

*End of knowledge transfer guide. Regenerate Word export: `pandoc jem/docs/KNOWLEDGE_TRANSFER.md -o jem/docs/JEM_Knowledge_Transfer.docx` from repo root.*
