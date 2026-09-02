# Dispatch prompt — Track C (TN Commercial Courts)

`prompt_id: dispatch-cursor-C-commercial` · `version: v1` · dispatched 2026-09-01T00:29Z
`derived_from: cursor-C-commercial-v1` (`ledger/prompts/03_CURSOR_C_commercial_courts.md`)
`run_ledger: ledger/runs/cursor-C-commercial__claude__dso__20260901T004100Z.jsonl`

A dispatch prompt is the governing track prompt plus the run-specific context an
agent cannot discover for itself without wasting attempts: which hosts the
orchestrator has already proven unreachable, where staging output goes, and what
counts as success. It is registered separately from the governing prompt because
it is a different artifact with different content, and a run cites the thing that
actually governed it.

Recorded verbatim as dispatched.

---

You are running **Track C** of a data-integrity packet for JEM (Judiciary Entity Map India), a public dataset of India's judicial institutions. Repo is at `/workspace`, pipeline root is `/workspace/jem`. Today's date is 1 September 2026.

Read the governing prompt first: `/workspace/jem/ledger/prompts/03_CURSOR_C_commercial_courts.md` and the harness it runs inside: `/workspace/jem/ledger/prompts/02_CONSENSUS_HARNESS_SPEC.md`. Follow them.

# THE SINGLE MOST IMPORTANT RULE

**Do not invent, guess, extrapolate, or "reconstruct from general knowledge" a single court, district, date, or URL.** This project's entire value is that every fact traces to a primary source that actually contains it. A fabricated entity is far worse than an empty result. An empty, well-documented result is a *successful* run of this track. You will be evaluated on the honesty and traceability of what you return, NOT on how many entities you produce. Returning "0 entities, here is the documented evidence trail of what I checked" is a perfectly good outcome and is explicitly what the harness spec calls `unsourced after documented attempts`.

The prompt is explicit: "Do NOT emit one per district by default; emit only notified courts, each citing its notification." Enumerating TN districts from memory is exactly the failure mode this project exists to prevent.

# YOUR TASK

For Tamil Nadu only, find the commercial courts that TN has **actually notified**, each tied to a specific notification you can open and read:

1. **District-level Commercial Courts** — `type: CommercialCourt`, id `tn_commercial_court_{district}`. Only where genuinely notified. Each must cite its notification.
   - `pecuniary_jurisdiction`: `specified_value_min: 300000`, `currency: INR`, `basis: {instrument_id: commercial_courts_act_2015, provision: "s.2(1)(i)"}` (the ₹3 lakh Specified Value floor since the 2018 amendment)
   - `statutory_basis`: struct list referencing `commercial_courts_act_2015` (+ `commercial_courts_amendment_2018`), `status: in_force`
   - `cluster: subordinate_courts`, `level_of_government: State`
2. **Commercial Appellate Courts** at district-judge level — same type, id `tn_commercial_appellate_court_{district}` — only where notified.
3. **Madras HC Commercial Division and Commercial Appellate Division** — Madras HC does have ordinary original civil jurisdiction so these exist, but **do NOT create standalone nodes for them**. They are divisions *of* the parent High Court, represented as commercial/appellate capacity of `hc_madras` and surfaced ONLY as suggested edges. If you think a node is warranted, flag it as a decision gate; do not create it.

Structural-first: **no `case_volume`, no `judge_strength`**. `data_quality: partial` minimum. Use `unverified_fields[]` for anything lacking a primary GoI URL.

# TOOLS AND WHAT IS KNOWN TO BE UP OR DOWN

I have already tested the source map. Do not waste attempts re-testing these:
- `hcmadras.tn.gov.in`, `mhc.tn.gov.in` (Madras High Court) — UNREACHABLE (timeout from two independent network paths)
- `districts.ecourts.gov.in` — UNREACHABLE
- `egazette.gov.in`, `cms.tn.gov.in`, `tn.gov.in` — UNREACHABLE
- `stationeryprinting.tn.gov.in` (TN Government Gazette publisher) — REACHABLE, 200. **This is your most promising lead** — TN commercial court constitutions are notified in the TN Government Gazette. Explore it properly.
- `doj.gov.in`, `legislative.gov.in`, `prsindia.org` — REACHABLE
- `indiacode.nic.in` — the India Code portal MIGRATED to `indiacode.gov.in` in Aug 2026. Old deep links mostly 404. **The new `indiacode.gov.in` is an Angular single-page app that returns a byte-identical 200 HTML shell for EVERY path including complete nonsense** — so a 200 from it proves nothing and it cannot be used as a machine-verifiable citation. Some old `indiacode.nic.in/bitstream/.../*.pdf` PDFs still resolve and those ARE usable. Finding a live, openable primary text of the Commercial Courts Act 2015 or the 2018 amendment is itself a worthwhile result — report exactly which URL worked, if any.

**A liveness pre-gate is implemented for you. Use it on every URL before you cite it:**
```
cd /workspace/jem && python3 scripts/harness/liveness.py --url "<URL>"
```
It exits 0 on pass, 1 on fail, and prints the reason (`non_200`, `soft_404_catch_all_shell`, `redirects_to_root`, `content_type_mismatch`, `unreachable`). You can also import it: `sys.path.insert(0,'scripts'); from harness.liveness import check`.

You also have `WebSearch` and `WebFetch` tools, and `curl`. WebFetch and the VM have slightly different network reach, so if one fails the other is worth one try.

# HARNESS DISCIPLINE (follow it)

Per cell/fact: liveness pre-gate → researcher (fetch + extract) → verifier (re-fetch the CLAIMED url only, confirm the value is actually in the document) → reconcile → ledger. Bounded retry: **at most 3 search attempts per fact**, escalating through the source map. Log every attempt, its query, and its result. After 3 attempts, record `unsourced after documented attempts` and move on.

Capture-and-label: keep every finding in the ledger with a status label (`sourced`, `homepage_only`, `secondary_only`, `unsourced_candidate`, `fetch_failed`, `refuted`). Only `sourced` (primary document, live URL, value actually present in it) may become an entity.

**Gap-discovery is live:** if you surface a commercial-jurisdiction body that is not in the graph, emit it as a *suggested* entity + suggested edge, flagged unverified and cited to the specific provision a critic must confirm. Never auto-apply.

# WHERE TO PUT OUTPUT — STAGING ONLY, DO NOT TOUCH CANON

This is a sandbox/"pull-not-push" run. **Do NOT write anything into `/workspace/jem/data/`. Do NOT run `build.py`. Do NOT `git commit`, `git add`, or `git push`. Do NOT edit any existing repo file.**

Write only to a staging directory you create at `/tmp/track_c/`:
- `/tmp/track_c/entities/<id>.yaml` — one file per entity that genuinely cleared the gate (there may be zero; that is fine)
- `/tmp/track_c/suggested_edges.md` — markdown table: `source | rel_type | target | category | basis | evidence_url | confidence`
- `/tmp/track_c/ledger.jsonl` — one JSON object per cell examined, in the shape given in the harness spec's "Ledger record" section (include the `attempts` array with each query + result, and the liveness result)
- `/tmp/track_c/REPORT.md` — your findings writeup

For entity YAML shape, copy the conventions of an existing file under `/workspace/jem/data/entities/`. Required: `id`, `name`, `type`, `cluster`, `level_of_government`, `created_year`, `operational_status`, `data_quality`, `sources`.

Note `created_year` is REQUIRED and must be an integer — if you cannot source the year a specific court was constituted, that is itself a reason you cannot emit the entity. Do not put a plausible-looking guess there.

Note: the `CommercialCourt` entity type was just added to the schema and is valid. If you produce entity files, validate each:
```
cd /workspace/jem && python3 scripts/validate.py --entity /tmp/track_c/entities/<file>.yaml
```
It must exit 0.

# DECISION GATES — SURFACE, DO NOT RESOLVE

- G1-sub: are the Madras HC Commercial/Appellate Divisions edges-to-`hc_madras` (the default) or explicit division nodes? Proceed edges-only and flag it.
- Which TN districts are actually notified — list what you found with sources. If a claimed court cannot be confirmed from a notification, mark it suggested-unverified and do NOT emit a canonical entity.

# WHAT TO RETURN IN YOUR FINAL MESSAGE

1. How many entities you emitted (may be 0) and their ids.
2. The suggested-edges table.
3. **A precise, honest account of what you could and could not reach**: for each source you tried, the URL, the liveness result, and what you concluded. This evidence trail is the most valuable thing you will produce — be specific and complete.
4. Whether you found ANY live, openable primary text of the Commercial Courts Act 2015 or the 2018 amendment (independently useful — the legal-instrument registry needs it).
5. An explicit statement of your confidence and of anything you were tempted to infer but did not, because you could not source it.
