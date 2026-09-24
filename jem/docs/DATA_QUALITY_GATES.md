# JEM data quality gates

What the automated checks guarantee, and what they do not.

## Guarantee levels

| Level | Meaning | Tools |
|-------|---------|-------|
| L0 Schema | YAML matches Pydantic models | `validate.py` |
| L1 Referential | Relationship endpoints exist | `validate_graph_refs.py` |
| L2 Derived | Scores computable | `derive.py` |
| L3 Artifact | `graph.json` builds | `build.py` |
| L4 Institutional | Bodies exist in law / official rosters | Partial: maintainer audit plus `test_institutions` |
| L5 Sourced | Every claim has a primary source | Policy, with a strict URL check only |

The public claim is that JEM v1.x is L0 to L3 certified on every PR. L4 and L5 are
not fully automated.

## Current CI (`.github/workflows/validate.yml`)

- `validate.py --strict`
- `derive.py`
- `validate_graph_refs.py` (not `--strict` by default in CI)

Run institution checks locally or in extended QA:

```bash
cd jem
pytest tests/test_institutions.py -v
python3 scripts/audit_graph_semantics.py
```

## Path A session checklist (maintainers)

After any bulk entity or routing change:

```bash
cd jem
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py --strict
python3 scripts/derive.py
python3 scripts/build.py
pytest tests/test_institutions.py -v
python3 scripts/audit_graph_semantics.py
```

Before adding a new institution id, especially a `*_bench_*` one:

- [ ] A primary source URL names this body specifically
- [ ] Config updated if generator-driven
- [ ] Routing maps updated if district appellate paths change
- [ ] `ENTITY_BUILD_ROADMAP.md` and the checklist updated

## Path B rules (apply these to Path A for new institutions)

From `verification_v1.md`:

- No field without source support
- Reject an invented or wrong `entity_name`
- `verbatim_excerpt` must appear in the source (Path B)
- The Path A analogue is a bench-specific gazette or official roster URL in `sources[]`

## Planned automation

| Item | Status |
|------|--------|
| `test_institutions.py`, checking HC_BENCHES_DEF against disk and graph | Implemented |
| `audit_graph_semantics.py`, checking district routing against relationship YAML | Implemented |
| `validate.py` bench-specific source requirement | Planned |
| CI `--strict` on graph refs | Planned |

## Known intentional non-institutions

These are scaffolds, not phantoms:

- `gstat_bench_generic`, gated on GSTAT constitution
- `state_*_generic`, template entities with `state_data`
- `drt_city_n`, a documented placeholder with no entity file

## Report a structural error

[GitHub data correction issue](https://github.com/datastiltskin/jem/issues/new?template=data_correction.yml)

See also: [`RCA_AI_HALLUCINATION_TRICHY_BENCH.md`](RCA_AI_HALLUCINATION_TRICHY_BENCH.md)
