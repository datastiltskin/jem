# Session 4A — Extraction Prompt

**Context:** `CLAUDE.md`

## Task

Write the extraction system prompt for the JEM fetcher agent.

This prompt will be sent to claude-sonnet-4-6 with raw HTML/PDF text from Indian government sources (gazette, ministry sites, court websites).

The prompt must enforce:
- Extract ONLY explicitly stated information
- Return `[]` for ambiguous, implicit, or inferred content
- Never infer dates not directly stated
- Extract entity names verbatim (fuzzy match happens downstream)
- JSON only output, no preamble
- Per-item fields: `entity_name`, `position`, `event_type`, `event_date`, `reference_number`, `verbatim_excerpt`, `confidence` (0-1)
- `confidence = 1.0` only for gazette notifications with explicit reference numbers
- `confidence < 0.7` → return `[]` (too uncertain to stage)

Also write:
- 5 example input/output pairs covering gazette appointment, vacancy notice, reform event, ambiguous content (→ `[]`), and unrelated content (→ `[]`)
- List of 10 failure modes specific to Indian govt HTML and how to detect them in the output

**Output:** Prompt string + examples + failure modes.
