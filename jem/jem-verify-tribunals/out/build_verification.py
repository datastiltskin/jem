"""Materialize the reviewed evidence as the requested CSV and honest run metadata.

This is an export of this Codex session's research, not a model API harness.
It reads only out/inputs and out/fetch_log, and writes only beside this file.
"""
import csv
import datetime as dt
import hashlib
import json
import os
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
HEADER = "entity_id,type,field,current_value,current_source_type,current_source_url,verdict,verified_value,verified_as_of,source_class,source_title,source_url,table_or_section,verbatim_excerpt,primary_count,independent_secondary_count,confidence_tier,njdg_stamp_valid,anomaly_flags,notes".split(",")
PROMPT_SHA = "81136dad77f0e2381729244a3e565bb00444427c8a851c2b47bddaa5ea0ce21d"
CLAIMS_SHA = "43f3f75b86e9435ff5d046342c62b295c0f540938eba983fb9cb8c1299614d93"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def ratio(disposed, filed):
    return str((Decimal(disposed) / Decimal(filed)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP))


# Values below are observations from archived primary documents. They are not
# interchangeable with the claims when period, case category or unit differs.
REVIEWS = {}


def review(entities, labels, section, observations, flags=()):
    for entity in entities.split():
        REVIEWS[entity] = dict(source_labels=labels.split(), section=section,
                               observations=observations, flags=list(flags))


review("sat", "sat_recheck tribunals_2025",
       "SEBI AR 2025-26, Chapter 10, Table 10.35 and section 10.3 A, printed page 156 / PDF page 18",
       "FY2025-26: opening 960, filed 429, dismissed 135, remanded 28, allowed 47, modified orders 88, withdrawn 25, closing 1066. Disposed = 135+28+47+88+25 = 323, also stated in the narrative. 960+429-323 = 1066. Rate = 0.7529. This verifies the supplied method anchor, not the input's 2024-12-01 snapshot or undefined last_year. LS 1007 also reports CY2024 disposal 374 and pending 1085, another different period. No matching-period average duration located.",
       ["period_mismatch", "anchor_verified_different_period"])
review("cestat", "cestat_monthly tribunals_2025",
       "CESTAT monthly statement, PDF pages 2-3, November closing and December 2024 opening, TOTAL row",
       "December 2024 opening pending is 72179, also November closing. December fresh filings 1486, restored 9, remanded 3, disposed 1846, closing 71845. The statement warns that variations can arise from physical verification. LS 1007 annexure reports CY2023 disposal 14403 and CY2024 disposal 23821. Neither defines the input's last_year interval. No matching-period mean duration located.")
review("ka_state_cdrc", "ka_consumer_nov consumer_state_2024",
       "Karnataka November 2024 statistics, PDF page 1, Proforma IV, STATE COMMISSION TOTAL",
       "At 30 November 2024 close, statewide state-commission pending is 9947: appeals 8658 plus complaints 1289. Since-inception filed 73792 and disposed 63845 are cumulative, not annual. Treat November close as the opening balance on 1 December, subject to no intervening adjustments. LS 2574 gives consumer complaints filed 8687 and disposed 2590 over 2022-01-01 to 2024-10-31, not one year and not all appeals. Cohort tables in the monthly report are not annual disposal flows. No matching-period mean duration located.",
       ["cumulative_not_annual"])
review("ka_cdrc_bengaluru", "ka_consumer_nov",
       "Karnataka November 2024 statistics, PDF page 1, district commission rows",
       "At November 2024 close, Bengaluru Urban pending 380, Bengaluru Rural 46, Urban I Additional 443, II Additional 492, III Additional 442, IV Additional 358. The input does not identify which commission or grouping its generic Bengaluru entity represents. Do not select or sum branches without a unit definition.",
       ["entity_scope_ambiguous"])
review("cat", "cat_ar tribunals_2025",
       "DoPT AR 2024-25, Annexure V, printed page 160 / PDF page 170, annual institution/disposal/pendency rows",
       "CY2023 institution 25742, disposal 31672, pending 74615. CY2024 institution 32998, disposal 35460, pending 72153. March 2025 row gives 7411, 9625, 69939. The annexure heading refers to December 2024 despite an appended March 2025 row. LS 1007 repeats CY2023/2024 disposal and pending figures, likely from the same tribunal returns. None directly establishes a 2024-12-01 snapshot or the undefined last_year. No matching-period mean duration located.",
       ["period_mismatch"])
review("aft", "aft_reply tribunals_2025",
       "RS 4152, 30 March 2026, page 1 table and LS 1007, 5 December 2025, page 3 annexure",
       "RS 4152's 2024 row is registered 9837, disposed 7993, pending 1844 in a table requested as at January 2026. Each yearly pending equals registered minus disposed, consistent with a registration-cohort remainder rather than the entire year-end backlog. LS 1007 instead gives 2024 disposed 7706 and pending 6058. Scope and disagreement remain unresolved. Do not replace the full pending claim with 1844 or average the two sources. No matching-period mean duration located.",
       ["primary_figures_conflict_or_scope_differs", "possible_cohort_not_backlog", "period_mismatch"])
review("drt", "drt_reply tribunals_2025",
       "LS 440, 5 February 2024, annexure, OA/SA pending as at 24 January 2024",
       "All-DRT pending 215431 = original applications 162317 + securitisation applications 53114 as at 24 January 2024. LS 1007's CY2024 pending is 233901. Neither date matches 1 December 2024. No replacement selected.",
       ["period_mismatch"])
review("nclt", "nclt_nclat_2024 tribunals_2025",
       "RS 1654, 6 August 2024, part (d) and LS 1007 annexure",
       "NCLT pending 19770 as at 30 June 2024. LS 1007 gives CY2023 disposed 9818 / pending 19793 and CY2024 disposed 14150 / pending 14961. Different dates and an undefined last_year prevent a matched replacement. No matching-period filing total or mean duration established.",
       ["period_mismatch"])
review("nclat", "nclt_nclat_2024 tribunals_2025",
       "RS 1654, 6 August 2024, part (e) and LS 1007 annexure",
       "NCLAT pending 3019 as at 30 June 2024. LS 1007 gives CY2023 disposed 2385 / pending 180 and CY2024 disposed 2487 / pending 894. Date and possible cohort/scope differences remain unresolved. Do not average or treat overlapping ageing bands as additive. No matching-period filing total or mean duration established.",
       ["period_mismatch", "possible_scope_difference"])
review("itat", "tribunals_2025 itat_pib itat_reports itat_ar_hindi",
       "LS 1007 annexure, ITAT row and PIB PRID 2210455, year-end review",
       "LS 1007 reports CY2023 disposed 33008 and CY2024 disposed 38370. PIB repeats 38370 for calendar 2024 and gives 52088 for 2025 up to 1 December. These do not resolve last_year at input date 2024-12-01. The Legal Affairs annual-report index returned an empty client-rendered shell. The attempted 2023-24 Hindi PDF returned HTTP 404. No matching-period filing total or mean duration established.",
       ["annual_period_undefined", "primary_fetch_failed"])
review("merc", "merc_ar merc_index",
       "MERC AR 2023-24, printed page 3 / PDF page 39, petition table, visually checked against native OCR",
       "FY2023-24 opening 101, received/suo motu/remanded 254, disposed by order 155, withdrawn/disposed 12, closing 188. Total disposals derived as 155+12 = 167, with 101+254-167 = 188. Inflow includes categories beyond fresh filings. Rate for these flows is 167/254 = 0.6575. The March 2024 close is not the input's December snapshot. No matching-period mean duration located.",
       ["period_mismatch", "inflow_scope_includes_remands"])
review("derc", "derc_ar derc_index",
       "DERC AR 2022-23, printed page 22 / PDF page 96, disposal paragraph",
       "FY2022-23 disposals: 25 petitions under section 142 plus 41 other petitions = 66. The public annual-report index located in this run ends at 2022-23. That does not establish the input's 2024-12-01 pending or undefined annual interval. No matching-period pending, filed or mean duration located.",
       ["period_mismatch"])
review("kerc", "kerc_ar kerc_reports",
       "KERC AR 2023-24, PDF page 38, section 10.1(4), and page 6",
       "FY2023-24 adjudication petitions filed 91 and finally disposed 140. Ratio 140/91 = 1.5385 applies only to this scope. Do not substitute separate RTI application statistics for tribunal cases. No pending count or mean duration supporting the input located.",
       ["annual_period_undefined", "adjudication_scope"])
review("tnerc", "tnerc_ar tnerc_summary",
       "TNERC AR 2023-24, PDF page 89 section 4, statistical summary and CAG management-report section 4",
       "Section 4 table for FY2023-24 sums to opening 133, admitted 116, disposed 135, pending 114. Components (opening/admitted/disposed/pending): dispute 9/31/18/22, review 8/4/11/1, miscellaneous 112/78/103/87, power-purchase approval 4/3/3/4. Another summary/audit table in the same report totals opening 162, filed 99, disposed 135, pending 116. Category coverage or reporting conflicts remain unresolved. Do not average or choose between 114 and 116 pending, or 116 and 99 inflow. The live 2026 summary is also a different period. No matching-period mean duration located.",
       ["primary_internal_conflict_or_scope_differs", "period_mismatch"])
review("mh_rera", "mh_rera_ar mh_rera_reports",
       "MahaRERA AR 2023-24, PDF page 14, section 3 complaints table and current-position paragraphs",
       "Report table gives opening 7155, received during year 3949 and disposed 3059, implying closing 8045. Text also reports, as at 30 April 2024, registered-project complaints 23932 and disposals 15887 (difference 8045), plus unregistered complaints 974 and disposals 774. All categories imply pending 8245, not the same scope as registered projects. The FY title and April update need care. No primary substantiates the December claim or mean 365 days.",
       ["period_mismatch", "registered_vs_all_complaints"])
review("ka_rera", "ka_rera_home",
       "Karnataka RERA official homepage and searches for annual complaint statistics",
       "The live official portal was fetched, but no dated primary table grounding these December 2024 figures was located. Current portal links and search snippets are not historical counts. No claim is marked NA merely because an annual report was not found.",
       ["matching_primary_not_located"])
review("cci", "cci_ar_retry",
       "CCI AR 2024-25, tables B1, F1 and F2, printed pages 12, 29-30, scanned pages checked with native OCR and images",
       "FY2023-24 combinations: opening 8, notifications 111 plus one suo motu case = 112, disposal 94 without modifications + 3 with modifications + 4 invalid/withdrawn = 101, closing 19. F2 gives average approval time 16 working days, a combinations-only measure. FY2024-25 combinations received 139, disposed 138 and closing 20. Antitrust B1 is a prima-facie stage table: a section 26(1) referral to investigation is not final disposal. Do not combine antitrust screening and merger totals into one generic caseload or replace the generic duration with merger working days. Initial 30 MB download limit failed, then a 100 MB limit succeeded.",
       ["case_category_ambiguous", "duration_scope_and_unit_mismatch", "period_mismatch"])
review("ngt", "ngt_dashboard",
       "NGT bench-wise dashboard, total for 1 August 2025 to 31 July 2026 and monthly May-July 2026 rows",
       "Current rolling-year filed 5326, disposed 3936, pending 5890 as at 31 July 2026, rate 0.7390. Input date is 30 April 2026. May/June/July filed totals are 375/188/412 and disposed totals 274/108/401. Back-calculation 5890 - ((375-274)+(188-108)+(412-401)) = 5698 is consistent with the stored pending if there were no adjustments, but is not a directly published April pending figure. Do not refute April 5698 merely with July 5890. Input 1937/1976 rounds to 0.9803, not 0.9813. Underlying historical annual counts remain unverified, so 0.9803 is an arithmetic diagnostic, not a verified replacement.",
       ["period_mismatch", "historical_pending_conditionally_consistent"])
review("lok_adalat_generic", "lok_adalat_pib",
       "PIB PRID 2040672, Annexures A-C, National, State and Permanent Lok Adalat tables",
       "National Lok Adalat CY2023 disposal 85342217. State Lok Adalat FY2023-24 disposal 1207103 and Permanent Lok Adalat FY2023-24 disposal 232763 are separately tabulated. The generic entity does not specify the programme, calendar/fiscal interval, or inclusion of pre-litigation settlements. Do not mix these counts or equate pre-litigation settlements with court-filed cases.",
       ["entity_scope_ambiguous", "annual_period_undefined"])
review("dl_state_cdrc tn_state_cdrc", "consumer_state_2024 consumer_2024 consumer_stats",
       "LS 2574, 11 December 2024, Annexure I, and LS 1389, 4 December 2024, Annexure A",
       "LS 2574 state-commission consumer complaints over 1 January 2022 to 31 October 2024: Delhi filed 2421 / disposed 901, Tamil Nadu 4982 / 1521. These are multi-year and may exclude appeals. LS 1389 gives combined SCDRC plus DCDRC figures, not state-commission-only pending. Do not assign statewide district-plus-state totals to a state commission. NCDRC stats page timed out. No matching-period mean duration located.",
       ["aggregate_scope_mismatch", "cumulative_not_annual", "primary_fetch_failed"])
review("mh_state_cdrc mh_cdrc_mumbai mh_cdrc_pune mh_cdrc_nagpur",
       "mh_consumer_quarterly mh_consumer_dec mh_consumer_index consumer_state_2024 consumer_2024 consumer_stats",
       "Maharashtra commission monthly-report archive, internal PDF dates, plus LS 2574 / LS 1389 annexures",
       "Official archive links have mismatched labels: the PDF saved as mh_consumer_quarterly has December 2023 content, while the link saved as mh_consumer_dec contains June 2023 content and the impossible printed date 31/06/2023. Neither establishes December 2024 pending. Tables distinguish state circuit benches, several Mumbai district commissions, Pune and Additional Pune, Nagpur and Additional Nagpur. Do not select an unspecified branch or use all-Maharashtra SCDRC+DCDRC totals for the state commission. LS 2574's state-commission complaints filed 9017 / disposed 787 cover January 2022 to October 2024, not one year. NCDRC stats page timed out.",
       ["period_mismatch", "archive_label_date_mismatch", "entity_scope_requires_review", "primary_fetch_failed"])
review("tn_cdrc_chennai", "consumer_2024 tn_consumer_policy consumer_stats",
       "LS 1389 Annexure A and attempted Tamil Nadu policy-note / NCDRC statistics sources",
       "LS 1389 contains state-plus-district aggregates, not a Chennai-specific total. The generic Chennai entity also needs a North/South or combined-commission definition. The attempted Tamil Nadu 2025-26 policy-note URL returned HTTP 404 and NCDRC stats timed out. No matching-period direct primary count located.",
       ["entity_scope_ambiguous", "aggregate_scope_mismatch", "primary_fetch_failed"])


def main():
    (ROOT / "inputs/verifier_prompt.md").chmod(0o444)
    assert digest(ROOT / "inputs/verifier_prompt.md") == PROMPT_SHA
    assert digest(ROOT / "inputs/claims_to_verify.csv") == CLAIMS_SHA
    claims = list(csv.DictReader((ROOT / "inputs/claims_to_verify.csv").open(newline="")))
    entities = list(dict.fromkeys(r["entity_id"] for r in claims))
    assert len(claims) == 140 and len(entities) == 44
    records = [json.loads(line) for line in (ROOT / "fetch_log/manifest.jsonl").read_text().splitlines()]
    sources = {r["label"]: r for r in records}
    assert sources["sat_recheck"]["curl_exit"] == 0
    for entity in entities:
        if entity not in REVIEWS:
            assert all(r["field"] == "njdg_source_stamp" for r in claims if r["entity_id"] == entity)
            review(entity, "njdg_scope", "NIC NJDG project description and verifier prompt source-validity rule",
                   "Only a source stamp is supplied for this entity. Assess NJDG source applicability only. No numerical claim or unpublished-caseload inference is added.")
    for item in REVIEWS.values():
        item["source_urls"] = [sources[label]["requested_url"] for label in item["source_labels"]]
    if (ROOT / "run_artifacts.json").exists():
        previous = json.loads((ROOT / "run_artifacts.json").read_text())
        previous_meta = json.loads((ROOT / previous["meta"]).read_text())
        stamp = dt.datetime.fromisoformat(previous_meta["timestamp_utc"])
    else:
        stamp = dt.datetime.now(dt.timezone.utc)
    timestamp = stamp.strftime("%Y%m%d_%H%M%S")
    basename = "codex__verify-trib-01__agriya__" + timestamp
    rates = {}
    for entity in entities:
        values = {r["field"]: r["current_value"] for r in claims if r["entity_id"] == entity}
        if "disposal_rate" in values:
            filed = Decimal(values["filed_last_year"])
            disposed = Decimal(values["disposed_last_year"])
            actual = ratio(disposed, filed)
            rates[entity] = dict(stored=values["disposal_rate"], recomputed_4dp=actual,
                                 matches_4dp=Decimal(actual) == Decimal(values["disposal_rate"]),
                                 exact=Decimal(values["disposal_rate"]) * filed == disposed,
                                 underlying_counts_verified=False)
    outputs = []
    with (ROOT / (basename + ".csv")).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADER, lineterminator="\n")
        writer.writeheader()
        for entity in entities:
            reviewed = REVIEWS[entity]
            for claim in (r for r in claims if r["entity_id"] == entity):
                row = dict.fromkeys(HEADER, "")
                for key in HEADER[:6]:
                    row[key] = claim[key]
                row.update(verdict="UNSOURCED", primary_count=0,
                           independent_secondary_count=0, confidence_tier="UNSOURCED")
                flags = []
                field = claim["field"]
                if field == "njdg_source_stamp":
                    if claim["current_value"] == "present":
                        row.update(verdict="REFUTE", verified_value="absent",
                                   source_class="GoI_primary", source_title="NIC: National Judicial Data Grid",
                                   source_url=sources["njdg_scope"]["requested_url"],
                                   table_or_section="Project description: eCourts scope",
                                   primary_count=1, confidence_tier="partial", njdg_stamp_valid="FALSE")
                        row["notes"] = "recommend strip NJDG source. REFUTE refers to source validity, not whether the supplied stamp is present. verified_value=absent is the recommended state after removal. Applies the prompt's explicit exclusion rule, supported by NIC's court-system scope. No independent inspection of repository sources arrays."
                        if entity == entities[0]:
                            row["verbatim_excerpt"] = "cases in High Courts and Subordinate Courts"
                    else:
                        row.update(verdict="NA", notes="Input stamp is absent. No NJDG source to strip. NA applies to stamp validity, not to the body's caseload. Validity left blank because there is no source stamp to assess. Repository absence not independently audited.")
                else:
                    flags.extend(reviewed["flags"])
                    value = Decimal(claim["current_value"])
                    if any(value == Decimal(42) * Decimal(10) ** n for n in range(-6, 13)):
                        flags.append("value_on_42_ladder")
                    if field == "pending_cases" and value % 100 == 0:
                        flags.append("pending_round_thousand" if value % 1000 == 0 else "pending_round_hundred")
                    if field == "avg_disposal_days" and value == 365:
                        flags.append("avg_disposal_days_365")
                    url = claim["current_source_url"]
                    if claim["current_source_type"] in {"AnnualReport", "DoJ_Report", "Tribunal_Report"} and (not url or urlparse(url).path in {"", "/"}):
                        flags.append("report_source_empty_or_homepage")
                    if field in {"filed_last_year", "disposed_last_year", "disposal_rate"}:
                        flags.append("annual_period_undefined")
                    row.update(source_class="government_primary_reviewed_not_matched",
                               source_title=reviewed["source_labels"][0],
                               source_url=reviewed["source_urls"][0], table_or_section=reviewed["section"])
                    row["notes"] = ("Input data_as_of=" + claim["data_as_of"] + ". " + reviewed["observations"]
                                    + " Reviewed/attempted URLs: " + " | ".join(reviewed["source_urls"])
                                    + ". No primary establishes this field with matching period and scope. Recommend withdraw/null pending a dated source. UNSOURCED describes this search result, not proof of fabrication or non-publication. primary_count counts documents grounding a verdict or verified replacement, not every reviewed document.")
                    if field == "disposal_rate":
                        diagnostic = rates[entity]
                        flags.append("rate_matches_stored_inputs_4dp" if diagnostic["matches_4dp"] else "rate_arithmetic_mismatch")
                        if diagnostic["exact"]:
                            flags.append("rate_exactly_equals_stored_disposed_over_filed")
                        row["notes"] += " Stored-count arithmetic gives " + diagnostic["recomputed_4dp"] + ". Arithmetic agreement does not verify those counts."
                    if entity == "cestat" and field == "pending_cases":
                        row.update(verdict="REFUTE", verified_value="72179", verified_as_of="2024-12-01",
                                   source_class="GoI_primary", source_title="CESTAT monthly institution, disposal and pendency statement",
                                   table_or_section="PDF page 3, December 2024, opening pending, TOTAL row",
                                   verbatim_excerpt="TOTAL 72179", primary_count=1, confidence_tier="partial")
                        row["notes"] = "Input data_as_of=2024-12-01. Published December opening pending is 72179, also November closing on PDF page 2. Interpret date-only snapshot as opening balance. The source notes possible physical-verification adjustments. Replace stored 120000 subject to this boundary convention."
                        flags.append("date_only_interpreted_as_opening_balance")
                    if entity == "ka_state_cdrc" and field == "pending_cases":
                        row.update(verdict="REFUTE", verified_value="9947", verified_as_of="2024-11-30",
                                   source_class="state_government_primary", source_title="Karnataka consumer commissions: November 2024 statistics",
                                   table_or_section="PDF page 1, Proforma IV, STATE COMMISSION TOTAL, pending column",
                                   verbatim_excerpt="TOTAL 73792 63845 9947", primary_count=1, confidence_tier="partial")
                        row["notes"] = "Input data_as_of=2024-12-01. The immediately preceding monthly close is 9947 on 2024-11-30, with appeals 8658 plus complaints 1289. This REFUTE assumes November close equals 1 December opening with no intervening adjustment. If data_as_of instead means 1 December close, downgrade to UNSOURCED pending that exact snapshot. State commission scope includes its benches, not district commissions."
                        flags.append("previous_close_as_next_opening_assumption")
                row["anomaly_flags"] = "|".join(dict.fromkeys(flags))
                writer.writerow(row)
                outputs.append(row)
            stream.flush()
            os.fsync(stream.fileno())
    counts = dict(Counter(r["verdict"] for r in outputs))
    counts.setdefault("CONFIRM", 0)
    numeric_refutes = [r for r in outputs if r["verdict"] == "REFUTE" and r["field"] != "njdg_source_stamp"]
    invalid_stamps = [r["entity_id"] for r in outputs if r["njdg_stamp_valid"] == "FALSE"]
    anchor = dict(status="PASS_SOURCE_AND_ARITHMETIC", period="FY2025-26", as_of="2026-03-31",
                  opening=960, filed=429, disposal_components=[135, 28, 47, 88, 25], disposed=323,
                  pending=1066, disposal_rate_4dp=ratio(323, 429), source_label="sat_recheck",
                  independently_blinded=False, note="Re-fetched and read the primary table, then recomputed. Expected answer and peer summary had already been exposed. Not a matched-period replacement for the input snapshot.")
    dump("evidence.json", dict(interpretation="Related primary figures are observations, not accepted replacements unless the CSV says REFUTE/CONFIRM. No secondaries ground integers.",
                              entities=REVIEWS, rate_diagnostics=rates, sat_anchor=anchor, sources=sources))
    metadata = dict(record_scope="original_verification_run_before_relocation_and_publication",
                    rater="agriya", model="codex", model_version=None,
                    context="repo-hosted Codex session + supplied files + live web + user email + peer summary in RUN_SETUP",
                    web_search=True, temperature=None, prompt_version="verify-trib-v1", batch_id="verify-trib-01",
                    timestamp_utc=stamp.isoformat(), entities_n=44, rows_n=140, tokens_in=None, tokens_out=None,
                    cost_estimate=None, model_family_exposed="GPT-6", harness="existing Codex agent session",
                    installed_codex_cli_version="0.153.0", cli_used_for_model_inference=False,
                    requested_temperature=0.2, calibration_eligible=False, metadata_complete_for_calibration=False,
                    run_status="review_and_pipeline_sample_with_protocol_deviations",
                    unknown_fields={"model_version": "Exact serving model identifier/snapshot is not exposed by this session.",
                                    "temperature": "Sampling temperature cannot be set or observed in the existing session.",
                                    "tokens_in": "No authoritative inference usage counter available.",
                                    "tokens_out": "No authoritative inference usage counter available.",
                                    "cost_estimate": "Actual session cost unavailable. No separate paid model API requests were made. Zero would not be a measured cost."},
                    repo_indexing="unknown automatic indexing, none explicitly invoked", canonical_repo_contents_read=False,
                    peer_summary_exposed=True, peer_result_csv_or_meta_or_fetch_logs_read=False,
                    protocol_deviations=[
                        "The supplied workspace is a JEM checkout. No canonical dataset was read or changed, but an isolated context arm cannot be certified.",
                        "Only the card and a 17-row sample were attached locally. Shared prompt and full 140-row claims were retrieved with gh from the linked verifier/deepseek branch.",
                        "The downloaded RUN_SETUP unexpectedly contains Prajna's detailed summary. It was read before recognizing the blinding problem. The email also contained aggregate findings and the expected SAT anchor.",
                        "This is the existing agent session, not a fresh model invocation with the card prepended and controlled temperature. Prompt bytes were preserved, but prompt-only inference is not claimed.",
                        "Research was batched across sources. Export appends and fsyncs one entity at a time, but the research itself did not follow a strictly one-entity inference loop.",
                        "The 2-5M-token and one-day effort estimates were not measured or enforced. Research is a bounded search pass, not proof that missing figures are unpublished.",
                        "SAT anchor was source-checked but cannot be called independently blinded. Different-period primary values are kept in notes instead of overwriting historical claims.",
                        "Two pending replacements use an explicitly disclosed start-of-day/month boundary convention.",
                        "NA on AFT means there is no supplied NJDG stamp to invalidate, not that AFT caseload is inapplicable.",
                        "Primary HTTP response bodies, PDF text/OCR and 15 search-result batches are archived. Early web preflight and product-documentation tool interactions were not exhaustively archived."
                    ], input_provenance=dict(repository="datastiltskin/jem", ref="verifier/deepseek",
                        prompt_path="jem/jem-verify-tribunals/inputs/verifier_prompt.md",
                        claims_path="jem/jem-verify-tribunals/inputs/claims_to_verify.csv",
                        setup_path="jem/jem-verify-tribunals/RUN_SETUP.md", local_sample_used_as_claims=False,
                        sha256={p.name: digest(p) for p in sorted((ROOT / "inputs").iterdir()) if p.is_file()}),
                    verdict_counts=counts, numeric_rows_n=96, numeric_refutes_n=len(numeric_refutes),
                    numeric_verified_entities_n=len({r["entity_id"] for r in numeric_refutes}),
                    njdg_invalid_n=len(invalid_stamps), sat_anchor_check=anchor,
                    artifacts=dict(csv=basename + ".csv", evidence="evidence.json", summary="SUMMARY.md", validation="validation.json", fetch_manifest="fetch_log/manifest.jsonl"),
                    writes_confined_to="out/", committed=False, pushed=False, pr_created=False,
                    regeneration_performed=False, recommended_use="Schema/pipeline exercise and human source review only. Exclude from blinded model-agreement calibration.")
    metadata["handoff"] = dict(repository_path="jem/jem-verify-tribunals/out",
                               branch="verifier/codex",
                               verification_decisions_changed_for_publication=False,
                               publication_sanitization_report="publication_sanitization.json",
                               note="Run-time committed/pushed flags describe the original local verification. The user subsequently authorized relocation, commit and publication. Source HTTP session cookies and CSRF values are removed from the publication archive, with original download hashes retained.")
    dump(basename + ".meta.json", metadata)
    lines = ["# Agriya verifier sample", "",
             "Review sample for DSo, packaged on the `verifier/codex` branch at `jem/jem-verify-tribunals/out/`. Do not include this run in blinded model-agreement calibration. No canonical data was changed. The original local verification was subsequently packaged for publication at Agriya's request.", "",
             "1. **Coverage:** 140 input rows across 44 entities. Primary-backed numeric replacements for 2 entities, each with a disclosed reporting-boundary assumption. All 44 source-stamp rows assessed. Related figures and unresolved date/scope differences are preserved in `evidence.json`. This coverage count excludes generic NJDG policy evidence.", "",
             "2. **Verdicts:** CONFIRM 0, REFUTE 45, UNSOURCED 94, NA 1. REFUTE comprises 2 numeric claims and 43 invalid NJDG sources. UNSOURCED is a bounded-search outcome, not proof that a value is false or unpublished. NA is AFT's already-absent stamp.", "",
             "3. **SAT anchor:** primary table and arithmetic PASS: pending 1,066, filed 429, disposed 323 for FY2025-26. Disposals = 135 + 28 + 47 + 88 + 25. Balance = 960 + 429 - 323 = 1,066. Rate = 0.7529. The table was fetched and visually inspected. Independence cannot be claimed because the expected answer and peer summary were already exposed. These figures do not refute the input's December 2024 snapshot solely by differing from it.", "",
             "   [SEBI annual report, Table 10.35, printed page 156](" + sources["sat_recheck"]["requested_url"] + ")", "",
             "4. **Every REFUTE:**", "", "   | Entity and field | Stored → proposed | Direct source and qualification |",
             "   | --- | --- | --- |"]
    for row in numeric_refutes:
        lines.append("   | " + row["entity_id"] + " · " + row["field"] + " | " + row["current_value"] + " → " + row["verified_value"] + " | [Primary document](" + row["source_url"] + "). " + row["notes"] + " |")
    lines += ["", "   Each of the following 43 entities has `njdg_source_stamp: present → absent`, meaning **recommend strip NJDG source**. This refutes source applicability, not the input's description that a stamp exists. [NIC's NJDG scope](" + sources["njdg_scope"]["requested_url"] + ") supports the prompt's explicit source-exclusion rule.", "",
              "   " + ", ".join("`" + entity + "`" for entity in invalid_stamps) + ".", "",
              "5. **NJDG stamps:** 43 rows have `njdg_stamp_valid=FALSE`. AFT's absent stamp has blank validity and NA verdict. Do not treat blank as TRUE.", "",
              "6. **Metadata:** every required key is present, but calibration metadata is **not complete**. Exact model version, actual temperature, token counts and cost are unavailable and are null with reasons. The context is labelled as a repo-hosted session with peer-summary exposure. `calibration_eligible=false`. The shared prompt is byte-preserved with SHA-256 `" + PROMPT_SHA + "`. Do not replace unknown usage with zero or claim the requested 0.2 temperature was used.", "",
              "NGT arithmetic also needs review: 1,937 / 1,976 = 0.9803 at four decimals, rather than 0.9813. This does not validate the underlying counts. The current July dashboard can be conditionally back-calculated to April pending 5,698, so a newer 5,890 does not by itself refute the April value.", "",
              "CSV: `" + basename + ".csv`. Metadata: `" + basename + ".meta.json`. Source archive: `fetch_log/`. Validation: `validation.json`.", "",
              "Commit message: `Add Codex tribunal verification sample`."]
    (ROOT / "SUMMARY.md").write_text("\n".join(lines) + "\n")
    dump("run_artifacts.json", dict(basename=basename, csv=basename + ".csv", meta=basename + ".meta.json"))
    print(json.dumps(dict(csv=basename + ".csv", verdict_counts=counts, invalid_stamps=len(invalid_stamps))))


if __name__ == "__main__":
    main()
