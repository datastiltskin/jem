# Session 6 — Digest Prompt

**Context:** `CLAUDE.md`

## Task

Write the nightly digest system prompt for the operational monitor.

Input: JSON summary of yesterday's staging activity (injected at runtime).

Output must:
- Executive summary (3 sentences max)
- Anomalies flagged with severity
- Recommended human actions
- No false urgency — `all_clear` section when nothing critical

**Output:** Prompt string for `jem/.claude/prompts/digest_v1.md`.
