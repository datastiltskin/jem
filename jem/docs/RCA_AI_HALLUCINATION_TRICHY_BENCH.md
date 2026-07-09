# RCA: Tiruchirappalli HC bench hallucination (May–Jun 2026)

**Status:** Resolved (entity removed; config cleaned; TN routing corrected)  
**Severity:** Major — fabricated institution in public structural dataset  
**Detection:** Human maintainer (domain knowledge), not CI  
**License:** CC0 (this document)

## Summary

JEM briefly contained `hc_madras_bench_tiruchirappalli` — a **non-existent**
permanent bench of the Madras High Court. Madras HC has **one** permanent bench
at **Madurai** (est. 2004). Tiruchirappalli has a district court only.

The error entered via AI-assisted bulk corpus expansion (Path A), passed all
automated structural validation, and partially survived a fix as **config drift**
until Jun 2026.

## Ground truth

| Claim | Fact |
|-------|------|
| Madras HC permanent benches | **Madurai only** |
| `hc_madras_bench_tiruchirappalli` | **Never existed** |
| `tn_district_court_tiruchirappalli` | **Valid** (district court, not HC bench) |
| Madurai bench `created_year` | **2004** (not 1948) |

Primary sources for Madurai bench: Madras High Court (Establishment of a
Permanent Bench at Madurai) Order, 2004; 2009 amendment restoring some districts
to principal seat.

## Timeline

| Date | Commit / event |
|------|----------------|
| 2026-05-18 | `914d2dc` — full corpus restore introduces Trichy bench in `hc_benches_config.py`, generates entity YAML, routes 10 central TN districts |
| 2026-05-19 | `c3be2a6` — entity YAML **deleted**; `hc_benches_config.py` **not updated** → config drift begins |
| 2026-05-19 – 06-15 | Graph has 13 benches; config lists 14; generators still reference Trichy; CI green |
| 2026-06-15 | Checklist audit flags config/graph drift |
| 2026-06-15 | `fa00717` + maintainer session — config cleaned, generator notes fixed, TN cascade routing corrected |

## Architecture: two pipelines

### Path A — YAML corpus (incident path)

```
hc_benches_config.py
  → generate_v1_states_bundle.py
  → entity YAML + relationship YAML
  → validate.py → derive.py → build.py → graph.json
```

### Path B — Fetcher / verifier (not involved)

```
GoI source text
  → fetcher (extraction_v1.md)
  → staging_records (SQLite)
  → verifier (verification_v1.md)
  → expert portal (needs_review)
```

Path B requires `verbatim_excerpt` in source and rejects invented bodies.
Path A had no equivalent institution-existence gate at the time of the incident.

## Amplification chain

1. Single tuple in `HC_BENCHES_DEF`
2. Generator writes `hc_madras_bench_tiruchirappalli.yaml`
3. `TN_DISTRICT_TO_BENCH` maps central TN → Trichy bench
4. `tn_relationships.yaml` AppealableTo / AdministrativeSupervision edges
5. All refs resolve → `validate_graph_refs.py` passes

### Telltales in the phantom entity (git: `914d2dc`)

- `created_year: 1948` (parent HC era, not bench order)
- `data_quality: partial` with generic Constitution / India Code URLs
- No gazette or hcmadras.tn.nic.in citation for a Tiruchirappalli bench

Compare: `hc_madras_bench_madurai.yaml` cites 2004 Order and 2009 amendment.

## Decision gate matrix

| Gate | Catches | Trichy case |
|------|---------|-------------|
| `validate.py` | Schema, enums | ✅ Passed |
| `validate.py --strict` | Missing source URLs | ✅ Passed (generic URLs) |
| `validate_graph_refs.py` | Dangling IDs | ✅ Passed |
| CI (`.github/workflows/validate.yml`) | Above on PR | ✅ Green |
| `derive.py` / `build.py` | Scores, merge | ✅ Passed |
| `jem_build.sh` human gates | Infra sessions | ❌ Not used for bulk data |
| Session 4A verifier | Excerpt in source | ❌ Path A only |
| Expert portal | Human review queue | ❌ Path A only |
| Maintainer domain review | Institutional truth | ✅ **Final catch** |
| Config ↔ disk sync test | Drift | ❌ **Not in CI** (ad hoc Jun 15) |

## Secondary failure: repair cascade

After Trichy removal, 10 central TN districts were wrongly routed to
`hc_madras_bench_madurai` instead of `hc_madras` (principal seat). Fixed in
Jun 2026 maintainer session. Some relationship **ids** may still contain
`hc_madras_bench_madurai` in the name while **targets** point to `hc_madras` —
cosmetic inconsistency only.

## Jun 2026 phantom audit (post-fix)

Manual audit across 1,103+ entities found:

- **One fabricated institution:** Trichy HC bench (removed)
- **Phantom script IDs:** `hc_mizoram`, `hc_arunachal_pradesh` in generator
  (never existed as entities; AR/MZ use Gauhati HC + benches) — removed
- **Intentional scaffolds (not phantoms):** `gstat`, `gstat_bench_generic`,
  `*_generic` labour/VAT scaffolds — `Not_Constituted` or `Partial_Operational`

## Learnings

1. **Structural CI ≠ factual CI** — 0 errors means consistent, not true.
2. **Config is data** — `hc_benches_config.py` changes need the same rigor as YAML.
3. **Partial deletes create drift** — entity-only removal without config update.
4. **Plausible geography camouflages fiction** — TN two-zone split mimics real HC patterns.
5. **Repair can introduce new errors** — re-check routing after removing fiction.
6. **Path B rules must apply to Path A** — no new institution without primary source.

## Mitigations

See [`DATA_QUALITY_GATES.md`](DATA_QUALITY_GATES.md) for current status.

| # | Control | Target |
|---|---------|--------|
| 1 | `tests/test_institutions.py` — `HC_BENCHES_DEF` == bench YAML == `HighCourtBench` entities | CI |
| 2 | `scripts/audit_graph_semantics.py` — district routing maps vs relationship packs | Release tags |
| 3 | Schema rule: new `HighCourtBench` requires bench-specific `statutory_basis` or gazette URL | `validate.py` (planned) |
| 4 | Generator checklist: entity + config + routing + docs in one PR | Process |
| 5 | v1.1 roster audit: HC benches, tribunal benches vs official sites | Maintainer |
| 6 | `data_quality` policy: generator output defaults `partial`; `verified` human-only | Policy |

## References

- `jem/scripts/hc_benches_config.py` — bench ground truth for generators
- `jem/.claude/prompts/verification_v1.md` — Path B verifier rules
- `jem/docs/ENTITY_BUILD_ROADMAP.md` — structural release planning and category tracking
- `MASTER_CHECKLIST.md` — v1.1 structural integrity items
- Blog: [When the graph is green but wrong](https://friedso.com/blog/jem-when-the-graph-is-green-but-wrong/)

## Changelog

| Date | Change |
|------|--------|
| 2026-07-07 | Initial RCA published |
