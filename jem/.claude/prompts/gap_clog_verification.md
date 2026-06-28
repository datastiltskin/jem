# JEM — Verify new tribunal/gap data + research HC clog from institutional gaps

You are working in `/Users/user/Documents/repo/jem`. Read `jem/CLAUDE.md`, `entity_schema.yaml`, and these files:

## A. Verify (correct or flag for removal)
1. `jem/data/relationships/tribunal_appellate_completion_jun2026.yaml`
2. `jem/data/relationships/tribunal_appellate_batch2_jun2026.yaml`
3. Entity YAMLs with recent `structural_gap` / `gap_resolution_note`:
   - gstat.yaml, gstat_bench_generic.yaml
   - atfe.yaml, fema_adjudicating_authority_generic.yaml, fema_special_director_generic.yaml
   - environmental_appellate_authority_generic.yaml, water/air/ep/forest act generics
   - gram_nyayalaya_generic.yaml, ngt.yaml, sat.yaml, ncdrc.yaml
4. Merged entities: tnerc.yaml, rera_tn/rj/up/wb.yaml

For each edge or gap claim: confirm statutory section exists on India Code or official GoI source. Mark **verified** | **partial** | **remove** with URL.

## B. Research — HC clog / writ load from tribunal gaps (PRIMARY SOURCES REQUIRED)

### Priority 1: GSTAT not fully operational → GST cases at High Courts
Search for: writ petitions, appeals pending at High Courts because GSTAT/state benches not functional; Mohit Minerals; ~8100 cases figure in GSTAT Procedure Rules 2025; CBIC/DoR statements; HC orders staying recovery pending GSTAT.

### Priority 2: Similar patterns (find documented cases with numbers if available)
- SAT single bench / quorum crisis → SC/HC backlog
- NGT below statutory strength → disposal delays
- Gram Nyayalaya under-rollout → district court load
- ATFE/FEMA — cases at HC under s.19 vs tribunal
- APTEL electricity disputes — any documented HC interim load before APTEL disposal
- IPAB abolition → direct HC patent/TM appeals
- Any other entity in JEM with `structural_gap.flag: true` where primary sources document spillover to HCs or SC

For each finding, capture:
- **metric** (case count, pendency, disposal days — only if sourced)
- **court/body affected**
- **gap cause** (which JEM entity)
- **primary source** (URL, report title, date)
- **data_quality**: verified only with GoI/HC/SC primary; else partial

## C. Write back to JEM (YAML only)

1. Update `gap_description` and add field `gap_spillover` (nested under each gap object) when spillover is documented:
   ```yaml
   gap_spillover:
     affected_body: hc_delhi  # or high_courts_all, supreme_court_india, etc.
     spillover_type: writ_load | appellate_backlog | interim_stay_cluster
     metric_note: "verbatim short quote or number from source"
     source_url: ...
     source_label: ...
     data_as_of: YYYY-MM-DD
   ```
2. Add `gap_resolution_note` to any structural_gap entry still missing it (aft, nmc, cit_appeals_generic, lokpal, etc.) — sourced only.
3. Fix any **remove** findings from section A (edit YAML to correct statutory_basis or delete unsupported claims).
4. Do NOT invent case counts. If no number found, describe qualitatively with source.
5. Run from `jem/`: `python3 scripts/validate.py` and fix until exit 0.
6. Run `python3 scripts/validate_graph_refs.py`, `python3 scripts/build.py` (writes repo-root graph.json).

## D. Output markdown report to stdout

Sections:
1. Verification summary (edges/gaps checked, pass/fail counts)
2. GSTAT → HC clog evidence table
3. Other spillover findings table
4. Files modified list
5. Claims **not** found in primary sources (do not add)

Use web search / fetch India Code, Gazette, greentribunal.gov.in, cbic-gst.gov.in, efiling.gstat.gov.in, DoJ, Lok Sabha, SC/HC judgments where needed.
