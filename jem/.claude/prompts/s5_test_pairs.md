# Session 5 — Harness Test Pairs

**Context:** `CLAUDE.md`, `harness/system_prompt.txt` (if available)

## Task

Write 15 test Q&A pairs for harness regression testing.

Categories:
- Entity lookup (3)
- Relationship traversal (3)
- Structural gap explanation (2)
- Legal advice refusal (2)
- Unverified data flagging (2)
- Out-of-scope refusal (3)

Each pair: `user_query`, `expected_behaviors` (bullet list, not exact text), `must_not_contain`.

**Output:** Markdown table or structured list for `tests/fixtures/harness_test_pairs.md`.
