# JEM GitHub Pages site

This folder is the published **orchestration dashboard** — the repository's clickable community page, not the interactive map.

- Live (after Pages is enabled): https://datastiltskin.github.io/jem/
- Map (product): https://friedso.com/apps/jem/
- Source HTML: `jem/ledger/dashboard/index.html`
- How to enable / regenerate: `jem/docs/GITHUB_PAGES.md`

Regenerate with:

```bash
cd jem
python3 scripts/harness/render_orchestration.py
python3 scripts/harness/publish_dashboard.py
```
