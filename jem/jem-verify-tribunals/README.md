# Agriya's tribunal verifier handoff

Batch `verify-trib-01`, prompt `verify-trib-v1`, 44 entities and 140 claims.

Start with [DSo's six-point summary](out/SUMMARY.md). The [output folder](out/) contains the requested CSV and matching metadata, primary-source archive, evidence notes, and validation results. It uses the same output path as the `verifier/deepseek` branch so DSo can retrieve the two submissions separately.

| Requested item | Available result |
| --- | --- |
| Full claims verification table | [Codex CSV](out/codex__verify-trib-01__agriya__20260906_042259.csv), one row per input key |
| Run metadata | [Matching meta.json](out/codex__verify-trib-01__agriya__20260906_042259.meta.json), with explicit unknowns and deviations |
| Six-point response | [SUMMARY.md](out/SUMMARY.md), including every REFUTE and source URL |
| Live primary evidence | [Fetch archive](out/fetch_log/) and [evidence catalog](out/evidence.json) |
| SAT method check | Recomputed 1,066 pending, 429 filed and 323 disposed from the archived SEBI table |
| NJDG stamp check | 43 present stamps marked invalid, AFT's absent stamp marked NA |
| Validation | [validation.json](out/validation.json), separating artifact validity from calibration eligibility |
| Canonical data boundary | No case-volume or source rows changed in canonical JEM data |

**Use this submission for pipeline testing and human source review.** A blinded calibration run remains outstanding. The setup file exposed the peer summary, the model's exact serving version and sampling settings were unavailable, and usage/cost were unmeasured. `calibration_eligible=false` must remain attached to this sample.

The two numeric REFUTEs also disclose reporting-boundary assumptions. DSo should resolve those assumptions and the undefined `last_year` intervals before applying any changes. The output is a verifier submission, and does not perform reconciliation or regeneration.

Run the portable checks from the repository root:

```sh
python3 jem/jem-verify-tribunals/out/validate.py
```

See [the output README](out/README.md) for interpretation, provenance and export instructions. Only this handoff directory belongs to the commit. The original local `attachments/` folder is excluded.
