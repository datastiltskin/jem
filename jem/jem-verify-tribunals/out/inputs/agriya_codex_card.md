# RATER CARD — Agriya · Codex

<!-- Paste this ABOVE verifier_prompt.md. Do not edit verifier_prompt.md itself. -->

```
rater: agriya
harness: Codex CLI + API
model: codex
model_version: <FILL — exact model string you invoke, e.g. the codex/gpt model id>
```

- **Loop:** one entity per iteration; append rows incrementally so a crash
  doesn't lose the run. Save every fetched PDF/page into `out/fetch_log/` for
  audit.
- **Context arm (identical to Prajna — this matters):** provided files + web
  search only, temperature 0.2. **Do NOT point Codex at any JEM repo clone for
  this run.** If your setup unavoidably indexes a repo, do not pretend it
  didn't — record `context: "repo-indexed"` in `meta.json` instead. A mislabelled
  context arm silently poisons the calibration study.
- **Web fetch is mandatory.** If Codex cannot fetch live pages/PDFs in this run,
  stop and tell DSo before starting. A verifier without sources is not a
  verifier.
- **Budget:** ~2–5M tokens for the whole 44-entity pass — comfortably inside
  your Pro window (to Sep 5). Run **this verifier pass first**; keep the
  regenerator pass for after.
- **Method self-check:** SAT should verify to 1,066 / 429 / 323 from SEBI AR
  2025-26 Table 10.35. Re-derive it; if your independent run lands there, your
  method is sound. If it lands on 420/380/345/365, something is reading a stale
  snapshot — stop and flag.

See `RUN_SETUP.md` for the folder layout, `meta.json` fields, and the 6-point
summary to return to DSo.
