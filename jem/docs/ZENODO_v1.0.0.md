# Zenodo release v1.0.0 — upload guide (updated July 2026)

**Git ref:** `v1.0.0` → commit `f3a5904` (`main`)  
**Corpus:** 1,145 entities · 1,835 relationships · 0 orphan nodes · 187 high/severe IR

---

## Option A — GitHub integration (now enabled)

Your Zenodo settings show `datastiltskin/jem` linked with the toggle **ON**.

1. Push the tag (if not already on GitHub):
   ```bash
   git push origin v1.0.0
   ```
2. Zenodo auto-ingests the tag and creates a draft deposit.
3. Open [zenodo.org/account/settings/github/repository/datastiltskin/jem](https://zenodo.org/account/settings/github/repository/datastiltskin/jem) → review the new release draft.
4. Edit metadata (use abstracts below) → **Publish**.

**Note:** GitHub integration produces **one archive per tag** (full repo tarball). For **split DOIs** (dataset CC0 + software MIT), still use Option B for Record 1 and Record 2, and link the GitHub-generated deposit as a related identifier.

---

## Option B — Manual split uploads (recommended for papers)

Pre-built archives (`python3 jem/scripts/package_zenodo_release.py --ref v1.0.0`):

| File | Record | Licence |
|------|--------|---------|
| `build/zenodo/jem-dataset-1.0.0.zip` | Dataset | CC0 |
| `build/zenodo/jem-software-1.0.0.zip` | Software | MIT |

### Dataset Zenodo abstract

```
Judiciary Entity Map (JEM) is an open, source-linked structural dataset of India's
judicial and quasi-judicial ecosystem. Release v1.0.0 (July 2026) contains 1,145
entities and 1,835 typed relationships spanning constitutional courts, high court
benches, subordinate court lattices, central and state tribunals, regulatory bodies,
consumer commissions, ombudsmen, and the appointment, funding, audit, complaint,
and appellate chains that connect them.

Zero orphan nodes under strict graph-reference checking. Entity schema v0.1.0.
Licence: CC0 1.0.

Git tag: v1.0.0 (commit f3a5904).
```

### Software Zenodo abstract

```
Software companion to JEM dataset v1.0.0: static web map (vanilla JS, D3),
semantic-zoom renderer, and Python pipeline (validate, derive, build).
Licence: MIT. Pair with the dataset Zenodo record (CC0).
```

---

## Post-publish

- Paste dataset DOI into root `CITATION.cff`
- Paste software DOI into `jem/CITATION-software.cff`
- Cross-link all three Zenodo records (GitHub archive + split uploads)
