# Full QA Audit

**Context files:**
- `CLAUDE.md`
- All files in `jem/.claude/decisions/`
- All files in `jem/.claude/outputs/`

## Task

Full QA audit of JEM build decisions.

Review all decision files and session outputs. Identify:
1. Any architectural decision that contradicts CLAUDE.md constraints
2. Any prompt that could produce hallucinated data (extraction, verification, harness system prompt)
3. Any missing data quality gate in the pipeline
4. Any endpoint or tool that could return unverified data without flagging it
5. Any test gap — use cases described in this thread that have no corresponding test
6. Any server resource risk (RAM, connections, concurrent processes)

**Output:**
- Issues table: severity (critical/major/minor), location, description, fix recommendation
- Green list: what is correctly designed
- Priority fix order
