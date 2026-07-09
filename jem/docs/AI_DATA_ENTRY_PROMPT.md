# JEM — uniform AI data-entry prompt

Copy everything inside the **prompt box** below into **Claude**, **Cursor Agent**, or **ChatGPT** (with the JEM repo open as context). One prompt for co-maintainers and contributors; your **role** and **task** lines control what the assistant may do.

**Phased build tasks (→ 1,500+ entities):** pick a `TASK` from [`ENTITY_BUILD_ROADMAP.md`](ENTITY_BUILD_ROADMAP.md) — use only prompts listed under **Active prompts**; done categories are archived there.

**Canonical file:** `jem/docs/AI_DATA_ENTRY_PROMPT.md`

---

## Who uses which workflow

| Role | What you do | What maintainers do |
|------|-------------|---------------------|
| **Contributor** | Use the prompt + a roadmap `TASK` → produce YAML **drafts** → **[GitHub issue only](https://github.com/datastiltskin/jem/issues/new?template=data_correction.yml)** with attachments | `validate.py`, merge, relationships, release |
| **Co-maintainer** | `ROLE: co-maintainer` → validate locally → PR | Review issues; merge; wire relationships |

| Rule | Detail |
|------|--------|
| **Submissions** | **GitHub issues only** (no email) |
| **New entities** | Contributors may submit **proposed** YAML; maintainers merge after validation |
| **Relationships** | **Maintainer-only** — contributors must not submit relationship YAML |

---

## Prompt box (copy from line below through end of code fence)

```
You are helping with Judiciary Entity Map (India) — JEM, an open CC0 structural dataset of Indian courts, tribunals, regulators, and related bodies. You are working in a clone of the JEM repository.

=== REPO CONVENTIONS (do not violate) ===
• Map STRUCTURE only: appointment chains, funding, oversight, appellate paths, complaint mechanisms, operational status, case-volume fields when sourced — NOT case outcomes, NOT individual judge names, NOT editorial opinions.
• Entity IDs: permanent snake_case (e.g. hc_madras, mh_district_court_pune). Never rename an existing id.
• data_quality: use partial unless every changed fact has a primary GoI source URL; never set verified without official sources; never set derived.scores_validated (maintainers only).
• Primary sources (in order): india-code.nic.in, egazette.gov.in, main.sci.gov.in, official ministry/HC sites, doj.gov.in, NJDG/e-Courts URLs, PIB, law commission. Avoid Wikipedia and news-only citations.
• Schema: read jem/data/schema/entity_schema.yaml and jem/data/schema/relationship_schema.yaml before writing YAML.
• Templates: copy the closest existing file under jem/data/entities/ (same type/cluster/state). Match field names and nesting exactly.
• Paths: new state entities usually go under jem/data/entities/_generated/states/{state_code}/. Relationships: MAINTAINER-ONLY — do not output relationship YAML unless ROLE is co-maintainer and TASK explicitly says to wire edges.
• Do NOT run generate_v1_states_bundle.py unless the user explicitly asks (high overwrite risk).
• Do NOT hand-edit jem/data/derived/ or commit graph.json unless the user is a maintainer running a release build.
• Phased work: read jem/docs/ENTITY_BUILD_ROADMAP.md — only execute TASKs for categories still marked pending or updated.

=== YOUR SESSION ===
ROLE: [contributor | co-maintainer]
TASK: [from ENTITY_BUILD_ROADMAP.md Active prompts, or custom one sentence]
CATEGORY_ID: [e.g. C15 UP pack — for issue title]
ENTITY_ID (if editing existing): [id or none]
STATE / CLUSTER (if relevant): [e.g. KL, regulatory_bodies, backbone]
PRIMARY SOURCES I HAVE: [paste URLs and access dates]

=== IF ROLE = contributor ===
1. Read the relevant existing YAML if ENTITY_ID is set; otherwise find the closest template entity.
2. Produce ONLY entity YAML file(s) as deliverables — sources[] on every factual claim you add or change.
3. At the top of your reply, list: CATEGORY_ID, files to create/update (paths), entity ids touched, table field | new value | source URL.
4. Tell the user to open a GitHub issue only (data correction template or new issue titled [data] CATEGORY_ID …) and attach YAML. Do NOT claim merged or verified.
5. New entity ids: allowed only as proposed drafts for maintainer review (per TASK). Never submit relationship YAML or rel_* files.

=== IF ROLE = co-maintainer ===
1. Same quality rules as contributor.
2. Relationships: only when TASK says maintainer wiring; then edit jem/data/relationships/ and run validate_graph_refs.py.
3. After editing, run from jem/ and report output:
   python3 scripts/validate.py --strict
   python3 scripts/validate.py --entity <path>
   python3 scripts/validate_graph_refs.py
   python3 scripts/derive.py
4. Suggest commit: data(scope): description. If category complete, remind user to update ENTITY_BUILD_ROADMAP.md + README entity table to done and archive prompt.
5. Production deploy is founder-only; PR needs CI + CODEOWNERS.

=== OUTPUT FORMAT ===
• Complete YAML in fenced blocks; first line: # jem/data/entities/...
• Missing facts: null + data_quality_notes; do not invent.
• Conflicts: data_quality contested + both sources.
• End with: suggested GitHub issue title and checklist for contributor.

=== TASK-SPECIFIC INSTRUCTIONS (paste from ENTITY_BUILD_ROADMAP.md or custom) ===

Begin by stating ROLE, CATEGORY_ID, and TASK; list files you will read; then deliver.
```

---

## After the assistant responds

**Contributors**

1. Save YAML from the chat.
2. Open a **[GitHub issue only](https://github.com/datastiltskin/jem/issues/new?template=data_correction.yml)** — title `[data] C15 UP pack` (example), attach files, include the field/source table.
3. Maintainers validate: `python3 scripts/validate.py --entity path/to/file.yaml`

**Co-maintainers**

```bash
cd jem
pip install -r scripts/requirements.txt
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py
python3 scripts/derive.py
```

When a **category is complete:** set status **done** in `ENTITY_BUILD_ROADMAP.md`, archive the prompt, sync [README entity build progress](../../README.md#entity-build-progress).

---

## Optional one-liner (Cursor)

> Follow `jem/docs/AI_DATA_ENTRY_PROMPT.md`; ROLE co-maintainer; TASK from `ENTITY_BUILD_ROADMAP.md` P1-A.

---


