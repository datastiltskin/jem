## Summary

<!-- What does this PR change? For v0.9 community PRs: data-quality upgrades only unless maintainers approved wider scope. -->

## Entity / files touched

<!-- e.g. jem/data/entities/_generated/states/tn/tn_district_court_chennai.yaml -->

- [ ] I did **not** add new entity `id`s or new relationship topology *(unless I am a maintainer)*
- [ ] I did **not** set `data_quality: verified` or `derived.scores_validated: true` *(maintainers only)*

## Primary sources

<!-- Link every factual change to indiacode, gazette, DoJ, NJDG URL, judgment, or official ministry page -->

| Field changed | Source URL | Accessed date |
|---------------|------------|---------------|
| | | |

## Local checks (required for `jem/data/**` changes)

Run from `jem/`:

```bash
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py
python3 scripts/derive.py
```

- [ ] `validate.py --strict` passes (0 errors)
- [ ] I ran `derive.py` if I changed fields that affect scores
- [ ] I did **not** hand-edit `jem/data/derived/` or commit a rebuilt `graph.json` unless maintainers asked for a release build

## Out of scope (confirm none of these)

- [ ] No case outcomes or party-specific results
- [ ] No individual judge names or conduct opinions
- [ ] No editorial commentary without structural sourcing

## Type of change

- [ ] Data-quality upgrade (community)
- [ ] Maintainer: structural / schema / tooling
- [ ] Maintainer: release (`graph.json` rebuild)
- [ ] Docs only

## Additional notes

<!-- Optional: link to related issue # -->
