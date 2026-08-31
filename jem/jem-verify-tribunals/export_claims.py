#!/usr/bin/env python3
"""
export_claims.py — build claims_to_verify.csv for the JEM tribunal verifier pass.

RUN THIS YOURSELF (DSo), from the repo root (jem/). It emits the CURRENT stored
case_volume values + NJDG source-stamp presence for the 44 entities under test.
This CSV is the thing the verifier tests, so it MUST reflect live YAML — not any
prior reconstruction, not the RCA tables. Attach its output to both rater emails.
The raters never run this (they have no repo); it is a maintainer convenience.

Usage:
    cd jem
    python3 export_claims.py > claims_to_verify.csv
    # a coverage line (found/missing) is printed to stderr, not into the CSV
"""
import sys
import glob
import csv

try:
    import yaml
except ImportError:
    sys.exit("pip install pyyaml")

ENTITIES = {
    # CentralTribunal (12)
    "aft", "aptel", "cat", "cestat", "drat", "drt", "itat", "nclat", "nclt",
    "ngt", "sat", "tdsat",
    # RegulatoryBodyQJ (12)
    "cci", "derc", "dl_rera", "irdai", "ka_rera", "kerc", "merc", "mh_rera",
    "sebi", "tn_rera", "tnerc", "trai",
    # ConsumerCommission (10)
    "dl_state_cdrc", "ka_cdrc_bengaluru", "ka_state_cdrc", "mh_cdrc_mumbai",
    "mh_cdrc_nagpur", "mh_cdrc_pune", "mh_state_cdrc", "py_cdrc",
    "tn_cdrc_chennai", "tn_state_cdrc",
    # ADRBody (7)
    "dl_slsa", "ka_slsa", "lok_adalat_generic", "mh_slsa", "nalsa", "py_slsa",
    "tn_slsa",
    # ArbitralInstitution (3)
    "diac", "iiac", "mcia",
}

NUMERIC_FIELDS = [
    "pending_cases", "filed_last_year", "disposed_last_year",
    "disposal_rate", "avg_disposal_days",
]


def is_njdg_source(s):
    if not isinstance(s, dict):
        return False
    t = str(s.get("type", "")).lower()
    u = str(s.get("url", "")).lower()
    return t == "njdg" or "njdg.ecourts.gov.in" in u


def main():
    w = csv.writer(sys.stdout)
    w.writerow([
        "entity_id", "type", "field", "current_value",
        "current_source_type", "current_source_url", "data_as_of",
    ])
    found = set()
    for path in glob.glob("data/entities/**/*.yaml", recursive=True):
        try:
            with open(path, encoding="utf-8") as f:
                d = yaml.safe_load(f)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        eid = d.get("id")
        if eid not in ENTITIES:
            continue
        found.add(eid)
        etype = d.get("type", "")
        cv = d.get("case_volume") or {}
        cst = cv.get("source_type", "")
        csu = cv.get("source_url", "")
        cda = cv.get("data_as_of", "")
        for fld in NUMERIC_FIELDS:
            if cv.get(fld) is not None:
                w.writerow([eid, etype, fld, cv.get(fld), cst, csu, cda])
        stamped = any(is_njdg_source(s) for s in (d.get("sources") or []))
        w.writerow([eid, etype, "njdg_source_stamp",
                    "present" if stamped else "absent", "", "", cda])
    missing = sorted(ENTITIES - found)
    for eid in missing:
        w.writerow([eid, "", "NOT_FOUND", "", "", "", ""])
    print(f"# {len(found)}/{len(ENTITIES)} found; {len(missing)} missing: {missing}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
