# Tribunal appellate gap audit — research task

Read `jem/CLAUDE.md`, `graph.json` (repo root), and `jem/data/relationships/tribunal_appellate_completion_jun2026.yaml`.

## Your task

Produce a markdown gap audit listing tribunal and quasi-judicial entities that still lack **verified** appellate-chain edges after the Jun 2026 completion batch.

## Rules (non-negotiable)

1. **No invented statutes, sections, or entity ids.** Every proposed edge must cite a primary source (India Code URL, Gazette notification, or official GoI/tribunal website).
2. Mark each item `verified` | `partial` | `blocked` with reason.
3. Distinguish:
   - statutory appeal (`is_binding: true`)
   - writ-only review (`is_binding: false`, constitutional_basis)
4. Flag duplicate entities (e.g. `tnerc` vs `serc_tn`).
5. Electricity: cite Electricity Act 2003 ss.111, 125 — note friedso.com TANGEDCO dispute research as **secondary context only**, not primary source.
6. Do not write YAML files — markdown report only.

## Output sections

1. Executive summary (counts)
2. Tier 1 — central tribunals still missing outgoing appellate
3. Tier 2 — missing incoming (upstream) edges
4. Tier 3 — state tribunals / generics needing per-state wiring
5. Regulators (RegulatoryBodyQJ) with adjudicatory orders needing appeal paths
6. Recommended next batch (prioritized, max 30 edges) with statutory_basis per edge

Respond with markdown only.
