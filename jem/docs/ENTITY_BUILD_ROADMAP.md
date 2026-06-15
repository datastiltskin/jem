# JEM — entity build roadmap (~1,500 target)

**Current corpus:** 1,103 entities (v1.2.0, Jun 2026) · **Target:** ~1,500 structural entities  
**Tracker:** this file is the source of truth; [`README.md`](../../README.md#entity-build-progress) mirrors the status table for GitHub.

## Status legend

| Status | Meaning |
|--------|---------|
| **done** | Category merged to `main`; prompt archived below |
| **updated** | Substantial data in repo; prompts remain for quality pass or sub-tasks |
| **pending** | Not started or scaffold-only — **use active prompt** |

## Maintainer workflow (when a category is finished)

1. Set status to **done** in the table below and set `Last updated` date.
2. Move its prompt from [Active prompts](#active-prompts) to [Completed prompts](#completed-prompts-archive).
3. Update the same row in [README § Entity build progress](../../README.md#entity-build-progress).
4. Commit: `docs(roadmap): mark <category> done` (+ data commits if applicable).
5. **Relationships** for that category: wire in a separate maintainer-only session (not contributor prompts).

**Contributors:** GitHub issues only — use [data correction](https://github.com/dso6060/jem_prototype/issues/new?template=data_correction.yml) or attach YAML to an issue.  
**New entities:** proposed drafts welcome; maintainers merge after `validate.py`.  
**Relationships:** maintainer-only.

---

## Category tracker

| ID | Category | Est. entities | In repo (May 2026) | Status | Phase | Owner |
|----|----------|---------------|----------------------|--------|-------|-------|
| C01 | Constitutional courts (SC + 25 HCs) | ~26 | ~27 + benches | **done** | 0 | Maintainer |
| C02 | HC permanent benches | ~14 | ~13 + UP/WB/RJ routing wired | **updated** | 1 | Maintainer |
| C03 | Central tribunals (principal) | ~15 | ~14 | **done** | 0 | Maintainer |
| C04 | Central tribunals — regional benches (CESTAT×8, AFT×11, DRT×25, ITAT×25) | ~56 | ~69 | **updated** | 2 | Mixed |
| C05 | Quasi-judicial regulators (SEBI, TRAI, SERC/RERA gens) | ~80 | ~76 | **updated** | 1 | Mixed |
| C06 | Consumer commissions (NCDRC + state/district) | ~70 | ~54 | **updated** | 2 | Contributor drafts |
| C07 | ADR (NALSA, SLSA, Lok Adalat, mediation, arbitration institutes) | ~40 | ~37 | **updated** | 1 | Mixed |
| C08 | Ministries & executive governance | ~60 | ~68 | **done** | 0 | Maintainer |
| C09 | Appointment bodies & officeholders | ~25 | ~17 | **updated** | 1 | Maintainer |
| C10 | Digital infrastructure (e-Committee, NIC, CIS, NJDG) | ~8 | 4 (e_committee_sc, nic_india, ecourts, njdg) | **updated** | **1** | Maintainer |
| C11 | Security (CRPF, CISF, state police, court marshal) | ~10 | 5 scaffolds | **updated** | 1 | Contributor drafts |
| C12 | Investigation & prosecution | ~15 | partial | **updated** | 1 | Mixed |
| C13 | Training, audit, lokayukta (NJA, CAG, state SJA/SLSA) | ~40 | partial | **updated** | 2 | Contributor drafts |
| C14 | Phase-1 state packs (MH, DL, KA, TN lattice, PY) | ~220 | ~171 | **done** | 0 | Maintainer |
| C15 | State packs — Batch A (UP, WB, RJ, AP, TS, GJ) | ~420 | UP/WB/RJ/AP/TS/GJ full packs | **updated** | **1** | Contributor drafts |
| C16 | State packs — Batch B (MP, BR, KL, PB, HR, OD) | ~360 | MP/BR/KL/PB/HR/OD full packs | **updated** | 1 | Contributor drafts |
| C17 | State packs — Batch C (NE, HP, UK, GA, CG, JH) | ~280 | NE+CG/GA/HP/JH/UK full packs (Jun 2026) | **updated** | 2 | Contributor drafts |
| C18 | State packs — Batch D (UTs, JK/LA, SK) | ~120 | CH/AN/LD/LA/JK/SK/PY expanded | **updated** | 2 | Contributor drafts |
| C19 | Tax / revenue stack (GSTAT, CIT(A), DRP, VAT tribunals) | ~45 | ~33 (AO, CIT(A), JCIT(A), ITAT×25, DRP, AAR, CAAR, GSTAT) | **updated** | 2 | Contributor drafts |
| C20 | Labour (CGIT, EPFAT, state labour courts) | ~35 | 10 (+ state_labour_court_generic) | **updated** | 2 | Maintainer |
| C21 | Defence (court martial, AFT benches) | ~12 | 12 (AFT principal + 11 benches, court_martial_generic) | **updated** | 2 | Maintainer |
| C22 | Specialized regulators (FSSAI, AERA, ICADR, PFRDA entity) | ~10 | 7 (+ PFRDA partial) | **updated** | 2 | Maintainer |
| C23 | IP (patent controller, TM registry; IPAB historical) | ~5 | 5 (CGPDTM, TMR, ipab, compat) | **updated** | 3 | Maintainer |
| C24 | State tribunals (SAT, transport, mental health boards) | ~35 | 5 (4 generics + state_vat_tribunal_generic) | **updated** | 3 | Contributor drafts |
| C25 | People / roles layer (judges, advocates, parties) | ~20 | partial | **pending** | 3 | Optional |
| C26 | Relationship wiring & orphan cleanup (~139 orphans) | — | **done** | **done** | 1–3 | **Maintainer only** |
| C27 | Data-quality upgrade (sources, partial→complete) | 668 | ongoing | **updated** | all | Contributor |
| C28 | Numerics (`judge_strength`, NJDG `case_volume`) | 1103 | partial (746 stubs) | **partial** | 2 | Maintainer + NJDG |

*Last roadmap review: 2026-06-15 (Wave 4–5 state packs — NE/CG/GA/HP/JH/UK + UTs; ~1,100 entities)*

---

## Build phases (path to 1,500+)

| Phase | Goal | Categories | ~Entities added |
|-------|------|------------|-----------------|
| **0** | Backbone shipped | C01, C03, C08, C14 | 506 (baseline) |
| **1** | Structural integrity + thin clusters filled | C02, C10, C11, C15 (Batch A start), C26 (incremental), C27 | +150–250 → ~700 |
| **2** | State expansion + tribunals | C15–C18, C04, C06, C19–C22 | +400–500 → ~1,200 |

**Phase 2 acceptance rubric:** [`PHASE2_ACCEPTANCE_RUBRIC.md`](PHASE2_ACCEPTANCE_RUBRIC.md)
| **3** | District resolution + remainder | C06 districts, C04 DRT benches, C23–C25, C28 | +300+ → **1,500+** |

---

## Active prompts

Copy the **base prompt** from [`AI_DATA_ENTRY_PROMPT.md`](AI_DATA_ENTRY_PROMPT.md), then paste one **TASK block** below into `=== TASK-SPECIFIC INSTRUCTIONS ===`.

**Base reminder:** set `ROLE: contributor` (issues only) or `ROLE: co-maintainer`. Do **not** output relationship YAML unless you are a maintainer explicitly wiring edges.

---

### Phase 1 — priority (run these first)

#### P2-D · C06 District CDRC — high-volume states · `pending` · Contributor

```
TASK: For state XX [user picks: GJ|AP|TS|KL]: draft 5 district CDRC entities with consumerhelpline or state CDRC sources. Template: jem/data/entities/_generated/states/tn/tn_cdrc_chennai.yaml. IDs: {st}_cdrc_{city}.
No relationships.
```

#### P2-E · C15 State pack — Andhra Pradesh (AP) · `pending` · Contributor

```
TASK: Full AP state pack mirroring MH template (ap_ prefix), 6 named districts including Amaravati/Visakhapatnam/Guntur.
No relationships.
```

#### P2-F · C15 State pack — Gujarat (GJ) · `pending` · Contributor

```
TASK: Full GJ state pack mirroring MH, include Ahmedabad and Vadodara named district courts if distinct from principal.
No relationships.
```

---

### Phase 3 — scale to 1,500+

#### P3-B · C18 Remaining state packs Batch C · `pending` · Contributor

```
TASK: Pick one state from Batch C (AS, BR, CG, GA, HP, JH, UK, NE states): produce full state pack from MH template. Confirm state code and HC mapping in notes.
No relationships.
```

#### P3-C · C06 TN district NJDG numerics · `pending` · Maintainer

```
TASK: Maintainer session. When NJDG district export available: update case_volume on tn_district_court_* YAML (37 without pending_cases). Use merge_njdg_snapshot.py plan. Contributor may attach export via issue only.
```

#### P3-D · C28 judge_strength bulk · `pending` · Maintainer

```
TASK: Maintainer-only. Populate judge_strength (allotted, appointed, data_as_of, source_url) for all ConstitutionalCourt and HighCourtBench from DoJ vacancy report URL in data_quality_notes.
```

---

## Completed prompts (archive)

*Move prompts here when category status → **done**. Keeps active list short.*

#### ~~P0 · C14 Phase-1 state packs~~ · **done** 2026-05

```
TASK: (Completed) MH, DL, KA, TN 38-district lattice, PY packs merged.
```

#### ~~P0 · C01 Constitutional courts + C03 Central tribunals principal~~ · **done** 2026-05

```
TASK: (Completed) SC, 25 HCs, central tribunal principal nodes in graph (~506 baseline).
```

#### ~~P0 · C08 Ministries & governance~~ · **done** 2026-05

```
TASK: (Completed) Governance graph Phase 6 — ministries, appointment committees, CBI selection committee.
```

#### ~~P2-A · C04 CESTAT regional benches (8)~~ · **done** 2026-06

```
TASK: (Completed) 8 CESTAT bench entities + BenchOf to cestat + AppealableTo HC edges (tribunal_completion_jun2026.yaml).
```

#### ~~P2-B · C04 AFT regional benches~~ · **done** 2026-06

```
TASK: (Completed) 11 AFT bench entities + BenchOf wiring to principal aft. Canonical Ladakh/J&K seat: aft_srinagar (not aft_jammu).
```

#### ~~P2-C · C19 Tax stack — CIT(A) / JCIT(A)~~ · **done** 2026-06

```
TASK: (Completed) ao_income_tax_generic, cit_appeals_generic, jcit_appeals_generic; DRP/AAR/CAAR pre-existed;
gstat_bench_generic scaffolded (Not_Constituted). ITAT chain wired: JCIT→ITAT, DRP→ITAT, ITAT→high_courts_all.
```

#### ~~M-T1 · ITAT per-zone → HC~~ · **done** 2026-06

```
TASK: (Completed) 25 itat_* bench entities + BenchOf→itat + AppealableTo HC edges in itat_bench_relationships.yaml.
Removed aggregate rel_itat_to_high_courts_all. Zone table in itat.yaml data_quality_notes.
```

#### ~~M-T2 · DRT Option B alias pass~~ · **done** 2026-06

```
TASK: (Completed) DRT-I/II/III aliases and Option B rollup notes on 8 multi-bench city rollups.
```

#### ~~M-T3 · GSTAT watch~~ · **gated** 2026-06

```
TASK: (Monitoring) gstat + gstat_bench_generic remain Not_Constituted; M-T3 watch note added. Flip on gazette.
```

#### ~~M-T4 · state_labour_court_generic~~ · **done** 2026-06

```
TASK: (Completed) state_labour_court_generic scaffold under C20.
```

#### ~~M-T5 · CESTAT quality pass~~ · **done** 2026-06

```
TASK: (Completed) cestat.gov.in source + quality notes on all 8 cestat_* bench entities.
```

#### ~~M-T6 · AFT Ladakh watch~~ · **gated** 2026-06

```
TASK: (Monitoring) aft_srinagar M-T6 review note; LA provisional pending post-2019 MoD gazette.
```

#### ~~P1-A · C10 Digital infrastructure~~ · **done** 2026-06

```
TASK: (Completed) e_committee_sc, nic_india, ecourts_services_generic, njdg_generic.
```

#### ~~P1-B · C11 Security bodies~~ · **done** 2026-06

```
TASK: (Completed) crpf, cisf, state_police_generic, court_marshal_sc, sheriff_hc_generic scaffolds.
```

#### ~~P1-C/D/E · C15 UP/WB/RJ packs~~ · **done** 2026-06

```
TASK: (Completed) Core pack entities + named districts per state; up/wb/rj_relationships.yaml wired.
Remaining: up_serc, full district lattices (v1.4 scope).
```

#### ~~P1-F · C02 HC bench routing UP/WB/RJ~~ · **done** 2026-06

```
TASK: (Completed) up_relationships.yaml, wb_relationships.yaml, rj_relationships.yaml.
```

#### ~~P1-G · C27 NE HC quality~~ · **done** 2026-06

```
TASK: (Completed) DoJ HC listing source added to 7 NE High Courts.
```

#### ~~Tribunal completion batch~~ · **done** 2026-06

```
TASK: (Completed) DRAT BenchOf×5, CGIT BenchOf×6 (cgit_principal), CESTAT→HC×9, tax appellate edges.
Skipped: duplicate DRT→DRAT (25 pre-wired), state_sales_tax (covered by state_vat_tribunal_generic).
```

#### ~~P3-A · C04 DRT batches 1–2 (25 location entities)~~ · **done** 2026-06

```
TASK: (Completed) 25 DRT location entities (batches 1+2); 5 DRAT bench entities; 25 AppealableTo
edges in central_tribunal_regulator_relationships.yaml. Gazette passes b3+b4: Siliguri 2017,
Lucknow/Dehradun S.O. 454(E), Hyderabad→DRAT Kolkata (G.S.R. 538(E)/2018), Jabalpur dual-HC.
BLOCKED: bench-numbered sub-entities (drt_city_n) — gated on drt.gov.in.
```

#### ~~drt_b5 · C20 MoLE funding wiring~~ · **done** 2026-06

```
TASK: (Completed) 16 edges in cgit_epfat_mole_relationships.yaml — all 6 CGIT benches
PrimaryFunder + PolicyOversight → ministry_labour_employment; EPFAT and EPFO funding/oversight.
Skipped drt_appellate_relationships.yaml (25 DRT→DRAT edges already wired; b5 used drt_bangalore).
```

#### ~~Batch 3 · C21 Defence + C22 Regulators + C23 IP~~ · **done** 2026-06

```
TASK: (Completed) court_martial_generic, fssai, aera, icadr, press_council_india, state_election_commission_generic,
insurance_ombudsman_generic, patent_controller, trade_marks_registry, compat. Relationships in
batch3_c21_c22_c23_relationships.yaml. Schema: ConsultedOn_Removal added for SEC removal inquiry (Art. 243K(2)).
ipab upgraded in-place (not ipab_abolished). Ministry stubs: MoHFW, MoCA, MIB, MoCI, GBIC.
```

---

## Open items (gated)

| Item | Gate | Owner |
|------|------|-------|
| `drt_city_n` bench-numbered sub-entities | `drt.gov.in` accessible | Maintainer |
| GSTAT bench stubs | GSTAT constituted | Maintainer |
| CGIT/EPFAT `judge_strength` numerics | MoLE quarterly data | Maintainer |
| Labour Code IRC 2020 transition notes | Labour Codes notified | Maintainer |
| G.S.R. 538(E)/2018 eGazette PDF | Manual `egazette.gov.in` fetch | Maintainer |
| CBDT Notification 96/2021 direct PDF | `incometaxindia.gov.in` archive | Maintainer |
| EPFAT operational status | MoLE confirmation post–Finance Act 2017 | Maintainer |

---

## Contributor issue checklist

When opening a GitHub issue with drafted YAML:

- [ ] Title: `[data] <category-id> <short description>`
- [ ] Category ID from table (e.g. C15 UP pack)
- [ ] Attach `.yaml` or paste in fenced block
- [ ] Table: field | value | source URL
- [ ] Confirm: no relationships, no `verified` unless primary source per field, no judge names

---

*Sync README after edits. Regenerate KT docx: `pandoc jem/docs/KNOWLEDGE_TRANSFER.md -o jem/docs/JEM_Knowledge_Transfer.docx`*
