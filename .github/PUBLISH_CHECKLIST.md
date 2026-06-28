# GitHub publish checklist

Repository: **https://github.com/dso6060/jem** (public)

## 1. Create repository

- [x] Create public repo `jem` under `@dso6060` (renamed from `jem_prototype`)
- [x] Push `main` with `.github/` scaffolding
- [x] Description: *Open structural map of India's judicial ecosystem — institutional capacity, relationships, and systemic gaps.*
- [x] Topics: `india`, `judiciary`, `open-data`, `legal-tech`
- [x] Homepage: https://friedso.com/apps/jem/
- [x] Maintainer contact: [@dso6060](https://github.com/dso6060) (GitHub Issues / security advisories only — no public email)
- [ ] Licence: MIT (code) — note in README that `jem/data/` is CC0

## 2. Replace placeholders

- [x] `REPO_NAME` → `jem` in issue templates, SUPPORT, CONTRIBUTING, roadmap, AI prompt (was `jem_prototype`)
- [x] Co-maintainer `@Prajna1999` in `CODEOWNERS` and `TEAM.md`

## 3. Repository settings

- [ ] **Settings → General → Features:** enable **Issues** and **Discussions**
- [ ] **Discussions → Categories:** ensure `Q&A` and `Disputes` (or map templates to existing categories)
- [ ] **Settings → Branches → `main`:** require PR, require status checks (`Validate JEM Data`), require CODEOWNERS review
- [x] **Branch `friedso_v1`:** production deploy line for friedso.com; ruleset `friedso_v1 production deploy` (PR required; merge bypass @dso6060 only)
- [x] Invite co-maintainer **@Prajna1999** as collaborator (admin); `CODEOWNERS` updated

## 4. Labels (create if not auto-created)

| Label | Color suggestion | Use |
|-------|------------------|-----|
| `data` | green | Data corrections |
| `community` | blue | Community-submitted |
| `needs-source` | yellow | Source requests |
| `contested` | orange | Conflicting sources |
| `expert-review` | purple | Think-tank / legal review |
| `triage` | gray | Needs maintainer routing |
| `bug` | red | Bugs |

## 5. Verify CI

- [ ] Open a test PR touching `jem/data/` — workflow `Validate JEM Data` passes
- [ ] Confirm `validate_graph_refs.py` runs in CI

## 6. Announce

- [x] Link canonical demo (attribution): https://friedso.com/apps/jem/
- [ ] Point contributors to `jem/docs/CONTRIBUTING.md` and data-correction template
