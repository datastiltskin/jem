# JEM — entity build roadmap (~1,500 target)

**Current corpus:** 592 entities (Jun 2026) · **Target:** ~1,500 structural entities  
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
| C02 | HC permanent benches | ~14 | ~13 | **updated** | 1 | Maintainer |
| C03 | Central tribunals (principal) | ~15 | ~14 | **done** | 0 | Maintainer |
| C04 | Central tribunals — regional benches (CESTAT×8, AFT×9, DRT×39) | ~56 | ~44 (CESTAT 8, AFT 11, DRT 25) | **updated** | 2 | Mixed |
| C05 | Quasi-judicial regulators (SEBI, TRAI, SERC/RERA gens) | ~80 | ~76 | **updated** | 1 | Mixed |
| C06 | Consumer commissions (NCDRC + state/district) | ~70 | ~54 | **updated** | 2 | Contributor drafts |
| C07 | ADR (NALSA, SLSA, Lok Adalat, mediation, arbitration institutes) | ~40 | ~37 | **updated** | 1 | Mixed |
| C08 | Ministries & executive governance | ~60 | ~68 | **done** | 0 | Maintainer |
| C09 | Appointment bodies & officeholders | ~25 | ~17 | **updated** | 1 | Maintainer |
| C10 | Digital infrastructure (e-Committee, NIC, CIS, NJDG) | ~8 | ~1 | **pending** | **1** | Maintainer |
| C11 | Security (CRPF, CISF, state police, court marshal) | ~10 | scaffold | **pending** | 1 | Contributor drafts |
| C12 | Investigation & prosecution | ~15 | partial | **updated** | 1 | Mixed |
| C13 | Training, audit, lokayukta (NJA, CAG, state SJA/SLSA) | ~40 | partial | **updated** | 2 | Contributor drafts |
| C14 | Phase-1 state packs (MH, DL, KA, TN lattice, PY) | ~220 | ~171 | **done** | 0 | Maintainer |
| C15 | State packs — Batch A (UP, WB, RJ, AP, TS, GJ) | ~420 | scaffold ~5 each | **pending** | **1** | Contributor drafts |
| C16 | State packs — Batch B (MP, BR, KL, PB, HR, OD) | ~360 | scaffold | **pending** | 1 | Contributor drafts |
| C17 | State packs — Batch C (NE, HP, UK, GA, CG, JH) | ~280 | scaffold | **pending** | 2 | Contributor drafts |
| C18 | State packs — Batch D (UTs, JK/LA, SK) | ~120 | scaffold | **pending** | 2 | Contributor drafts |
| C19 | Tax / revenue stack (GSTAT, CIT(A), DRP, VAT tribunals) | ~45 | 2 (AO, CIT(A) gens) | **updated** | 2 | Contributor drafts |
| C20 | Labour (CGIT, EPFAT, state labour courts) | ~35 | 0 | **pending** | 2 | Contributor drafts |
| C21 | Defence (court martial, AFT benches) | ~12 | 12 (AFT principal + 11 benches, court_martial_generic) | **updated** | 2 | Maintainer |
| C22 | Specialized regulators (FSSAI, AERA, ICADR, PFRDA entity) | ~10 | 7 (+ PFRDA partial) | **updated** | 2 | Maintainer |
| C23 | IP (patent controller, TM registry; IPAB historical) | ~5 | 5 (CGPDTM, TMR, ipab, compat) | **updated** | 3 | Maintainer |
| C24 | State tribunals (SAT, transport, mental health boards) | ~35 | 0 | **pending** | 3 | Contributor drafts |
| C25 | People / roles layer (judges, advocates, parties) | ~20 | partial | **pending** | 3 | Optional |
| C26 | Relationship wiring & orphan cleanup (~139 orphans) | — | partial | **updated** | 1–3 | **Maintainer only** |
| C27 | Data-quality upgrade (sources, partial→complete) | 592 | ongoing | **updated** | all | Contributor |
| C28 | Numerics (`judge_strength`, NJDG `case_volume`) | 592 | sparse | **pending** | 2 | Maintainer + NJDG |

*Last roadmap review: 2026-06-12 (Batch 3 C21/C22/C23 merged)*

---

## Build phases (path to 1,500+)

| Phase | Goal | Categories | ~Entities added |
|-------|------|------------|-----------------|
| **0** | Backbone shipped | C01, C03, C08, C14 | 506 (baseline) |
| **1** | Structural integrity + thin clusters filled | C02, C10, C11, C15 (Batch A start), C26 (incremental), C27 | +150–250 → ~700 |
| **2** | State expansion + tribunals | C15–C18, C04, C06, C19–C22 | +400–500 → ~1,200 |
| **3** | District resolution + remainder | C06 districts, C04 DRT benches, C23–C25, C28 | +300+ → **1,500+** |

---

## Active prompts

Copy the **base prompt** from [`AI_DATA_ENTRY_PROMPT.md`](AI_DATA_ENTRY_PROMPT.md), then paste one **TASK block** below into `=== TASK-SPECIFIC INSTRUCTIONS ===`.

**Base reminder:** set `ROLE: contributor` (issues only) or `ROLE: co-maintainer`. Do **not** output relationship YAML unless you are a maintainer explicitly wiring edges.

---

### Phase 1 — priority (run these first)

#### P1-A · C10 Digital infrastructure · `pending` · Maintainer

```
TASK: Draft entity YAML (maintainer review) for digital infrastructure cluster: e_committee_sc, nic_india, ecourts_services_generic, njdg_generic — copy structure from jem/data/entities/_generated/backbone/department_of_justice.yaml and existing digital cluster stubs. Statutory basis + funding + complaint paths. data_quality: partial minimum.
STATE / CLUSTER: digital_infrastructure
Do not add relationships; list suggested rel_* ids for maintainers in a table at end.
```

#### P1-B · C11 Security bodies · `pending` · Contributor

```
TASK: Draft entity YAML (maintainer review) for: crpf, cisf, state_police_generic, court_marshal_sc, sheriff_hc_generic. Template: nearest SecurityBody or ExecutiveBody in jem/data/entities/. Include operational_status and sources[] per field.
Do not add relationships.
```

#### P1-C · C15 State pack — Uttar Pradesh (UP) · `pending` · Contributor

```
TASK: Draft proposed new-entity YAML pack for UP (state code up), mirroring MH pack: up_rera, up_serc or serc_generic state_data, up_bar_council, up_sja, up_slsa, up_lokayukta, up_advocate_general, up_state_cdrc, up_district_courts_generic, 8 named high-volume district courts (Lucknow, Prayagraj, Varanasi, Ghaziabad, Agra, Meerut, Gorakhpur, Bareilly), up_special_courts. Copy jem/data/entities/_generated/states/mh/ as template. IDs must be snake_case with up_ prefix.
Do not add relationships. Submit as GitHub issue with YAML attachments.
```

#### P1-D · C15 State pack — West Bengal (WB) · `pending` · Contributor

```
TASK: Draft proposed new-entity YAML pack for WB mirroring MH: wb_rera, wb_slsa, wb_sja, wb_lokayukta, wb_advocate_general, wb_state_cdrc, wb_district_courts_generic, named districts Kolkata, Howrah, Darjeeling, Murshidabad, Nadia, wb_special_courts. Template: jem/data/entities/_generated/states/mh/.
No relationships in deliverable.
```

#### P1-E · C15 State pack — Rajasthan (RJ) · `pending` · Contributor

```
TASK: Draft proposed new-entity YAML pack for RJ mirroring MH (rera, slsa, sja, lokayukta, AG, state cdrc, generic district rollup, 6 named districts Jaipur, Jodhpur, Udaipur, Kota, Ajmer, Bikaner, special courts).
No relationships.
```

#### P1-F · C02 HC bench routing · `updated` · Maintainer only

```
ROLE: co-maintainer
TASK: Maintainer-only. Wire bench appellate/supervisory edges for UP, WB, RJ per jem/scripts/hc_benches_config.py — create up_relationships.yaml, wb_relationships.yaml, rj_relationships.yaml. Run validate_graph_refs.py --strict. Do not add new entity files unless bench nodes missing.
```

#### P1-G · C27 Data-quality — northeast HCs · `updated` · Contributor

```
TASK: For each HC in NE (hc_gauhati, hc_manipur, hc_meghalaya, hc_tripura, hc_mizoram, hc_sikkim, hc_arunachal_pradesh): upgrade data_quality from unverified/partial to partial/complete with DoJ or HC official source URLs for created_year, operational_status, judge_strength or case_volume if available. One entity per issue or one PR scoped to NE HCs only.
```

---

### Phase 2 — tribunals & regulators

#### P2-A · C04 CESTAT regional benches (8) · `pending` · Contributor

```
TASK: Draft 8 new CentralTribunal entities: cestat_chennai, cestat_mumbai, cestat_kolkata, cestat_bangalore, cestat_ahmedabad, cestat_hyderabad, cestat_allahabad, cestat_chandigarh. Parent act + bench jurisdiction states in data_quality_notes. operational_status from cestat.gov.in. Template: jem/data/entities/_generated/backbone/cestat.yaml. Not_Constituted if bench inactive.
No relationships.
```

#### P2-C · C19 Tax stack — CIT(A) generic · `pending` · Contributor

```
TASK: Draft cit_appeals_generic and ao_income_tax_generic as quasi-judicial / executive adjudication entities with statutory_basis, appointment, funding from CBDT, gap notes on backlog. Template: regulatory or executive bodies. Mark extreme backlog in structural_gap if sourced.
No relationships.
```

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

#### P3-A · C04 DRT benches (39) · `pending` · Maintainer-led batches

```
TASK: Draft DRT bench entities in batches of 10: batch 1 IDs drt_chennai, drt_mumbai, drt_delhi, drt_kolkata, drt_bangalore, drt_hyderabad, drt_ahmedabad, drt_pune, drt_allahabad, drt_chandigarh. Template: jem/data/entities/_generated/backbone/drt.yaml. List parent DRAT for maintainer wiring.
No relationships in file.
```

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

#### ~~P2-B · C04 AFT regional benches~~ · **done** 2026-06

```
TASK: (Completed) 11 AFT bench entities + BenchOf wiring to principal aft. Includes jammu, jabalpur beyond original 9-bench list.
```

#### ~~Batch 3 · C21 Defence + C22 Regulators + C23 IP~~ · **done** 2026-06

```
TASK: (Completed) court_martial_generic, fssai, aera, icadr, press_council_india, state_election_commission_generic,
insurance_ombudsman_generic, patent_controller, trade_marks_registry, compat. Relationships in
batch3_c21_c22_c23_relationships.yaml. Schema: ConsultedOn_Removal added for SEC removal inquiry (Art. 243K(2)).
ipab upgraded in-place (not ipab_abolished). Ministry stubs: MoHFW, MoCA, MIB, MoCI, GBIC.
```

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
