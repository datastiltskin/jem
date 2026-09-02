# Dispatch prompt — Track N independent recount verifier

`prompt_id: dispatch-cursor-N-recount` · `version: v1` · dispatched 2026-09-01T00:27Z
`derived_from: cursor-N-classification-v1` (`ledger/prompts/05_CURSOR_N_classification_counting.md`)
`run_ledger: ledger/runs/cursor-N-recount__20260901T002914Z.jsonl`
`model: gpt-5.6-sol-high` — chosen deliberately for base-model-family diversity
against the orchestrator's Claude Opus 5.

The independence rules in section "THE RULES OF YOUR INDEPENDENCE" are the
substance of this prompt. A verifier that reads the implementation under test,
or peeks at the answer before computing its own, is a mirror rather than a check.

Recorded verbatim as dispatched.

---

You are the **independent recount verifier** for the N track of the JEM (Judiciary Entity Map India) data pipeline. Repo root: `/workspace`, pipeline root: `/workspace/jem`.

# WHY YOU EXIST

Another agent just refactored entity counting into a derived artifact. The governing spec (`/workspace/jem/ledger/prompts/05_CURSOR_N_classification_counting.md`) requires that a SECOND agent, on a DIFFERENT model family, independently recompute the same numbers via a DIFFERENT CODE PATH. If the two counts disagree, the classification map or the generic flags are wrong, and the correct action is to STOP and surface it — not to reconcile it quietly.

This exists because a previous version of this project published a hand-maintained entity total that turned out to be wrong ("83 real numbers"). Derived numbers get the same consensus discipline as leaf data.

# THE RULES OF YOUR INDEPENDENCE

1. **Do NOT import, read, copy, or execute `/workspace/jem/scripts/derive.py`.** Not its counting function, not any helper. Write your own counter from scratch.
2. **Do NOT read `/workspace/jem/data/derived/entity_counts.yaml` before you have computed your own numbers.** Compute first, compare second. If you peek first you are not a verifier, you are a mirror.
3. You MAY read `/workspace/jem/scripts/classification.py`. The `type → (nature, function)` map is the *definition* being counted, not the code path under test. Disagreeing with the map would be a redefinition, not a recount. Use it as the authority for the mapping, but write your own iteration/tallying logic.

# WHAT TO COMPUTE

Walk the raw YAML under `/workspace/jem/data/entities/` (recursively, all `*.yaml`, skipping any path containing "schema") and compute:

- The six buckets: for each `nature` in {institution, personnel} × each `function` in {judicial, quasi_judicial, support_apparatus}, the number of entities.
- Rules: an entity with `is_generic_rollup: true` is EXCLUDED from all buckets and counted separately as a generic. An entity with a `classification_override: {nature, function}` uses the override instead of its `type`. Everything else classifies by its `type` through the map.
- Also report: `total_countable` (sum of the six buckets), `generics_excluded`, and `total_entity_files` (every entity file you parsed, generics included).

Note `data/legal_instruments/` is reference data, NOT entities — it must not be counted. Confirm you excluded it.

# THEN COMPARE

Only after your numbers are computed and written down, read `/workspace/jem/data/derived/entity_counts.yaml` and compare bucket by bucket.

# EXPECTED VALUES (for your final check only — do NOT let these steer your computation)

Compute your own numbers FIRST and record them verbatim before you look at this section again. The committed artifact claims: institution×judicial 397, institution×quasi_judicial 436, institution×support_apparatus 226, personnel×judicial 8, personnel×quasi_judicial 0, personnel×support_apparatus 14, total_countable 1081, generics_excluded 64, total_entity_files 1145. If you find something different, that is a FINDING and you must report it loudly rather than assuming you made the mistake.

# ALSO SANITY-CHECK THESE INVARIANTS

- Does `total_countable + generics_excluded == total_entity_files`? Report the arithmetic.
- Are there any entity files whose `type` is absent from the classification map (and which lack an override)? List them. There should be none.
- Do any entities carry `is_generic_rollup: true` whose `id` does NOT end in `_generic`, or vice versa (id ends in `_generic` but flag missing/false)? List any mismatches — this is exactly the "generic flags are wrong" failure the spec warns about.
- Confirm no entity appears twice (duplicate `id` across files). Report any duplicates.

# OUTPUT

Write your ledger record to `/workspace/jem/ledger/runs/cursor-N-recount__<UTC timestamp>.jsonl` (create the file; use a timestamp like `20260901T004500Z`). One JSON object, including: your independently computed buckets, the artifact's buckets, a per-bucket diff, the PASS/FAIL verdict on exact match, your `model` and `model_version` so a reader can judge model diversity, the invariant check results, and a UTC timestamp.

Do NOT modify any other file. Do NOT `git add`, `git commit`, or `git push`. Do NOT run `build.py` or `derive.py`.

# FINAL MESSAGE

Report: (1) your independently computed six buckets and totals, (2) PASS or FAIL on exact match with the artifact, (3) the per-bucket diff if any, (4) the results of the four invariant sanity checks, (5) the path of the ledger file you wrote, and (6) an explicit statement of what code path you used so a reader can confirm it was genuinely independent of derive.py.
