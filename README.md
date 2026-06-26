# Judiciary Entity Map (India) - JEM

<p align="center">
  <img src="jem/web/public/assets/jem-lockup.png" alt="JEM" width="320">
</p>

**Open structural map of India's judicial ecosystem — institutional capacity, relationships, and systemic gaps.**

*Working name during early builds was “d3lem”; the project and paths are now **JEM** / `jem/`.*

JEM maps *how* courts, tribunals, regulators, and oversight bodies are built — appointment chains, funding flows, independence risk, structural gaps, case volume and clogging — not *what* they decide. The goal is **structural literacy**: a dashboard-oriented view of institutional **carrying capacity** for administrators, litigants, journalists, ministry officials, and other stakeholders.

→ **Canonical demo (attribution):** https://friedso.com/apps/jem/  
→ **Data licence:** CC0 (public domain)  
→ **Code licence:** MIT  
→ **GitHub:** https://github.com/dso6060/jem_prototype  
→ **Release:** `v1.0.0` (Jun 2026) — **1,117 entities**, **1,882 relationships**, **0 orphan nodes** · audit passes 1–4 + QA sprint (Jun 2026)  
→ **Maintainer:** [@dso6060](https://github.com/dso6060) · co-maintainer [@Prajna1999](https://github.com/Prajna1999) (UI) — contact via [GitHub Issues](https://github.com/dso6060/jem_prototype/issues)  
→ **Maintainer guide:** [`jem/docs/KNOWLEDGE_TRANSFER.md`](jem/docs/KNOWLEDGE_TRANSFER.md) · [`jem/docs/JEM_Knowledge_Transfer.docx`](jem/docs/JEM_Knowledge_Transfer.docx)  
→ **AI data-entry prompt:** [`jem/docs/AI_DATA_ENTRY_PROMPT.md`](jem/docs/AI_DATA_ENTRY_PROMPT.md) · **Entity roadmap:** [`jem/docs/ENTITY_BUILD_ROADMAP.md`](jem/docs/ENTITY_BUILD_ROADMAP.md)

### Disclaimer

Judiciary Entity Map (India) (JEM) presents structural information about institutions and their formal relationships, derived from public sources. It does not provide legal advice, predict case outcomes, or assess individual conduct. Independence Risk and Discretionary Power scores are algorithmic indicators of *structural design*, not findings of bias or misconduct. Data may be incomplete or outdated; verify critical facts against primary sources before relying on them in litigation, policy, or journalism. Corrections are welcome via [GitHub issues](https://github.com/dso6060/jem_prototype/issues/new?template=data_correction.yml) with citations.

---

## What it shows

| Layer | What you see |
|---|---|
| Appellate chain | Court hierarchy — who reviews whom |
| Appointment | Who nominates, recommends, formally appoints |
| Funding | Which ministry controls the budget |
| Supervisory | HC control over subordinate courts (Article 235) |
| Audit | CAG / PAC chains |
| Complaints | Bias complaint pathways for each entity |
| Digital | e-Committee, NIC, eCourts infrastructure |
| Security | CRPF / CISF / State Police / Court Marshal |
| People/Roles | Judges, advocates, prosecutors, parties (toggle) |
| Case volume | Pending cases, disposal rate, clog severity |
| Structural gaps | Documented shortfalls — legislative vacuums, accountability gaps, independence conflicts |
| Circularity | Entities playing conflicting roles (appointer + litigant, funder + regulated) |

---

## V1 entity coverage

**Snapshot (v1.0.0, Jun 2026):** full structural packs for **all states and UTs** (35 codes), central tribunal bench lattice (CESTAT×9 locations, AFT×11 locations / 15 courts, DRT×39 + DRAT×5, ITAT×63 benches / 27 stations — graph has 27 ITAT station entities), tax/labour/defence/IP stacks, regulators (IFSCA, CERC, IBBI, NMC), and **0 orphan entities** in `graph.json`. TN retains the deepest district lattice (38 courts); other states use core pack + named high-volume districts.

**Constitutional courts:** Supreme Court · All 25 High Courts (complete) · 13 permanent HC benches

**Central tribunals:** NCLT · NCLAT · NGT · ITAT · SAT · CAT · DRT · DRAT · TDSAT · APTEL · ATFE · CESTAT · AFT · GSTAT (Partial_Operational)

**Quasi-judicial regulators:** SEBI · RBI · CCI · TRAI · IRDAI · IBBI · NMC · IFSCA · CERC · Lokpal · NCAHP · Banking Ombudsman (RBI IOS) · Insurance Ombudsman (IRDAI) · TNERC · SERC (generic) · RERA (generic) · TN RERA

**Consumer redressal:** NCDRC · State CDRC (generic) · District CDRC (generic) · TN SCDRC · Chennai DCDRC · PY CDRC

**ADR:** NALSA · SLSA (generic) · Lok Adalat · Mediation Council (Not_Constituted) · ACI (Not_Constituted) · TN SLSA · PY SLSA · IIAC · DIAC · MCIA · Gram Nyayalaya (Partial_Operational)

**Ministries / Departments:** MoLJ · DoJ · MoF · MCA · DoPT · MHA · MeitY · MoD · MoEFCC · MoCA · DoT · MoP · MoHFW · MoLE · CBDT · Parliament

**Security:** CRPF · CISF · State Police (generic) · Court Marshal (SC) · Sheriff (HC)

**Digital infrastructure:** e-Committee (SC) · NIC India

**Professional bodies:** BCI · State Bar Council (generic) · BC Tamil Nadu & Puducherry

**Appointment bodies:** Collegium SC · President · Governor (generic) · LG Puducherry · CJI (office)

**Prosecution:** AG India · SG India · ASGs · Advocate General (generic) · TN AG · PY AG · Public Prosecutor (generic) · Special PP (generic)

**Investigative:** CBI · Enforcement Directorate

**Training / Audit:** NJA · SJA (generic) · TNSJA · CAG India · Lokayukta (generic) · TN Lokayukta · PY Lokayukta (NC)

**Subordinate courts:** District & Sessions Court (generic) · Civil Judge/MM (generic) · Special Court (generic) · TN District Courts · Chennai District Court · PY District Courts · TN Special Courts · Gram Nyayalaya (generic)

**People/Roles:** CJI · SC Judge · HC Judge · District Judge · Magistrate · Advocate · Senior Advocate · AOR · Petitioner · Respondent · Accused · Victim · Registrar General

**Sample state — Tamil Nadu + Puducherry UT** (TN also has full per-district lattice)

**All other states/UTs:** core pack (SERC/RERA, SJA, SLSA, lokayukta, AG, SCDRC, district CDRCs, 5–10 named district courts, special courts) — see `jem/data/entities/_generated/states/`

---

## Entity build progress

**1,117 / ~1,500** structural entities in repo (**v1.0.0**, Jun 2026). Full phased prompts and maintainer workflow: [`jem/docs/ENTITY_BUILD_ROADMAP.md`](jem/docs/ENTITY_BUILD_ROADMAP.md) · acceptance rubric: [`jem/docs/PHASE2_ACCEPTANCE_RUBRIC.md`](jem/docs/PHASE2_ACCEPTANCE_RUBRIC.md).

| Status | Meaning |
|--------|---------|
| **done** | Merged; prompt archived — no new copy-paste task |
| **updated** | In repo but quality/sub-tasks remain |
| **pending** | Use active prompt in roadmap |

| ID | Category | Est. | Status | Phase |
|----|----------|------|--------|-------|
| C01 | Constitutional courts (SC + 25 HCs) | ~26 | **done** | 0 |
| C02 | HC permanent benches | ~14 | **updated** — count unverified; needs per-bench DoJ/gazette citation | 1 |
| C03 | Central tribunals (principal) | ~15 | **done** | 0 |
| C04 | Tribunal regional benches (CESTAT, AFT, DRT, ITAT) | ~69 | **updated** | 2 |
| C05 | Quasi-judicial regulators | ~80 | **updated** | 1 |
| C06 | Consumer commissions | ~70 | **updated** | 2 |
| C07 | ADR / NALSA / arbitration | ~40 | **updated** | 1 |
| C08 | Ministries & governance | ~60 | **done** | 0 |
| C09 | Appointment bodies | ~25 | **updated** | 1 |
| C10 | Digital infrastructure | ~8 | **updated** | **1** |
| C11 | Security bodies | ~10 | **updated** | 1 |
| C12 | Investigation & prosecution | ~15 | **updated** | 1 |
| C13 | Training, audit, lokayukta | ~40 | **updated** | 2 |
| C14 | State packs MH, DL, KA, TN, PY | ~220 | **done** | 0 |
| C15 | State packs Batch A (UP, WB, RJ, AP, TS, GJ) | ~420 | **updated** | 1 |
| C16 | State packs Batch B (MP, BR, KL, PB, HR, OD) | ~360 | **updated** | 1 |
| C17 | State packs Batch C (NE, HP, UK, GA, CG, JH) | ~280 | **updated** | 2 |
| C18 | State packs Batch D (UTs, JK/LA, SK, PY) | ~120 | **updated** | 2 |
| C19 | Tax / revenue stack | ~45 | **updated** | 2 |
| C20 | Labour tribunals | ~35 | **updated** | 2 |
| C21 | Defence (AFT benches, court martial) | ~12 | **updated** | 2 |
| C22 | Specialized regulators (FSSAI, AERA, …) | ~10 | **updated** | 2 |
| C23 | IP entities | ~5 | **updated** | 3 |
| C24 | State tribunals (SAT, transport, MHRB, VAT) | ~35 | **updated** | 3 |
| C25 | People / roles layer | ~20 | **pending** | 3 |
| C26 | Relationship wiring (orphans) | — | **done** | 1–3 |
| C27 | Data-quality upgrades | 1117 | **updated** | all |
| C28 | NJDG / judge_strength numerics | 1117 | **partial** — see below | 2 |

**Contributors:** copy prompts from the roadmap + [`AI_DATA_ENTRY_PROMPT.md`](jem/docs/AI_DATA_ENTRY_PROMPT.md) → open a **GitHub issue** with YAML (no email). **New entities:** proposed drafts OK. **Relationships:** maintainers only.

*Maintainers: when a category is **done**, update this table and move its prompt to the roadmap archive.*

---

## Numerics status (C28) — `judge_strength` & NJDG snapshots

**Category C28 is structurally started but numerically incomplete in v1.0.0.** Topology and schema are in place; populated counts depend on **external GoI sources** that are **not stored in this repository**.

### Coverage audit (Jun 2026)

| Field | Entities with block | With real numbers | Status |
|---|---|---|---|
| `judge_strength` (allotted / appointed) | **746** | **39** | Stubs attached; bulk fill blocked on DoJ / HC rosters |
| `case_volume` / pending caseload | **153** | **84** | Rollup merge from prior NJDG snapshot only |

Scripts: [`populate_v12_numerics.py`](jem/scripts/populate_v12_numerics.py) (idempotent stubs) · [`merge_njdg_snapshot.py`](jem/scripts/merge_njdg_snapshot.py) (external snapshot) · plan: [`NJDG_MERGE_PLAN.md`](jem/docs/NJDG_MERGE_PLAN.md).

### The NJDG snapshot problem

1. **No district export in git.** The National Judicial Data Grid does not publish a bulk, versioned dataset suitable for committing to the repo. v1 historically merged a **maintainer-local** `graph.json` export (~216 nodes with `_detail.case_volume`). That snapshot path is documented in [`NJDG_MERGE_PLAN.md`](jem/docs/NJDG_MERGE_PLAN.md) but **must not be committed** (size, ToS, staleness).

2. **Rollups merged; new courts are empty.** `merge_njdg_snapshot.py --apply` applied `case_volume` to ~139 entities (HCs, tribunals, MH/DL/KA/TN rollups). The **v1.2 state-pack expansion** added 400+ court entities with **no matching NJDG rows** in the old snapshot — they have structural YAML only.

3. **Per-district pendency is gated (v1.3).** Example: TN has 38 district-court entities; **1** has district-level pending data (Chennai). Bombay HC and Madras HC use custom CMS — NJDG reliability is **Low** for those chains (see gap registry). Filling `tn_district_court_*`, `mh_district_court_*`, and peers requires **district-level NJDG exports** or a maintainer-attached snapshot via GitHub issue.

4. **`judge_strength` will not be invented.** `populate_v12_numerics.py` adds schema-correct blocks with `allotted: null`, `appointed: null`, and `source_url` placeholders pointing at DoJ vacancy reports and HC/tribunal roster pages. Populating ~700 remaining courts requires a maintainer pass from primary sources:
   - [DoJ judicial vacancy reports](https://doj.gov.in/report-and-committees/judicial-vacancy-reports)
   - Official HC bench rosters (parent HC holds sanctioned strength; benches report appointed only)
   - Tribunal annual / quarterly member-strength reports

### Maintainer workflow

```bash
cd jem
python3 scripts/populate_v12_numerics.py                    # judge_strength stubs (idempotent)
python3 scripts/merge_njdg_snapshot.py --snapshot /path/to/graph.json --plan report.md
python3 scripts/merge_njdg_snapshot.py --snapshot /path/to/graph.json --apply
python3 scripts/validate.py --strict && python3 scripts/derive.py && python3 scripts/build.py
```

**Contributors:** attach NJDG exports or per-court primary-source URLs in a GitHub issue; maintainers run merge + validation. Do not email snapshots.

### Release targets

| Milestone | Numerics scope |
|---|---|
| **v1.0.0** (current) | Schema + 746 `judge_strength` stubs + 84 rollup `case_volume` rows |
| **v1.3** | Per-district NJDG when district exports exist (TN 38/38, MH/KA bootstrap districts) |
| **v2.0** | Live NJDG API, staleness UI, year-over-year clog trends |

---

## Gap Registry

The canonical record of everything not yet in the data layer, deferred to v2, out of scope, or awaiting community contribution. Maintained so derivative research projects know exactly what is and is not covered.

---

### A. Structural gaps in the data (rendered as `*` markers on entities)

| Entity | Gap | Severity |
|---|---|---|
| GSTAT | Partially operational — Principal Bench constituted Sep 2023; Procedure Rules 2025 in force; state bench appointments incomplete. ~8,100+ GST cases still at HCs (per Rules notification; figure contested). | Critical |
| ACI | Not constituted — ~7 years since legislation. SC issued notice 23 Jan 2025. | Critical |
| TN Lokayukta | Operational — Chairperson Justice P. Rajamanickam (Feb 2025). TN Lokayukta Act 2018. CM probe needs assembly approval. | Moderate |
| AFT | No HC appeal path — only direct SC SLP. 11 locations / 15 courts. MoD appointer-litigant loop. Bench vacancies Mar 2026: Jabalpur/Guwahati/Srinagar fully vacant. | Critical/High |
| Allahabad HC | ~50% vacancy — 80 of 160 posts (Jul 2025 snapshot). India's highest-volume HC. | Critical |
| Patna HC | ~17% vacancy — 9 of 53 posts (44 judges, Jun 2026). Improving after 7 appointments. | Moderate |
| NCDRC | July 2025 monthly disposal 122% (DoCA) — prior 0.78 Critical clog label withdrawn as stale. Full backlog needs fresh export. | Moderate |
| Mediation Council | Not constituted — ~3 years since Mediation Act 2023. Same pattern as ACI. | High |
| Gram Nyayalaya | 333 of 488 notified operational (Oct 2025). Target ~6,000 (Law Commission 1986). UP leads with 109 — not zero. | High |
| NGT | Below statutory minimum both tracks — 6 judicial + 7 expert (Aug 2025); Act requires ≥10 each. | High |
| SAT | Single Mumbai bench (nationwide). Quorum crisis Dec 2023–Apr 2024; CJI Jul 2024 called for additional benches. | Moderate |
| CBI | Parent DoPT (MoPP&P) — not MHA. State consent withdrawals restrict jurisdiction. | Moderate |
| ED | Parent Department of Revenue / MoF — not MHA. | Moderate |
| NJA | Funded via DoJ but governed by SC (CJI chairs Governing Council). | Moderate |
| AG / SG | AG India is constitutional (Art. 76); SG and ASGs are statutory only — scoring must not treat SG as constitutional. | — |
| NCLT | Complaint goes to appointing ministry (MCA) — structural conflict. | High |
| Collegium SC | No criteria, no timeline, no external review. NJAC struck down 2015. | High |
| State Police | No explicit statutory obligation on state police to provide HC judge security (executive function). | Critical |
| NIC India | No SLA with courts. Answers to MeitY, not judiciary. | High |
| CESTAT | MoF appointer-litigant loop — CBIC is respondent in every case. | High |
| TNERC | State appoints regulator + owns TANGEDCO (primary regulated entity). | High |
| CJI (Master of Roster) | No codified rules for bench/case assignment. Full discretion. | High |
| Lokpal | Fully operational — Chairperson Justice A.M. Khanwilkar (oath 10 Mar 2024). 2022–2024 chairperson vacancy closed. | — |
| PY Lokayukta | Not constituted — 12+ years since Lokpal Act (Jan 2014). UT-with-legislature mandate ambiguous. | High |
| RBI (Ombudsman) | Appellate authority is Dy Governor of same RBI. | Moderate |
| Insurance Ombudsman | Rs 50L cap (Nov 2023 amendment). Awards binding on insurer; limited enforcement if defied — escalate to IRDAI/consumer court. | Moderate |
| NMC | No dedicated medical negligence tribunal — routes through consumer courts. | Moderate |
| Bombay HC, Madras HC | Custom CMS — NJDG reliability Low. | Moderate |
| BCI / State Bar Councils | Self-regulatory — no external oversight body. | Moderate |
| Special Courts | Executive designates specific courts for PMLA, NIA, POCSO. | Moderate |

---

### B. Known entities not yet in v1 — community contribution needed

> **Note (v1.0.0):** Many items below are now **in graph** as principals, regional benches, or generics (CESTAT×9 locations, AFT×11 locations (15 courts), DRT×39 + DRAT×5, ITAT×63 benches / 27 stations (25 station entities in graph), CGIT, EPFAT, IP stack, state VAT/SAT stubs). This section lists remaining depth work — per-bench DRT sub-entities, constituted GSTAT benches, per-district NJDG numerics.

**Tax / Revenue tribunals (remaining depth):**

| Entity | Notes |
|---|---|
| CESTAT regional benches (8) + Principal | Chennai, Mumbai, Kolkata, Bangalore, Ahmedabad, Hyderabad, Allahabad, Chandigarh (+ Principal Delhi = 9 locations) |
| GSTAT state benches (31) | Principal Bench constituted; state benches being notified — enter individual benches as gazette confirms full constitution |
| Dispute Resolution Panel (DRP) | Income Tax Act Section 144C. Inside CBDT — severe circularity. |
| AAR (Income Tax) | Authority for Advance Rulings. Slow, documented delays. |
| CAAR (Customs) | Reconstituted 2021. Replaced AAR Customs. |
| Income Tax Officer / CIT(A) | Pre-tribunal tax adjudication chain — AO → CIT(A) → ITAT |
| State Sales Tax / VAT Appellate Tribunal (generic) | ~28 bodies. Pre-GST legacy caseload still significant. |
| Board of Revenue (state generic) | Highest revenue appellate body per state. Land disputes, very high volume in agrarian states. |

**Labour / Employment:**

| Entity | Notes |
|---|---|
| CGIT (Central Govt Industrial Tribunal) | Under MoLE. Public sector labour disputes. |
| Industrial Tribunal (Central) | Multiple benches. PSU disputes. |
| EPFAT | Employees' Provident Fund Appellate Tribunal. |
| State Industrial Tribunals / Labour Courts (generic) | One per state, high volume. |

**Defence:**

| Entity | Notes |
|---|---|
| AFT regional benches (9) | Chandigarh, Lucknow, Kolkata, Guwahati, Chennai, Kochi, Jaipur, Mumbai, Hyderabad |
| Court Martial (generic) | Army/Navy/Air Force. Executive judicial proceedings. No external appeal until AFT. |
| Summary Court Martial | Expedited procedure — no legal representation for accused. |

**Specialised regulators:**

| Entity | Notes |
|---|---|
| PFRDA | Pension Fund Regulatory. PFRDA Act 2013 quasi-judicial functions. |
| FSSAI | Food Safety adjudication. Appellate → HC. |
| AERA | Airport Economic Regulatory Authority. Appellate → TDSAT. |
| ICADR | International Centre for ADR, Delhi. GoI-funded. |
| Press Council of India | Quasi-judicial media complaints. |
| State Election Commission (generic) | Electoral dispute adjudication. Distinct from ECI. |
| Telecom Mediation and Conciliation Authority | Under DoT, separate from TRAI/TDSAT. |

**Intellectual property:**

| Entity | Notes |
|---|---|
| IPAB (Abolished 2021) | Historical entity. IP appeals now before HCs. Transitional provisions poorly implemented. |
| Patent Office (Controller) | Controller has adjudicatory functions — pre/post-grant opposition. |
| Trade Marks Registry | Adjudicatory functions on opposition, cancellation. |

**State-level tribunals (generic entities needed):**

| Entity | Notes |
|---|---|
| State Administrative Tribunals | MH and HP have own SATs alongside CAT. |
| State Transport Appellate Tribunal (generic) | Motor Vehicles Act. ~20 states. |
| State Mental Health Review Boards | Mental Healthcare Act 2017 — quasi-judicial. |
| Debt Recovery Tribunals (individual benches) | 39 DRT benches — generic covered, individual entries pending. |

---

### C. State-level entities by phase

**Phase 1 — complete (MH, DL, KA, TN, PY):** full packs; TN has 38-district lattice.

**Phase 2 — complete (v1.0.0):** core packs for all remaining states and UTs (AP, TS, GJ, UP, WB, RJ, MP, BR, KL, PB, HR, OD, NE states, CG, GA, HP, JH, UK, CH, AN, LD, LA, JK, SK, PY).

**Phase 3 — District resolution (next):**

Individual DLSA entities (650+), individual district CDRC entries (670+), individual DRT bench entities.

---

### D. Deferred to v2

| Feature | Why deferred |
|---|---|
| **HC permanent benches + judge strength (allotted/appointed)** | **Partially in v1.2** — bench stubs + 746 `judge_strength` blocks; only 39 populated. Bulk fill deferred to maintainer DoJ/HC pass; see C28 section above |
| State/Central Govt as major litigant (diamond nodes) | New node type, `FrequentLitigantIn` relationship, government litigation data from DoJ |
| Live NJDG API integration | Rate limiting, cache invalidation, staleness UI — v1 uses static snapshots; district exports not in repo (C28) |
| Case flow Sankey | Separate D3 Sankey module — appeal_rate_percent data needs verification across all tiers |
| Appointment delay pipeline | `avg_days_vacancy_unfilled` data not yet populated |
| Litigant journey mode | New interaction model, separate state machine |
| Canvas renderer for L1/L2 | Required for 60fps at 500+ nodes — SVG sufficient for current entity count |
| Chunked graph.json | Required at 1500+ entities — ~5.6 MB manageable at 1,117 |
| Year-over-year clog trend | Needs multiple NJDG historical snapshots |
| Funding flow Sankey | Budget figures incomplete across entities |
| COMPAT (abolished) as historical entity | Needs historical rendering only — time scroller work |
| IPAB (abolished) as historical entity | Same |

---

### E. Out of scope by design — separate project candidates

These are structurally related but have different data models, source types, or audiences. JEM's YAML schema and pipeline could be forked as a starting point.

| Domain | Rationale for separation |
|---|---|
| **International courts** (ICJ, PCA, ITLOS, WTO) | Treaty-based, bilateral obligations, different governance model |
| **Revenue / land administration** (Patwari → Tehsildar → DM → Board of Revenue) | Not courts. Revenue Department chain, not Law Department. Warrants its own map. |
| **Military justice in depth** (Court Martial proceedings, JAG corps) | Classified proceedings, defence ministry jurisdiction, specialist source material |
| **Parliamentary committees** (Standing Committee on Law, PAC) | Legislative oversight — adjacent but not adjudicatory |
| **District Legal Services Authorities (individual)** | 650+ bodies — access-to-justice mapping warrants a dedicated project |
| **Quasi-judicial revenue chain** (AO → CIT(A) → ITAT) | Tax dispute chain is a full structural map in itself |
| **State CID / Vigilance Directorates** | Executive, not judicial — corruption oversight mapping is a sibling project |
| **Legal information systems** (SCC, Manupatra, Indian Kanoon) | Private entities, different governance model, different research question |
| **Panchayati Raj dispute resolution** | Sub-state, informal, high variability — limited formal structure |
| **Professional legal education** (NLUs, BCI Legal Aid clinics, law schools) | Education governance, not adjudication |
| **Alternative dispute resolution in contracts** (commercial arbitration clause mapping) | Contract-level, not institutional |

---

## Build

From the repository root, app scripts and data live under `jem/`:

```bash
cd jem
pip install -r scripts/requirements.txt
python scripts/validate.py            # 0 errors required
python scripts/derive.py              # Scores + auto-gap detection
python scripts/build.py               # Compile graph.json

# Diagnostics
python scripts/derive.py --explain nclt
python scripts/derive.py --clog-report
python scripts/derive.py --gaps-only
```

**Deploy** (static hosting — any provider):

1. From repo root, after a clean build:

```bash
cd jem
pip install -r scripts/requirements.txt
python scripts/validate.py --strict
python scripts/derive.py
python scripts/build.py
cd ..
./jem/scripts/deploy_prep.sh
```

2. Ship **both** artifacts to your host:
   - Repo-root **`graph.json`** → `public/graph.json` on the server (materialize the file; do not rely on the symlink alone).
   - **`jem/web/`** (HTML, CSS, JS) → your app directory.

3. **Examples** (set your own paths; not stored in this repo):
   - **rsync/SSH:** `export JEM_REMOTE='user@your-host:~/path/to/apps/jem'` then rsync `graph.json` and `jem/web/` (see [`jem/docs/V1_RELEASE_RUNBOOK.md`](jem/docs/V1_RELEASE_RUNBOOK.md)).
   - **Local preview:** `cd jem/web && python3 -m http.server 8080` (ensure `public/graph.json` resolves).
   - **Static hosts:** upload `jem/web/` plus `graph.json` as `public/graph.json` (Netlify, S3, GitHub Pages, nginx, etc.).

Production deploy is **maintainer-only** from branch **`friedso_v1`** (see [`.github/GOVERNANCE.md`](.github/GOVERNANCE.md)). Public workflow: [`jem/docs/SESSION_WORKFLOW.md`](jem/docs/SESSION_WORKFLOW.md) · [`deploy_friedso_production.sh`](jem/scripts/deploy_friedso_production.sh) · [`deploy_prep.sh`](jem/scripts/deploy_prep.sh).

GitHub: https://github.com/dso6060/jem_prototype — Actions validates PRs; **does not auto-deploy**.

**Mirrors:** You may host copies elsewhere; courtesy attribution: *Structural data from [Judiciary Entity Map (JEM)](https://friedso.com/apps/jem/).*

---

## Phased expansion

| Phase | Scope | Mechanism | Status |
|---|---|---|---|
| 0 | Central institutions + TN + PY sample | Maintainer | **Done** |
| 1 | MH + DL + KA full state entities | Maintainer | **Done** |
| 2 | All remaining states + UTs (core packs) | Maintainer + agents | **Done** (`v1.0.0`) |
| 3 | District resolution + per-district NJDG numerics | Community + maintainer | **Next** (blocked on district exports — C28) |
| 4 | Revenue courts, Board of Revenue per state | Specialist contributors | Open |

---

## Contributing

See [jem/docs/CONTRIBUTING.md](jem/docs/CONTRIBUTING.md). **v1.2+:** contributors may submit **proposed entity YAML** via GitHub issues; maintainers merge after `validate.py`. **Relationships** remain maintainer-only.

GitHub scaffolding (issue/PR templates, CODEOWNERS, governance): [`.github/`](.github/) · publish steps: [`.github/PUBLISH_CHECKLIST.md`](.github/PUBLISH_CHECKLIST.md) · team placeholders: [`jem/docs/TEAM.md`](jem/docs/TEAM.md).

Every field that affects a score or gap marker needs a primary source. `data_quality: unverified` renders with a dashed border — always better to be honest about what is and is not verified.

No case outcomes. No individual judge names. No editorial commentary. Structural facts from Constitution, statutes, judgments, official reports only.
