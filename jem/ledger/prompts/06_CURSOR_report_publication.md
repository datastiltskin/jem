# CURSOR — Track · Report-Publication (meta-provenance)

`prompt_id: report-publication-v1` · runs PARALLEL to the verify-trib-01 pass on
the same 44 (different question, same entities, same harness). Extend to all of
JEM in later passes.

## ROLE
Researcher-in-harness. For each entity, determine whether a body that should
publish reports actually does, and populate the `report_publication` block (S3).
Same intra-run consensus (file 02): liveness → researcher → verifier → gated
critic → reconcile → ledger.

## SCOPE (pass 1)
The 44 contaminated tribunal/regulator/ADR/consumer/arbitral entities (43
countable + `lok_adalat_generic`, whose block you populate but which is not
counted). This directly explains the `case_volume` gaps the verify pass is
probing: a body that doesn't publish is *why* its numbers are unsourceable, and
that is the correct finding, not a failure.

## Per entity — populate `report_publication`
- `publishes_reports`: yes | no | not_required | unknown
- `statutorily_required`: yes | no | unknown — **research the legal duty** (the
  parent Act's reporting/annual-report provision) and record
  `statutorily_required_source` (its OWN provenance — the section imposing it)
- `report_type`, `expected_cadence`
- `last_published` + `last_published_url` — the URL must PASS liveness and be the
  actual report document, not a homepage
- `data_as_of`, `source_type`, `source_url`

## "No reports found" is a verified finding
A negative is a *claim*, and proving it is where the critic earns its keep. The
researcher must document its search (own site publications page → parent ministry
archive → PIB / Lok Sabha references) across the bounded N≤3 retry, and write the
trail into `notes`: `"no reports found after checking X, Y, Z"`. A bare "none
found" is rejected by the critic. The documented trail is what makes the negative
credible and is retained in the ledger under `capture-and-label`.

## Statutory-duty edge
If a body is `statutorily_required: yes` but `publishes_reports: no`, that is a
first-class accountability finding (feeds ACS). Flag it clearly in `notes` — do
not soften it.

## Output
- `report_publication` block per entity (Option A path + block, OR a CSV keyed by
  entity_id if you prefer a single artifact for the maintainer to merge).
- Ledger JSONL per entity with the search trail and liveness results.
- `validate.py --entity` to exit 0 for any entity whose YAML you touch.

## Decision gate (surface)
- `statutorily_required` sometimes needs a fine reading of the parent Act. Where
  you can't confirm the duty from a primary provision, set `unknown` (not `no`) —
  absence of a found duty is not proof of no duty.
