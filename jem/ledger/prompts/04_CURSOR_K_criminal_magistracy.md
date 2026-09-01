# CURSOR — Track K · TN Sub-District Criminal Magistracy

`prompt_id: cursor-K-criminal-v1` · run AFTER schema S is applied and green.
Parallel-safe with Track C (disjoint file scopes).

## ROLE
Co-maintainer, generation. Entity YAML only + SUGGESTED edge table. Same harness
(file 02), same no-invented-data discipline, same do-not-auto-apply on edges.

## SCOPE (TN only, judicial magistracy, structural-first)
Generate, for Tamil Nadu, the judicial criminal courts BELOW the District &
Sessions Court:

- Chief Judicial Magistrate — `cjm_{district}`
- Additional Chief Judicial Magistrate — `acjm_{district}` (where notified)
- Judicial Magistrate First Class — `jmfc_{district}` (named, per district)
- Judicial Magistrate Second Class — `jm2_{district}` (where they exist)

`type: SubordinateCriminalCourt`; cluster `subordinate_courts`; level `State`;
named per TN district. **Executive magistrates (District Magistrate / SDM under
BNSS) are OUT of this track** — they classify as support_apparatus and belong to
a separate pass.

### Legal basis — BNSS primary, CrPC retained (temporal)
Ground the court hierarchy and magistrate powers on **BNSS 2023 ss.21–23**
(classes of criminal courts; sentencing powers), with CrPC retained as the
superseded predecessor. Every criminal-court entity carries a `statutory_basis`
struct LIST:

```yaml
statutory_basis:
  - { instrument_id: bnss_2023, provision: "ss.21-23", status: in_force,   effective_from: '2024-07-01' }
  - { instrument_id: crpc_1973, provision: "ss.6-29",  status: superseded, repealed_on: '2024-07-01' }
```

### Criminal "quantum" = sentencing power, not money
The routing quantum for criminal courts is offence-gravity / sentencing ceiling
(BNSS s.23), NOT a pecuniary value. Do **not** use `pecuniary_jurisdiction`.
Capture the sentencing ceiling in `data_quality_notes` (e.g. "JMFC: imprisonment
up to 3 years and/or fine up to ₹50,000 per BNSS s.23") and encode routing in the
suggested edges. A structured criminal-jurisdiction block is deferred to the
detail phase — flag it, don't build it now.

Structural-first: **no `case_volume`, no `judge_strength`.**

## SUGGESTED edges (table only)
- `jmfc_{d}` / `jm2_{d}` / `cjm_{d}` → `AppealableTo` → Sessions/District &
  Sessions Court of that district (category `appellate_chain`, basis BNSS s.-),
  routed by offence gravity.
- `AdministrativeSupervision` from the relevant High Court bench (`hc_madras` or
  its Madurai bench per territorial jurisdiction) → note only.
- Table columns: `source | rel_type | target | category | basis | evidence_url | confidence`.

## Per-entity protocol (harness-embedded)
Primary = BNSS on india-code + TN/Madras HC notifications establishing the named
courts. Liveness-gate → researcher → verifier → gated critic (challenge: is this
court actually established? is the sentencing ceiling BNSS-current or a CrPC
carry-over misstated?) → reconcile → ledger. Capture-and-label; only `sourced`
into YAML.

## Output
- `### PATH: data/entities/_generated/states/tn/criminal/{id}.yaml` + full YAML.
- Suggested-edges table.
- Ledger JSONL per file. `validate.py --entity` to exit 0. No build.py.

## Decision gates (surface, do not resolve)
- Confirm the named TN districts and which magistrate classes are actually
  notified in each — do not emit a court you cannot tie to a notification.
- The temporal `statutory_basis` struct is new; if any existing TN criminal
  entity already exists as a string, leave it (backfill is a separate pass).
