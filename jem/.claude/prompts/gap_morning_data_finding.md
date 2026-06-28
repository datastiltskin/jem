# JEM — Morning gap data-finding (read-only)

**Mode: RESEARCH REPORT ONLY.** Produce a markdown report. Do **not** edit YAML, `graph.json`, SQLite, or any repository files.

Working directory: `/Users/user/Documents/repo/jem`. Read `jem/CLAUDE.md`, `entity_schema.yaml`, and overnight outputs:

- `jem/.claude/outputs/gap_data_validation_latest.md`
- `jem/.claude/outputs/gap_clog_verification.md` (if present)

## Objective

After an overnight validation run was blocked by Claude session/rate limits, collect **fresh primary-source metrics** for tribunal vacancy, pendency, and documented spillover to High Courts / district courts. Focus on gaps already flagged in JEM with thin or partial `gap_spillover` data.

## Source priority (fetch or search; cite URL + date)

1. **Department of Justice (DoJ)** — NJDG dashboards, pendency bulletins, vacancy statements for district/subordinate judiciary and tribunal coordination reports.
2. **greentribunal.gov.in** — NGT pendency / disposal dashboards (note `data_as_of` on page).
3. **Ministry / department annual reports** — e.g. MoEFCC, DoR/CBIC for GST tribunal context, MCA for NCLT/NCLAT where relevant to mapped entities.
4. **Lok Sabha / Rajya Sabha** — starred/unstarred replies on judicial vacancies, tribunal strength, case pendency (india.gov.in / loksabhadocs).
5. **Official tribunal sites** — efiling.gstat.gov.in, SAT, NCLT portals — only when primary.
6. **Supreme Court / High Court** — judgments or orders documenting writ clusters from tribunal non-functionality (indiankanoon / official court sites).

Do **not** treat news blogs or law-firm commentary as **verified**; mark **partial** and keep the blog as secondary only.

## Entities to prioritise

Cross-check against current YAML / latest validation report:

- GSTAT / GST Appellate benches — HC writ load, CBIC/DoR cited figures
- NGT — strength vs pendency
- SAT — quorum / bench availability → SC/HC spillover
- Gram Nyayalaya — rollout vs district court pendency (DoJ / NFSJ references)
- ATFE / FEMA adjudication — HC s.19 load if documented
- Any `structural_gap.flag: true` entity in latest validation with missing spillover numbers

## Output format (markdown)

1. **Executive summary** — what was found overnight vs what this run added
2. **Vacancy & strength table** — body, sanctioned / working strength, as-of date, source URL
3. **Pendency table** — body, metric, value, as-of date, source URL
4. **Spillover / clog table** — gap cause (JEM entity id), affected court/body, metric_note (short verbatim), source, data_quality (`verified` | `partial`)
5. **Recommended YAML edits** — bullet list for human/agent apply (field paths, suggested values); **no file writes**
6. **Sources not found** — claims searched but no primary number

Use web search and fetch. Respond with markdown only.
