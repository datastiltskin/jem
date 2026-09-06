# Agriya verifier sample

Review sample for DSo, packaged on the `verifier/codex` branch at `jem/jem-verify-tribunals/out/`. Do not include this run in blinded model-agreement calibration. No canonical data was changed. The original local verification was subsequently packaged for publication at Agriya's request.

1. **Coverage:** 140 input rows across 44 entities. Primary-backed numeric replacements for 2 entities, each with a disclosed reporting-boundary assumption. All 44 source-stamp rows assessed. Related figures and unresolved date/scope differences are preserved in `evidence.json`. This coverage count excludes generic NJDG policy evidence.

2. **Verdicts:** CONFIRM 0, REFUTE 45, UNSOURCED 94, NA 1. REFUTE comprises 2 numeric claims and 43 invalid NJDG sources. UNSOURCED is a bounded-search outcome, not proof that a value is false or unpublished. NA is AFT's already-absent stamp.

3. **SAT anchor:** primary table and arithmetic PASS: pending 1,066, filed 429, disposed 323 for FY2025-26. Disposals = 135 + 28 + 47 + 88 + 25. Balance = 960 + 429 - 323 = 1,066. Rate = 0.7529. The table was fetched and visually inspected. Independence cannot be claimed because the expected answer and peer summary were already exposed. These figures do not refute the input's December 2024 snapshot solely by differing from it.

   [SEBI annual report, Table 10.35, printed page 156](https://www.sebi.gov.in/reports-and-statistics/publications/aug-2026/Chapter%2010.pdf)

4. **Every REFUTE:**

   | Entity and field | Stored → proposed | Direct source and qualification |
   | --- | --- | --- |
   | ka_state_cdrc · pending_cases | 20000 → 9947 | [Primary document](https://kscdrc.karnataka.gov.in/storage/pdf-files/Statistics/StatisticsfortheMonthofNovember-2024.pdf). Input data_as_of=2024-12-01. The immediately preceding monthly close is 9947 on 2024-11-30, with appeals 8658 plus complaints 1289. This REFUTE assumes November close equals 1 December opening with no intervening adjustment. If data_as_of instead means 1 December close, downgrade to UNSOURCED pending that exact snapshot. State commission scope includes its benches, not district commissions. |
   | cestat · pending_cases | 120000 → 72179 | [Primary document](https://cestat.gov.in/openfile/2/8799). Input data_as_of=2024-12-01. Published December opening pending is 72179, also November closing on PDF page 2. Interpret date-only snapshot as opening balance. The source notes possible physical-verification adjustments. Replace stored 120000 subject to this boundary convention. |

   Each of the following 43 entities has `njdg_source_stamp: present → absent`, meaning **recommend strip NJDG source**. This refutes source applicability, not the input's description that a stamp exists. [NIC's NJDG scope](https://www.nic.gov.in/project/national-judicial-data-grid/) supports the prompt's explicit source-exclusion rule.

   `py_slsa`, `py_cdrc`, `mh_cdrc_mumbai`, `mh_state_cdrc`, `mh_cdrc_pune`, `merc`, `mh_slsa`, `mh_cdrc_nagpur`, `mh_rera`, `ka_slsa`, `kerc`, `ka_cdrc_bengaluru`, `ka_rera`, `ka_state_cdrc`, `dl_state_cdrc`, `derc`, `dl_slsa`, `dl_rera`, `tn_slsa`, `tn_rera`, `tnerc`, `tn_cdrc_chennai`, `tn_state_cdrc`, `nclat`, `itat`, `sat`, `lok_adalat_generic`, `iiac`, `irdai`, `cat`, `drt`, `aptel`, `sebi`, `drat`, `cestat`, `nclt`, `mcia`, `tdsat`, `ngt`, `diac`, `cci`, `trai`, `nalsa`.

5. **NJDG stamps:** 43 rows have `njdg_stamp_valid=FALSE`. AFT's absent stamp has blank validity and NA verdict. Do not treat blank as TRUE.

6. **Metadata:** every required key is present, but calibration metadata is **not complete**. Exact model version, actual temperature, token counts and cost are unavailable and are null with reasons. The context is labelled as a repo-hosted session with peer-summary exposure. `calibration_eligible=false`. The shared prompt is byte-preserved with SHA-256 `81136dad77f0e2381729244a3e565bb00444427c8a851c2b47bddaa5ea0ce21d`. Do not replace unknown usage with zero or claim the requested 0.2 temperature was used.

NGT arithmetic also needs review: 1,937 / 1,976 = 0.9803 at four decimals, rather than 0.9813. This does not validate the underlying counts. The current July dashboard can be conditionally back-calculated to April pending 5,698, so a newer 5,890 does not by itself refute the April value.

CSV: `codex__verify-trib-01__agriya__20260906_042259.csv`. Metadata: `codex__verify-trib-01__agriya__20260906_042259.meta.json`. Source archive: `fetch_log/`. Validation: `validation.json`.

Commit message: `Add Codex tribunal verification sample`.
