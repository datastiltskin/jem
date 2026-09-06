# Tribunal verification handoff

Start with [the six-point summary](SUMMARY.md). This is a review and pipeline sample for `verify-trib-01`. It is **not eligible for blinded model-agreement calibration**. The metadata records uncontrolled model settings, unknown usage and cost, repo-hosted context, and exposure to the peer summary appended to the shared setup file.

The result covers the full 140-row, 44-entity claims file. The locally attached 17-row sample was not substituted for it. Canonical JEM data was neither inspected nor changed during verification. Agriya subsequently requested this handoff on the `verifier/codex` branch at `jem/jem-verify-tribunals/out/`. No PR or message to DSo is part of this handoff.

The metadata's `record_scope` distinguishes the original verification from later packaging. Its `committed=false` and `pushed=false` fields describe the original run, and its `handoff` entry records the publication context. Relocation and publication do not make this an independent or controlled experiment.

Files:

- `codex__*.csv` and the matching `.meta.json` are the requested handoff pair. `run_artifacts.json` gives their exact names.
- [SUMMARY.md](SUMMARY.md) contains all six requested points and every REFUTE.
- [evidence.json](evidence.json) records primary-document observations, conflicting figures, date and scope limitations, arithmetic diagnostics, and source URLs.
- [validation.json](validation.json) separates artifact checks from failed calibration requirements.
- `inputs/` preserves the shared prompt, claims, card and setup bytes. The export script pins the prompt read-only. Git does not preserve that permission, so SHA-256 is the portable integrity check after cloning. **RUN_SETUP.md contains peer findings and must not be read by a future blinded rater.**
- `fetch_log/` contains HTTP response bodies, headers, timestamps and SHA-256 hashes in `manifest.jsonl`, extracted text, OCR, selected table images, and 15 archived web-search result batches. `.response` files beginning with `%PDF` are PDFs. Search snippets do not establish verified counts.
- [publication_sanitization.json](publication_sanitization.json) records removal of HTTP session cookies and HTML CSRF values before publication. Download hashes remain recorded separately where bytes changed. Primary case-count PDFs are unchanged.
- [changes.diff](changes.diff) shows the text handoff additions. Large source archives and unchanged supplied inputs are excluded from that review diff.

Interpretation:

- A numeric REFUTE has a direct primary source and a proposed replacement. Both pending-count replacements disclose a start-of-day boundary assumption. If that convention is inappropriate, downgrade them to UNSOURCED until an exact-date source is obtained.
- UNSOURCED means this search did not establish the field at the input's period and scope. Related figures appear in notes, with `verified_value` left blank. It is not proof that a number is fabricated or unpublished.
- Input `last_year` has no explicit calendar, fiscal or rolling interval. Do not silently select one or replace a December 2024 snapshot with a later figure.
- `primary_count` counts documents grounding the verdict or replacement, not every document examined. A reviewed primary can therefore appear on an UNSOURCED row with count zero. Reviewed and attempted URLs appear in notes.
- For stamps, REFUTE challenges NJDG applicability. `verified_value=absent` recommends removal, it does not claim the supplied stamp was absent. The source rule is explicit in the prompt and supported by NIC's description. AFT has no stamp to assess, so NA and blank validity apply.
- No independent secondary affirmations were counted. Repeated government returns were not treated as independent confirmations.
- Arithmetic agreement alone does not establish filing/disposal counts. SAT's verified FY2025-26 anchor is retained separately from the older claims. NGT's stored rate fails its own arithmetic.

Reproduce the local export and validation with Python 3.9 or newer. From the repository root:

```sh
cd jem/jem-verify-tribunals
python3 out/build_verification.py
python3 out/validate.py
```

This rebuilds the CSV from the recorded review decisions. It does not rerun a model or perform a new independent verification. It reuses the existing result basename, so only one CSV and matching meta remain. Both scripts are confined to their own `out/` directory. The CSV flushes after each entity.

The fetch helper used `curl` and `pypdf==6.8.0`. To fetch additional sources, first install the extraction dependency into the output folder. These commands also run from `jem/jem-verify-tribunals/`:

```sh
python3 -m pip install --no-cache-dir --target out/_vendor pypdf==6.8.0
python3 out/fetch.py unique_label 'https://official.example/report.pdf'
```

Use a new label to preserve earlier responses. A failed fetch is logged, and no number is inferred from it. The helper limits HTTPS downloads to 100 MB and 40 seconds. Some failed attempts have headers but no body. The initial SAT download predates the manifest, and a second timestamped fetch (`sat_recheck`) anchors its provenance. The two SAT bodies have been compared by hash.

Before publishing any additional downloads, run `python3 out/sanitize_archive.py` and rebuild the export so the evidence catalog reflects the publication hashes. This removes session material from the archive and records its changes without preserving token values.

Scanned MERC, CCI and Maharashtra consumer reports were processed with macOS PDFKit and Vision using `ocr.swift`. Key SAT, CESTAT, Karnataka consumer, MERC and CCI tables were also rendered using `render.swift` and visually inspected. OCR is an aid and can contain errors. The Maharashtra archive has mismatched link labels and internal report dates, which are explicitly flagged.

Generated dependency and compiler caches were removed from this handoff. Source files and extraction results remain available offline. The review diff can be refreshed with `python3 out/make_diff.py` after regenerating the artifacts.

Commit message: `Add Codex tribunal verification sample`.
