# Session 5 — Harness System Prompt

**Context:** `CLAUDE.md`, `jem/.claude/decisions/schema_lock.md`

## Task

Write the chatbot harness system prompt for JEM researcher assistant.

Must include:
- JEM scope defined (structural map, not case outcomes)
- Legal advice declined with redirect to qualified counsel
- Citation instruction (cite entity id + source URL when available)
- Unverified flag instruction — always surface `data_quality` and `unverified_fields`
- No individual judge names
- Structural gap and independence risk explained in plain language

**Output:** Full system prompt text ready for `harness/system_prompt.txt`.
