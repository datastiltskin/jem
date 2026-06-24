-- JEM SQLite schema v1 — derived from .claude/decisions/schema_lock.md
-- Do not edit without updating schema_lock.md and bumping schema_version

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now')),
    description TEXT
);

CREATE TABLE IF NOT EXISTS entities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_hindi TEXT,
    abbreviation TEXT,
    type TEXT NOT NULL,
    cluster TEXT NOT NULL,
    level_of_government TEXT NOT NULL,
    legislature_status TEXT,
    created_year INTEGER NOT NULL,
    enacted_year INTEGER,
    operational_year INTEGER,
    abolished_year INTEGER,
    operational_status TEXT NOT NULL,
    constitutional_basis TEXT,
    statutory_basis TEXT,
    parent_hc TEXT,
    data_quality TEXT NOT NULL,
    data_quality_notes TEXT,
    unverified_fields_json TEXT,
    position TEXT,
    entity_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS entity_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    alias TEXT NOT NULL,
    UNIQUE(entity_id, alias)
);

CREATE TABLE IF NOT EXISTS entity_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    source_type TEXT,
    url TEXT,
    title TEXT,
    accessed_date TEXT
);

CREATE TABLE IF NOT EXISTS jurisdictional_scope (
    entity_id TEXT PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    is_all_india INTEGER NOT NULL DEFAULT 0,
    is_shared_multi INTEGER NOT NULL DEFAULT 0,
    shared_appointer TEXT,
    states_covered_json TEXT NOT NULL DEFAULT '[]',
    uts_covered_json TEXT NOT NULL DEFAULT '[]',
    jurisdiction_types_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS statutory_basis_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    basis_type TEXT NOT NULL,
    citation TEXT NOT NULL,
    source_url TEXT,
    notes TEXT
);

CREATE TABLE IF NOT EXISTS relationships (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL REFERENCES entities(id) ON DELETE RESTRICT,
    target TEXT NOT NULL REFERENCES entities(id) ON DELETE RESTRICT,
    relationship_type TEXT NOT NULL,
    relationship_category TEXT NOT NULL,
    is_binding INTEGER,
    is_constitutional INTEGER,
    year_established INTEGER,
    year_abolished INTEGER,
    data_quality TEXT,
    contested_note TEXT,
    notes TEXT,
    statutory_basis TEXT,
    relationship_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS vacancy_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_id TEXT REFERENCES entities(id) ON DELETE SET NULL,
    entity_name_raw TEXT NOT NULL,
    position TEXT,
    event_type TEXT NOT NULL,
    event_date TEXT,
    reference_number TEXT,
    verbatim_excerpt TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_url TEXT,
    promoted_from_staging_id INTEGER,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS staging_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    position TEXT,
    event_type TEXT NOT NULL,
    event_date TEXT,
    reference_number TEXT,
    verbatim_excerpt TEXT NOT NULL,
    confidence REAL NOT NULL,
    source_url TEXT,
    status TEXT NOT NULL DEFAULT 'needs_review',
    fetched_at TEXT NOT NULL DEFAULT (datetime('now')),
    raw_source_hash TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    actor TEXT NOT NULL,
    details_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS data_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    staging_id_a INTEGER NOT NULL REFERENCES staging_records(id),
    staging_id_b INTEGER REFERENCES staging_records(id),
    conflict_type TEXT NOT NULL,
    description TEXT NOT NULL,
    resolved INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(type);
CREATE INDEX IF NOT EXISTS idx_entities_cluster ON entities(cluster);
CREATE INDEX IF NOT EXISTS idx_entities_operational_status ON entities(operational_status);
CREATE INDEX IF NOT EXISTS idx_entities_data_quality ON entities(data_quality);
CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source);
CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target);
CREATE INDEX IF NOT EXISTS idx_relationships_category ON relationships(relationship_category);
CREATE INDEX IF NOT EXISTS idx_staging_status ON staging_records(status);
CREATE INDEX IF NOT EXISTS idx_vacancy_events_entity ON vacancy_events(entity_id);

INSERT OR IGNORE INTO schema_version (version, description) VALUES (1, 'Initial schema lock Session 0');
