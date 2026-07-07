# Contributing to Judiciary Entity Map (India) - JEM

## v0.9 contribution scope (read first)

| You can submit (PR or issue) | Maintainers only |
|------------------------------|------------------|
| Source links, factual corrections on **existing** entities | New entity `id`s or relationship topology |
| `data_quality` / `data_quality_notes` with citations | Schema or `derive.py` formula changes |
| Request `contested` with two primary sources | `derived.scores_validated: true` |

**GitHub:** Use the [data correction](https://github.com/datastiltskin/jem/issues/new?template=data_correction.yml) issue template or open a PR (checklist auto-applied).

Governance: [`.github/GOVERNANCE.md`](../../.github/GOVERNANCE.md) · Team: [`TEAM.md`](TEAM.md)

**Using AI (Claude / Cursor):** [`AI_DATA_ENTRY_PROMPT.md`](AI_DATA_ENTRY_PROMPT.md) + phased `TASK`s in [`ENTITY_BUILD_ROADMAP.md`](ENTITY_BUILD_ROADMAP.md). Submit via **GitHub issues only**. Proposed new entities OK; **relationships are maintainer-only**.

---

## Structural vs institutional accuracy

CI validates schema and reference integrity (L0–L3), not whether every institution
exists in law. See [`RCA_AI_HALLUCINATION_TRICHY_BENCH.md`](RCA_AI_HALLUCINATION_TRICHY_BENCH.md)
and [`DATA_QUALITY_GATES.md`](DATA_QUALITY_GATES.md). New `HighCourtBench` or tribunal
bench entities require a bench-specific primary source before merge.

## Principles

1. **Primary sources only.** Every `data_quality: verified` field requires a direct link to an official GoI source: india-code.nic.in, official gazette notification, Supreme Court judgment on main.sci.gov.in, or official ministry website.

2. **No editorial judgment on outcomes.** This map captures structural facts. Whether an entity *uses* its discretionary power well is not in scope. We record that it *has* discretionary power.

3. **Contested facts get the `contested` quality flag**, not a resolution. Both positions must be cited.

4. **IDs are permanent.** Once an entity has an `id` and relationships reference it, the id cannot change. Choose carefully — snake_case, no hyphens.

---

## Adding a new entity

1. Find the correct cluster for your entity (see `data/schema/entity_schema.yaml` for cluster values).

2. Copy the closest existing entity file as a template.

3. Fill all required fields:
   - `id`, `name`, `type`, `cluster`
   - `level_of_government`
   - `created_year`, `operational_status`
   - `data_quality` — start with `partial` unless you have a primary source
   - `sources` — at least one entry required for `verified`

4. Validate locally:
   ```bash
   python scripts/validate.py --entity data/entities/your_cluster/your_entity.yaml
   ```

5. Open a PR. GitHub Actions will validate automatically.

---

## Data quality rules

| Set to | When |
|---|---|
| `verified` | All fields populated, primary GoI source linked for every factual claim |
| `complete` | All fields populated, secondary source acceptable |
| `partial` | Some fields missing, or source is secondary/inferred |
| `unverified` | Community-submitted, not yet reviewed |
| `contested` | A factual dispute exists — cite both positions |

Never set `verified` without a working primary source URL.

---

## Correcting an existing entity

1. Check the `sources` field — is the claim actually sourced?
2. If the source is wrong or outdated, update the URL and `accessed_date`.
3. If the fact itself is wrong, correct the field and update `data_quality` if needed.
4. If there's active dispute (e.g., Lokpal jurisdiction over HC judges), set `data_quality: contested` and add both source URLs.

---

## Primary source hierarchy

In descending order of preference:

1. Constitution of India text — india-code.nic.in
2. Central Act text — india-code.nic.in
3. Official Gazette notification — egazette.gov.in
4. Supreme Court judgment — main.sci.gov.in
5. High Court judgment — respective HC website
6. Official Government of India website (doj.gov.in, mha.gov.in, etc.)
7. PIB press release — pib.gov.in
8. Parliamentary standing committee report
9. Law Commission report

Avoid: news articles, Wikipedia, secondary commentary.

---

## Adding relationships

Relationships live in `data/relationships/` organised by category:
`appointments.yaml`, `funding.yaml`, `appellate_chains.yaml`, `supervisory.yaml`,
`audit.yaml`, `complaint_mechanisms.yaml`, `digital.yaml`, `security.yaml`.

Each relationship requires:
- `id` (format: `rel_{source}_{type}_{target}`)
- `source` and `target` — must be valid entity ids
- `relationship_type` — from the controlled vocabulary in relationship_schema.yaml
- `relationship_category` — determines arc colour in the renderer
- `data_quality` and `sources`

---

## What not to contribute

- Case outcome data (which party won, which judge ruled how)
- Personal opinions on judicial performance
- Content without a primary source link
- Duplicate entities (check existing files first)
