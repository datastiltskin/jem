# Track C — TN Commercial Courts · findings report

`prompt_id: cursor-C-commercial-v1` · harness: `02_CONSENSUS_HARNESS_SPEC.md` ·
run date **1 September 2026** · staging only, canon untouched.

---

## 0 · Headline

Tamil Nadu has notified commercial courts, and the notifications are live, openable and
verifiable — but **TN does not notify them district by district.** The operative
instrument designates courts *by class*: "the Principal District Courts/District Courts
except [three named districts]". Only **five** commercial courts are named individually
anywhere in the notification chain, and those five are what this run emits.

Anyone reconstructing "one commercial court per TN district" from general knowledge would
produce roughly 38 entities that no notification names, with invented ids, invented seats
and an invented ₹3 lakh pecuniary floor that is in fact wrong for the District-Judge tier.
That is the failure mode this track exists to prevent, and the primary source is
unusually explicit about it.

| | |
|---|---|
| Entities emitted | **5** (all validate `exit 0`, also under `--strict`) |
| Notification claims verified | **13 / 13 CONFIRM** (independent re-fetch, literal string check) |
| Ledger records | 18 — 13 `sourced`, 3 `unsourced_candidate`, 1 `secondary_only`, 1 `fetch_failed` |
| Suggested entities (not emitted) | 5 |
| Suggested edges | 15 (5 appellate + 5 statutory-ref + 5 gap-discovery) |
| Districts invented | 0 |

---

## 1 · Entities emitted

All five are `type: CommercialCourt`, `cluster: subordinate_courts`,
`level_of_government: State`, `parent_hc: hc_madras`, `data_quality: partial`, no
`case_volume`, no `judge_strength`.

| id | name | created_year | pecuniary (INR) | constituting notification | operational evidence |
|---|---|---|---|---|---|
| `tn_commercial_court_chennai` | Principal Commercial Court, Chennai | 2019 | 300,000 – 10,000,000 | II(2)/HO/892/2021, 1st proviso s.3(1) | indirect (2024 amendment presupposes it) |
| `tn_commercial_court_chennai_additional` | Additional Commercial Court, Chennai | 2024 | 300,000 – 10,000,000 | II(2)/HO/10/2024, 1st proviso s.3(1) | none located — flagged |
| `tn_commercial_court_coimbatore` | Commercial Court (District Judge), Coimbatore | 2021 | >2,500,000 | II(2)/HO/887/2021, s.3(1) | **strong** — judge posted 11 Aug 2026 |
| `tn_commercial_court_salem` | Commercial Court (District Judge), Salem | 2021 | >2,500,000 | II(2)/HO/887/2021, s.3(1) | **strong** — judge posted 29 Jul 2022 |
| `tn_commercial_court_chengalpattu` | Commercial Court (District Judge), Kancheepuram at Chengalpattu | 2021 | >2,500,000 | II(2)/HO/887/2021, s.3(1) | none located — flagged |

**Zero `tn_commercial_appellate_court_*` entities were emitted.** Reason in §3, gate G2-sub.

---

## 2 · The full notification chain, as read from the gazette

Every line below was read out of a PDF that passed the liveness pre-gate and was
re-fetched independently by the verifier.

**2016** — TN Gazette No. 28, Part II-Sec. 2, 13 July 2016, p. 402.
Notification **II(2)/HO/417/2016** (G.O. Ms. No. 500, Home (Courts-II), 28 June 2016),
s.3: constitutes *one Commercial Court in each Judicial District in the State of Tamil
Nadu, except city of Chennai*, appointing the Principal District Judge / District Judge as
its Judge. No district is named. Superseded in 2021.

**2019** — TN Gazette No. 40, Part II-Sec. 2, 2 October 2019, pp. 796-797.
Notification **II(2)/HO/786/2019** (G.O. Ms. No. 480, Home (Courts-II), 10 September
2019), s.3: designates the Court of the Principal Judge, City Civil Court, Chennai as
Commercial Court for the entire Judicial District of Chennai, *"pecuniary Jurisdiction
exceeding Rupees three lakhs but not exceeding Rupees one crore"*. Superseded in 2021.
This is the earliest sourced date for a Chennai commercial court, hence `created_year: 2019`.

**2021** — TN Gazette No. 51, Part II-Sec. 2, 22 December 2021, pp. 512-513. One G.O.
(**Ms. No. 555, Home (Courts-II), 6 December 2021**) carrying seven notifications. This is
the operative instrument.

| # | Notification | Provision | Effect |
|---|---|---|---|
| I | II(2)/HO/886/2021 | s.3(1) | **3 dedicated** Commercial Courts at Coimbatore, Kancheepuram at Chengalpattu, Salem — **Senior Civil Judge level**, ₹3 lakh–₹25 lakh, over the respective District Headquarters |
| II | II(2)/HO/887/2021 | s.3(1) | **3 dedicated** Commercial Courts at the same three places — **District Judge level**, **more than ₹25 lakh**, over the respective Districts |
| III | II(2)/HO/888/2021 | s.3A | designates *those same three DJ-level courts* as **Commercial Appellate Courts** for their districts |
| IV | II(2)/HO/889/2021 | s.3(1) | **by class**: all Principal Sub-Courts/Sub-Courts *except* in those three district HQs → SCJ-level Commercial Courts, ₹3 lakh–₹25 lakh |
| V | II(2)/HO/890/2021 | s.3(1) | **by class**, superseding 417/2016: all Principal District Courts/District Courts *except* in those three districts → Commercial Courts, >₹25 lakh |
| VI | II(2)/HO/891/2021 | s.3A | **by class**: those same District Courts → Commercial Appellate Courts for their districts |
| VII | II(2)/HO/892/2021 | 1st proviso s.3(1) | superseding 786/2019: Commercial Court at Chennai, **District Judge level**, entire Judicial District of Chennai, ₹3 lakh–₹1 crore |

Each of I, II, IV, V takes effect *"with effect from the dates on which the Judges assume
charge"* — constitution and commencement are separate events, which is why
`operational_status` is flagged rather than assumed.

**2024** — TN Gazette No. 1, Part II-Sec. 2, 3 January 2024, pp. 4-5.
G.O. Ms. No. 604, Home (Courts.II), 30 November 2023.
**II(2)/HO/10/2024**: designates the XXIII Additional City Civil Court, Chennai as
**Additional Commercial Court, Chennai**, District Judge level, ₹3 lakh–₹1 crore.
**II(2)/HO/11/2024**: amends 892/2021 so that "Commercial Court at Chennai" reads
"**Principal** Commercial Court at Chennai".

**Operational corroboration (also primary).**
TN Gazette No. 33, 17 Aug 2022, p. 914 — a judge posted as *"Judge, Commercial Court
(District Judge) at Salem vice Thiru M. Thandavan"*; a named outgoing incumbent plus a
named successor is direct evidence the Salem court functions.
TN Gazette No. 34, 26 Aug 2026, **II(2)/HO/654/2026** (G.O. (Rt) No. 807, 11 Aug 2026),
s.3(3) — a judge posted to *"Commercial Court (District Judge), Coimbatore, vice Thiru.
K.Hariharan, transferred"*. Three weeks before this run.

Individual judge names stay in the ledger and in this narrative evidence trail; none is
written into entity YAML, per the project's data rules.

---

## 3 · Decision gates — surfaced, not resolved

**G1-sub — Madras HC Commercial Division and Commercial Appellate Division.**
Proceeded edges-only as instructed: no standalone node. Beyond the prompt's default there
is now a *sourcing* reason to hold the line. Under ss.4 and 5 these divisions are
constituted by the **Chief Justice of the High Court**, not by the State Government, so
they will never appear in the TN Government Gazette — and both Madras HC domains are
unreachable. Their existence rests entirely on secondaries this run. **Recommendation:
keep edges-only until a Madras HC primary is reachable.**

**G2-sub — Commercial Appellate Courts are not separate bodies (new; needs a ruling).**
The governing prompt anticipates `tn_commercial_appellate_court_{district}` entities. The
notification does not support them. Notifications III and VI *designate the Commercial
Courts themselves* as the Commercial Appellate Courts for their districts. The appellate
forum is the same bench wearing a second hat. Emitting a separate node would assert an
institution the primary source says does not separately exist, so none was emitted.
**Options: (a) leave as-is, appellate capacity captured in `data_quality_notes` (what this
run did); (b) add a boolean/enum field such as `also_commercial_appellate_court` to the
schema; (c) emit separate nodes anyway and accept the double-count.** Recommend (b).

**G3-sub — the id scheme cannot survive Chennai.**
`tn_commercial_court_{district}` assumes one court per district. Chennai has had two since
January 2024 (Principal + Additional). This run used
`tn_commercial_court_chennai_additional`. **A maintainer ruling on multi-court districts is
needed before Track C is generalised to other states** — Maharashtra and Delhi will hit
this immediately.

**G4-sub — the ₹3 lakh floor is wrong for the District-Judge tier.**
The prompt specifies `specified_value_min: 300000` with basis `s.2(1)(i)` for every
emitted court. That is correct as the *statutory* Specified Value floor and correct as the
*notified* floor for the two Chennai courts. It is **not** the notified floor for
Coimbatore, Salem and Chengalpattu, which Notification II constitutes for disputes *"having
pecuniary jurisdiction of more than Rs. 25 lakh"*. TN splits the statutory range across two
tiers. Those three entities therefore carry `specified_value_min: 2500000` with the
divergence spelled out in `pecuniary_jurisdiction.notes`. **I did not overwrite the source
to match the template.** If the intended semantics of `specified_value_min` is "statutory
floor of the Act" rather than "floor notified for this court", all three should be changed
to 300000 — that is a schema-semantics ruling, not a data question.

**G5-sub — which TN districts are actually notified (the question as asked).**
*Individually named in a notification:* Chennai, Coimbatore, Salem, and "Kancheepuram at
Chengalpattu". That is the complete list. Everything else is covered by a class-wide
designation that names no district at all. **No claimed court was found that could not be
confirmed, because no source enumerates districts to claim from.** The honest answer to
"which districts" is: the notification says *all of them except three, by class* — and
turning that into entities requires an authoritative list of TN judicial districts that
this run could not reach (`districts.ecourts.gov.in` unreachable). Note the list is
non-obvious: judicial districts are not revenue districts, and the notification's own
phrase "Kancheepuram at Chengalpattu" shows the 2019 Kancheepuram/Chengalpattu split had
not cleanly propagated to the judicial map. See `suggested_edges.md` §3b for the
`is_generic_rollup` alternative.

---

## 4 · Evidence trail — every source tried, its liveness result, and the conclusion

Liveness results are from `scripts/harness/liveness.py` on this VM, on this run date.

### 4a · Reachable and used (all became citations)

| URL | gate | conclusion |
|---|---|---|
| `https://stationeryprinting.tn.gov.in/` | 200, HTML | Live. TN Government Gazette publisher; the single productive source of this run. |
| `https://stationeryprinting.tn.gov.in/search_gazette.php` | 200 | Live POST full-text search over 2008-2026. `search=<term>&search_year=All`. Indexes *titles/keywords*, not full text — see 4d. |
| `https://stationeryprinting.tn.gov.in/gazette_list_details.php?id=<b64>&date=<b64>` | 200 | Live per-issue file listing. Both params base64. **The `date` param selects the year; `id` is the issue number.** This is how the 2016 and 2019 issues were reached, since the keyword index does not return them. |
| `.../gazette/2016/28-II-2.pdf` | **pass** (200, application/pdf) | Notification II(2)/HO/417/2016. Text extracts cleanly. |
| `.../gazette/2019/40_II_2.pdf` | **pass** | Notification II(2)/HO/786/2019. Text extracts cleanly. |
| `.../gazette/2021/51_II_2.pdf` | **pass** | G.O. Ms. No. 555 — all seven notifications. The core source. |
| `.../gazette/2022/33_II_2.pdf` | **pass** | Salem judge posting. |
| `.../gazette/2024/1_II_2_2024.pdf` | **pass** | Notifications 10/2024 and 11/2024. |
| `.../gazette/2026/34_II_2_2026.pdf` | **pass** | Coimbatore judge posting, 11 Aug 2026. |

Note the 2016 filename uses hyphens (`28-II-2.pdf`) and later years use underscores
(`51_II_2.pdf`, `1_II_2_2024.pdf`). The convention changes across years, so file paths must
be read off the listing page, not constructed.

### 4b · Reachable but unusable as a citation

| URL | gate | conclusion |
|---|---|---|
| `.../gazette/2018/23_IV_4.pdf` | **pass** (200, application/pdf) | TN Gazette Part IV-Sec. 4, 6 June 2018 — the State reprint of the central **Commercial Courts (Amendment) Ordinance 2018**. 7 pages yield **1,057 characters**: a scanned image with no OCR layer. Live and authentic, but no text check can confirm a value in it, so it cannot clear the verifier. **Best OCR candidate produced by this run.** |
| `.../gazette/2015/50-IV-4.pdf` | **pass** | Same situation for the **2015 Ordinance** (22 pages, 110 KB of text extracts, but it is the Ordinance not the Act as amended). Recorded as a candidate. |
| `https://prsindia.org/billtrack/the-commercial-courts-...-amendment-bill-2018` | **pass** | The only Act-related URL that passed the gate. Secondary — a legislative-research summary, not the enacted text. Label `secondary_only`; not cited in any entity. |

### 4c · Dead — India Code (the significant negative)

| URL | gate result | note |
|---|---|---|
| `indiacode.nic.in/handle/123456789/2181` | **404** | Handle currently in JEM's instrument registry. Wrong *and* dead. |
| `indiacode.nic.in/bitstream/123456789/2181/1/A2016-4.pdf` (+ 3 case/format variants) | **404** | |
| `indiacode.nic.in/handle/123456789/9962` , `.../9962/1/A2018-28.pdf` | **404** | 2018 amendment. |
| `indiacode.nic.in/bitstream/123456789/2156/1/a2016-04.pdf` | **404** | The *correct* handle (2156), found via search. Still dead. |
| `indiacode.nic.in/bitstream/123456789/2156/1/201604.pdf` | **404** | |
| `indiacode.nic.in/handle/123456789/2156` | **404** | |
| `indiacode.nic.in/` (root) | 200 | Serves only a meta-refresh migration notice to `indiacode.gov.in`. |
| `indiacode.nic.in/bitstream/123456789/2077/1/A2007-55.pdf` | **404** | **Control probe.** This is the AFT Act URL already cited in `data/entities/_generated/backbone/aft_chennai.yaml`. It is dead too. |
| `indiacode.gov.in/handle/123456789/2181` | **soft_404_catch_all_shell** | 200, but byte-identical to a random nonsense control path. Proves nothing. |
| `indiacode.gov.in/bitstream/123456789/2156/1/a2016-04.pdf` | 200, `text/html`, 2,338 bytes | Same shell. |
| `www.indiacode.gov.in/...` | connection failure (000) | The `www.` host does not resolve/serve. |
| `legislative.gov.in/sites/default/files/A2016-4.pdf` | **404** | |
| `legalaffairs.gov.in/sites/default/files/Commercial%20Court%20Act%2C%202015.pdf` | **404** | Surfaced by search with content; dead on fetch. |

Two conclusions worth escalating beyond this track:

1. **The briefing's assumption that "some old `indiacode.nic.in/bitstream/.../*.pdf` PDFs
   still resolve" did not hold on any of the 8 legacy bitstream paths tested, including one
   already cited in JEM canon.** `WebFetch` returned 404 on the same URL from its own
   network path, so this is not a VM artefact. **Every `indiacode.nic.in` citation in the
   corpus is likely dead.** A corpus-wide `liveness.py --corpus-sample` sweep is warranted.
2. **Registry defect:** `data/legal_instruments/instruments.yaml` gives handle
   `123456789/2181` for `commercial_courts_act_2015`; the real handle is `123456789/2156`
   (the Act is No. 4 of 2016). Both dead, but the id is wrong independently of that. Not
   fixed here — this run does not touch canon.

### 4d · Searched and genuinely absent

- **A TN notification constituting the Madras HC Commercial Division.** Gazette searches
  for `Commercial Division` and `Commercial Appellate` across all years return only the
  2015 and 2018 central Ordinance reprints. This is the *expected* result, not a gap:
  ss.4-5 vest that power in the Chief Justice, so it belongs in a High Court notification.
- **Any commercial-court notification after January 2024.** The only post-2024 hit is the
  August 2026 judge posting. Caveat: the index is keyword-based and demonstrably
  incomplete — it does not return the 2016 or 2019 notifications either, which were found
  only by following supersession references inside the 2021 text. So "no notification after
  2024" is a weaker negative than "no notification exists".
- **Any Chengalpattu judge posting.** Full-text scans of the 2022, 2024 and 2026 issues
  found none.

### 4e · Not re-tested (maintainer pre-tested as down)

`hcmadras.tn.gov.in`, `mhc.tn.gov.in`, `districts.ecourts.gov.in`, `egazette.gov.in`,
`cms.tn.gov.in`, `tn.gov.in`. Taken as given per the briefing; no attempts spent.

---

## 5 · Was any live primary text of the Act or the 2018 amendment found?

**No.** This is a clean negative after 3 documented attempts (ledger record
`commercial_courts_act_2015 / primary_text_url`, label `fetch_failed`).

The nearest miss is genuinely useful and is the one lead worth chasing:
`https://stationeryprinting.tn.gov.in/gazette/2018/23_IV_4.pdf` — a live,
gate-passing, State-Gazette-authenticated reprint of the **Commercial Courts (Amendment)
Ordinance 2018** (No. 3 of 2018), indexed under "CENTRAL ACTS AND ORDINANCES". It fails
only because it is a scan with no text layer. **OCR would very likely yield a citable
primary text of the 2018 amendment.** The companion
`.../gazette/2015/50-IV-4.pdf` does the same for the 2015 Ordinance.

Second-order finding for the legal-instrument registry: state gazettes reprint central
Acts and Ordinances in Part IV-Section 4. With India Code down, **state gazette Part IV
reprints are a viable fallback corpus for central primary text** — reachable, dated,
authenticated, and stable-URL'd.

---

## 6 · Confidence, and what I did not do

**Confidence in the five emitted entities: high on existence, jurisdiction level,
pecuniary band, territorial limits and constituting instrument.** These are quoted from a
State Government Gazette PDF that passed the liveness gate, and every quoted string was
re-confirmed present by an independent re-fetch (13/13 CONFIRM). Under the harness's
`shared_bias_risk` rule these are single-family (one model), so `model_diversity: 1` and
they should not promote above `partial` until a second model family re-runs them —
`data_quality: partial` is set on all five accordingly.

**Lower confidence, explicitly flagged in `unverified_fields`:** `operational_status` for
Chengalpattu and Chennai-Additional (constituted, but commencement depends on a judge
assuming charge and no evidence of that was found); `created_year` for Chennai (2019 vs
2021 turns on whether the 2021 supersession is continuation or fresh constitution, which
the text does not settle) and for Chennai-Additional (G.O. 2023 vs gazette publication
2024).

### Things I could have written and did not, because I could not source them

- **A per-district expansion of the class-wide designation.** The single largest
  temptation. Notification V covers every TN district court except three, and TN's district
  list is common knowledge — but it is not *in the notification*, and no live GoI source for
  the judicial-district list was reachable. **Zero districts were enumerated from memory.**
- **`tn_commercial_appellate_court_*` nodes**, even though the governing prompt asks for
  them, because the notification designates the *same* courts in both roles.
- **The three Senior-Civil-Judge-level dedicated courts.** Properly notified, but two
  secondaries contradict each other on whether the tier ever commenced, and no primary
  evidence of a judge assuming charge exists. Surfaced as suggested entities with the
  conflict stated rather than silently resolved.
- **A `commercial_courts_act_2015` source URL on any entity.** No live URL exists to cite,
  so the entities cite the notifications that *recite* the sections, and
  `unverified_fields` says exactly that.
- **`s.2(1)(i)` / `s.13(1A)` as read provisions.** Section numbers in the YAML appear only
  where the *notification itself* recites them (s.3(1), s.3(3), s.3A). s.2(1)(i) appears
  only as `pecuniary_jurisdiction.basis` per the prompt's explicit instruction, with a note
  that it was not read from the Act. s.13(1A) appears only in the suggested-edges table,
  marked as unconfirmed.
- **A Madras HC Commercial Division constitution date, bench count or roster.** Secondary
  sources offer "three commercial divisions and three commercial appellate divisions", a
  first sitting of 4 December 2017, "80 commercial courts across 40 judicial districts", and
  various pendency figures. **None is in any entity, edge or field.** They are recorded in
  the ledger as `secondary_only` so a future run can see they were considered and rejected.
- **`case_volume` / `judge_strength`.** Out of scope per the prompt; pendency numbers were
  encountered in secondaries and discarded.

### Process notes

- Canon untouched: nothing written outside `/tmp/track_c/`; no `build.py`, no `git add`,
  `commit` or `push`; no existing repo file read-modified. Mid-run, `git status` briefly
  showed `jem/scripts/requirements.txt` modified and `jem/tests/test_schema_s.py`
  untracked; both belong to the concurrently-running schema-S track and were committed by
  it as `125f39d test: regression tests for S schema`. This run neither created nor edited
  them. The working tree is clean as of the end of this run.
- Three verifier claims initially returned REFUTE. Rather than wave them through, they were
  diagnosed: two were the `ﬁ` ligature in "Notiﬁcation" and one was a page-break header
  interposed mid-sentence. The needles were narrowed to fragments that survive extraction
  and re-run to 13/13. `verify.py` is re-runnable and is the reproducible artifact.

## 7 · Files

| path | contents |
|---|---|
| `/tmp/track_c/entities/*.yaml` | 5 entities, all `validate.py --entity` exit 0, also under `--strict` |
| `/tmp/track_c/suggested_edges.md` | 15 suggested edges + 5 suggested entities, none auto-applied |
| `/tmp/track_c/ledger.jsonl` | 18 records in the harness Ledger-record shape |
| `/tmp/track_c/verify.py` | re-runnable verifier: liveness + re-fetch + literal string check |
| `/tmp/track_c/verifier.json` | verifier output, 13/13 CONFIRM |
| `/tmp/track_c/gen_entities.py`, `gen_ledger.py` | deterministic generators for the above |
| `/tmp/track_c/raw/` | every gazette PDF fetched, plus extracted text and liveness JSONL |
