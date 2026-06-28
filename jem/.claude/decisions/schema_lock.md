# Schema Lock — Session 0 Ground Truth

**Locked:** 2026-06-24  
**Source schemas:** `entity_schema.yaml` v1.3.0 (repo root, canonical), `jem/data/schema/relationship_schema.yaml` v0.1.0  
**Migration source:** `graph.json`

---

## 1. Fields Missing for Temporal Vacancy Tracking

| YAML / graph field | Gap | SQLite resolution |
|--------------------|-----|-----------------|
| `appointment.avg_days_vacancy_unfilled` | Point-in-time only, no event history | `vacancy_events` table |
| `appointment.sanctioned_strength` / `working_strength` | Snapshot in appointment blob | `vacancy_events` + `judge_strength` JSON |
| `judge_strength.*` | No temporal series | `vacancy_events` with `event_type` |
| `case_volume.vacancy_count` | Case-volume context, not appointment events | Denormalized read; events in `vacancy_events` |
| No `event_type` enum in entity schema | Needed for staging pipeline | `vacancy_events.event_type` |
| No `position` field on entity | Officeholder role at event time | `vacancy_events.position` |

## 2. Fields Missing for Statutory Basis Layer

| Gap | SQLite resolution |
|-----|-------------------|
| `constitutional_basis` / `statutory_basis` are flat strings | `statutory_basis_records` normalized table |
| `amendment_history` list not queryable | JSON in `entity_json` + optional `statutory_basis_records` |
| Relationship `statutory_basis` absent in rel schema | `relationships.statutory_basis` TEXT column |
| No citation URL per basis | `statutory_basis_records.source_url` |

## 3. Fields Missing for Jurisdictional Scope

| Gap | SQLite resolution |
|-----|-------------------|
| `jurisdiction_scope` nested object | `jurisdictional_scope` normalized table |
| `states_covered` / `uts_covered` not filterable | `jurisdictional_scope.states_covered_json`, `uts_covered_json` |
| `jurisdiction_types` list | `jurisdictional_scope.jurisdiction_types_json` |
| `level_of_government` on entity | `entities.level_of_government` column |

## 4. Naming Inconsistencies

| Location | Issue | Lock decision |
|----------|-------|---------------|
| `jem/data/schema/entity_schema.yaml` v0.1.0 vs root v1.3.0 | Duplicate, divergent | Root `entity_schema.yaml` is canonical |
| graph `relationship_category` vs schema `relationship_type` | Both exist | Store both; `relationship_type` is enum value |
| YAML `data_quality_notes` vs graph | Present in graph | `entities.data_quality_notes` |
| `derived` object in graph | Auto-computed scores | JSON in `entities.entity_json` key `derived` |

## 5. graph.json Migration Problems

| Issue | Mitigation |
|-------|------------|
| Nested objects vary per entity | `entity_json` TEXT column for all non-scalar top-level fields |
| `sources` is list of objects | Normalize to `entity_sources` |
| `aliases` is list | Normalize to `entity_aliases` |
| Some relationship endpoints may reference missing entities | `validate_db.py` FK check; build logs warnings |
| `_detail` internal field | Store in `entity_json`, not indexed |

## 6. SQLite Table Definitions

### schema_version

| Column | Type | Constraints |
|--------|------|-------------|
| version | INTEGER | PRIMARY KEY |
| applied_at | TEXT | NOT NULL DEFAULT (datetime('now')) |
| description | TEXT | |

### entities

| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY |
| name | TEXT | NOT NULL |
| name_hindi | TEXT | |
| abbreviation | TEXT | |
| type | TEXT | NOT NULL |
| cluster | TEXT | NOT NULL |
| level_of_government | TEXT | NOT NULL |
| legislature_status | TEXT | |
| created_year | INTEGER | NOT NULL |
| enacted_year | INTEGER | |
| operational_year | INTEGER | |
| abolished_year | INTEGER | |
| operational_status | TEXT | NOT NULL |
| constitutional_basis | TEXT | |
| statutory_basis | TEXT | |
| parent_hc | TEXT | |
| data_quality | TEXT | NOT NULL |
| data_quality_notes | TEXT | |
| unverified_fields_json | TEXT | |
| position | TEXT | |
| entity_json | TEXT | NOT NULL DEFAULT '{}' |

### entity_aliases

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| entity_id | TEXT | NOT NULL REFERENCES entities(id) ON DELETE CASCADE |
| alias | TEXT | NOT NULL |
| UNIQUE(entity_id, alias) | | |

### entity_sources

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| entity_id | TEXT | NOT NULL REFERENCES entities(id) ON DELETE CASCADE |
| source_type | TEXT | |
| url | TEXT | |
| title | TEXT | |
| accessed_date | TEXT | |

### jurisdictional_scope

| Column | Type | Constraints |
|--------|------|-------------|
| entity_id | TEXT | PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE |
| is_all_india | INTEGER | NOT NULL DEFAULT 0 |
| is_shared_multi | INTEGER | NOT NULL DEFAULT 0 |
| shared_appointer | TEXT | |
| states_covered_json | TEXT | NOT NULL DEFAULT '[]' |
| uts_covered_json | TEXT | NOT NULL DEFAULT '[]' |
| jurisdiction_types_json | TEXT | NOT NULL DEFAULT '[]' |

### statutory_basis_records

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| entity_id | TEXT | NOT NULL REFERENCES entities(id) ON DELETE CASCADE |
| basis_type | TEXT | NOT NULL |
| citation | TEXT | NOT NULL |
| source_url | TEXT | |
| notes | TEXT | |

### relationships

| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY |
| source | TEXT | NOT NULL REFERENCES entities(id) ON DELETE RESTRICT |
| target | TEXT | NOT NULL REFERENCES entities(id) ON DELETE RESTRICT |
| relationship_type | TEXT | NOT NULL |
| relationship_category | TEXT | NOT NULL |
| is_binding | INTEGER | |
| is_constitutional | INTEGER | |
| year_established | INTEGER | |
| year_abolished | INTEGER | |
| data_quality | TEXT | |
| contested_note | TEXT | |
| notes | TEXT | |
| statutory_basis | TEXT | |
| relationship_json | TEXT | NOT NULL DEFAULT '{}' |

### vacancy_events (target table for promoted staging)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| entity_id | TEXT | REFERENCES entities(id) ON DELETE SET NULL |
| entity_name_raw | TEXT | NOT NULL |
| position | TEXT | |
| event_type | TEXT | NOT NULL |
| event_date | TEXT | |
| reference_number | TEXT | |
| verbatim_excerpt | TEXT | NOT NULL |
| confidence | REAL | NOT NULL |
| source_url | TEXT | |
| promoted_from_staging_id | INTEGER | |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |

### staging_records

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| entity_name | TEXT | NOT NULL |
| position | TEXT | |
| event_type | TEXT | NOT NULL |
| event_date | TEXT | |
| reference_number | TEXT | |
| verbatim_excerpt | TEXT | NOT NULL |
| confidence | REAL | NOT NULL |
| source_url | TEXT | |
| status | TEXT | NOT NULL DEFAULT 'needs_review' |
| fetched_at | TEXT | NOT NULL DEFAULT (datetime('now')) |
| raw_source_hash | TEXT | |

### audit_log

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| action | TEXT | NOT NULL |
| table_name | TEXT | NOT NULL |
| record_id | TEXT | NOT NULL |
| actor | TEXT | NOT NULL |
| details_json | TEXT | NOT NULL DEFAULT '{}' |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |

### data_conflicts

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| staging_id_a | INTEGER | NOT NULL REFERENCES staging_records(id) |
| staging_id_b | INTEGER | REFERENCES staging_records(id) |
| conflict_type | TEXT | NOT NULL |
| description | TEXT | NOT NULL |
| resolved | INTEGER | NOT NULL DEFAULT 0 |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |

## 7. Indexes

| Index | Columns |
|-------|---------|
| idx_entities_type | entities(type) |
| idx_entities_cluster | entities(cluster) |
| idx_entities_operational_status | entities(operational_status) |
| idx_entities_data_quality | entities(data_quality) |
| idx_relationships_source | relationships(source) |
| idx_relationships_target | relationships(target) |
| idx_relationships_category | relationships(relationship_category) |
| idx_staging_status | staging_records(status) |
| idx_vacancy_events_entity | vacancy_events(entity_id) |

## 8. Schema Version

Current locked version: **2**

### v2 additions (community corrections + auth)

#### users

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| oauth_provider | TEXT | NOT NULL |
| oauth_sub | TEXT | NOT NULL, UNIQUE with oauth_provider |
| display_name | TEXT | NOT NULL |
| avatar_url | TEXT | |
| profile_url | TEXT | |
| email | TEXT | |
| role | TEXT | NOT NULL DEFAULT 'new' (`new` \| `trusted` \| `expert` \| `maintainer`) |
| approved_correction_count | INTEGER | NOT NULL DEFAULT 0 |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |
| last_login_at | TEXT | |

#### sessions

| Column | Type | Constraints |
|--------|------|-------------|
| id | TEXT | PRIMARY KEY |
| user_id | INTEGER | NOT NULL REFERENCES users(id) ON DELETE CASCADE |
| expires_at | TEXT | NOT NULL |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |

#### correction_proposals

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| scope | TEXT | NOT NULL (e.g. `entity:supreme_court_india`, `overview`) |
| entity_id | TEXT | REFERENCES entities(id) ON DELETE SET NULL |
| body | TEXT | NOT NULL |
| source_url | TEXT | NOT NULL |
| status | TEXT | NOT NULL DEFAULT 'pending_review' |
| author_id | INTEGER | NOT NULL REFERENCES users(id) ON DELETE CASCADE |
| reviewed_by | INTEGER | REFERENCES users(id) ON DELETE SET NULL |
| review_note | TEXT | |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |
| reviewed_at | TEXT | |

#### correction_votes

| Column | Type | Constraints |
|--------|------|-------------|
| user_id | INTEGER | NOT NULL REFERENCES users(id) |
| proposal_id | INTEGER | NOT NULL REFERENCES correction_proposals(id) |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |
| PRIMARY KEY | (user_id, proposal_id) | |

#### mcp_tokens (Phase 2 — expert MCP bearer tokens)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | NOT NULL REFERENCES users(id) ON DELETE CASCADE |
| token_hash | TEXT | NOT NULL UNIQUE |
| label | TEXT | |
| expires_at | TEXT | |
| revoked_at | TEXT | |
| created_at | TEXT | NOT NULL DEFAULT (datetime('now')) |

#### insight_requests (v3 — smart-search telemetry)

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| insight_id | TEXT | NOT NULL UNIQUE |
| title | TEXT | NOT NULL |
| query_text | TEXT | |
| request_count | INTEGER | NOT NULL DEFAULT 1 |
| first_requested_at | TEXT | NOT NULL DEFAULT (datetime('now')) |
| last_requested_at | TEXT | NOT NULL DEFAULT (datetime('now')) |

Cap: retain at most **1000** distinct `insight_id` rows; prune oldest by `last_requested_at` on insert.
