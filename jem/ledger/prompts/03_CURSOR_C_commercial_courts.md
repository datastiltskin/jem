# CURSOR — Track C · TN Commercial Courts

`prompt_id: cursor-C-commercial-v1` · run AFTER schema S is applied and green.

## ROLE
Co-maintainer, generation. Emit **entity YAML only** + a **SUGGESTED edge table**.
Do not auto-apply relationships. Do not edit `derived/`, `graph.json`, or
`graph.css`. Run inside the intra-run consensus harness (file 02): every fact is
liveness-gated → researched → verified → (gated) critiqued → reconciled →
ledgered. No fact enters a file without a primary source that contains it.

## SCOPE (TN only, structural-first)
Generate, for Tamil Nadu:

1. **District-level Commercial Courts** — `type: CommercialCourt` — ONLY in
   districts where TN has actually *notified* a commercial court. Research the
   constitution: TN government notifications + Madras HC. Do NOT emit one per
   district by default; emit only notified courts, each citing its notification.
   - id: `tn_commercial_court_{district}`
   - `pecuniary_jurisdiction`: `specified_value_min: 300000`, `currency: INR`,
     `basis: {instrument_id: commercial_courts_act_2015, provision: "s.2(1)(i)"}`
     (₹3 lakh floor since the 2018 amendment)
   - `statutory_basis`: struct list referencing `commercial_courts_act_2015`
     (+ `commercial_courts_amendment_2018`), `status: in_force`
   - cluster: `subordinate_courts`; level_of_government: `State`
2. **Commercial Appellate Courts** at district-judge level — same type, id
   `tn_commercial_appellate_court_{district}` — only where notified.
3. **Madras HC Commercial Division + Commercial Appellate Division** — Madras HC
   HAS ordinary original civil jurisdiction, so these exist. Do **NOT** create
   standalone nodes. Represent them as commercial/appellate *capacity of*
   `hc_madras`, surfaced only as SUGGESTED edges (below). If you believe a node
   is warranted, flag it as a decision gate — do not create it.

Structural-first: **no `case_volume`, no `judge_strength`.** Those are deferred.
`data_quality: partial` minimum; `unverified_fields[]` for anything without a
primary GoI URL.

## SUGGESTED edges (table only — never written to relationship files)
- `tn_commercial_court_{d}` → `AppealableTo` → the Commercial Appellate Division
  of `hc_madras` (represent as edge to `hc_madras`, category `appellate_chain`,
  note "Commercial Appellate Division"), OR → `tn_commercial_appellate_court_{d}`
  where a district appellate court is notified — resolve per the notification.
- `tn_commercial_court_{d}` → `EstablishedUnder` → (statutory_ref) — note only.
- Emit as a markdown table: `source | rel_type | target | category | basis | evidence_url | confidence`.

## Gap-discovery
If research surfaces a commercial-jurisdiction body not in the graph, emit it as
a suggested entity + suggested edge (unverified, cited), per harness §gap-discovery.

## Per-entity protocol (harness-embedded)
For every non-obvious field: liveness-check the source URL → researcher extracts
from primary (TN notification, Madras HC, Commercial Courts Act on india-code) →
verifier confirms the value is at the claimed URL and the source is eligible →
critic (gated) challenges homepage-vs-document and whether the court is actually
notified → reconcile → append to `ledger/runs/`. Capture-and-label: keep failed/
partial finds in the ledger; only `sourced` fields go into the YAML.

## Output
- Option A: `### PATH: data/entities/_generated/states/tn/commercial/{id}.yaml`
  then full YAML.
- Suggested-edges markdown table at the end.
- Ledger JSONL appended per file.
- Run `python3 scripts/validate.py --entity <path>` per file to exit 0.
  Do not run build.py.

## Decision gates (surface, do not resolve)
- G1-sub: are Madras HC Commercial/Appellate Divisions edges-to-`hc_madras`
  (default) or do you want explicit division nodes? Proceed edges-only; flag.
- Which TN districts are actually notified — list what you found + sources; if a
  claimed court can't be confirmed from a notification, mark it suggested-unverified,
  do NOT emit a canonical entity.
