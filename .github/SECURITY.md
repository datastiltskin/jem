# Security policy

JEM is an open structural map (YAML → `graph.json` → web UI) with an optional researcher infrastructure layer (FastAPI, MCP tools, SQLite). There are no user accounts and no secrets in the public dataset.

**Do not commit:** `jem/data/jem.db`, `jem/.env`, API keys (`ANTHROPIC_API_KEY`), or ephemeral `.claude/outputs/`. Use `jem/.env.example` as a template.

## Reporting

- **Data integrity / malicious PRs:** [GitHub security advisory](https://github.com/datastiltskin/jem/security/advisories/new) (private report to maintainers).
- **Production hosting:** [@dso6060](https://github.com/dso6060) via GitHub — not handled by co-maintainers by default.

## Scope

In scope: tampered YAML intended to misrepresent institutional facts, compromised GitHub Actions workflows, dependency supply-chain issues in `jem/scripts/requirements.txt` and `jem/scripts/requirements-dev.txt`, exposed API keys in commits.

Out of scope: Disagreement with structural interpretation of law (use contested-fact process instead).
