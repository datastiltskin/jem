# RATER CARD — Prajna · DeepSeek

<!-- Paste this ABOVE verifier_prompt.md. Do not edit verifier_prompt.md itself. -->

```
rater: prajna
harness: DeepSeek API + script
model: deepseek-v4-flash
model_version: deepseek-v4-flash
```

- **Web fetch is the gating dependency.** Your script **must** wire a live
  search/fetch tool (Tavily, SerpAPI, or direct HTTP fetch of the PDFs/pages).
  **DeepSeek answering from model knowledge alone is NOT verification** — it will
  confidently reproduce plausible caseloads, which is exactly the failure this
  pass exists to catch. If you cannot wire a fetch tool, stop and tell DSo before
  running.
- **Loop:** one entity per iteration; append rows incrementally; save fetched
  documents to `out/fetch_log/`.
- **Context arm (identical to Agriya):** provided files + web search only,
  temperature 0.2. Same prompt (`verify-trib-v1`), same output header, same
  context string. The only intended difference between your run and Agriya's is
  the **model** — keep everything else matched or the agreement table measures
  tooling, not models.
- **Method self-check:** SAT should verify to 1,066 / 429 / 323 from SEBI AR
  2025-26 Table 10.35 (re-derive, don't copy). Landing on 420/380/345/365 means a
  stale snapshot leaked in — stop and flag.

See `RUN_SETUP.md` for the folder layout, `meta.json` fields, and the 6-point
summary to return to DSo.
