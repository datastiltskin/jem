# Phase 2 acceptance rubric

Canonical checklist for marking C15–C20 **done** in `ENTITY_BUILD_ROADMAP.md`.  
Merged from Claude co-maintainer research session (Jun 2026).

## Hard gates

1. `python3 scripts/validate.py --strict` → 0 errors  
2. `python3 scripts/validate_graph_refs.py --strict` → 0 broken refs  
3. `python3 scripts/derive.py` → exit 0  
4. `python3 scripts/build.py` → exit 0  

## Orphan targets

| Milestone | Max orphans |
|-----------|-------------|
| After C15 Batch A (UP, WB, RJ, AP, TS, GJ) | < 130 |
| After C15 + C16 (MP, BR, KL, PB, HR, OD) | < 100 |
| Phase 2 complete | < 70 |

## Per-state core pack (C15–C18)

Required entity patterns: `rera_{st}` or `{st}_rera`, `serc_{st}`, `slsa_{st}`, `{st}_sja`, `{st}_lokayukta`, `{st}_advocate_general`, `{st}_state_cdrc`, `{st}_district_courts_generic`, 6–10 `{st}_district_court_*`, `{st}_special_courts`, 3–4 `{st}_cdrc_*`.

Conditional: `{st}_vat_tribunal` (high-volume states), `{st}_sat` (MH, HP, AP, WB, OD, KL, TS, JK per research table).

## Explicitly gated (watch note only)

- GSTAT constituted benches  
- `drt_{city}_n` sub-entities (drt.gov.in)  
- Bulk `judge_strength` / per-district NJDG `case_volume` (v1.2/v1.3)  

## Maintainer decision gates (lokayukta)

- **DG-L1** Manipur incumbent  
- **DG-L2** West Bengal operational status  
- **DG-L3** Tripura incumbent  
- **DG-L4** Meghalaya Act notification  
- **DG-L5** J&K post-2019 accountability body  
- **DG-L6** Puducherry UT scope  

## Labour / tribunal wiring (C20)

- `labour_tribunal_relationships.yaml` — ESI + generic labour/industrial → MoLE  
- `state_tribunal_relationships.yaml` — per-state VAT/SAT/industrial → HC  
- Do not duplicate `cgit_epfat_mole_relationships.yaml`  
