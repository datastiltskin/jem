# JEM — Data-Integrity + Lattice-Generation Specification Packet

Generated for DSo, Aug 2026. This packet is a *specification*, not applied code.
Nothing here edits canonical JEM. You apply the schema, run the Cursor prompts,
review the suggested edges, and promote through the pipeline.

## Design invariants (hold across every file)

1. **Ledger vs canon.** Every run appends to an append-only ledger; canon is a
   replayable derivation of the ledger. Nothing enters consensus from an
   uncommitted artifact.
2. **Capture at ingest, filter at promotion.** The ledger captures everything a
   researcher finds, labelled by status. Only *sourced* values cross into canon.
   Nothing is silently dropped.
3. **Primary source contains the value.** A secondary buys confidence, never the
   integer/fact. Derived quantities are recomputed, not copied.
4. **Pull-not-push.** Contributors/raters write only into a sandbox; infra reads.
5. **Prompt = versioned config.** Every prompt is registered and versioned; it
   changes only through the registry's deliberate revision loop, never by an
   agent mid-run.
6. **Structural-first.** All of JEM is structure now; numerics/detail deferred to
   later verified passes.
7. **Relationships are maintainer-reviewed.** Generation emits entities + a
   SUGGESTED edge table. Edges are never auto-applied.
8. **Generics are not entities.** `is_generic_rollup: true` nodes are never
   counted in entity totals.

## File manifest

| # | File | Kind | You do |
|---|------|------|--------|
| 01 | `01_SCHEMA_SPEC.md` | spec | read first |
| — | `validate_additions.py` | code | merge into `scripts/validate.py` |
| — | `classification.py` | code | add as `scripts/classification.py` |
| — | `legal_instruments.seed.yaml` | data | seed `data/legal_instruments/`, then verify |
| 02 | `02_CONSENSUS_HARNESS_SPEC.md` | spec | the shared research pipeline; C/K/report all cite it |
| 03 | `03_CURSOR_C_commercial_courts.md` | prompt | run in Cursor (generation) |
| 04 | `04_CURSOR_K_criminal_magistracy.md` | prompt | run in Cursor (generation) |
| 05 | `05_CURSOR_N_classification_counting.md` | prompt | run in Cursor (refactor + recount verify) |
| 06 | `06_CURSOR_report_publication.md` | prompt | run in Cursor (meta-provenance track) |
| 07 | `07_prompt_registry.yaml` | data | commit as `ledger/prompt_registry.yaml` |
| 08 | `08_public_inspection_prompt.md` | prompt | publish; anyone can run read-only |

## Apply / run order (dependencies matter)

```
S  Apply schema first ─────────────────────────────────────────────┐
   validate_additions.py + classification.py + legal_instruments    │  (C/K/N
   Run: validate.py --strict on the untouched corpus → must stay 0  │   validate
                                                                     │   against S)
        ┌────────────────────────────┬─────────────────────────────┘
        ▼                            ▼
   C  TN commercial courts      K  TN criminal magistracy   ← parallel-safe
      (Cursor, generation)         (Cursor, generation)        (disjoint scopes)
        └────────────┬───────────────┘
                     ▼
   N  Classification + counting reform  (recompute counts over enlarged corpus)
      + independent recount verify (second agent; counts must match)

   report-publication track (06) runs PARALLEL to C/K on the 44 — different
   question, same entities, same harness.
```

`S` is the gate before everything: C/K/N/report all validate against the new
schema, so it lands and stays green first. `N` runs last because it counts the
corpus C and K just enlarged.

## Scope of this batch (confirmed)

- Lattice generation is **TN-only**, **named** courts, **structural-only**.
- Verification pass 1 = the **contaminated 44** (43 countable + `lok_adalat_generic`,
  which is verified-but-not-counted). This is ~a quarter of JEM's full
  tribunal/regulator/ADR/consumer universe (~180+); the rest follow in later
  passes.
- Gap-discovery is live: the pass emits **suggested missing entities/edges**
  (e.g. `ifsca` + `ifsca AppealableTo sat`) as unverified, maintainer-reviewed.
