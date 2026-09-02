# Dispatch prompt — Track K (TN Sub-District Criminal Magistracy)

`prompt_id: dispatch-cursor-K-criminal` · `version: v1` · dispatched 2026-09-01T00:28Z
`derived_from: cursor-K-criminal-v1` (`ledger/prompts/04_CURSOR_K_criminal_magistracy.md`)
`run_ledger: ledger/runs/cursor-K-criminal__claude__dso__20260901T003800Z.jsonl`

Recorded verbatim as dispatched.

---

You are running **Track K** of a data-integrity packet for JEM (Judiciary Entity Map India), a public dataset of India's judicial institutions. Repo is at `/workspace`, pipeline root is `/workspace/jem`. Today's date is 1 September 2026.

Read the governing prompt first: `/workspace/jem/ledger/prompts/04_CURSOR_K_criminal_magistracy.md` and the harness it runs inside: `/workspace/jem/ledger/prompts/02_CONSENSUS_HARNESS_SPEC.md`. Follow them.

# THE SINGLE MOST IMPORTANT RULE

**Do not invent, guess, extrapolate, or "reconstruct from general knowledge" a single court, district, date, or URL.** This project's entire value is that every fact traces to a primary source that actually contains it. A fabricated entity is far worse than an empty result. An empty, well-documented result is a *successful* run of this track. You will be evaluated on the honesty and traceability of what you return, NOT on how many entities you produce. Returning "0 entities, here is the documented evidence trail of what I checked" is a perfectly good outcome and is explicitly what the harness spec calls `unsourced after documented attempts`.

Enumerating TN's 38 districts from memory and emitting a CJM for each is exactly the failure mode this project exists to prevent. Do not do it. The prompt is explicit: "do not emit a court you cannot tie to a notification."

# YOUR TASK

For Tamil Nadu only, find the **judicial criminal courts below the District & Sessions Court** that are actually notified/established, each tied to a specific instrument you can open and read:
- Chief Judicial Magistrate — `cjm_{district}`
- Additional Chief Judicial Magistrate — `acjm_{district}` (where notified)
- Judicial Magistrate First Class — `jmfc_{district}`
- Judicial Magistrate Second Class — `jm2_{district}` (where they exist)

Executive magistrates (District Magistrate / SDM) are OUT of scope for this track.

Legal basis is **BNSS 2023 ss.21-23** (classes of criminal courts; sentencing powers) with CrPC 1973 ss.6-29 retained as the superseded predecessor. Each entity carries a `statutory_basis` struct LIST:
```yaml
statutory_basis:
  - { instrument_id: bnss_2023, provision: "ss.21-23", status: in_force,   effective_from: '2024-07-01' }
  - { instrument_id: crpc_1973, provision: "ss.6-29",  status: superseded, repealed_on: '2024-07-01' }
```
The criminal routing quantum is sentencing power, NOT money — do **not** use `pecuniary_jurisdiction`. Put the sentencing ceiling in `data_quality_notes` only if you can source it from BNSS s.23 primary text.

# TOOLS AND WHAT IS KNOWN TO BE UP OR DOWN

I have already tested the source map. Do not waste attempts re-testing these:
- `hcmadras.tn.gov.in`, `mhc.tn.gov.in` (Madras High Court) — UNREACHABLE (timeout from two independent network paths)
- `districts.ecourts.gov.in` — UNREACHABLE
- `egazette.gov.in`, `cms.tn.gov.in`, `tn.gov.in` — UNREACHABLE
- `stationeryprinting.tn.gov.in` (TN Government Gazette publisher) — REACHABLE, 200
- `doj.gov.in`, `legislative.gov.in`, `prsindia.org` — REACHABLE
- `indiacode.nic.in` — the India Code portal MIGRATED to `indiacode.gov.in` in Aug 2026. Old deep links mostly 404. **The new `indiacode.gov.in` is an Angular single-page app that returns a byte-identical 200 HTML shell for EVERY path including complete nonsense** — so a 200 from it proves nothing and it cannot be used as a machine-verifiable citation. Some old `indiacode.nic.in/bitstream/.../*.pdf` PDFs still resolve and those ARE usable. Finding a live, openable BNSS primary text is itself a worthwhile result — report exactly which URL worked, if any.

**A liveness pre-gate is implemented for you. Use it on every URL before you cite it:**
```
cd /workspace/jem && python3 scripts/harness/liveness.py --url "<URL>"
```
It exits 0 on pass, 1 on fail, and prints the reason (`non_200`, `soft_404_catch_all_shell`, `redirects_to_root`, `content_type_mismatch`, `unreachable`). You can also import it: `sys.path.insert(0,'scripts'); from harness.liveness import check`.

You also have `WebSearch` and `WebFetch` tools, and `curl`. WebFetch and the VM have slightly different network reach, so if one fails the other is worth one try.

# HARNESS DISCIPLINE (follow it)

Per cell/fact: liveness pre-gate → researcher (fetch → extract) → verifier (re-check claim vs CLAIMED source only) → reconcile → ledger. Bounded retry: **at most 3 search attempts per fact**, escalating through the source map. Log every attempt, its query, and its result. After 3 attempts, record `unsourced after documented attempts` and move on.

Capture-and-label: keep every finding in the ledger with a status label (`sourced`, `homepage_only`, `secondary_only`, `unsourced_candidate`, `fetch_failed`, `refuted`). Only `sourced` (primary document, live URL, value actually present in it) may become an entity.

# WHERE TO PUT OUTPUT — STAGING ONLY, DO NOT TOUCH CANON

This is a sandbox/"pull-not-push" run. **Do NOT write anything into `/workspace/jem/data/`. Do NOT run `build.py`. Do NOT `git commit`, `git add`, or `git push`. Do NOT edit any existing repo file.**

Write only to a staging directory you create at `/tmp/track_k/`:
- `/tmp/track_k/entities/<id>.yaml` — one file per entity that genuinely cleared the gate (there may be zero; that is fine)
- `/tmp/track_k/suggested_edges.md` — markdown table: `source | rel_type | target | category | basis | evidence_url | confidence`
- `/tmp/track_k/ledger.jsonl` — one JSON object per cell examined, in the shape given in the harness spec's "Ledger record" section (include the `attempts` array with each query + result, and the liveness result)
- `/tmp/track_k/REPORT.md` — your findings writeup

For entity YAML shape, copy the conventions of an existing file under `/workspace/jem/data/entities/`. Required: `id`, `name`, `type`, `cluster`, `level_of_government`, `created_year`, `operational_status`, `data_quality`, `sources`. For this track: `type: SubordinateCriminalCourt`, `cluster: subordinate_courts`, `level_of_government: State`. Structural-first: **no `case_volume`, no `judge_strength`**.

Note `created_year` is REQUIRED and must be an integer — if you cannot source when a specific court was established, that is itself a reason you cannot emit the entity. Do not put a plausible-looking guess there.

If (and only if) you produce entity files, validate each one:
```
cd /workspace/jem && python3 scripts/validate.py --entity /tmp/track_k/entities/<file>.yaml
```
It must exit 0.

# DECISION GATES — SURFACE, DO NOT RESOLVE

- Which TN districts and which magistrate classes are actually notified — report what you found with sources; do not fill gaps by pattern.
- If an existing TN criminal entity already has `statutory_basis` as a plain string, leave it alone (backfill is a separate pass).

# WHAT TO RETURN IN YOUR FINAL MESSAGE

1. How many entities you emitted (may be 0) and their ids.
2. The suggested-edges table.
3. **A precise, honest account of what you could and could not reach**: for each source you tried, the URL, the liveness result, and what you concluded. This evidence trail is the most valuable thing you will produce — be specific and complete.
4. Whether you found ANY live, openable primary text of BNSS 2023 (this is independently useful — the legal-instrument registry needs it).
5. An explicit statement of your confidence and of anything you were tempted to infer but did not, because you could not source it.
