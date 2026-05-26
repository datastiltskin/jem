# Judiciary Entity Map (India) - JEM

**Open structural map of India's judicial ecosystem — institutional capacity, relationships, and systemic gaps.**

An open, honest structural study of the Indian judicial ecosystem.
Maps institutional relationships — appointment chains, funding flows,
oversight mechanisms, complaint pathways — not case outcomes.

**Canonical demo (attribution):** https://friedso.com/apps/jem/  
**Knowledge transfer (maintainers):** [`docs/KNOWLEDGE_TRANSFER.md`](docs/KNOWLEDGE_TRANSFER.md) · [`docs/JEM_Knowledge_Transfer.docx`](docs/JEM_Knowledge_Transfer.docx)  
**AI data entry (copy-paste):** [`docs/AI_DATA_ENTRY_PROMPT.md`](docs/AI_DATA_ENTRY_PROMPT.md) · **Build roadmap (1,500+):** [`docs/ENTITY_BUILD_ROADMAP.md`](docs/ENTITY_BUILD_ROADMAP.md)

---

## What this is

The Indian judiciary involves roughly 1,500 distinct institutional entities across constitutional courts, subordinate courts, central and state tribunals, arbitration bodies, regulatory quasi-judicial bodies, investigative agencies, digital infrastructure bodies, audit bodies, and training institutions. No public map of their structural relationships exists.

JEM maps:
- Who appoints whom, and whether that appointment is binding
- Who funds whom, and whether the funder equals the appointer
- Which audit bodies exist for each entity
- Which complaint mechanisms exist for bias or misconduct, and whether complainants have locus
- How digital infrastructure is governed (e-Committee vs DoJ vs NIC)
- Where bodies have been legislated but never constituted

**Independence Risk** and **Discretionary Power** scores are algorithmically derived from structural data attributes. They are structural indicators, not judgments on conduct. All scores are labelled "Pending community review" until validated.

---

## Quickstart

```bash
# 1. Install Python dependencies
pip install -r scripts/requirements.txt

# 2. Validate all data files
python scripts/validate.py

# 3. Derive structural scores
python scripts/derive.py

# 4. Build graph.json (written to ../graph.json at the repo root; web/public/graph.json is a symlink)
python scripts/build.py

# 4b. Safe staging build (does NOT overwrite repo-root graph.json)
./scripts/build_safe.sh

# 5. Local preview or deploy (see docs/V1_RELEASE_RUNBOOK.md — generic static host)
# cd web && python3 -m http.server 8080
```

The frontend requires no build step. It is vanilla HTML + JS + CSS.
All CDN dependencies load from jsdelivr/cdnjs.

**v1 release (deploy/smoke/tag):** [docs/V1_RELEASE_RUNBOOK.md](docs/V1_RELEASE_RUNBOOK.md) · **Session workflow:** [docs/SESSION_WORKFLOW.md](docs/SESSION_WORKFLOW.md) · **Restore data:** [docs/V1_DATA_RESTORE.md](docs/V1_DATA_RESTORE.md) · **Checklist:** [../MASTER_CHECKLIST.md](../MASTER_CHECKLIST.md)

---

## Repository structure

```
data/
  schema/          Canonical YAML schema definitions
  entities/        One YAML file per entity, organised by cluster
  relationships/   Typed relationship files by category
  sources/         Source registries (constitution articles, acts, judgments)
  derived/         Auto-generated score output (do not edit manually)

scripts/
  validate.py      Pydantic v2 validation of all YAML files
  derive.py        Computes independence risk + discretionary power scores
  build.py         Compiles everything to web/public/graph.json
  requirements.txt pydantic>=2.0.0, pyyaml>=6.0

web/
  index.html       Main entry point
  src/             Vanilla JS modules (no build step)
  styles/          CSS
  public/          graph.json → symlink to ../../../graph.json (repo root; built by scripts/build.py)

docs/
  ARCHITECTURE.md  System design and score formulae
  DATA_MODEL.md    Independence risk and discretionary power formula documentation
  CONTRIBUTING.md  How to add or correct entities
  SOURCES.md       Primary source registry
  ENTITY_TAXONOMY.md  Coverage scorecard (~1,500 target entities)

.github/
  workflows/
    validate.yml   Runs on every PR — validate + derive, no deploy
```

---

## Visualisation

The map uses **semantic zoom** — four levels of detail:

| Level | What you see | How to reach it |
|---|---|---|
| L0 Constellation | 8 cluster blocks, aggregate metrics | Default / zoom out fully |
| L1 Backbone | Individual entity nodes, DAG layout | Scroll in / click cluster |
| L2 Sub-entity | Sub-entities, edge labels | Scroll in further |
| L3 Detail | Full entity card, sources, score breakdown | Click any entity |

The **time scroller** (1950 → present) is persistent across all levels.
Dragging it fades in/out entities based on `created_year` and `abolished_year`.

**Font = data quality:**
- Black bold = `verified` (primary source confirmed)
- Black normal = `complete`
- Grey italic = `partial` (some fields missing)
- Light-grey italic = `unverified`
- Red dotted-underline italic = `contested`
- Dashed node border = `Not_Constituted` (legislated but not set up)
- Faded / strikethrough = `Abolished`

---

## Adding entities

See `docs/CONTRIBUTING.md`. Short version:

1. Copy the closest existing YAML from `data/entities/`
2. Fill all fields — at minimum: `id`, `name`, `type`, `cluster`, `level_of_government`, `created_year`, `operational_status`, `data_quality`, `sources`
3. Run `python scripts/validate.py --entity path/to/your/file.yaml`
4. Open a PR — GitHub Actions validates automatically

Do not set `data_quality: verified` unless you have a direct link to a primary Government of India source.

---

## Licences

- `data/` — **CC0** (Public Domain). No attribution required.
- `scripts/` and `web/` — **MIT**.

---

## Status

Current coverage: ~8 sample entities (build scaffolding only).
Target: ~1,500 structural entities.

Priority data entry order:
1. All 25 High Courts
2. Subordinate court type definitions (civil + criminal tiers)
3. Central tribunals (NCLT, NGT, ITAT, CAT, SAT, DRT, Consumer Commissions)
4. Appointment bodies (Collegium, President, Governors, State PSCs)
5. Digital infrastructure cluster (NIC, CIS, NJDG, DoJ)
6. Security entities (MHA, State Police, CISF, Court Marshal)
7. Audit chain (CAG, PACs)
8. All relationship files (funding, appellate_chain, supervisory, audit, complaint)
