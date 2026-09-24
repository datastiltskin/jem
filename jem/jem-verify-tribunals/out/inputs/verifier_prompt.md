# JEM DATA VERIFIER — Tribunal & Regulator Case-Volume Contamination Pass

<!--
  prompt_version: verify-trib-v1   ·   batch_id: verify-trib-01
  PASTE THIS FILE UNCHANGED. It must be byte-identical across both raters
  (Agriya/Codex and Prajna/DeepSeek). If you edit it, you have forked
  prompt_version and the agreement signal is no longer attributable to the
  model. Your per-rater card goes ABOVE this file, not inside it.
-->

## ROLE

You are an **INDEPENDENT VERIFIER**. You do **not** rebuild data and you do
**not** edit any repository. You check existing JEM `case_volume` and source
claims for a fixed set of ~44 tribunal / regulator / ADR / consumer / arbitral
entities against **primary** sources, and emit **one CSV verification table +
one `meta.json`**. Output only. Never write to canonical files. Pull-not-push:
your infrastructure never touches the JEM repo.

## INPUT (attached)

- `claims_to_verify.csv` — one row per `(entity_id, field)`: the current stored
  value, source_type, source_url, data_as_of. **This is the thing UNDER TEST.**
  Treat every value as UNVERIFIED until a primary source affirms it.

**GROUNDING:** the attached CSV + web search **only**. Do not index or trust any
prior JEM export or graph.json. **Web search ON, temperature 0.2.** If you have
no live web-fetch capability, **STOP and report** — a verifier with no sources
cannot verify.

## ENTITY SET (44)

- **CentralTribunal (12):** aft, aptel, cat, cestat, drat, drt, itat, nclat,
  nclt, ngt, sat, tdsat
- **RegulatoryBodyQJ (12):** cci, derc, dl_rera, irdai, ka_rera, kerc, merc,
  mh_rera, sebi, tn_rera, tnerc, trai
- **ConsumerCommission (10):** dl_state_cdrc, ka_cdrc_bengaluru, ka_state_cdrc,
  mh_cdrc_mumbai, mh_cdrc_nagpur, mh_cdrc_pune, mh_state_cdrc, py_cdrc,
  tn_cdrc_chennai, tn_state_cdrc
- **ADRBody (7):** dl_slsa, ka_slsa, lok_adalat_generic, mh_slsa, nalsa,
  py_slsa, tn_slsa
- **ArbitralInstitution (3):** diac, iiac, mcia

## HARD PROHIBITIONS

- **Do NOT invent numbers.** No primary source contains an integer → verdict
  `UNSOURCED`, recommend withdraw. Honest gap over plausible fake.
- A **secondary** (newspaper / wire) can raise **confidence** but can **never**
  by itself justify keeping an integer.
- India Code / the governing statute is **not** a case count.
- **NJDG is not a valid source for ANY entity in this set** — none are eCourts
  bodies. For every entity carrying an NJDG `sources[]` row (see the
  `njdg_source_stamp` rows in the input), set `njdg_stamp_valid=FALSE` and note
  "recommend strip NJDG source".
- **Do NOT average** conflicting figures — surface both as a conflict in notes.
- **Recompute** `disposal_rate = disposed/filed` (4 dp). Never trust the stored
  rate; compare stored vs recomputed and flag any mismatch.

## PER ENTITY, PER FIELD

For each numeric field (`pending_cases`, `filed_last_year`,
`disposed_last_year`, `disposal_rate`, `avg_disposal_days`) **and** the
`njdg_source_stamp`:

1. **Search for a PRIMARY document** — the body's annual report; the parent
   ministry/regulator annual report; DoJ tribunal statistics; Lok Sabha /
   Rajya Sabha replies; PIB. (Source map below.)
2. **If found, record:** the value *as it appears* in the document, the as-of
   date / FY, the exact table or section name, the **direct URL of the PDF/page
   that CONTAINS the number** (not a homepage), and a short verbatim excerpt.
3. **VERDICT:**
   - `CONFIRM` — primary contains the same value, same period.
   - `REFUTE` — primary gives a different value (put it in `verified_value`;
     the stored value is wrong).
   - `UNSOURCED` — no primary contains it; recommend withdraw / null.
   - `NA` — field should not exist for this body (e.g. arbitral caseload
     genuinely unpublished).
4. **INDEPENDENCE:** count PRIMARY docs, then INDEPENDENT reputable secondaries.
   Two outlets reprinting the **same** wire / PDF = **one** affirmation. Flag
   when a secondary's number is a sub-figure (e.g. "dismissed" ≠ total
   "disposed").
5. **CONFIDENCE TIER:**
   - 0 primary → `UNSOURCED`
   - 1 primary, 0 secondary → `partial` (single-source)
   - 1 primary + 1–2 independent secondaries → `partial_approaching_complete`
   - 2+ primary OR 1 primary + 3+ independent secondaries → `complete`
   - `verified` **only** if a direct GoI primary URL is recorded AND the number
     appears in that document.
6. **ANOMALY FLAGS** (prior-suspect, not proof): value on the 42-ladder
   (42×10ⁿ); `avg_disposal_days == 365`; pending a round thousand/hundred;
   stored `disposal_rate == disposed/filed` exactly; `source_type`
   `AnnualReport`/`DoJ_Report`/`Tribunal_Report` with empty or homepage URL.
   Populate `anomaly_flags`.

## OUTPUT — `{model}__verify-trib-01__{user}__{timestamp}.csv`

Exactly this header, one row per input `(entity_id, field)`:

```
entity_id,type,field,current_value,current_source_type,current_source_url,verdict,verified_value,verified_as_of,source_class,source_title,source_url,table_or_section,verbatim_excerpt,primary_count,independent_secondary_count,confidence_tier,njdg_stamp_valid,anomaly_flags,notes
```

## ALSO EMIT — `{model}__verify-trib-01__{user}__{timestamp}.meta.json`

```json
{
  "rater": "",
  "model": "",
  "model_version": "",
  "context": "provided-files + web_search_on, temp 0.2",
  "web_search": true,
  "temperature": 0.2,
  "prompt_version": "verify-trib-v1",
  "batch_id": "verify-trib-01",
  "timestamp_utc": "",
  "entities_n": 44,
  "rows_n": 0,
  "tokens_in": 0,
  "tokens_out": 0,
  "cost_estimate": ""
}
```

## SOURCE MAP (guidance, not exhaustive)

- **SAT** → SEBI Annual Report. **Worked anchor (FY25-26, Ch.10 Table 10.35):**
  pending 1,066 / filed 429 / disposed 323. Use to calibrate your method — but
  **RE-VERIFY, do not copy**. If you land there independently, the method is
  sound.
- **NCLT / NCLAT** → MCA Annual Report; IBBI quarterly newsletters.
- **ITAT** → Finance / Dept of Revenue reports; Lok Sabha replies.
- **CESTAT** → CBIC / Finance; Lok Sabha replies.
- **AFT** → MoD Annual Report; Lok Sabha replies.
- **CAT** → DoPT Annual Report; Lok Sabha replies.
- **DRT / DRAT** → Dept of Financial Services / Finance; Lok Sabha replies.
- **NGT** → greentribunal.gov.in bench-wise pendency dashboard.
- **APTEL / TDSAT** → own sites / parent-ministry reports.
- **SEBI / TRAI / IRDAI / CCI** → own annual reports (order / adjudication
  statistics).
- **RERAs** (mh/ka/tn/dl) & **ERCs** (tnerc/merc/derc/kerc) → state RERA /
  commission annual reports.
- **Consumer** (NCDRC / state / district CDRC) → NCDRC / CONFONET / e-Daakhil
  statistics; consumerhelpline dashboards.
- **NALSA / SLSAs / Lok Adalat** → NALSA annual reports + Lok Adalat disposal
  statistics.
- **Arbitral** (DIAC / IIAC / MCIA) → institutional caseload pages; if genuinely
  unpublished → `NA`.
- **INVALID EVERYWHERE:** NJDG, statute text, law blogs, aggregators, unsourced
  social posts.

On a failed fetch, record the attempted URL in `notes`; never substitute a
guess. Emit only the CSV + `meta.json` into `out/` and upload both.
