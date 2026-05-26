# Judiciary Entity Map (India) - JEM

**Open structural map of India's judicial ecosystem — institutional capacity, relationships, and systemic gaps.**

*Working name during early builds was “d3lem”; the project and paths are now **JEM** / `jem/`.*

JEM maps *how* courts, tribunals, regulators, and oversight bodies are built — appointment chains, funding flows, independence risk, structural gaps, case volume and clogging — not *what* they decide. The goal is **structural literacy**: a dashboard-oriented view of institutional **carrying capacity** for administrators, litigants, journalists, ministry officials, and other stakeholders.

→ **Canonical demo (attribution):** https://friedso.com/apps/jem/  
→ **Data licence:** CC0 (public domain)  
→ **Code licence:** MIT  
→ **GitHub:** https://github.com/dso6060/jem_prototype  
→ **Maintainer guide:** [`jem/docs/KNOWLEDGE_TRANSFER.md`](jem/docs/KNOWLEDGE_TRANSFER.md) · [`jem/docs/JEM_Knowledge_Transfer.docx`](jem/docs/JEM_Knowledge_Transfer.docx)  
→ **AI data-entry prompt:** [`jem/docs/AI_DATA_ENTRY_PROMPT.md`](jem/docs/AI_DATA_ENTRY_PROMPT.md) · **Entity roadmap:** [`jem/docs/ENTITY_BUILD_ROADMAP.md`](jem/docs/ENTITY_BUILD_ROADMAP.md)

### Disclaimer

Judiciary Entity Map (India) (JEM) presents structural information about institutions and their formal relationships, derived from public sources. It does not provide legal advice, predict case outcomes, or assess individual conduct. Independence Risk and Discretionary Power scores are algorithmic indicators of *structural design*, not findings of bias or misconduct. Data may be incomplete or outdated; verify critical facts against primary sources before relying on them in litigation, policy, or journalism. Corrections are welcome via GitHub with citations (once the public repository is published).

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

**Constitutional courts:** Supreme Court · All 25 High Courts (complete)

**Central tribunals:** NCLT · NCLAT · NGT · ITAT · SAT · CAT · DRT · DRAT · TDSAT · APTEL · ATFE · CESTAT · AFT · GSTAT (Not_Constituted)

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

**Training / Audit:** NJA · SJA (generic) · TNSJA · CAG India · Lokayukta (generic) · TN Lokayukta (NC) · PY Lokayukta (NC)

**Subordinate courts:** District & Sessions Court (generic) · Civil Judge/MM (generic) · Special Court (generic) · TN District Courts · Chennai District Court · PY District Courts · TN Special Courts · Gram Nyayalaya (generic)

**People/Roles:** CJI · SC Judge · HC Judge · District Judge · Magistrate · Advocate · Senior Advocate · AOR · Petitioner · Respondent · Accused · Victim · Registrar General

**Sample state — Tamil Nadu + Puducherry UT**

---

## Entity build progress

**506 / ~1,500** structural entities in repo (May 2026). Full phased prompts and maintainer workflow: [`jem/docs/ENTITY_BUILD_ROADMAP.md`](jem/docs/ENTITY_BUILD_ROADMAP.md).

| Status | Meaning |
|--------|---------|
| **done** | Merged; prompt archived — no new copy-paste task |
| **updated** | In repo but quality/sub-tasks remain |
| **pending** | Use active prompt in roadmap |

| ID | Category | Est. | Status | Phase |
|----|----------|------|--------|-------|
| C01 | Constitutional courts (SC + 25 HCs) | ~26 | **done** | 0 |
| C02 | HC permanent benches | ~14 | **updated** | 1 |
| C03 | Central tribunals (principal) | ~15 | **done** | 0 |
| C04 | Tribunal regional benches (CESTAT, AFT, DRT) | ~56 | **pending** | 2 |
| C05 | Quasi-judicial regulators | ~80 | **updated** | 1 |
| C06 | Consumer commissions | ~70 | **updated** | 2 |
| C07 | ADR / NALSA / arbitration | ~40 | **updated** | 1 |
| C08 | Ministries & governance | ~60 | **done** | 0 |
| C09 | Appointment bodies | ~25 | **updated** | 1 |
| C10 | Digital infrastructure | ~8 | **pending** | **1** |
| C11 | Security bodies | ~10 | **pending** | 1 |
| C12 | Investigation & prosecution | ~15 | **updated** | 1 |
| C13 | Training, audit, lokayukta | ~40 | **updated** | 2 |
| C14 | State packs MH, DL, KA, TN, PY | ~220 | **done** | 0 |
| C15 | State packs Batch A (UP, WB, RJ, AP, TS, GJ) | ~420 | **pending** | **1** |
| C16 | State packs Batch B | ~360 | **pending** | 1 |
| C17 | State packs Batch C (NE, hills) | ~280 | **pending** | 2 |
| C18 | State packs Batch D (UTs, JK/LA) | ~120 | **pending** | 2 |
| C19 | Tax / revenue stack | ~45 | **pending** | 2 |
| C20 | Labour tribunals | ~35 | **pending** | 2 |
| C21 | Defence (AFT benches, court martial) | ~12 | **pending** | 2 |
| C22 | Specialized regulators (FSSAI, AERA, …) | ~10 | **pending** | 2 |
| C23 | IP entities | ~5 | **pending** | 3 |
| C24 | State tribunals (SAT, transport, MHRB) | ~35 | **pending** | 3 |
| C25 | People / roles layer | ~20 | **pending** | 3 |
| C26 | Relationship wiring (orphans) | — | **updated** | 1–3 |
| C27 | Data-quality upgrades | 506 | **updated** | all |
| C28 | NJDG / judge_strength numerics | 506 | **pending** | 2 |

**Contributors:** copy prompts from the roadmap + [`AI_DATA_ENTRY_PROMPT.md`](jem/docs/AI_DATA_ENTRY_PROMPT.md) → open a **GitHub issue** with YAML (no email). **New entities:** proposed drafts OK. **Relationships:** maintainers only.

*Maintainers: when a category is **done**, update this table and move its prompt to the roadmap archive.*

---

## Gap Registry

The canonical record of everything not yet in the data layer, deferred to v2, out of scope, or awaiting community contribution. Maintained so derivative research projects know exactly what is and is not covered.

---

### A. Structural gaps in the data (rendered as `*` markers on entities)

| Entity | Gap | Severity |
|---|---|---|
| GSTAT | Not constituted — 8 years since legislation. 15,000+ GST cases at HCs instead. | Critical |
| ACI | Not constituted — 6 years since legislation. SC issued notice 2025. | Critical |
| TN Lokayukta | Not constituted — 9 years. No anti-corruption oversight for India's 2nd-largest GDP state. | Critical |
| AFT | No HC appeal path — only direct SC SLP. 44% vacancy. MoD appointer-litigant loop. | Critical/High |
| Allahabad HC | 43% vacancy — 69 of 160 posts. India's highest-volume HC. | Critical |
| Patna HC | 47% vacancy — 25 of 53 posts. | Critical |
| NCDRC | Disposal rate 0.78 — backlog growing. Only Critical clog entity in v1. | Critical |
| Mediation Council | Not constituted — 2 years since legislation. Same pattern as ACI. | High |
| Gram Nyayalaya | <500 of 5,000 envisaged operational. UP: zero. | High |
| NGT | 45% vacancy — 9 of 20 posts. | High |
| NCLT | Complaint goes to appointing ministry (MCA) — structural conflict. | High |
| Collegium SC | No criteria, no timeline, no external review. NJAC struck down 2015. | High |
| State Police | No binding obligation to provide HC judge security. Active litigation 2024–25. | Critical |
| NIC India | No SLA with courts. Answers to MeitY, not judiciary. | High |
| CESTAT | MoF appointer-litigant loop — CBIC is respondent in every case. | High |
| TNERC | State appoints regulator + owns TANGEDCO (primary regulated entity). | High |
| CJI (Master of Roster) | No codified rules for bench/case assignment. Full discretion. | High |
| PY Lokayukta | Not constituted — 12 years since Lokpal Act. | High |
| RBI (Ombudsman) | Appellate authority is Dy Governor of same RBI. | Moderate |
| Insurance Ombudsman | Rs 50L cap. Awards nominally binding but unenforceable. | Moderate |
| NMC | No dedicated medical negligence tribunal — routes through consumer courts. | Moderate |
| Bombay HC, Madras HC | Custom CMS — NJDG reliability Low. | Moderate |
| BCI / State Bar Councils | Self-regulatory — no external oversight body. | Moderate |
| Special Courts | Executive designates specific courts for PMLA, NIA, POCSO. | Moderate |

---

### B. Known entities not yet in v1 — community contribution needed

**Tax / Revenue tribunals (high priority):**

| Entity | Notes |
|---|---|
| CESTAT regional benches (8) | Chennai, Mumbai, Kolkata, Bangalore, Ahmedabad, Hyderabad, Allahabad, Chandigarh |
| GSTAT state benches (31) | Planned but not constituted — enter as Not_Constituted with state variations |
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

**Phase 1 — Cursor Pro (from 28 April):**

| State/UT | Entity count (est.) | Key additions |
|---|---|---|
| Maharashtra | ~140 | City Civil Court Mumbai · MERC · MahaRERA · MH Lokayukta · 36 district courts |
| Delhi | ~80 | DERC · Delhi RERA · Delhi Lokayukta · 11 district courts |
| Karnataka | ~120 | City Civil Court Bangalore · KERC · KA RERA · KA Lokayukta · 31 district courts |

**Phase 2 — Community PRs:**

All remaining states — same entity types as Phase 1, scaled to each state's district count.

**Phase 3 — District resolution:**

Individual DLSA entities (650+), individual district CDRC entries (670+), individual DRT bench entities.

---

### D. Deferred to v2

| Feature | Why deferred |
|---|---|
| **HC permanent benches + judge strength (allotted/appointed)** | **In v2.0 data model** — see `jem/docs/V2_DATA_MODEL.md`; generator emits bench stubs; populate counts from DoJ/NJDG |
| State/Central Govt as major litigant (diamond nodes) | New node type, `FrequentLitigantIn` relationship, government litigation data from DoJ |
| Live NJDG API integration | Rate limiting, cache invalidation, staleness UI — v1 uses static snapshots |
| Case flow Sankey | Separate D3 Sankey module — appeal_rate_percent data needs verification across all tiers |
| Appointment delay pipeline | `avg_days_vacancy_unfilled` data not yet populated |
| Litigant journey mode | New interaction model, separate state machine |
| Canvas renderer for L1/L2 | Required for 60fps at 500+ nodes — SVG sufficient for current entity count |
| Chunked graph.json | Required at 1500+ entities — 658KB manageable now |
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

Production deploy is **maintainer-only**; see the release runbook. GitHub Actions validates PRs touching `jem/data/**` or `jem/scripts/**` — **does not auto-deploy**.

**Mirrors:** You may host copies elsewhere; courtesy attribution: *Structural data from [Judiciary Entity Map (JEM)](https://friedso.com/apps/jem/).*

---

## Phased expansion

| Phase | Scope | Mechanism | When |
|---|---|---|---|
| 0 | Central institutions + TN + PY sample | Built | Done |
| 1 | MH + DL + KA full state entities | Cursor Pro | From 28 April |
| 2 | Remaining 22 states + 5 UTs | Community PRs | Ongoing |
| 3 | District resolution (DLSAs, individual CDRCs) | Community PRs | Ongoing |
| 4 | Revenue courts, Board of Revenue per state | Specialist contributors | Open |

---

## Contributing

See [jem/docs/CONTRIBUTING.md](jem/docs/CONTRIBUTING.md). **v0.9:** community contributions are **data-quality upgrades on existing entities** only; maintainers handle new entities and relationship topology.

GitHub scaffolding (issue/PR templates, CODEOWNERS, governance): [`.github/`](.github/) · publish steps: [`.github/PUBLISH_CHECKLIST.md`](.github/PUBLISH_CHECKLIST.md) · team placeholders: [`jem/docs/TEAM.md`](jem/docs/TEAM.md).

Every field that affects a score or gap marker needs a primary source. `data_quality: unverified` renders with a dashed border — always better to be honest about what is and is not verified.

No case outcomes. No individual judge names. No editorial commentary. Structural facts from Constitution, statutes, judgments, official reports only.
