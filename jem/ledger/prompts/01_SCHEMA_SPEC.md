# S — Schema foundation spec

Six changes to `scripts/validate.py` (+ two new files). All are additive and
back-compatible: existing entities keep validating. Apply, then run
`validate.py --strict` on the untouched corpus — it must still return 0 errors
before you generate anything.

## S1 · `CommercialCourt` entity type

Add `"CommercialCourt"` to `ENTITY_TYPES`. Justified by the Commercial Courts
Act 2015: district-level commercial courts are constituted by notification as
courts equivalent to district courts. They are standalone judicial bodies →
their own type.

**Not** typed CommercialCourt: the HC Commercial Division and Commercial
Appellate Division. Those are constituted by the Chief Justice from among HC
judges — divisions *of* the parent High Court, not separate institutions. They
are represented as commercial jurisdiction/appellate capacity of the parent HC
(routing edges to `hc_madras`), not as new nodes. Only five HCs have original
civil jurisdiction (Bombay, Calcutta, Delhi, Himachal Pradesh, Madras), so this
only arises for Madras in the TN batch.

## S2 · `pecuniary_jurisdiction` block

New top-level optional block on `EntityModel`. Carries the money threshold that
routes a matter — a *property* of the court. Routing itself stays in edges (S is
the property; edges are the relation — both, per G2).

```yaml
pecuniary_jurisdiction:
  specified_value_min: 300000      # ₹3 lakh floor for commercial courts (2018 amendment)
  specified_value_max: null
  currency: INR
  is_unlimited: false
  basis: { instrument_id: commercial_courts_act_2015, provision: "s.2(1)(i)" }   # legal-basis ref (S4)
  notes: null
```

## S3 · `report_publication` block

New optional block on `EntityModel`. Meta-provenance: does a body that should
publish reports actually do so. Feeds ACS and explains why some `case_volume`
gaps are the correct answer. `"no"` is a *verified* finding, not a blank.

```yaml
report_publication:
  publishes_reports: yes | no | not_required | unknown
  statutorily_required: yes | no | unknown
  statutorily_required_source: https://...        # its OWN provenance (the duty)
  report_type: annual_report | statistics | ...
  last_published: 'YYYY-MM-DD' | null
  last_published_url: https://...                 # must pass liveness
  expected_cadence: annual | quarterly | ...
  data_as_of: 'YYYY-MM-DD'
  source_type: AnnualReport | GoIWebsite | OfficialReport | ...
  source_url: https://...
  notes: "no reports found after checking X, Y, Z"
```

## S4 · Legal-basis reference + instrument registry (temporal layer)

The bounded temporal design — **not** bitemporality. Transition dates live once,
in a registry, referenced by id, never copied into N entity files.

**New dataset** `data/legal_instruments/` — each instrument defined + verified
once (see `legal_instruments.seed.yaml`). Kept OUT of entity counts (it is
reference data, not a judiciary entity).

**New reusable ref object** `LegalBasisRef`:

```yaml
{ instrument_id: bnss_2023, provision: "ss.21-23", status: in_force,
  effective_from: '2024-07-01', repealed_on: null, source: https://... }
```

`statutory_basis` and `constitutional_basis` on **both** `EntityModel` and
`RelationshipModel` become a **string-or-struct union**:
`Union[str, LegalBasisRef, List[LegalBasisRef]]`. Existing string values stay
valid (no mass rewrite). New entities use the struct. A superseded instrument is
carried alongside the in-force one, e.g. a criminal court:

```yaml
statutory_basis:
  - { instrument_id: bnss_2023, provision: "ss.21-23", status: in_force,  effective_from: '2024-07-01' }
  - { instrument_id: crpc_1973, provision: "ss.6-29",  status: superseded, repealed_on: '2024-07-01' }
```

Backfill order: new entities (C/K) use structs immediately; existing files stay
strings; opportunistic backfill starts with the CrPC→BNSS criminal-adjacent set.

## S5 · Two-axis classification + generic flag

Classification is **derived from `type`** via one committed map (see
`classification.py`) — no per-entity field, no drift. Two orthogonal axes:

- **nature:** `institution` | `personnel`
- **function:** `judicial` | `quasi_judicial` | `support_apparatus`

"Judicial personnel" = `personnel × judicial`, derived, never a bucket. The old
"non-judicial" bucket is renamed `support_apparatus` (executive/legislative
enabling ecosystem). A small `classification_override: {nature, function}` is
allowed only for genuinely ambiguous types (`StatutoryBodyNotConstituted`,
`ProposedBody`, and case-by-case `LegalOfficer`/`ADRBody`), and must be justified
in `data_quality_notes`.

New field on `EntityModel`: `is_generic_rollup: Optional[bool] = False`.
Generics (`*_generic`) set it true and are **excluded from all entity counts**.

## S6 · Relationship legal-basis (mirror of S4)

`RelationshipModel.statutory_basis` / `.constitutional_basis` take the same
string-or-struct union, so a routing edge grounded on BNSS (formerly CrPC)
carries its own transition.

---

## Apply notes

- `validate_additions.py` contains the new Pydantic models + the enum edit +
  field additions. Merge its blocks into `scripts/validate.py` at the marked
  points; add `from typing import Union` to the imports.
- `classification.py` is a standalone module imported by `validate.py` (to assert
  every `type` is mapped), and by `derive.py`/`build.py` (to compute counts).
- `legal_instruments.seed.yaml` seeds the registry. Every instrument is
  `data_quality: partial` until a primary india-code URL is verified per row
  (the transition *dates* are well-established; the *source URLs* need the same
  liveness + primary-source check as any cell).
- After applying: `validate.py --strict` on the untouched corpus → expect 0. Only
  then generate.
