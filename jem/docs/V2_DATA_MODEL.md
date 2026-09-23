# JEM v2.0 data model additions

License: CC0

This document records the schema and UI fields introduced for v2.0 that were not in the original v1 checklist, such as the Canvas renderer, NJDG live fetch, and major litigants.

## 1. High Court permanent benches

### Entity type: `HighCourtBench`

Permanent benches of a High Court, such as the Madurai Bench of Madras HC, are neither district courts nor the consolidated `hc_*` node alone.

Map rendering: `HighCourtBench` nodes use a crescent shape rather than a full circle, so they stay visually distinct from principal `hc_*` circles and from district courts. See `jem/web/src/nodeShapes.js`.

| Field | Purpose |
|--------|---------|
| `type` | `HighCourtBench` |
| `cluster` | `constitutional_courts` |
| `parent_hc` | Parent entity id, e.g. `hc_madras` |
| `seat_city` | Bench city (generator field; optional in schema) |

### Relationship: `BenchOf`

- Source: the bench entity  
- Target: the parent `hc_*`  
- Category: `statutory_ref`

### District routing

Where a state pack lists explicit districts, appellate and supervision edges may target a bench instead of the parent HC, when that is configured in `jem/scripts/hc_benches_config.py`. Examples include the TN Madurai bench, MH Nagpur and Aurangabad, and KA Dharwad. Principal-seat districts continue to use `hc_*` directly.

### Generator

Run from repo root:

```bash
python3 jem/scripts/generate_v1_states_bundle.py
```

Bench YAML is written under `jem/data/entities/_generated/high_courts/benches/`.

---

## 2. Judge strength (allotted & appointed)

### Block: `judge_strength`

Required on all court and court-like entities in v2.0 data passes.

| Field | Meaning |
|--------|---------|
| `allotted` | Sanctioned posts (DoJ / NJDG "sanctioned strength") |
| `appointed` | Working judges actually in post |
| `vacancy_count` | Optional; may be derived as `allotted − appointed` |
| `data_as_of` | ISO date of snapshot |
| `source_type` | `DoJ_Report`, `NJDG_Snapshot`, `HC_Report`, etc. |
| `source_url` | Primary URL |

Legacy note: `case_volume.sanctioned_strength` and `working_strength` remain valid. The detail panel prefers `judge_strength` and falls back to `case_volume` for display.

### UI

The Level 3 detail panel always shows a Judge strength section for court-like types, with "Not yet recorded" when values are null.

### Validation

`JudgeStrengthModel` in `jem/scripts/validate.py`. Optional fields may be null in partial data.

---

## 3. HC → Supreme Court appellate backbone

The generator adds `AppealableTo` / `appellate_chain` from each `hc_*` to `supreme_court_india` (Article 136 / SLP framing in `notes`).
