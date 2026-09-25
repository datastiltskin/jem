"""Check the handoff contract, input preservation, arithmetic and source archive."""
import csv
import hashlib
import json
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHECKS = []


def check(name, condition):
    CHECKS.append(dict(check=name, passed=bool(condition)))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    artifacts = json.loads((ROOT / "run_artifacts.json").read_text())
    meta = json.loads((ROOT / artifacts["meta"]).read_text())
    evidence = json.loads((ROOT / "evidence.json").read_text())
    claims = list(csv.DictReader((ROOT / "inputs/claims_to_verify.csv").open(newline="")))
    with (ROOT / artifacts["csv"]).open(newline="") as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
        expected = "entity_id,type,field,current_value,current_source_type,current_source_url,verdict,verified_value,verified_as_of,source_class,source_title,source_url,table_or_section,verbatim_excerpt,primary_count,independent_secondary_count,confidence_tier,njdg_stamp_valid,anomaly_flags,notes".split(",")
        check("exact CSV header and no surplus columns", reader.fieldnames == expected and all(None not in row for row in rows))
    keys = lambda items: Counter((r["entity_id"], r["field"]) for r in items)
    check("140 rows and 44 entities", len(rows) == 140 and len({r["entity_id"] for r in rows}) == 44)
    check("every input key occurs exactly once", keys(rows) == keys(claims) and all(n == 1 for n in keys(rows).values()))
    check("input columns and order preserved", all(all(row[k] == claim[k] for k in expected[:6]) for row, claim in zip(rows, claims)))
    check("shared prompt byte identity", digest(ROOT / "inputs/verifier_prompt.md") == "81136dad77f0e2381729244a3e565bb00444427c8a851c2b47bddaa5ea0ce21d")
    check("full claims byte identity", digest(ROOT / "inputs/claims_to_verify.csv") == "43f3f75b86e9435ff5d046342c62b295c0f540938eba983fb9cb8c1299614d93")
    prompt_read_only = (ROOT / "inputs/verifier_prompt.md").stat().st_mode & 0o222 == 0
    check("valid verdict vocabulary", all(r["verdict"] in {"CONFIRM", "REFUTE", "UNSOURCED", "NA"} for r in rows))
    check("verdict counts agree with metadata", dict(Counter(r["verdict"] for r in rows)) == {k:v for k,v in meta["verdict_counts"].items() if v})
    check("numeric missing evidence never becomes a replacement", all(not r["verified_value"] for r in rows if r["field"] != "njdg_source_stamp" and r["verdict"] in {"UNSOURCED", "NA"}))
    checksums = []
    for line in (ROOT / "fetch_log/manifest.jsonl").read_text().splitlines():
        record = json.loads(line)
        if "body" in record:
            body = (ROOT / record["body"]).resolve()
            checksums.append(body.is_relative_to(ROOT) and body.exists() and digest(body) == record["sha256"] and body.stat().st_size == record["bytes"])
    check("all recorded HTTP body hashes and sizes match", bool(checksums) and all(checksums))
    successful = {s["requested_url"] for s in evidence["sources"].values() if s["curl_exit"] == 0 and s["response"].startswith("200\n")}
    numeric = [r for r in rows if r["field"] != "njdg_source_stamp" and r["verdict"] in {"REFUTE", "CONFIRM"}]
    check("numeric replacements have fetched primary, date, section and excerpt", all(r["source_url"] in successful and r["verified_as_of"] and r["table_or_section"] and r["verbatim_excerpt"] and int(r["primary_count"]) >= 1 for r in numeric))
    for row in numeric:
        label = evidence["entities"][row["entity_id"]]["source_labels"][0]
        text = (ROOT / "fetch_log" / (label + ".txt")).read_text()
        check(row["entity_id"] + " replacement integer occurs in primary extraction", row["verified_value"] in text)
        check(row["entity_id"] + " boundary assumption disclosed", "opening" in row["notes"].lower() and "assumption" in row["anomaly_flags"] or "interpreted_as_opening" in row["anomaly_flags"])
    stamp_rows = [r for r in rows if r["field"] == "njdg_source_stamp"]
    check("all 43 present NJDG stamps invalidated", len([r for r in stamp_rows if r["current_value"] == "present"]) == 43 and all(r["njdg_stamp_valid"] == "FALSE" and "recommend strip NJDG source" in r["notes"] for r in stamp_rows if r["current_value"] == "present"))
    check("absent AFT stamp is not falsely marked valid", all(r["entity_id"] == "aft" and not r["njdg_stamp_valid"] and r["verdict"] == "NA" for r in stamp_rows if r["current_value"] == "absent"))
    anchor = evidence["sat_anchor"]
    check("SAT components sum to narrative disposal", sum(anchor["disposal_components"]) == anchor["disposed"] == 323)
    check("SAT opening plus filed less disposed equals closing", anchor["opening"] + anchor["filed"] - anchor["disposed"] == anchor["pending"] == 1066)
    sat_text = (ROOT / "fetch_log/sat_recheck.txt").read_text()
    check("SAT anchor numbers occur in archived primary", all(str(value) in sat_text.replace(",", "") for value in [1066, 429, 323]))
    rates = []
    mismatches = []
    for row in rows:
        if row["field"] != "disposal_rate":
            continue
        values = {r["field"]: Decimal(r["current_value"]) for r in rows if r["entity_id"] == row["entity_id"] and r["field"] in {"filed_last_year", "disposed_last_year"}}
        result = (values["disposed_last_year"] / values["filed_last_year"]).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        rates.append(evidence["rate_diagnostics"][row["entity_id"]]["recomputed_4dp"] == str(result))
        if result != Decimal(row["current_value"]):
            mismatches.append(row["entity_id"])
            check("arithmetic mismatch is surfaced", "rate_arithmetic_mismatch" in row["anomaly_flags"])
    check("all 18 rates independently recomputed", len(rates) == 18 and all(rates))
    check("NGT is the sole stored arithmetic mismatch", mismatches == ["ngt"])
    required = "rater model model_version context web_search temperature prompt_version batch_id timestamp_utc entities_n rows_n tokens_in tokens_out cost_estimate".split()
    check("all required metadata keys present", all(k in meta for k in required))
    check("unknown calibration fields have explicit explanations", all(meta[k] is None and meta["unknown_fields"].get(k) for k in ["model_version", "temperature", "tokens_in", "tokens_out", "cost_estimate"]))
    check("study deviations cannot be mistaken for eligible calibration", meta["calibration_eligible"] is False and meta["metadata_complete_for_calibration"] is False and meta["peer_summary_exposed"] is True)
    check("one result CSV and one matching meta JSON", len(list(ROOT.glob("codex__*.csv"))) == 1 and len(list(ROOT.glob("codex__*.meta.json"))) == 1)
    result = dict(artifact_checks_passed=all(c["passed"] for c in CHECKS), checks=CHECKS,
                  calibration_requirements_passed=False,
                  calibration_failures=["Exact model version unavailable", "Actual temperature uncontrolled and unknown", "Usage and cost unmeasured", "Repo-hosted context", "Peer summary exposed"],
                  human_review_required=["Confirm the opening-balance convention for the two numeric REFUTEs", "Resolve undefined annual intervals and unit scopes before applying candidate figures"],
                  local_prompt_read_only=prompt_read_only,
                  prompt_permissions_note="Git preserves executable bits, not read-only permissions. SHA-256 is the portable integrity check. The export script reapplies chmod 0444.",
                  recorded_http_bodies_checked=len(checksums))
    (ROOT / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["artifact_checks_passed"] else 1)


if __name__ == "__main__":
    main()
