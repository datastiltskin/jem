# RCA: Tiruchirappalli HC bench hallucination (May to Jun 2026)

**Status:** Resolved (entity removed, config cleaned, TN routing corrected)  
**Severity:** Major, a fabricated institution in a public structural dataset  
**Detection:** Human maintainer with domain knowledge, not CI  
**License:** CC0 (this document)

## Summary

JEM briefly contained `hc_madras_bench_tiruchirappalli`, a non-existent
permanent bench of the Madras High Court. Madras HC has one permanent bench,
at Madurai, established 2004. Tiruchirappalli has a district court only.

The error came in through AI-assisted bulk corpus expansion (Path A), passed all
automated structural validation, and then partially survived a fix as config
drift until Jun 2026.

## Ground truth

| Claim | Fact |
|-------|------|
| Madras HC permanent benches | Madurai only |
| `hc_madras_bench_tiruchirappalli` | Never existed |
| `tn_district_court_tiruchirappalli` | Valid, a district court rather than an HC bench |
| Madurai bench `created_year` | 2004, not 1948 |

Primary sources for the Madurai bench: Madras High Court (Establishment of a
Permanent Bench at Madurai) Order, 2004, and the 2009 amendment restoring some
districts to the principal seat.

## Timeline

| Date | Commit / event |
|------|----------------|
| 2026-05-18 | `914d2dc`: full corpus restore introduces the Trichy bench in `hc_benches_config.py`, generates entity YAML, routes 10 central TN districts |
| 2026-05-19 | `c3be2a6`: entity YAML deleted, `hc_benches_config.py` not updated, so config drift begins |
| 2026-05-19 to 06-15 | Graph has 13 benches, config lists 14, generators still reference Trichy, CI green |
| 2026-06-15 | Checklist audit flags the config/graph drift |
| 2026-06-15 | `fa00717` plus a maintainer session: config cleaned, generator notes fixed, TN cascade routing corrected |

## Architecture: two pipelines

### Path A, the YAML corpus (the incident path)

```
hc_benches_config.py
  → generate_v1_states_bundle.py
  → entity YAML + relationship YAML
  → validate.py → derive.py → build.py → graph.json
```

### Path B, fetcher and verifier (not involved)

```
GoI source text
  → fetcher (extraction_v1.md)
  → staging_records (SQLite)
  → verifier (verification_v1.md)
  → expert portal (needs_review)
```

Path B requires `verbatim_excerpt` in the source and rejects invented bodies.
Path A had no equivalent institution-existence gate at the time of the incident.

## Amplification chain

1. Single tuple in `HC_BENCHES_DEF`
2. Generator writes `hc_madras_bench_tiruchirappalli.yaml`
3. `TN_DISTRICT_TO_BENCH` maps central TN to the Trichy bench
4. `tn_relationships.yaml` gets AppealableTo and AdministrativeSupervision edges
5. All refs resolve, so `validate_graph_refs.py` passes

### Telltales in the phantom entity (git: `914d2dc`)

- `created_year: 1948`, the parent HC era rather than a bench order
- `data_quality: partial` with generic Constitution and India Code URLs
- No gazette or hcmadras.tn.nic.in citation for a Tiruchirappalli bench

Compare `hc_madras_bench_madurai.yaml`, which cites the 2004 Order and the 2009 amendment.

## Decision gate matrix

| Gate | Catches | Trichy case |
|------|---------|-------------|
| `validate.py` | Schema, enums | Passed |
| `validate.py --strict` | Missing source URLs | Passed, on generic URLs |
| `validate_graph_refs.py` | Dangling IDs | Passed |
| CI (`.github/workflows/validate.yml`) | The above, on PR | Green |
| `derive.py` / `build.py` | Scores, merge | Passed |
| `jem_build.sh` human gates | Infra sessions | Not used for bulk data |
| Session 4A verifier | Excerpt in source | Path A only, so no |
| Expert portal | Human review queue | Path A only, so no |
| Maintainer domain review | Institutional truth | The final catch |
| Config against disk sync test | Drift | Not in CI (done ad hoc Jun 15) |

## Secondary failure: the repair cascade

After the Trichy removal, 10 central TN districts were wrongly routed to
`hc_madras_bench_madurai` instead of `hc_madras`, the principal seat. Fixed in a
Jun 2026 maintainer session. Some relationship ids may still contain
`hc_madras_bench_madurai` in the name while their targets point at `hc_madras`.
That is a cosmetic inconsistency only.

## Jun 2026 phantom audit (post-fix)

A manual audit across 1,103+ entities found:

- One fabricated institution: the Trichy HC bench, since removed
- Phantom script IDs: `hc_mizoram` and `hc_arunachal_pradesh` in the generator.
  They never existed as entities, since AR and MZ use Gauhati HC plus benches. Removed.
- Intentional scaffolds rather than phantoms: `gstat`, `gstat_bench_generic`, and
  the `*_generic` labour and VAT scaffolds, all `Not_Constituted` or `Partial_Operational`

## Learnings

1. Structural CI is not factual CI. Zero errors means consistent, not true.
2. Config is data. Changes to `hc_benches_config.py` need the same rigor as YAML.
3. Partial deletes create drift, as with entity-only removal without a config update.
4. Plausible geography camouflages fiction. The TN two-zone split mimics real HC patterns.
5. Repair can introduce new errors, so re-check routing after removing fiction.
6. Path B rules must apply to Path A. No new institution without a primary source.

## Mitigations

See [`DATA_QUALITY_GATES.md`](DATA_QUALITY_GATES.md) for current status.

| # | Control | Target |
|---|---------|--------|
| 1 | `tests/test_institutions.py`, asserting `HC_BENCHES_DEF` == bench YAML == `HighCourtBench` entities | CI |
| 2 | `scripts/audit_graph_semantics.py`, comparing district routing maps against relationship packs | Release tags |
| 3 | Schema rule: a new `HighCourtBench` requires a bench-specific `statutory_basis` or gazette URL | `validate.py` (planned) |
| 4 | Generator checklist: entity, config, routing, and docs in one PR | Process |
| 5 | v1.1 roster audit: HC benches and tribunal benches against official sites | Maintainer |
| 6 | `data_quality` policy: generator output defaults to `partial`, and `verified` is human-only | Policy |

## References

- `jem/scripts/hc_benches_config.py`, bench ground truth for generators
- `jem/.claude/prompts/verification_v1.md`, Path B verifier rules
- `jem/docs/ENTITY_BUILD_ROADMAP.md`, structural release planning and category tracking
- `MASTER_CHECKLIST.md`, v1.1 structural integrity items
- Blog: [When the graph is green but wrong](https://friedso.com/blog/jem-when-the-graph-is-green-but-wrong/)

## Changelog

| Date | Change |
|------|--------|
| 2026-07-07 | Initial RCA published |
