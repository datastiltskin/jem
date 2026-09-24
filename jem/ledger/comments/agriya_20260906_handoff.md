# Comment — Agriya Codex handoff (2026-09-06)

Recorded as a ledger comment when the inter-model consensus rung was first
exercised on `integrate/consensus-20260906`. This is provenance, not a
protocol waiver. Agriya's `meta.json` already sets `calibration_eligible=false`.

## Email (Agriya → Divya and Prajna)

> Dear Divya and Prajna,
>
> Thanks for sending these details, and apologies for the delay! I have pushed
> a branch containing the Codex verifier output (I ran it again today after
> realising I messed something up in the prompt). Please note that I have not
> verified it in detail myself beyond a cursory look, but it covers all 44
> entities and 140 claims, with the CSV, metadata, six-point summary, and
> primary-source archive included. I hope you find some of it useful, and
> please let me know whenever you would like me to run something again. You
> can use it to exercise the consensus pipeline. This run may not be eligible
> for blinded calibration IMO, because the setup file exposed Prajna's
> summary, and some required model/settings metadata was unavailable (some of
> those limitations are documented). I used the newly released GPT-6 Astra at
> Ultra effort for this pass.
>
> Here is the branch:
> https://github.com/datastiltskin/jem/tree/verifier/codex/jem/jem-verify-tribunals
>
> Best,
> Agriya

## What the pipeline does with this

- Join Prajna `deepseek__verify-trib-01__prajna__20260831_131656.csv` and
  Agriya `codex__verify-trib-01__agriya__20260906_042259.csv` on
  `(entity_id, field)`.
- Diversity = `{deepseek, gpt}` = 2 families when both rows exist.
- **Do not promote** any cell to canon from this sample.
- **Do not** count this pair in blinded model-agreement calibration.
- Surface period disagreements (SAT-shaped: later-FY primary vs stored
  2024-12-01 snapshot) on the expert queue.
