-- JEM SQLite schema v3 — insight request telemetry (schema_lock.md v3)
-- Applied after v2; safe to run multiple times (IF NOT EXISTS).

CREATE TABLE IF NOT EXISTS insight_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    insight_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    query_text TEXT,
    request_count INTEGER NOT NULL DEFAULT 1,
    first_requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_requested_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_insight_requests_last ON insight_requests(last_requested_at DESC);

INSERT OR IGNORE INTO schema_version (version, description)
VALUES (3, 'Insight request telemetry for unanswered smart-search questions');
