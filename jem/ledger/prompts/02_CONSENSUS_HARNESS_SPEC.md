# The intra-run consensus harness

The shared pipeline for any agent research-based data entry. C, K, and the
report-publication track all run *inside* this. It is the FIRST of four
consensus rungs:

```
intra-run (this spec) → inter-model raters (Prajna/Agriya + others)
                      → gold set → expert adjudication
```

Each rung catches what the one below cannot: the critic catches what a single
researcher rationalises; the multi-model rung catches one model's blind spot;
the gold set catches shared bias that agreement cannot.

## Per-cell flow

```
0. LIVENESS PRE-GATE        (deterministic, no LLM) ── fail-fast, token saver
1. RESEARCHER               (fetch → extract → propose entry + citation)
2. VERIFIER (+scorer)       (re-check claim vs CLAIMED source only; score researcher)
3. CRITIC                   (adversarial; TOKEN-GATED — suspect/sampled only)
4. RECONCILE                (deterministic merge → verdict + confidence)
5. LEDGER                   (append everything, labelled)
```

### 0 · Liveness pre-gate (deterministic)

Before any URL is accepted as a citation input, an HTTP HEAD/GET runs in the
harness — no LLM. Reject if: non-200; redirects to site root; content-type
mismatch (HTML where a PDF/table is claimed); or the URL is a bare homepage when
a document is claimed. A dead or homepage link is rejected **before** any
research token is spent. This is simultaneously the correctness gate that kills
homepage-backfill laundering and the cheapest possible token saver.

### 1 · Researcher

Fetches the primary source, extracts the value/fact, proposes the entry with a
direct document citation. **Bounded within-run retry:** on failure the researcher
reformulates its *search strategy* (never its prompt) — escalating through the
source map (own site → parent ministry → Lok Sabha/PIB → the report PDF), to a
hard cap of **N ≤ 3 attempts**, each attempt + query + result logged. After N it
returns `unsourced after documented attempts` — a strong, critic-defensible
negative, not a lazy blank.

> The agent adapts *tactics*; only the maintainer adapts *config*. The researcher
> never rewrites its governing prompt — that forks `prompt_version` silently. The
> prompt changes only through the registry's versioned revision loop.

### 2 · Verifier (+ performance scorer)

Independently re-fetches the **claimed** URL only (no re-research), confirms the
value appears there and the source is type-eligible, and emits a verdict
(`CONFIRM` / `REFUTE` / `UNSOURCED` / `NA`) plus a **score for the researcher**
(`supported` / `partial` / `unsupported`). Scores aggregate per (agent, context)
into the calibration signal.

### 3 · Critic (token-gated, separable, differently-modelled)

Runs only when a cell is suspect: single-source, low source authority, an anomaly
telltale (42-ladder, 365-day, round thousands, derived-equals-formula), a
gap-discovery candidate, or a random audit sample. Adversarial and terse: wrong
period? homepage not document? more-authoritative primary exists? Is a claimed
relationship's endpoint even in the graph? **The critic is the same artifact as
the public inspection prompt** (file 08) — run it on a *different* base model for
independence internally; publish it for outside audit. One artifact, two
audiences.

### 4 · Reconcile (deterministic)

Merges researcher entry + verifier verdict + critic note into an internal verdict
and a confidence tier. No LLM — committed code, re-runnable in CI.

## Capture-and-label (the ingest boundary)

The ledger is greedy: **nothing is dropped at capture.** Every finding is stored
with a status label, and filtering to canon happens only at the *promotion*
boundary.

| label | meaning | promotes to canon? |
|-------|---------|--------------------|
| `sourced` | primary contains the value at a live document URL | yes |
| `homepage_only` | value seen but only on a homepage/non-document | no (kept in ledger) |
| `secondary_only` | only secondaries; no primary | no |
| `unsourced_candidate` | proposed but unverified after N attempts | no |
| `fetch_failed` | source unreachable | no |
| `partial` | some fields sourced, others not | field-wise |
| `refuted` | primary gives a different value | no (verified value noted) |

The honest gap lives in canon; the attempt survives in the ledger. This is also
what makes a "no reports found" verdict credible — the ledger shows what was
checked.

## Confidence, weighted by model diversity

Confidence is **agreement × diversity**, not agreement count. Diversity =
distinct base-model families in the agreeing set (two runs of one model = one
family).

- promotion above `partial` requires **diversity ≥ 2** distinct families
- `shared_bias_risk: high` fires when agreement is high but diversity = 1
- tiers: `unsourced` → `partial` (1 primary) → `partial_approaching_complete`
  (1 primary + 1–2 independent secondaries) → `complete` (2+ primary, or 1
  primary + 3+ independent secondaries) → `verified` (direct GoI primary URL that
  contains the value). Independent secondaries: two outlets reprinting one
  wire/PDF = one affirmation.

## Gap-discovery (surface what's missing, not only what's wrong)

When a researcher hits a claimed relationship whose endpoint is not in the graph,
or a body that should exist and doesn't, it emits a **suggested entity** and/or
**suggested edge** to the ledger — flagged `unverified`, cited to the specific
provision the critic must confirm in primary text, maintainer-reviewed, never
auto-applied. Canonical example this batch: `ifsca` (RegulatoryBodyQJ) +
`ifsca AppealableTo sat`, to be confirmed against the IFSCA Act 2019 primary
text before promotion.

## Ledger record (append-only, committed)

`ledger/runs/{track}__{model}__{user}__{timestamp}.jsonl`, one object per cell:

```json
{ "entity_id":"", "field":"", "track":"", "prompt_version":"",
  "model":"", "model_version":"", "context":"", "temperature":0.2,
  "liveness":{"url":"","status":200,"is_document":true},
  "researcher":{"value":"","source_url":"","attempts":[]},
  "verifier":{"verdict":"CONFIRM","researcher_score":"supported","source_url":""},
  "critic":{"ran":true,"challenge":"","upheld":true},
  "reconcile":{"label":"sourced","confidence_tier":"partial","model_diversity":1,
               "shared_bias_risk":"low"},
  "suggested_entities":[], "suggested_edges":[],
  "tokens_in":0, "tokens_out":0, "timestamp_utc":"" }
```

Canon = a replayable derivation over `label == sourced` (+ promotion rule).
Re-run the derivation, reproduce the canon: that is the whole transparency claim.

## Token discipline (built into the shape)

Liveness is free (HTTP). Verifier is one fetch. Critic is gated, not universal.
Reconcile is code. So a clean cell costs 2 LLM passes (researcher + verifier); a
suspect cell costs 3. Never 3× across the board. The N≤3 retry cap and the
liveness pre-gate bound the fetch spend.
