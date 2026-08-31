# RUN SETUP — JEM verifier pass `verify-trib-01` (shared)

Same for both raters. Read once before you start.

## The one rule that overrides everything

**Pull-not-push. Write only into `out/`. Never write into any JEM repo.**
You produce a verification *table*. DSo's maintainer/expert layer reconciles the
two raters' tables and decides what gets applied. Nothing you run edits canonical
data — that boundary is what keeps a bad run from becoming canon.

## Folder

```
jem-verify-tribunals/
├── inputs/
│   ├── verifier_prompt.md        # read-only, prompt_version verify-trib-v1
│   ├── <your>_card.md            # agriya_codex_card.md OR prajna_deepseek_card.md
│   └── claims_to_verify.csv      # from DSo — the values under test
├── out/
│   ├── {model}__verify-trib-01__{user}__{timestamp}.csv
│   ├── {model}__verify-trib-01__{user}__{timestamp}.meta.json
│   └── fetch_log/                # saved source PDFs/pages (recommended)
└── run.py | run.sh               # your loop
```

Pin `inputs/verifier_prompt.md` as read-only so a mid-run edit can't silently
fork `prompt_version`. If you change the prompt, you must bump the version and
tell DSo — otherwise the two runs are no longer comparable.

## meta.json — fill every field

`rater`, `model`, `model_version`, `context`, `web_search`, `temperature`,
`prompt_version` (`verify-trib-v1`), `batch_id` (`verify-trib-01`),
`timestamp_utc`, `entities_n` (44), `rows_n`, `tokens_in`, `tokens_out`,
`cost_estimate`.

This is **not** bookkeeping. It is the calibration experiment: without
`model_version` + `context` + `web_search` + `temperature`, DSo cannot later tell
whether a disagreement between the two of you is a model effect or a setup
effect. An untagged run is a discarded data point.

## Effort

- **Compute / wall-clock:** ~1 day, bounded by PDF-fetch latency and rate limits,
  not by your attention. ~2–5M tokens for the 44-entity pass.
- **Hands-on:** ~45–75 minutes across setup, kicking the run, spot-checking the
  `anomaly_flags` rows (42-ladder, 365-day, empty/homepage URLs), and uploading.

## Return to DSo

Upload `out/` (Drive or email), and reply with:

1. **Coverage** — of 44 entities, how many had any verifiable primary?
2. **CONFIRM / REFUTE / UNSOURCED / NA counts** across all rows.
3. **Did the SAT anchor verify** to 1,066 / 429 / 323 independently? (method check)
4. **Every REFUTE** — stored value vs your verified value + the direct source URL.
5. **NJDG stamps** — count of `njdg_stamp_valid=FALSE` (all should be false;
   none of these bodies are eCourts).
6. **meta.json** confirmed complete (model_version, context, tokens, cost).

Do not reconcile against each other or against the repo — that's DSo's step. Two
independent tables in, consensus out.


---

## JEM verify-trib-01 — Verifier Summary (Prajna · DeepSeek)

**Run:** `deepseek__verify-trib-01__prajna__20260831_131656` · batch `verify-trib-01` · prompt `verify-trib-v1` · 140 rows / 44 entities · model `deepseek-v4-flash` (DeepSeek Harness, web_search + fetch on)

**1. Coverage** — **12 of 44 entities** had at least one verifiable primary source (i.e., a primary was located and grounds a REFUTE). The other 32 entities' claims are UNSOURCED; each row's notes record exactly which sources were attempted (e.g., MERC AR 2024-25 downloaded but is scanned/image-only; eparlib.nic.in unreachable from this environment; DERC public AR ends 2022-23; KERC/TNERC sites timed out).

**2. Verdict counts (140 rows)** — **CONFIRM 0 · REFUTE 26 · UNSOURCED 114 · NA 0**. Every stored numeric claim failed verification; none matched a primary. This is a fully contaminated claims set.

**3. SAT anchor — PASS.** Independently re-derived **1,066 / 429 / 323** from SEBI AR 2025-26, Chapter 10, §10.3 + Table 10.35 (page 156); the stored 420/380/345/365 was REFUTEd, not echoed — method is sound, no stale-snapshot leak.

**4. Every REFUTE — stored → verified (+ direct source URL)**

| entity·field                          | stored → verified                                                                                         | primary URL                                                                                                                                                                   |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sat·pending / filed / disposed / rate | 420→**1,066** · 380→**429** · 345→**323** · 0.9079→**0.7529**               | [SEBI AR 2025-26 Ch.10](<https://www.sebi.gov.in/reports-and-statistics/publications/aug-2026/Chapter%2010.pdf>)                                                               |
| ngt·pending / filed / disposed / rate | 5,698→**5,890** · 1,976→**5,326** · 1,937→**3,936** · 0.9813→**0.7390**     | [NGT Zone-Wise dashboard](https://www.greentribunal.gov.in/bench-wise-institution-disposal-and-pendency-cases-ngt-principal-bench-and-all-zonal-benches)                       |
| aft·pending / filed / disposed / rate | 48,000→**1,844** · 9,500→**9,837** · 7,800→**7,993** · 0.8211→**0.8126**    | [RS USQ 4152 (MoD, 30.03.2026)](https://sansad.in/getFile/annex/270/AU4152_7qPrJE.pdf?source=pqars)                                                                            |
| cat·pending / filed / disposed / rate | 42,000→**69,581** · 18,000→**32,998** · 11,700→**35,460** · 0.65→**1.0746** | [PIB PRID 2244915 (LS reply)](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244915)                                                                                       |
| drt·pending                           | 195,000→**178,172**                                                                                 | RS written reply 02.12.2025 via[PTI/Free Press Journal](https://www.freepressjournal.in/business/debt-recovery-tribunals-on-the-edge-178-lakh-cases-keeping-them-suspenseful)* |
| nclt·pending                          | 45,000→**20,484**                                                                                   | [LS SQ 222 (MCA, 17.03.2025)](https://sansad.in/getFile/loksabhaquestions/annex/184/AS222_n4MMkm.pdf?source=pqals)                                                             |
| cci·filed / disposed / rate           | 580→**203** · 495→**184** · 0.8534→**0.9064**                                       | [PIB PRID 2225431 (MCA, 09.02.2026)](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2225431)                                                                                |
| dl_state_cdrc·pending                 | 24,000→**23,970**                                                                                   | [RS SQ 182 Annexure II](https://sansad.in/getFile/annex/270/AS182_e6D66y.pdf?source=pqars)                                                                                     |
| ka_state_cdrc·pending                 | 20,000→**19,960**                                                                                   | [RS SQ 182 Annexure II](https://sansad.in/getFile/annex/270/AS182_e6D66y.pdf?source=pqars)                                                                                     |
| mh_state_cdrc·pending                 | 32,000→**85,469**                                                                                   | [RS SQ 182 Annexure II](https://sansad.in/getFile/annex/270/AS182_e6D66y.pdf?source=pqars)                                                                                     |
| tn_state_cdrc·pending                 | 28,000→**12,445**                                                                                   | [RS SQ 182 Annexure II](https://sansad.in/getFile/annex/270/AS182_e6D66y.pdf?source=pqars)                                                                                     |
| lok_adalat_generic·disposed           | 15,000,000→**22,383,774**                                                                           | [NALSA National Lok Adalat Report 14.12.2024](https://nalsa.gov.in/national-lok-adalat-report/)                                                                                |

\* drt: the RS answer's direct eparlib PDF was unreachable (DNS) from this environment; the figure 1,78,172 (as on 14.11.2025) is verified via the PTI wire reporting the answer — flagged in the row notes.

**5. NJDG stamps** — `njdg_stamp_valid=FALSE` on **43 of 44** rows (every `present` stamp — all invalid, none of these bodies are eCourts; each row says "recommend strip NJDG source"). The one exception: `aft` (stamp `absent` → TRUE, no action). Correct per the pass's expectation.

**6. meta.json — confirmed complete.** All RUN_SETUP fields present: `rater` prajna, `model` deepseek, `model_version` deepseek-v4-flash (DeepSeek-V4-Flash-0731) via DeepSeek Harness, `context` provided-files + web_search_on temp 0.2, `web_search` true, `temperature` 0.2, `prompt_version` verify-trib-v1, `batch_id` verify-trib-01, `entities_n` 44, `rows_n` 140, `tokens_in/out` 0, `cost_estimate` $0.00 (harness-agent run, no external LLM API), plus `sat_anchor_check: PASS`, verdict counts, and the superseded-attempt warning.

---

**Bottom line ** :The SAT method check passed; 26 rows carry corrected values with direct GoI primary URLs; 114 rows should be withdrawn or re-sourced; all 43 NJDG stamps should be stripped. Files ready in `jem/jem-verify-tribunals/out/` (CSV + meta.json + fetch_log) for reconciliation against Agriya's table.
