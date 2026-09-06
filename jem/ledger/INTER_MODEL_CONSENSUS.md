# Inter-model consensus — how to run

Rung 2 of the ladder in `prompts/02_CONSENSUS_HARNESS_SPEC.md`. This branch
(`integrate/consensus-20260906`) is the first place all four inputs live
together: Cursor intra-run harness, Prajna scrape scaffolding, Prajna
DeepSeek table, Agriya Codex table.

Not `main`. Nothing here writes canonical YAML.

## Run

From `jem/`:

```bash
# intra-run rungs already on this branch
python3 scripts/harness/liveness.py --help
python3 scripts/harness/public_inspection.py --help
python3 scripts/harness/reconcile.py --replay

# inter-model join of the two verify-trib-01 tables
python3 scripts/harness/inter_model.py --dry-run   # summary only
python3 scripts/harness/inter_model.py             # write ledger + CSV
```

The second command writes:

- `ledger/runs/inter-model__verify-trib-01__dso__<utc>.jsonl`
- `ledger/suggested/verify_trib_01_consensus.csv`

The first jsonl record is a **comment** carrying Agriya's 2026-09-06 email
caveats. Full text: `ledger/comments/agriya_20260906_handoff.md`.

## First run on this branch (2026-09-06)

| outcome | n | meaning |
|---|---|---|
| `agree_unsourced` | 69 | both raters: no matching-period primary |
| `agree_refute_njdg` | 43 | both recommend stripping the NJDG stamp |
| `disagree_period` | 22 | later-FY primary vs stored 2024-12-01 snapshot (SAT, NGT, CAT, AFT, CCI, …) |
| `disagree_verdict` | 5 | genuine split (e.g. CESTAT pending; SCDRC pending; Lok Adalat disposed) |
| `disagree_value` | 1 | `ka_state_cdrc.pending_cases`: Prajna 19,960 vs Agriya 9,947 |
| promoted to canon | **0** | by design for this sample |
| calibration-eligible cells | **0** | Agriya arm is not blinded |

Expert queue = 28 cells. Maintainer apply decisions, not auto-writes.

## Tests

```bash
pytest tests/test_harness.py tests/test_inter_model.py tests/test_schema_s.py
```
