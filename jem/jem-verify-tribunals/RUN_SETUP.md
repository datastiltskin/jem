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
