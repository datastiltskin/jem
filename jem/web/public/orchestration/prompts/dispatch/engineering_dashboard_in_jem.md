# Engineering dashboard in the JEM page flow

Route: `#/engineering`
Entry: About → Navigate this site → Engineering dashboard
JSON: `web/public/consensus_dashboard.json` (copy of `ledger/derived/…`)

Entity-page consensus notes are **sampled on SAT only**
(`CONSENSUS_NOTES_JEM_WIDE = false` in `web/src/consensusNotes.js`).
Do not flip JEM-wide until the SAT sample is confirmed.

Local preview of applied SAT figures:
`jem/web/?graph=staging#/entity/sat`
requires `web/public/graph.staging.json` (copy of `build/graph.staging.json`, gitignored).
