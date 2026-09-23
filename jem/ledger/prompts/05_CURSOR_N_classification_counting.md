# CURSOR — Track N · Classification + Counting Reform

`prompt_id: cursor-N-classification-v1` · run LAST (after C and K land), because
it counts the corpus they enlarged. This is a **refactor**, not entity
generation — it edits infra, not YAML data.

## ROLE
Maintainer, refactor. Implement two-axis classification and generic-exclusion
across the repo, then run an **independent recount verify**. Touch only the files
named below. Do not alter entity YAML values.

## Tasks

1. **Add `scripts/classification.py`** (provided in this packet) — the single
   source of truth `type → (nature, function)`, `is_countable`, overrides.

2. **`scripts/validate.py`** — assert every entity `type` is classifiable
   (already added in S5 as a model_validator). No further change.

3. **`scripts/derive.py`** — compute entity counts by `(nature, function)`,
   **excluding `is_generic_rollup: true`**. Emit a committed counts artifact:
   `data/derived/entity_counts.yaml` with, per bucket:
   `institution×judicial`, `institution×quasi_judicial`,
   `institution×support_apparatus`, `personnel×*`, plus `generics_excluded` and
   `total_countable`. Legal-instrument registry rows are NOT entities — exclude.

4. **`scripts/build.py`** — surface `nature`/`function` on each node for the UI;
   ensure any node badge/count reads from `entity_counts.yaml`, never a hand
   number.

5. **README + ENTITY_BUILD_ROADMAP** — replace every hand-maintained entity total
   with the derived buckets. Reconcile the known count discrepancies (the
   README/graph.json metadata gap) against the derived total; if they still
   disagree, that disagreement is a finding — log it, don't paper over it.

6. **Mark existing generics.** Find `*_generic` entities (e.g.
   `*_district_courts_generic`, `lok_adalat_generic`) and set
   `is_generic_rollup: true`. This is the ONLY entity-YAML edit N makes, and it's
   a flag, not a value.

## Independent recount verify (consensus on a derived metric)
After the refactor, a SECOND agent independently recomputes the six buckets from
the raw YAML — different code path, no reuse of derive.py — and the two counts
must match. **Any mismatch means the classification map or the generic flags are
wrong; stop and surface it.** Log both counts + the diff to
`ledger/runs/cursor-N-recount__{timestamp}.jsonl`. This applies the consensus
discipline to derived numbers, which is exactly where the "83 real numbers"
README error lived.

## Output
- Code diffs for `derive.py`, `build.py`, `classification.py` (new).
- `data/derived/entity_counts.yaml` (the derived buckets).
- The `is_generic_rollup` flag additions (list the entity paths touched).
- README/roadmap edits.
- Recount ledger + PASS/FAIL on count-match.
- Run: `validate.py --strict` → `derive.py` → `build.py`; paste the 0-error
  summary and the two matching counts.

## Decision gates (surface, do not resolve)
- The two REVIEW rows in `classification.py` (`ADRBody`, `LegalOfficer`) — confirm
  or override before publishing counts, since they move bucket totals.
- If the derived total still can't be reconciled with the README/graph.json
  metadata, present the gap as a table (source of each number) rather than
  forcing them equal.
