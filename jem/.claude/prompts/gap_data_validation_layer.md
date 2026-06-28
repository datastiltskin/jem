# JEM — Gap / tribunal data validation layer (read-only)

**Mode: VALIDATION ONLY.** Produce a markdown audit report. Do **not** edit YAML, graph.json, or any repository files.

Working directory: `/Users/user/Documents/repo/jem`. Read `jem/CLAUDE.md`, `entity_schema.yaml`, and `jem/.claude/outputs/gap_clog_verification.md` (manual baseline).

## Scope — verify every claim added Jun 2026

### A. `gap_spillover` entries (primary + partial tags)

Read gap objects in:

- `jem/data/entities/_generated/backbone/gstat.yaml`
- `jem/data/entities/_generated/backbone/gstat_bench_generic.yaml`
- `jem/data/entities/_generated/backbone/sat.yaml`
- `jem/data/entities/_generated/backbone/ngt.yaml`
- `jem/data/entities/_generated/backbone/gram_nyayalaya_generic.yaml`

For each `gap_spillover` item: confirm `metric_note` against `source_url`. Mark **verified** | **partial** | **remove** | **downgrade_to_partial**. Fetch primary sources (Gazette, greentribunal.gov.in, CBIC, indiankanoon, DoJ) — not tax blogs alone for **verified**.

Priority checks:

1. GSTAT 8,100+ / 2,800+ figure — locate CBIC Compliance Audit primary URL or mark **partial**
2. GSTAT HC writ cases (Delhi Mahanadi Exporttek, Telangana Upakar Infra) — confirm order exists
3. NGT 5,698 pendency (30 Apr 2026) — greentribunal.gov.in dashboard
4. SAT quorum → HC writ spillover (Business Standard Feb 2024)
5. Gram Nyayalaya → district court 4.5 crore pendency (SC NFSFJ Aug 2024)

### B. Tribunal appellate edges

- `jem/data/relationships/tribunal_appellate_completion_jun2026.yaml`
- `jem/data/relationships/tribunal_appellate_batch2_jun2026.yaml`

Spot-check every `statutory_basis` section number on India Code / official statute repository. Flag unsupported or wrong-section edges for removal.

### C. Structural gaps still missing enrichment

Entities with `structural_gap.flag: true` but thin notes:

- aft, nmc, cit_appeals_generic, lokpal_india, state_police_generic, hc_allahabad, hc_patna, py_lokayukta, arbitration_council_india (aci), mediation_council_india

Note any documented spillover to HC/SC/district courts with sources — **report only**, do not write YAML.

### D. Merged / dedup entities

- tnerc → serc_tn; rera_tn/rj/up/wb → canonical rera entities

Confirm Merged status and no duplicate appellate edges in `graph.json` (read repo-root `graph.json` meta + sample rel IDs).

### E. UI / build pipeline

Confirm `gap_spillover` flows to `graph.json` under entity `gaps[]`. Read `jem/scripts/build.py` gap flattening and `jem/web/src/gapDisplay.js`.

## Output format (markdown)

1. **Executive summary** — counts verified / partial / remove
2. **gap_spillover table** — entity, gap_id, claim, verdict, primary URL
3. **Tribunal edges table** — rel id, verdict, correction if needed
4. **Missing spillover opportunities** — gaps with HC clog evidence not yet in YAML
5. **Claims to remove or downgrade** — with reason
6. **Recommended YAML edits** — bullet list for human/agent apply (no auto-edit)
7. **Pipeline** — state whether `validate.py` / `validate_graph_refs.py` would pass (read files; do not assume)

Use web search and fetch for India Code, Gazette, greentribunal.gov.in, cbic-gst.gov.in, efiling.gstat.gov.in, DoJ, Lok Sabha, SC/HC judgments.
