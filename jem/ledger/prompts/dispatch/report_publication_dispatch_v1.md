# Dispatch prompt — Report-publication (meta-provenance) track

`prompt_id: dispatch-report-publication` · `version: v1` · dispatched 2026-09-01T00:39Z
`derived_from: report-publication-v1` (`ledger/prompts/06_CURSOR_report_publication.md`)
`staging_artifact: ledger/suggested/track_report_publication.csv`
`model: claude-sonnet-5-thinking-high`

Scope was cut from the governing prompt's 44 to 12 named bodies. Two reasons,
both recorded rather than silently applied: "the 44" is not reproducible from the
repo (the nearest principled definition yields 51, and the roster lives in the
earlier verification round's uncommitted artifacts), and 12 bodies with reachable
sites can be done properly where 44 could not.

Recorded verbatim as dispatched.

---

You are running the **report-publication (meta-provenance) track** for JEM (Judiciary Entity Map India), a public dataset of India's judicial institutions. Repo root `/workspace`, pipeline root `/workspace/jem`. Today's date is 1 September 2026.

Read the governing prompt: `/workspace/jem/ledger/prompts/06_CURSOR_report_publication.md` and the harness it runs inside: `/workspace/jem/ledger/prompts/02_CONSENSUS_HARNESS_SPEC.md`. Follow them.

# THE QUESTION YOU ARE ANSWERING

For each body: **does an institution that should publish reports actually publish them?** This explains why so many `case_volume` figures in JEM are unsourceable — a body that doesn't publish is *why* its numbers can't be traced, and establishing that is the correct finding, not a failure.

# THE SINGLE MOST IMPORTANT RULE

**Never guess.** Do not infer that a tribunal publishes an annual report because tribunals usually do. Do not record a `last_published` date you did not read off an actual document. A wrong "yes" is much worse than an honest "unknown". You are evaluated on traceability, not coverage.

Critically: **`unknown` and `no` are different claims.** Use `no` only when you have actually searched and documented the search. Use `unknown` when you could not establish it either way. For `statutorily_required`, if you cannot confirm the duty from a primary statutory provision, the answer is `unknown` — absence of a found duty is not proof of no duty.

# SCOPE — exactly these 12 entities

Work only on these, in this order. Do a genuinely good job on as many as you can rather than a shallow job on all 12; it is fine to stop early and report how far you got.

`cestat`, `nclt`, `nclat`, `cat`, `itat`, `ngt`, `sebi`, `cci`, `irdai`, `trai`, `ibbi`, `pfrda`

Each has a YAML file under `/workspace/jem/data/entities/` — find it (try `rg -l "^id: cestat" /workspace/jem/data/entities`) and read it for the body's official website and existing sources.

# THE FIELDS TO POPULATE (S3 `report_publication` block)

```yaml
report_publication:
  publishes_reports: yes | no | not_required | unknown
  statutorily_required: yes | no | unknown
  statutorily_required_source: https://...   # its OWN provenance: the section imposing the duty
  report_type: annual_report | statistics | ...
  last_published: 'YYYY-MM-DD' | null
  last_published_url: https://...            # must PASS liveness and be the actual report document
  expected_cadence: annual | quarterly | ...
  data_as_of: 'YYYY-MM-DD'
  source_type: AnnualReport | GoIWebsite | OfficialReport | ...
  source_url: https://...
  notes: "no reports found after checking X, Y, Z"
```

`source_type` must be one of: `Constitution`, `CentralAct`, `StateAct`, `SCJudgment`, `HCJudgment`, `GazetteNotification`, `GoIWebsite`, `OfficialReport`, `NJDG`, `AnnualReport`.

# "NO REPORTS FOUND" IS A VERIFIED FINDING — IF YOU SHOW YOUR WORK

A negative is a claim and proving it is the whole job. Document the search across the bounded N≤3 retry, escalating through the source map: the body's own publications page → parent ministry archive → PIB / Lok Sabha references. Write the trail into `notes`, e.g. `"no reports found after checking cestat.gov.in/publications, finmin.nic.in annual reports, PIB releases"`. **A bare "none found" is rejected.** The documented trail is what makes the negative credible.

# STATUTORY-DUTY EDGE — a first-class finding

If a body is `statutorily_required: yes` but `publishes_reports: no`, say so plainly in `notes`. Do not soften it. That is an accountability finding.

# TOOLS

**Liveness pre-gate — run it on every URL before you cite it:**
```
cd /workspace/jem && python3 scripts/harness/liveness.py --url "<URL>"
```
Exits 0 on pass, 1 on fail, prints the reason. A `last_published_url` that fails liveness may NOT be recorded as the citation.

Note it rejects `soft_404_catch_all_shell`: some government single-page apps return an identical 200 shell for every path, so a 200 alone proves nothing. If you see that reason, the URL is not usable as evidence.

Known unreachable from this network (don't burn attempts): `aftdelhi.nic.in`, `cercind.gov.in`, `dfs.gov.in`, `dopt.gov.in`, `ncdrc.nic.in`, `rct.indianrailways.gov.in`, `sat.gov.in`, `mca.gov.in` (403), `incometaxindia.gov.in` (403), `indiacode.nic.in` deep links (the portal migrated to `indiacode.gov.in`, which is an SPA that cannot serve as a machine-verifiable citation).

You also have `WebSearch`, `WebFetch`, and `curl`. WebFetch and the VM have slightly different network reach, so if one fails the other is worth one try.

# HARNESS DISCIPLINE

Per field: liveness pre-gate → researcher (fetch + extract) → verifier (re-fetch the CLAIMED url only, confirm the value is actually there) → reconcile → ledger. At most **3 attempts per fact**, each attempt + query + result logged. Capture-and-label: every finding goes in the ledger with a status (`sourced`, `homepage_only`, `secondary_only`, `unsourced_candidate`, `fetch_failed`, `refuted`); only `sourced` values go into a YAML block.

# WHERE TO PUT OUTPUT — STAGING ONLY

**Do NOT write into `/workspace/jem/data/`. Do NOT run `build.py` or `derive.py`. Do NOT `git add`, `git commit`, or `git push`. Do NOT edit any existing repo file.**

Write only to `/tmp/track_report/`:
- `/tmp/track_report/report_publication.csv` — keyed by `entity_id`, one column per field above. This is the artifact the maintainer merges.
- `/tmp/track_report/blocks.yaml` — a mapping of `entity_id` → the `report_publication` block, ready to paste
- `/tmp/track_report/ledger.jsonl` — one JSON object per entity, in the harness spec's ledger shape, including the `attempts` array (query + result per attempt) and liveness results
- `/tmp/track_report/REPORT.md` — your writeup

# WHAT TO RETURN

1. A compact table: entity_id, `publishes_reports`, `statutorily_required`, whether you found a live `last_published_url`.
2. Every case where `statutorily_required: yes` but `publishes_reports: no` — the accountability findings.
3. How many entities you completed of the 12, and where you stopped.
4. An honest account of what was reachable and what was not.
5. Explicitly: anything you were tempted to record but did not because you could not source it.
