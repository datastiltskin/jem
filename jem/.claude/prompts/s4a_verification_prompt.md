# Session 4A — Verification Prompt

**Context:** `CLAUDE.md`, `jem/.claude/prompts/extraction_v1.md` (if available)

## Task

Write the verification system prompt for the JEM verifier agent.

Given a staging record + source text, the verifier must:
- Confirm `verbatim_excerpt` appears in source text (fuzzy OK for whitespace)
- Flag hallucinated fields
- Assign `verification_status`: `confirmed` | `rejected` | `needs_human`
- Never upgrade `confidence` above extraction value
- Output JSON only

Include 3 example pairs and rejection criteria table.

**Output:** Prompt string + examples.
