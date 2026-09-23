# Track K — TN sub-district criminal magistracy

`prompt_id: cursor-K-criminal-v1` · harness: `02_CONSENSUS_HARNESS_SPEC.md` ·
run 2026-09-01 · **staging only, nothing written to `jem/data/`, no build, no commit**

## Headline

**One entity emitted: `cjm_nilgiris`.** It is the only court in Tamil Nadu for
which this run could open a primary document that gives all three of: the court's
existence, its establishment year, and its character as a Chief Judicial
Magistrate court. Everything else that looked promising failed on one of those
three, and is parked in the ledger rather than guessed into canon.

Independently useful: **a live, openable primary text of the enacted BNSS 2023 was
found**, and the BNSS/CrPC URLs currently in JEM's own legal-instrument registry
are both dead.

## 1 · What was emitted

| id | name | created_year | data_quality | validate.py |
|----|------|--------------|--------------|-------------|
| `cjm_nilgiris` | Chief Judicial Magistrate Court, The Nilgiris at Udhagamandalam | 2024 | complete | exit 0 |

Three mutually reinforcing Tamil Nadu Government Gazette instruments support it:

1. **TNGG No.10, Part II-Sec.2, 6 Mar 2024, p.72** — Home Department notification
   No. II(2)/HO/141/2024 [G.O. Ms. No. 130, Home (Courts-III), 9 Feb 2024], made
   under CrPC s.11(1) after consultation with the High Court, Madras. Gives the
   establishment and therefore `created_year: 2024`.
2. **TNGG No.33, Part VI-Sec.1, 16 Aug 2023, pp.326-329** — judicial notification
   No. VI(1)/514/2023 under CrPC s.14(1), naming "Chief Judicial Magistrate, The
   Nilgiris District at Udhagamandalam (Proposed Court)" and allotting it "All
   cases relating to the offences which are triable by the Chief Judicial
   Magistrate alone".
3. **TNGG No.34, Part II-Sec.2, 26 Aug 2026** — notification No. II(2)/HO/656/2026,
   which strips "Chief Judicial Magistrate" from the District Judge's court and
   inserts a separate "(aa) Court of Chief Judicial Magistrate, The Nilgiris at
   Uthagamandalam" with its own presiding officer. This is what moves the court
   from "proposed" in 2023 to `operational_status: Active`.

`data_quality: complete` rather than `verified`, because the sources are Tamil
Nadu State Gazette rather than a Government of India primary. `shared_bias_risk`
is flagged **high** in the ledger: three documents agree, but one model family
read all three, and the harness scores confidence as agreement × diversity.

## 2 · What was deliberately *not* emitted, and why

This is the more important half of the run.

**Ranipet and Tirupathur.** TNGG No.2, 10 Jan 2024, p.12 carries an item headed
"Establishment of Chief Judicial Magistrate Courts at Ranipet and Tirupathur under
the Code of Criminal Procedure". The operative text underneath it says something
different: notification No. II(2)/HO/29/2024 "hereby establishes **a Court of
Judicial Magistrate** at Ranipet in Ranipet District and a Court of Judicial
Magistrate at Tirupathur in Tirupathur District" — no class, no "Chief". A later
BNSS-era notification (TNGG No.18, 7 May 2025) names the relevant magisterial
courts of those districts as "District Munsif-cum-Judicial Magistrate Court,
Ranipet" and "Judicial Magistrate Court No. I, Tirupathur", neither styled Chief.
Emitting `cjm_ranipet` would promote a marginal heading over the instrument's own
operative words against a later contrary instrument. Labelled `partial`.

**Nanguneri (Tirunelveli district).** Existence and year are solidly sourced —
twice: Home Dept notification No. II(2)/HO/922/2018 (TNGG No.43, 24 Oct 2018)
establishing "a Court of Judicial Magistrate at Nanguneri" under CrPC s.11(1), and
the High Court's own re-designation notification No. VI(1)/332/2018 (TNGG No.37,
12 Sep 2018), which also reveals the 2012 antecedent G.O.(Ms) No.388. But no
opened document states the magistrate's **class**, and the id `jmfc_nanguneri`
would assert "first class". Nanguneri is also a taluk, not a district, so the
prompt's `jmfc_{district}` pattern does not fit it either way.

**The Nilgiris JMFC roster.** TNGG No.33 (2023) is the one document found that ties
named TN magistrate courts to the first class: it fixes local limits for
magistrates who "may exercise all or any powers of the Judicial Magistrates of the
First Class", listing as existing courts the Judicial Magistrate Court
Udhagamandalam, the Judicial Magistrate Additional Mahila Court Udhagamandalam,
the Judicial Magistrate Court Coonoor, the Judicial Magistrate Fast Track Court
Coonoor, and the District Munsif-cum-Judicial Magistrate Court Kotagiri. A
local-limits notification carries no establishment date, so `created_year` is
unavailable for every one of them — which the prompt makes a sufficient reason not
to emit.

**No ACJM anywhere.** No notification appointing an Additional Chief Judicial
Magistrate in any TN district was found. BNSS s.10(2) makes ACJM appointment
discretionary for the High Court ("may appoint"), so absence of evidence here is
weak evidence of absence, and is recorded as unsourced rather than as a gap.

**No JM2 anywhere.** No TN notification distinguishing a Judicial Magistrate of the
second class was found. TN's establishing notifications, in every instance opened,
say only "a Court of Judicial Magistrate".

**No 38-district roster.** The two sources that would hold one — the Madras High
Court and `districts.ecourts.gov.in` — are both unreachable. The gazette search is
summary-level and effectively begins around 2012, so it yields individual
establishment notifications, not a census. Most TN magistrate courts long predate
that archive. A district-by-district table built from this channel would be a
floor presented as a total.

## 3 · Evidence trail — every source tried

Liveness results are from `scripts/harness/liveness.py`; the raw log is at
`/tmp/track_k/raw/liveness_log.jsonl`.

### Legal instrument (BNSS 2023)

| URL | liveness | conclusion |
|-----|----------|------------|
| `https://www.indiacode.nic.in/handle/123456789/20099` | **404 `non_200`** | **The BNSS URL in JEM's own `data/legal_instruments/instruments.yaml` is dead.** |
| `https://indiacode.gov.in/handle/123456789/20099` | **200 `soft_404_catch_all_shell`** | Confirms the brief: the migrated portal returns a byte-identical shell for any path. The gate caught it. Not citable. |
| `https://www.indiacode.nic.in/bitstream/123456789/20099/1/a2023-46.pdf` | **404 `non_200`** | Guessed deep link. Dead. |
| `https://www.indiacode.nic.in/bitstream/123456789/20099/1/aa2023-46.pdf` | **404 `non_200`** | Guessed deep link. Dead. |
| `https://www.mha.gov.in/sites/default/files/250883_english_01042024.pdf` | 200 `pass` | Guessed file id. **Liveness passed but content refuted it** — the PDF is the Bharatiya *Nyaya* Sanhita (penal code), not BNSS. Discarded. A live 200 PDF on the right ministry can still be the wrong Act. |
| `https://www.mha.gov.in/sites/default/files/250882_english_01042024.pdf` | 200 (curl) | Neighbouring id probe, not pursued. |
| `https://www.mha.gov.in/sites/default/files/250884_english_01042024.pdf` | 404 | Probe. |
| `https://prsindia.org/files/bills_acts/bills_parliament/2023/Bharatiya_Nagarik_Suraksha_Sanhita,_2023.pdf` | 200 `pass` | 297pp, but it is the **Bill** ("A BILL", "ARRANGEMENT OF CLAUSES"). Not the enacted Act. `secondary_only`. |
| **`https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf`** | **200 `pass`, `application/pdf`** | **The answer.** 249pp, Gazette of India Extraordinary Part II-Sec.1 No.54, 25 Dec 2023, Ministry of Law and Justice (Legislative Department), Act No. 46 of 2023. ss.6-24 read directly on the VM. |
| `https://legislative.gov.in/` | 200 `pass` | Homepage reachable; not used as a citation. |
| `https://doj.gov.in/` | 200 `pass` | Homepage reachable; holds no per-court establishment notifications. Not used. |

### Tamil Nadu primary channel

`https://stationeryprinting.tn.gov.in/` — 200 `pass`. This was the **only**
reachable TN government primary source, and it carried the whole run. It exposes a
POST full-index search at `search_gazette.php` (`search`, `search_year`) over
Tamil Nadu Government Gazette issues, with direct PDF links. Queries run:

| query | issues returned | value |
|-------|-----------------|-------|
| `Judicial Magistrate` | 122 | Mostly record-destruction and court-holiday notifications. Surfaced the Home Dept establishment items. |
| `Chief Judicial Magistrate` | 24 | Surfaced TNGG 2024/2, 2024/10 and 2023/33 — the backbone of this run. |
| `Constitution of Judicial Magistrate` | 1 | TNGG 2018/43 (Nanguneri). |
| `Establishment of Chief Judicial Magistrate` | 1 | TNGG 2024/2 (Ranipet, Tirupathur). |
| `Judicial Magistrate Court at` | 62 | ~40 further establishment notifications, 2016-2026, captured in the ledger for a later pass. |
| `Additional Chief Judicial Magistrate` | 1 | A 2026 issue, unrelated to ACJM constitution. **No ACJM appointment notification found.** |
| `Second Class` | 4 | All boiler-attendant examinations. **No JM2 notification found.** |
| `creation of Judicial Magistrate Court` | 0 | — |
| `Constitution of a Court of Judicial Magistrate` | 0 | — |
| `Ranipet` / `Tirupathur` | 3 / 2 | Produced the non-corroborating 2025 BNSS notification. |

Gazette PDFs opened and read (all liveness `pass`, all `application/pdf`):

- `gazette/2024/2_II_2_2024.pdf` — Ranipet/Tirupathur; heading/operative conflict.
- `gazette/2024/10_II_2_2024.pdf` — Udhagamandalam establishment.
- `gazette/2023/33_VI_1_2023.pdf` — Nilgiris CJM bifurcation + first-class roster.
- `gazette/2026/34_II_2_2026.pdf` — 2026 confirmation the Nilgiris CJM court is live.
- `gazette/2018/43_II_2.pdf` — Nanguneri establishment.
- `gazette/2018/37_VI_1.pdf` — Nanguneri High Court re-designation + 2012 antecedent.
- `gazette/2024/16_II_2_2024.pdf` — Arakkonam (contents page only).
- `gazette/2025/18_II_2_2025.pdf` — BNSS s.9(1) proviso notification; MP/MLA courts.

### Not re-tested (declared unreachable in the brief)

`hcmadras.tn.gov.in`, `mhc.tn.gov.in`, `districts.ecourts.gov.in`, `egazette.gov.in`,
`cms.tn.gov.in`, `tn.gov.in`. The first two are the decisive gap: under BNSS s.9(2)
the High Court appoints the presiding officers and under s.10(1) it appoints the
CJM in every district, so Madras High Court holds the authoritative roster this
track needs.

## 4 · BNSS 2023 primary text — found

**`https://www.mha.gov.in/sites/default/files/2024-04/250884_2_english_01042024.pdf`**
— 249pp, `application/pdf`, liveness `pass`, verified on the VM (not via the search
tool's own extract). Text relevant to this track, read directly:

- **s.9(1)** — "In every district there shall be established as many Courts of
  Judicial Magistrates of the first class and of the second class, and at such
  places, as the State Government may, after consultation with the High Court, **by
  notification, specify**". This is why the track cannot pattern-fill: each JMFC/JM2
  court exists only by a specific notification.
- **s.9(2)** — "The presiding officers of such Courts shall be appointed by the High Court."
- **s.10(1)** — "In every district, the High Court shall appoint a Judicial
  Magistrate of the first class to be the Chief Judicial Magistrate."
  **s.10(2)** — the High Court "may appoint" an Additional Chief Judicial Magistrate.
- **s.13(1)** — "Every Chief Judicial Magistrate shall be subordinate to the
  Sessions Judge; and every other Judicial Magistrate shall, subject to the general
  control of the Sessions Judge, be subordinate to the Chief Judicial Magistrate."
- **s.23** — sentencing ceilings, verbatim: CJM "any sentence authorised by law
  except a sentence of death or of imprisonment for life or of imprisonment for a
  term exceeding seven years"; first class "imprisonment for a term not exceeding
  three years, or of fine not exceeding fifty thousand rupees, or of both, or of
  community service"; second class "imprisonment for a term not exceeding one year,
  or of fine not exceeding ten thousand rupees, or of both, or of community service".

**Registry repair recommended (not applied — canon is untouched this run).**
`data/legal_instruments/instruments.yaml` points `bnss_2023` at
`indiacode.nic.in/handle/123456789/20099` and `crpc_1973` at
`indiacode.nic.in/handle/123456789/16225`. The first is confirmed 404. The second
was not tested but is the same host and pattern.

## 5 · Decision gates — surfaced, not resolved

1. **TN does not notify magistrate class.** Every establishing notification opened
   says "a Court of Judicial Magistrate", never "of the first class". Yet BNSS
   s.9(1) speaks only of first- and second-class courts. Someone with access to
   Madras High Court records must decide how JEM assigns `jmfc_`/`jm2_` ids, or
   whether the track needs a class-agnostic id form.
2. **Gazette heading vs operative text.** TN gazettes head CJM-intended
   notifications "Establishment/Constitution of ... Chief Judicial Magistrate
   Court" while the operative text establishes a plain Court of Judicial Magistrate
   under CrPC s.11(1) / BNSS s.9(1) — because the State establishes the court and
   the High Court then designates its presiding officer as CJM under s.10(1). Which
   of the two JEM treats as the naming authority is a maintainer call.
3. **`jmfc_{district}` does not match TN's structure.** TN magistrate courts sit at
   taluk towns, several per district, numbered (Judicial Magistrate No. I,
   Ponneri), plus Mahila and Fast Track magisterial courts. One JMFC per district
   would misdescribe the state.
4. **The prompt's provision label.** The prompt describes BNSS ss.21-23 as "classes
   of criminal courts; sentencing powers". In the enacted Act, classes of criminal
   courts is **s.6**; s.21 is "Courts by which offences are triable", s.22 is
   HC/Sessions sentencing, s.23 is Magistrates' sentencing. The prescribed string
   `ss.21-23` is kept verbatim in the emitted entity, because the harness reserves
   config changes to the maintainer and the researcher adapts tactics only.
5. **Arakkonam's district.** TNGG 2024/16 places the Arakkonam JM court in "Vellore
   District" while TNGG 2024/2 puts the Arcot/Walajapet/Arakkonam courts under
   Ranipet District. Recorded, not corrected.
6. **Madurai bench allocation.** No primary allocating districts between `hc_madras`
   and `hc_madras_bench_madurai` was opened, so the supervision edge is written to
   `hc_madras`.
7. Per instruction, no existing TN criminal entity with a string `statutory_basis`
   was touched.

## 6 · Confidence, and what I was tempted to infer but did not

Confidence in `cjm_nilgiris` is **high on existence, establishment year and CJM
character** (three independent gazette instruments spanning 2023-2026, each opened
and read on the VM), and **explicitly absent on the date the Chief Judicial
Magistrate assumed charge**, which no opened document gives.

Confidence in the **negative** result — that no further TN magistrate court could be
promoted — is high, and is the intended outcome rather than a shortfall. The
blocking constraints are structural, not effort-related: TN does not state
magistrate class in its establishing notifications, and the roster-holding sources
are unreachable.

Things I could have written and did not, because no opened document supported them:

- **A CJM for each of TN's 38 districts.** BNSS s.10(1) says the High Court shall
  appoint a CJM in every district, which is genuinely tempting: it reads like a
  licence to generate 38 entities. It is not. It mandates an appointment, not a
  court establishment, and it supplies no `created_year` for any of them. This is
  the exact failure mode the brief names, and it would have been the easiest thing
  in this run to do.
- **`jmfc_ranipet`, `jmfc_tirupathur`, `jmfc_nanguneri`.** Existence and year are
  sourced for all three courts; the "first class" in the id is not sourced for any.
- **`cjm_ranipet`, `cjm_tirupathur`.** Supported by a gazette heading, contradicted
  by that gazette's own operative text, and not corroborated by the later BNSS-era
  notification.
- **A JMFC for each Nilgiris court in the 2023 roster.** Class is sourced there — the
  only place it is — but `created_year` is not, for any of them.
- **`created_year: 2023` for the Ranipet/Tirupathur courts** on the strength of the
  8 Dec 2023 G.O. date. Where used at all, the year is taken from the gazette
  publication that carries the operative establishment, and both dates are recorded.
- **Any inference from the ~40 unopened establishment notifications** listed in the
  ledger. They are captured as leads with their gazette dates, and nothing was
  claimed from an index summary that was not opened and read.

## 7 · Files produced (staging only)

```
/tmp/track_k/entities/cjm_nilgiris.yaml   validate.py --entity → exit 0
/tmp/track_k/suggested_edges.md           2 proposed edges, 3 blocked proposals
/tmp/track_k/ledger.jsonl                 9 cells, harness spec 02 shape
/tmp/track_k/REPORT.md                    this file
/tmp/track_k/build_ledger.py              regenerates the ledger
/tmp/track_k/raw/                         liveness_log.jsonl, gazette query HTML, downloaded PDFs
```

Nothing under `/workspace/jem/data/` was created, modified or deleted; `build.py`
was not run; no git operation of any kind was performed.
