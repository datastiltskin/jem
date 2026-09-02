# Orchestration run — 2026-09-01 · data-integrity packet

Run record for the execution of `ledger/00_PACKET_INDEX.md`. Six agents, four of
them dispatched as subagents. This file is the answer to "who did what, in what
order, under what permissions, and how did each one actually work".

Timings are UTC on 2026-09-01. Where a time comes from a file mtime or a git
commit it is exact; where it comes from an agent's self-reported ledger field it
is marked, because agents turn out to be unreliable clocks (see §6).

Dashboard (tables + animated swimlane): `ledger/dashboard/index.html`.
Diagram: `ledger/diagrams/orchestration.png` (static) and
`ledger/diagrams/orchestration.gif` (animated, one frame per wave).

---

## 1 · Agent roster

| # | Agent | Model | Fired by | Mode | Assigned | Completed |
|---|---|---|---|---|---|---|
| 0 | **Packet locator** (`bc-c7cba901`) | Claude Opus 5 | user turn 1 | blocking | Find the orchestrator packet in the repo | Established it did not exist anywhere in repo or filesystem — the negative that stopped a fabricated run |
| 1 | **Orchestrator** (this agent) | Claude Opus 5 | user turn 2 | — | Apply S, run N, build harness, review and promote, commit | S schema, N refactor + counts, 4 harness modules, 35 tests, README reconciliation, 12 commits, PR #31 |
| 2 | **Track K** (`bc-0a2bab58`) | Claude Opus 5 (inherited) | Orchestrator, after S green | background, ∥ with 3 | TN criminal magistracy below District & Sessions | 1 entity (`cjm_nilgiris`), 2 suggested edges, 9 ledger cells, 4 documented refusals, live BNSS primary located |
| 3 | **Track C** (`bc-ce92556e`) | Claude Opus 5 (inherited) | Orchestrator, after S green | background, ∥ with 2 | TN commercial courts | 5 entities, 15 suggested edges, 18 ledger cells, 13/13 claims verified, the by-class finding |
| 4 | **N recount verifier** (`bc-5b97a96a`) | **GPT-5.6 Sol** | Orchestrator, after N artifact committed | background | Independently recompute the six buckets | PASS, exact match on all six buckets + 4 invariants |
| 5 | **Report-publication** (`bc-6944b0b0`) | Claude Sonnet 5 | Orchestrator, after host reachability probe | background | `report_publication` on 12 bodies | 12/12 complete, 14/14 cited URLs live, the regulators-publish/tribunals-don't pattern |

Agent 4 is on a different base-model family **on purpose**. The harness scores
confidence as agreement × diversity, so a recount by another instance of the
orchestrator's own model would have added a second opinion worth roughly zero.

---

## 2 · Firing sequence

```
turn 1   ── Agent 0 ── packet not in repo ── STOP, ask for files
                                              │
turn 2   ┌─────────────────────────────────────┘
         ▼
WAVE 1   Agent 1: apply S ──► validate --strict = 0 on untouched corpus
         (serial, blocking — the gate everything else validates against)
         │
         ├── commit 26570c7 (00:13)
         ▼
WAVE 2   Agent 1: harness liveness gate ──► runs it on the registry
         │        finds 0/12 pass, uncovers the India Code migration
         ├── commit 70e3b74 (00:19)
         ▼
WAVE 3   ┌──────────────┬──────────────┐   dispatched ~00:22, all concurrent
         ▼              ▼              ▼
      Agent 2        Agent 3       Agent 1 continues
      Track K        Track C       N refactor, counts artifact, inspector
      (disjoint      (disjoint     │
       file scope)    file scope)  ├── commit 45c9633 (00:27) counts artifact
         │              │          │
         │              │          ▼
         │              │       WAVE 3b  Agent 4 fired ── needs the artifact
         │              │                to exist before it can verify it
         │              │          │        │
         │              │          │        ▼ PASS 00:29 ──► back to Agent 1
         │              │          ├── commits c615238, 9c903c3, 125f39d, a5a1db6
         │              │          ▼
         │              │       WAVE 3c  Agent 1 probes 46 tribunal hosts
         │              │                34 reachable ──► Agent 5 fired ~00:39
         │              │                                    │
         ▼              ▼                                    │
      K returns      C returns                               │
      staging        staging                                 │
         └──────┬───────┘                                    │
                ▼                                            │
WAVE 4   Agent 1: verifier rung on staged output             │
         downloads each cited PDF, extracts text,            │
         confirms notification numbers present (6/6)         │
         ├── promote 6 entities ── commit b366291 (00:52)    │
         ▼                                                   ▼
WAVE 5   Agent 1: merge report blocks ◄──────────────── Agent 5 returns
         ├── commit 4d10a40 (00:55)
         ▼
WAVE 6   Agent 1: PR #31, CI green
```

**What forced the ordering.** S is serial because C, K and N all validate against
it; a moving schema would make their output look like schema errors. C ∥ K is
safe because their file scopes are disjoint (`tn/commercial/` vs `tn/criminal/`).
N runs last because it counts the corpus C and K enlarge. Agent 4 cannot fire
before the artifact it audits exists. Agent 5 is independent of all of them and
only waited on a reachability probe.

---

## 3 · Permissions

Every subagent was `generalPurpose`, which grants the full tool set: shell, file
read/write, `WebSearch`, `WebFetch`, `curl`. **The restrictions below were
instruction-level, not sandbox-enforced.** That distinction matters and is
revisited in §6.

| Capability | Agent 2 (K) | Agent 3 (C) | Agent 4 (recount) | Agent 5 (report) |
|---|---|---|---|---|
| Read repo | yes | yes | yes, except `derive.py` | yes |
| Write `jem/data/` | **denied** | **denied** | **denied** | **denied** |
| Write staging `/tmp/track_*` | yes | yes | n/a | yes |
| Write `ledger/runs/` | via orchestrator | via orchestrator | **yes, direct** | via orchestrator |
| Run `validate.py --entity` | yes | yes | no | yes |
| Run `derive.py` / `build.py` | **denied** | **denied** | **denied** | **denied** |
| `git add/commit/push` | **denied** | **denied** | **denied** | **denied** |
| Network (search + fetch) | yes | yes | not needed | yes |
| Liveness gate | yes | yes | n/a | yes |
| Apply relationships | **denied** (suggest only) | **denied** (suggest only) | n/a | n/a |

Agent 4 carries two prohibitions the others do not, and they are the whole point
of it: it may not read or import `derive.py`, and it may not open
`entity_counts.yaml` until its own numbers are recorded. A verifier that reads
the implementation under test is a mirror. It complied by extracting the
classification map through `ast` parsing rather than importing it.

Only Agent 4 wrote directly into `ledger/runs/`, because its output *is* a ledger
record. The generation agents wrote ledgers into staging and the orchestrator
copied them in at promotion, which keeps the ingest boundary in one place.

---

## 4 · How each agent actually worked

Reconstructed from the `attempts` arrays in `ledger/runs/`, not from the agents'
summaries.

### Agent 0 — packet locator

Filename globs (`*PACKET*`, `*orchestrator*`) → content search → git history
across all branches → filesystem-wide `.zip` search. Four independent strategies,
all negative, which is what made the conclusion safe to act on. **Handover:** back
to the user with "not present, please resend" rather than a reconstruction from
the screenshot.

### Agent 1 — orchestrator

Ordered by dependency rather than by the packet's file numbering: read all 12
files first, then checked two things that gate everything — whether the corpus
uses types the classification map lacks (it does, 5 of them), and whether the
primary-source domains resolve (mostly not). Both checks changed the plan before
any code was written. Applied S → ran the gate → built the liveness gate → ran it
on the registry, which is what surfaced the India Code migration → hardened the
gate against soft-404 shells → N refactor → dispatched verification and research
→ verified returned work → promoted → committed.

### Agent 2 — Track K

```
BNSS primary hunt (7 attempts, the longest chain in the run)
  1  registry URL indiacode.nic.in/handle/…/20099      FAIL 404
  2  indiacode.gov.in (migrated host)                  FAIL soft_404_catch_all_shell
  3  two guessed bitstream deep links                  FAIL 404 both
  4  guessed MHA filename 250883_…pdf                  PASS liveness, REFUTED on content
                                                       (it is the penal code, not BNSS)
  5  PRS 297-page PDF                                  PASS liveness, REFUTED on content
                                                       (it is the Bill, not the enacted Act)
  6  WebSearch "…Act No. 46 of 2023 official gazette"  HIT → MHA 250884_2
  7  curl + pypdf on the VM, read the gazette header   CONFIRMED, 249pp, Act 46 of 2023
```

Attempts 4 and 5 are the run's best argument for keeping the verifier rung
separate from liveness: both URLs are live PDFs on credible hosts, and both are
the wrong document. Status codes cannot tell you that.

Court discovery then went: POST `search_gazette.php` for `Judicial Magistrate`
(122 issues, mostly noise) → narrow to `Chief Judicial Magistrate` (24 issues) →
open three candidate gazettes with `curl` + `pypdf` → read operative text.
For Ranipet and Tirupathur it searched a second styling, found none, opened a
2025 BNSS-era notification and recorded **non-corroboration** — the heading says
"Chief Judicial Magistrate" and the operative text does not.

**Handover:** staging files + a report naming the four things it refused and why.

### Agent 3 — Track C

```
1  POST search_gazette.php 'Commercial Court'          5 issues
2  variant queries 'Commercial Courts Act' etc.        +1 issue, no new constituting notification
3  gazette_list_details.php?id=<b64>&date=<b64>        reached 2019 and 2016 issues
                                                       (NOT in the keyword index — found only by
                                                        following supersession references inside
                                                        the 2021 text)
then per notification: liveness gate → curl → pypdf extract → read operative text
then verifier: independent re-fetch, literal string check, 13/13 CONFIRM
```

Step 3 is the reason this track succeeded where a search-only approach would have
stopped at the 2021 notification and missed that it supersedes two earlier ones.

**Handover:** 5 entities, a 15-row suggested-edge table, and four decision gates —
two of which (appellate courts are not separate bodies; the id scheme breaks on
Chennai) generalise well beyond Tamil Nadu.

### Agent 4 — recount verifier

Recorded its own numbers first → then opened the artifact → then compared. Wrote
its own directory walk and tally; pulled `TYPE_CLASSIFICATION` out of
`classification.py` by `ast` parsing so it never imported the module. Ran four
invariants beyond the buckets (arithmetic, unmapped types, generic flag/id
consistency, duplicate ids). **Handover:** one JSONL record written directly to
`ledger/runs/`, PASS.

### Agent 5 — report-publication

Per body: locate the entity YAML → find the official site → search its
publications page → escalate to parent ministry → escalate to PIB/CAG → liveness
the candidate document → record the trail either way. For the statutory duty it
went to the constituting Act's reporting section. When `indiankanoon.org` returned
403 to automated fetches it substituted self-hosted regulator copies and
**disclosed the substitution** rather than skipping the leg silently.

**Handover:** CSV + ready-to-merge blocks + ledger. The orchestrator applied two
corrections on merge (see §5).

---

## 5 · Handovers, and what changed at each boundary

Nothing crossed from an agent into canon untouched. Each handover was a filter.

| Handover | What the orchestrator did before accepting |
|---|---|
| Agents 2, 3 → 1 | Re-ran liveness on all 10 cited URLs (10/10 pass), then downloaded each PDF, extracted text and confirmed the constituting notification number and quoted values were literally present (6/6 confirm). Only then promoted. |
| Agent 4 → 1 | Read the ledger record and independently checked the arithmetic rather than trusting the PASS. |
| Agent 5 → 1 | Liveness-checked all 14 cited URLs, then **corrected two entries**: `trai` and `ibbi` had `statutorily_required: yes` resting on `lawgist.in`, a private reproduction rather than a primary provision, so both were downgraded to `unknown` with the reason recorded. Also normalised `publishes_reports: false` back to the string `"no"` — YAML 1.1 turns a bare `no` into a boolean. |
| 1 → repo | Suggested edges were **not** applied. They sit in `ledger/suggested/` because relationships are maintainer-reviewed. |

---

## 6 · Observations about the orchestration itself

Recorded because they affect how much the run's provenance can be trusted.

**Permissions were instruction-level, not enforced.** Every subagent could have
written to `jem/data/` or run `git commit`. None did — verified by a clean
`git status` after each return — but that is compliance, not containment. A
future run wanting a real guarantee needs a sandboxed working copy, not a
paragraph in the prompt.

**Agents are unreliable clocks and unreliable self-reporters.** Track K's ledger
records `model: claude-opus-4`; it actually inherited Opus 5. Both generation
ledgers carry self-declared timestamps that disagree with their files' mtimes.
This matters more than it looks: model diversity is computed from these strings,
so a wrong one could inflate apparent diversity and promote a value that only one
family ever vouched for. **Model identity should be stamped by the harness at
dispatch, not written by the agent.**

**The dispatch prompts were not registered until after the run.** Invariant 5
says a prompt is versioned config, and four prompts governed real runs before
they existed as artifacts. They are now in `ledger/prompts/dispatch/` and
registered; the fix for next time is to register before dispatching.

**Told that an empty result was a success, two agents still found real data.**
Both generation prompts said an empty, documented run was a good outcome. Neither
used it as an exit. The permission to fail seems to have made the refusals
cheaper rather than making the work lazier — Track C refused ~38 fabricated
entities and still produced 5 verified ones.

**Reachability probing before dispatch paid for itself.** The orchestrator tested
the source map first and handed each agent a list of dead hosts. Both generation
agents reported not re-testing them. Without that, a meaningful share of the N≤3
attempt budget would have gone to timeouts.
