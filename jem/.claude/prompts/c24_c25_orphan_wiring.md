# C24/C25 orphan wiring — relationship design

You are designing YAML relationships for JEM (Judiciary Entity Map India).

## Task

Produce a **complete** `relationships:` YAML list (only the list items, no file wrapper) to wire **25 orphan entities** to zero orphans under `validate_graph_refs.py --strict`.

Read these files first:
- `jem/data/schema/relationship_schema.yaml` — allowed `relationship_type` values only
- `jem/scripts/validate_graph_refs.py` — orphan = entity id not appearing as source or target in any relationship

## Orphans to wire

**C24 — duplicate RERA scaffolds (4):** merge pointers to canonical state-pack ids
- `rera_rj` → canonical `rj_rera` (entity notes say merged)
- `rera_tn` → canonical `tn_rera`
- `rera_up` → canonical `up_rera`
- `rera_wb` → canonical `wb_rera`

**C25 — people/roles archetypes (20):** `jem/data/entities/people_roles/role_*.yaml`
- JudicialOfficerRole: role_chief_justice, role_supreme_court_judge, role_high_court_judge, role_district_judge, role_sessions_judge, role_magistrate, role_metropolitan_magistrate, role_family_court_judge, role_court_registrar, role_registrar_general, role_public_prosecutor
- LegalProfessionalRole: role_advocate, role_senior_advocate, role_advocate_on_record, role_defence_counsel
- PartyRole: role_accused, role_petitioner, role_respondent, role_victim, role_witness

## Rules

1. **No invented relationship types** — use only enum values from relationship_schema.yaml
2. **Primary sources** — every edge needs `sources[]` with india-code.nic.in or Constitution URL
3. **data_quality: partial** for all edges (role-layer scaffolding)
4. RERA duplicates: use `statutory_ref` category; notes must say duplicate scaffold → canonical id
5. Role archetypes: link each role to the **most appropriate single institutional anchor** already in the graph (e.g. `chief_justice_india`, `supreme_court_india`, `collegium_hc_appointment`, `tn_district_courts_generic` as national exemplar for district judges, `mh_bar_council` or state bar council for advocates — pick one consistent anchor per role type, document in notes)
6. Party roles: link to `supreme_court_india` with `JurisdictionDefinedBy` or `EstablishedUnder` and note "litigant-journey archetype; appears in proceedings before courts/tribunals"
7. Unique `id` per relationship: `rel_{source}_{type}_{target}` snake_case
8. Do **not** name individual judges or litigants

## Output format

Return **only** valid YAML list entries (lines starting with `  - id:`), ready to paste under `relationships:` in a new file `c24_c25_orphan_relationships.yaml`. No markdown fences. No commentary.
