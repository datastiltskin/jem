# JEM data seeds

Authoritative YAML for v1 session passes. `generate_v1_states_bundle.py` copies
`seeds/entities/**` → `entities/_generated/**` and `seeds/relationships/*` for ADR
when present, instead of emitting stubs.

Edit seeds when enriching entities; run `python3 scripts/generate_v1_states_bundle.py`
to refresh `_generated/` outputs. Daily work: `scripts/safe_pipeline.sh` only.
