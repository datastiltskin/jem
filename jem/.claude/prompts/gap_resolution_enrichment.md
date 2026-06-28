# Enrich structural_gap entries with gap_resolution_note

For each entity YAML listed below that has `structural_gap.gaps`, add a
`gap_resolution_note` field to every gap object that lacks one.

## Entities to update
- gram_nyayalaya_generic.yaml
- sat.yaml
- ngt.yaml
- ncdrc.yaml
- aft.yaml
- nmc.yaml
- cit_appeals_generic.yaml
- lokpal_india.yaml
- state_police_generic.yaml
- hc_allahabad.yaml
- hc_patna.yaml
- py_lokayukta.yaml
- arbitration_council_india.yaml
- mediation_council_india.yaml

Paths under `jem/data/entities/` (search by id).

## Rules
1. **Primary sources only** — India Code, Gazette, official GoI/tribunal URLs, Lok Sabha replies cited in existing gap_source.
2. `gap_resolution_note` = 1–3 sentences on **expected path to resolution** or why timeline is **indeterminate**. No invented dates.
3. If no credible timeline exists, say so explicitly (e.g. "No statutory deadline; contingent on…").
4. Do NOT change gap_description, scores, or unrelated fields.
5. Write the updated YAML files directly.

Return a markdown table: entity id | gap_id | resolution note added (yes/no) | source used.
