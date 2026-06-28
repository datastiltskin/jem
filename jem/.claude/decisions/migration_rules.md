# Migration Rules — Session 0 Ground Truth

**Locked:** 2026-06-24

---

## 1. Naming Rules

- All table and column names: `snake_case`
- Primary keys: `id` (TEXT for domain ids, INTEGER AUTOINCREMENT for internal)
- Foreign keys: `{table}_id` or domain name (`entity_id`, `source`, `target`)
- JSON columns: suffix `_json` for serialized arrays/objects
- Boolean flags in SQLite: INTEGER 0/1

## 2. FK Strategy

| Relationship | ON DELETE |
|--------------|-----------|
| entity_aliases → entities | CASCADE |
| entity_sources → entities | CASCADE |
| jurisdictional_scope → entities | CASCADE |
| statutory_basis_records → entities | CASCADE |
| relationships.source/target → entities | RESTRICT |
| staging_records | No FK to entities (raw names pre-match) |
| vacancy_events → entities | SET NULL (preserve event if entity removed) |
| data_conflicts → staging_records | RESTRICT |

## 3. Staging vs Target

| Table | Mutability |
|-------|------------|
| entities, relationships | Rebuilt from graph.json on `--force`; otherwise append-only for manual edits (Session 2+) |
| entity_aliases, entity_sources, jurisdictional_scope | Rebuilt with parent entity on migration |
| staging_records | Append by fetcher; status updated by verifier/portal |
| vacancy_events | Append-only after promotion from staging |
| audit_log | Append-only, never update or delete |
| data_conflicts | Insert on conflict; `resolved` flag only mutable field |

## 4. JSON Blob Policy

**Scalar top-level graph fields** → dedicated columns on `entities` / `relationships`.

**Normalize:**
- `aliases` → `entity_aliases`
- `sources` → `entity_sources`
- `jurisdiction_scope` → `jurisdictional_scope`

**Store in `entity_json`** (remaining top-level keys):
`derived`, `appointment`, `funding`, `case_volume`, `judge_strength`, `appellate_health`, `structural_exception`, `structural_gap`, `structural_circularity`, `amendment_history`, `funding_source`, `funding_ministry`, `audited_by`, `audit_report_public`, `complaint_external_exists`, `appointment_criteria_public`, `reappointment_possible`, `_detail`, and any future nested fields.

**Store in `relationship_json`:** `sources` and any extra relationship keys not in scalar columns.

## 5. graph.json Field Mapping — entities

| graph.json field | Destination |
|------------------|-------------|
| id | entities.id |
| name | entities.name |
| name_hindi | entities.name_hindi |
| abbreviation | entities.abbreviation |
| type | entities.type |
| cluster | entities.cluster |
| level_of_government | entities.level_of_government |
| legislature_status | entities.legislature_status |
| created_year | entities.created_year |
| enacted_year | entities.enacted_year |
| operational_year | entities.operational_year |
| abolished_year | entities.abolished_year |
| operational_status | entities.operational_status |
| constitutional_basis | entities.constitutional_basis |
| statutory_basis | entities.statutory_basis + statutory_basis_records |
| parent_hc | entities.parent_hc |
| data_quality | entities.data_quality |
| data_quality_notes | entities.data_quality_notes |
| unverified_fields | entities.unverified_fields_json (JSON array) |
| position (graph) | `entity_json.canvas_position` when dict; `entities.position` when string |
| aliases | entity_aliases |
| sources | entity_sources |
| jurisdiction_scope | jurisdictional_scope |
| all other keys | entity_json |

## 6. graph.json Field Mapping — relationships

| graph.json field | Destination |
|------------------|-------------|
| id | relationships.id |
| source | relationships.source |
| target | relationships.target |
| relationship_type | relationships.relationship_type |
| relationship_category | relationships.relationship_category |
| is_binding | relationships.is_binding |
| is_constitutional | relationships.is_constitutional |
| year_established | relationships.year_established |
| year_abolished | relationships.year_abolished |
| data_quality | relationships.data_quality |
| contested_note | relationships.contested_note |
| notes | relationships.notes |
| sources + extras | relationship_json |

## 7. Idempotency

- `schema_version` table tracks applied DDL version (currently `1`)
- `build_db.py` default: if DB exists and `schema_version.version == 1` and entity count matches graph meta, skip
- `--force`: drop and recreate all tables, full remigration
- Production path default: `jem/data/jem.db`
- Test path: always use `tmp_path` or `:memory:` via `--db` flag

## 8. Indexes

Create all indexes listed in `schema_lock.md` section 7 during DDL apply.

## 9. WAL Mode

Enable `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON` on every connection.
