# JEM — uniform AI data-entry prompt

Copy everything inside the **prompt box** below into **Claude**, **Cursor Agent**, or **ChatGPT** (with the JEM repo open as context). One prompt for co-maintainers and contributors; your **role** and **task** lines control what the assistant may do.

**Canonical file:** share this link after the GitHub repo is published: `jem/docs/AI_DATA_ENTRY_PROMPT.md`

---

## Who uses which workflow

| Role | What you do | What maintainers do |
|------|-------------|---------------------|
| **Contributor** | Use the prompt to produce or fix YAML **drafts** with primary sources; share files (GitHub issue, PR, or email) | Run `validate.py`, merge into `jem/data/`, run full pipeline, release |
| **Co-maintainer** | Same prompt with `ROLE: co-maintainer`; may open PRs after local validation | Review contributor drafts; merge; coordinate with `@dso6060` on deploy |

**v0.9 default:** community **data-quality upgrades** on existing entities. New entities and new relationships are **maintainer-approved** — contributors still may submit **draft** YAML for review.

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
• Paths: new state entities usually go under jem/data/entities/_generated/states/{state_code}/. Relationships go in jem/data/relationships/ (existing pack or new file only if maintainer-approved).
• Do NOT run generate_v1_states_bundle.py unless the user explicitly asks (high overwrite risk).
• Do NOT hand-edit jem/data/derived/ or commit graph.json unless the user is a maintainer running a release build.

=== YOUR SESSION ===
ROLE: [contributor | co-maintainer]
TASK: [one sentence — e.g. "Upgrade sources for hc_allahabad" OR "Draft YAML for Kerala SERC" OR "Fix case_volume on tn_district_court_chennai from NJDG"]
ENTITY_ID (if editing existing): [id or none]
STATE / CLUSTER (if relevant): [e.g. KL, regulatory_bodies, backbone]
PRIMARY SOURCES I HAVE: [paste URLs and access dates]

=== IF ROLE = contributor ===
1. Read the relevant existing YAML if ENTITY_ID is set; otherwise find the closest template entity.
2. Produce ONLY the YAML file(s) as deliverables — complete, valid-looking content with sources[] on every factual claim you add or change.
3. At the top of your reply, list: files to create/update (paths), entity ids touched, and a table of field | new value | source URL.
4. Tell the user to submit via GitHub "Data correction" issue or PR (data-quality scope) OR send the YAML to maintainers for validation and merge. Do NOT claim the data is merged or verified.
5. Do not add new relationship topology or new entity ids unless TASK explicitly says "draft for maintainer review" and user provided maintainer approval in chat.

=== IF ROLE = co-maintainer ===
1. Same quality rules as contributor.
2. After editing, run these commands from jem/ and report full output:
   python3 scripts/validate.py --strict
   python3 scripts/validate.py --entity <path>   # for single-file edits
   python3 scripts/validate_graph_refs.py
   python3 scripts/derive.py
   # build.py only if user wants to refresh graph.json for local preview
3. Suggest a commit message: data(scope): short description
4. Remind: friedso.com deploy is founder-only; PR needs CI green + CODEOWNERS review.

=== OUTPUT FORMAT ===
• Show complete YAML file contents in fenced blocks with path comment on first line: # jem/data/entities/...
• For relationship changes, show relationship YAML snippets with rel_* ids following rel_{source}_{type}_{target} pattern.
• If information is missing, leave fields null and explain in data_quality_notes — do not invent facts.
• If two primary sources conflict, set data_quality: contested and cite both; do not pick a winner.

=== TASK-SPECIFIC INSTRUCTIONS (user fills in) ===
[Paste any extra instructions, pasted statute text, NJDG export rows, or field-level corrections here.]

Begin by stating ROLE and TASK, listing files you will read, then produce deliverables.
```

---

## After the assistant responds

**Contributors**

1. Save YAML from the chat into file(s) with the paths the model named.
2. Open a [data correction issue](https://github.com/dso6060/REPO_NAME/issues/new?template=data_correction.yml) or email maintainers (Divya Sornaraja / Prajna Prayas — see `TEAM.md`).
3. Maintainers run validation and merge.

**Co-maintainers**

```bash
cd jem
pip install -r scripts/requirements.txt
python3 scripts/validate.py --strict
python3 scripts/validate_graph_refs.py
python3 scripts/derive.py
# optional preview: python3 scripts/build.py
```

---

## Optional one-liner (Cursor)

Add to Cursor rules or paste at start of a Composer session:

> Follow `jem/docs/AI_DATA_ENTRY_PROMPT.md` prompt box; my ROLE is co-maintainer; TASK is: [your task].

---

*Regenerate Word export including this section: from repo root, `pandoc jem/docs/KNOWLEDGE_TRANSFER.md -o jem/docs/JEM_Knowledge_Transfer.docx`*
