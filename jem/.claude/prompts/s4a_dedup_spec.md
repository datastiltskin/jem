# Session 4A — Dedup Spec

**Context:** `CLAUDE.md`, `jem/.claude/decisions/schema_lock.md`

## Task

Design deduplication logic for staging records before promotion.

Define:
1. Match keys (entity_name fuzzy, event_type, event_date, reference_number)
2. Conflict resolution — always write to `data_conflicts`, never silent merge
3. Promotion criteria to target `vacancy_events` table
4. `audit_log` entry format per promotion

**Output:** Decision tables + pseudocode. No implementation.
