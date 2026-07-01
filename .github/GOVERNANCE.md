# JEM — governance (v0.9)

Lightweight rules for maintainers and future reviewers. Full context: [`jem/docs/KNOWLEDGE_TRANSFER.md`](../jem/docs/KNOWLEDGE_TRANSFER.md).

## Roles

| Role | GitHub | Responsibilities |
|------|--------|------------------|
| **Founder / lead maintainer** | [@dso6060](https://github.com/dso6060) | GitHub | Data curation, schema, production deploy (private), final merge on disputed facts |
| **Co-maintainers** | Prajna Prayas · [@Prajna1999](https://github.com/Prajna1999); Agriya Khetarpal · [@agriyakhetarpal](https://github.com/agriyakhetarpal) | Equal review on PRs; shared CODEOWNERS; no production deploy unless delegated later |
| **Community contributor** | Any GitHub user | **Data-quality upgrades only** (sources, corrections, notes) via PR or issue |
| **Domain / legal reviewer** | *TBD* | Advisory review; does not merge unless granted write access |
| **Think-tank / institution liaison** | *TBD* | Batch review, methodology feedback; contact via Expert Review issue template |

Update [`jem/docs/TEAM.md`](../jem/docs/TEAM.md) when names and affiliations are confirmed.

## Contribution scope (v0.9)

| Allowed without prior approval | Maintainer-only |
|-------------------------------|-----------------|
| Fix sources, URLs, `accessed_date` | New `id` / new entity files |
| Upgrade `data_quality` with citations | New relationships / graph topology |
| Add `data_quality_notes` | Schema changes (`entity_schema.yaml`) |
| Correct factual fields with primary links | `derive.py` formula changes |
| Request `contested` flag with two sources | Generator runs on full `_generated/` trees |
| | Set `derived.scores_validated: true` |

Widening scope (new states, gap-registry entities) requires an explicit maintainer announcement in Discussions or README.

## Review & merge

1. **CI must pass** — `validate.py --strict`, `derive.py`, `validate_graph_refs.py` on PRs touching data/scripts.
2. **CODEOWNERS approval** — at least one listed owner (both maintainers when co-maintainer is added).
3. **`verified` and `scores_validated`** — only maintainers after primary-source check and `derive.py --explain <id>`.
4. **Contested facts** — prefer [Dispute escalation](DISCUSSION_TEMPLATE/dispute-escalation.yml) → issue with both sources → `data_quality: contested`; no silent “winner picks” in PR comments.

## Escalation

| Step | Channel |
|------|---------|
| 1 | GitHub **Discussion** (category: Disputes) or contested-fact issue |
| 2 | Maintainer internal sync (founder + co-maintainer) |
| 3 | Optional: **Expert review** issue — tag `expert-review` when legal/think-tank reviewer is onboarded |
| 4 | YAML updated with `contested` or agreed correction + sources |

## Repository settings (checklist when repo is created)

- [x] Public repo under `@datastiltskin`
- [ ] Enable **Discussions**
- [ ] Branch protection on `main`: require PR, require status checks, require CODEOWNERS review
- [ ] Allow squash merge; disallow force-push to `main`
- [x] Add co-maintainers as **Admin** and keep `CODEOWNERS` updated

## Deploy

**Canonical demo (attribution):** https://friedso.com/apps/jem/ — production deploy **founder only** unless delegated. Mirrors may host `jem/web/` + `graph.json` with courtesy credit to that URL.

### Branches

| Branch | Purpose |
|--------|---------|
| `main` | Active development (data + UI); may move ahead of production |
| `friedso_v1` | **Production line** for friedso.com — deploy only from here |

**Rules (GitHub ruleset `friedso_v1 production deploy`):**

- Changes reach `friedso_v1` via **pull request** (no direct pushes).
- Only [@dso6060](https://github.com/dso6060) can **merge** PRs into `friedso_v1` (ruleset bypass on pull requests).
- Co-maintainers work on `main`; founder promotes to `friedso_v1` after `./jem/scripts/deploy_friedso_production.sh` + smoke tests ([`V1_RELEASE_RUNBOOK.md`](../jem/docs/V1_RELEASE_RUNBOOK.md)).

Personal repos cannot use classic “restrict push to user” branch protection; the ruleset above enforces the same intent.
