# JEM — Smart Search (structural insights)

**Audience:** legal researchers, journalists, and civic-tech users browsing the interactive map.

The **static map** at `jem/web/` includes curated structural Q&A alongside entity search. No API key or chat backend is required.

| Surface | URL (when hosted) | Who it is for |
|---------|-------------------|---------------|
| **Interactive map** | https://friedso.com/apps/jem/ | Browse entities, relationships, scores, and smart-search insights |
| **REST API** | `https://your-host/api/v1/…` | Programmatic access (see [MCP_SETUP.md](MCP_SETUP.md)) |

---

## What Smart Search does

JEM maps **institutional structure** — appointment chains, funding, oversight, appellate paths, operational status, and documented structural gaps. It does **not** map case outcomes.

In the toolbar search box you can:

1. **Search entities** by name, abbreviation, alias, constitutional article, or statute (Fuse.js).
2. **Ask common structural questions** via suggestion chips or natural-language-style phrases (e.g. “HC vacancies”, “GSTAT high court”, “peak creation year”).

Answers appear in a **one-box** panel (with a close button) sourced only from fields present in `graph.json`. When data is missing, the box states *Insufficient sourced data in JEM for this query* — it does not guess.

Below the one-box, related **entity profile cards** link to `#/entity/<id>` detail pages with the entity slug shown.

---

## Insight categories (v1)

- Judge vacancies (largest vacancy count, HC with most vacancies; duration-based “longest unfilled” only when `avg_days_vacancy_unfilled` is populated)
- Lifecycle (newest / oldest active / last abolished)
- Temporal aggregates (year or decade with most creations or abolitions)
- Operational status (not constituted, partial tribunals, de facto blocked)
- Structural gaps (critical gaps, tribunal→HC writ load, appellate gaps)
- Derived scores (highest independence risk, lowest structural health)
- Case volume (highest pendency overall; HC, tribunal, and subordinate/district breakdowns where NJDG-sourced)
- Geography (state with most district courts in corpus)

Implementation: `jem/web/src/smartSearch.js` (client-side over `graph.json`).

---

## Temporal data honesty

- **Map / graph.json:** point-in-time snapshot at `meta.generated_at`. Updating YAML and rebuilding replaces prior snapshot values; the static export does **not** retain historical vacancy series.
- **SQLite (`vacancy_events`):** event-level history for maintainer pipelines (fetcher → staging → promote). Not exposed in the static map search today.

For temporal pattern studies across time, use `vacancy_events` + `audit_log` in `jem.db` (maintainer stack), not the static graph alone.

---

## Maintainer notes

- Rebuild `graph.json` after data changes so insights reflect new judge_strength, gaps, and lifecycle fields.
- Add or edit insights in `smartSearch.js`; each `compute()` must cite only graph fields and entity `sources` / gap records.
- Chat harness (`/chat`, Anthropic API) was removed in favour of this deterministic search layer.
