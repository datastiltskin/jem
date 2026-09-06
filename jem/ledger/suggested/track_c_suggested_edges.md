# Track C — SUGGESTED edges (TN commercial courts)

`prompt_id: cursor-C-commercial-v1` · run 2026-09-01 · **NOT written to any relationship
file.** Maintainer review required. Nothing here has been auto-applied.

All evidence URLs below passed the liveness pre-gate (`scripts/harness/liveness.py`,
HTTP 200, `application/pdf`) and were re-fetched independently by the verifier stage,
which confirmed the quoted notification numbers and wording are literally present in the
document. See `verifier.json` (13/13 CONFIRM).

## 1 · Appellate chain — emitted entities → `hc_madras`

Under the Commercial Courts Act 2015 an appeal from a Commercial Court **at District
Judge level** lies to the **Commercial Appellate Division of the High Court**, not to a
district Commercial Appellate Court. All five emitted entities are at District Judge
level, so all five route to `hc_madras`.

**Caveat that a critic must resolve:** the TN notifications recite ss.3(1), 3(3) and 3A
but do **not** recite s.13, and no live primary text of the Act was openable this run
(see REPORT.md §4). The *forum* is therefore inferred from the Act's structure, not read
from its text. Confidence is capped at `low` for that reason alone — the endpoints
themselves are firmly sourced.

| source | rel_type | target | category | basis | evidence_url | confidence |
|---|---|---|---|---|---|---|
| `tn_commercial_court_chennai` | AppealableTo | `hc_madras` | appellate_chain | Commercial Appellate Division, Madras HC. Commercial Courts Act 2015 s.13(1A) — **provision not read from primary; critic must confirm**. Court is at District Judge level per Notification II(2)/HO/892/2021. | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | low |
| `tn_commercial_court_chennai_additional` | AppealableTo | `hc_madras` | appellate_chain | Commercial Appellate Division, Madras HC. Court is at District Judge level per Notification II(2)/HO/10/2024. Same s.13(1A) caveat. | https://stationeryprinting.tn.gov.in/gazette/2024/1_II_2_2024.pdf | low |
| `tn_commercial_court_coimbatore` | AppealableTo | `hc_madras` | appellate_chain | Commercial Appellate Division, Madras HC. District Judge level per Notification II(2)/HO/887/2021. Same s.13(1A) caveat. | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | low |
| `tn_commercial_court_salem` | AppealableTo | `hc_madras` | appellate_chain | Commercial Appellate Division, Madras HC. District Judge level per Notification II(2)/HO/887/2021. Same s.13(1A) caveat. | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | low |
| `tn_commercial_court_chengalpattu` | AppealableTo | `hc_madras` | appellate_chain | Commercial Appellate Division, Madras HC. District Judge level per Notification II(2)/HO/887/2021. Same s.13(1A) caveat. | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | low |

## 2 · Statutory reference

Target is a `data/legal_instruments/` registry id, not an entity. Note-only per the
governing prompt.

| source | rel_type | target | category | basis | evidence_url | confidence |
|---|---|---|---|---|---|---|
| `tn_commercial_court_chennai` | EstablishedUnder | `commercial_courts_act_2015` | statutory_ref | First proviso to s.3(1), recited verbatim in Notification II(2)/HO/892/2021 | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | high |
| `tn_commercial_court_chennai_additional` | EstablishedUnder | `commercial_courts_act_2015` | statutory_ref | First proviso to s.3(1), recited verbatim in Notification II(2)/HO/10/2024 | https://stationeryprinting.tn.gov.in/gazette/2024/1_II_2_2024.pdf | high |
| `tn_commercial_court_coimbatore` | EstablishedUnder | `commercial_courts_act_2015` | statutory_ref | s.3(1), recited verbatim in Notification II(2)/HO/887/2021 | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | high |
| `tn_commercial_court_salem` | EstablishedUnder | `commercial_courts_act_2015` | statutory_ref | s.3(1), recited verbatim in Notification II(2)/HO/887/2021 | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | high |
| `tn_commercial_court_chengalpattu` | EstablishedUnder | `commercial_courts_act_2015` | statutory_ref | s.3(1), recited verbatim in Notification II(2)/HO/887/2021 | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | high |

## 3 · Gap-discovery — suggested entities NOT emitted, with their edges

Every row below is backed by a verified notification, but each is withheld from canon for
the reason stated. Flagged `unverified`; never auto-apply.

### 3a · The Senior-Civil-Judge tier (three dedicated courts)

Notification II(2)/HO/886/2021 constitutes three Commercial Courts at the **Senior Civil
Judge level** at Coimbatore, Kancheepuram at Chengalpattu and Salem, ₹3 lakh to ₹25 lakh.
This is the tier that actually carries the ₹3 lakh statutory Specified Value floor.

Withheld because two secondary sources conflict on whether this tier ever became
operational, and no primary evidence of a Judge assuming charge at any of the three was
located. A March 2022 news report states there were then *no* commercial courts below
District Judge level in TN; an August 2024 report states TN and Puducherry had 80
commercial courts across 40 judicial districts (two per district, i.e. both tiers). Per
the harness this is a `data_conflict` to surface, not silently resolve.

| suggested source | rel_type | target | category | basis | evidence_url | confidence |
|---|---|---|---|---|---|---|
| `tn_commercial_court_coimbatore_scj` *(suggested)* | AppealableTo | `tn_commercial_court_coimbatore` | appellate_chain | s.3A — Notification II(2)/HO/888/2021 designates the DJ-level court as Commercial Appellate Court for appeals from the SCJ-level court in the same district | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | medium |
| `tn_commercial_court_salem_scj` *(suggested)* | AppealableTo | `tn_commercial_court_salem` | appellate_chain | s.3A — Notification II(2)/HO/888/2021, as above | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | medium |
| `tn_commercial_court_chengalpattu_scj` *(suggested)* | AppealableTo | `tn_commercial_court_chengalpattu` | appellate_chain | s.3A — Notification II(2)/HO/888/2021, as above | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | medium |

### 3b · The class-wide designations (rest of the state)

Notifications II(2)/HO/889, 890 and 891 of 2021 designate courts **by class, not by
name**: every Principal Sub-Court/Sub-Court outside the three dedicated district
headquarters becomes an SCJ-level Commercial Court, and every Principal District
Court/District Court outside those three districts becomes a Commercial Court (>₹25 lakh)
*and* the Commercial Appellate Court for its district.

Expanding these into `tn_commercial_court_{district}` entities would require enumerating
Tamil Nadu's judicial districts from outside the notification. The notification does not
list them and no live GoI source for the judicial-district list was reachable this run
(`districts.ecourts.gov.in` unreachable). **No per-district entities were created.** The
schema's `is_generic_rollup: true` is the natural home for this; that is a maintainer
decision, not one this run should take.

| suggested entity | type | basis | evidence_url | confidence |
|---|---|---|---|---|
| `tn_commercial_court_designated_district_generic` *(suggested, `is_generic_rollup: true`)* | CommercialCourt | s.3(1) — Notification II(2)/HO/890/2021: Principal District Courts/District Courts outside Coimbatore, Kancheepuram at Chengalpattu and Salem, designated as Commercial Courts, >₹25 lakh | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | medium |
| `tn_commercial_court_designated_subcourt_generic` *(suggested, `is_generic_rollup: true`)* | CommercialCourt | s.3(1) — Notification II(2)/HO/889/2021: Principal Sub-Courts/Sub-Courts outside the three district headquarters, designated as SCJ-level Commercial Courts, ₹3 lakh–₹25 lakh | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | medium |

| suggested source | rel_type | target | category | basis | evidence_url | confidence |
|---|---|---|---|---|---|---|
| `tn_commercial_court_designated_subcourt_generic` *(suggested)* | AppealableTo | `tn_commercial_court_designated_district_generic` *(suggested)* | appellate_chain | s.3A — Notification II(2)/HO/891/2021 designates those same District Courts as Commercial Appellate Courts for appeals from the SCJ-level Commercial Courts in their districts | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | medium |
| `tn_commercial_court_designated_district_generic` *(suggested)* | AppealableTo | `hc_madras` | appellate_chain | Commercial Appellate Division, Madras HC (District Judge level). Same unread-s.13(1A) caveat as §1. | https://stationeryprinting.tn.gov.in/gazette/2021/51_II_2.pdf | low |

### 3c · Madras HC Commercial Division and Commercial Appellate Division — NOT emitted

Per the governing prompt these are represented as commercial/appellate **capacity of**
`hc_madras`, surfaced only as the §1 edges above. No standalone node was created. See
decision gate **G1-sub** in REPORT.md.

No primary source constituting them was reachable this run. Under ss.4 and 5 of the Act
they are constituted by the **Chief Justice of the High Court**, not by the State
Government, so they would not appear in the TN Government Gazette at all — and both
Madras HC domains (`hcmadras.tn.gov.in`, `mhc.tn.gov.in`) are unreachable. Their
existence is attested only by secondary sources this run, so **no edge asserting a
Commercial Division constitution date or composition is proposed.**
