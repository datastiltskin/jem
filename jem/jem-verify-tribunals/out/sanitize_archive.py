"""Remove public-site session values from the publication copy of fetch logs."""
import datetime
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
ARCHIVE = ROOT / "fetch_log"
REPORT = ROOT / "publication_sanitization.json"
REPLACEMENT = b"[REDACTED_FOR_PUBLICATION]"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sanitize_headers(data):
    kept = []
    count = 0
    removed_previous = False
    for line in data.splitlines(keepends=True):
        if re.match(rb"(?i)^set-cookie\s*:", line):
            count += 1
            removed_previous = True
        elif removed_previous and line.startswith((b" ", b"\t")):
            continue
        else:
            kept.append(line)
            removed_previous = False
    return b"".join(kept), count


def sanitize_csrf_markup(data):
    count = 0

    def sanitize_tag(match):
        nonlocal count
        tag = match.group()
        name = re.search(rb"(?i)\bname\s*=\s*([\"'])(.*?)\1", tag)
        if not name or b"csrf" not in name.group(2).lower():
            return tag

        def sanitize_attribute(attribute):
            nonlocal count
            if attribute.group(3) == REPLACEMENT:
                return attribute.group()
            count += 1
            return attribute.group(1) + attribute.group(2) + REPLACEMENT + attribute.group(2)

        return re.sub(
            rb"(?i)(\b(?:content|value)\s*=\s*)([\"'])(.*?)\2",
            sanitize_attribute,
            tag,
        )

    cleaned = re.sub(rb"(?i)<(?:meta|input)\b[^>]*>", sanitize_tag, data)
    return cleaned, count


def main():
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if REPORT.exists():
        report = json.loads(REPORT.read_text())
    else:
        report = {
            "purpose": "Publication hygiene after verification. No case-count evidence is changed.",
            "created_at_utc": timestamp,
            "actions": [],
            "notes": [
                "Session cookies came from anonymous public HTTP responses, not authenticated accounts.",
                "Original hashes identify downloaded bytes, but no unsanitized copies are retained here.",
                "Manifest sha256 and bytes describe published bodies. original_download preserves download identity.",
                "Header publication hashes are recorded here because the fetch manifest originally hashed bodies only.",
                "This helper is idempotent. It does not perform a new verification run.",
            ],
        }

    for path in sorted(ARCHIVE.glob("*.headers")):
        original = path.read_bytes()
        published, count = sanitize_headers(original)
        if not count:
            continue
        path.write_bytes(published)
        report["actions"].append({
            "path": str(path.relative_to(ROOT)),
            "action": "remove_set_cookie_response_headers",
            "removed_headers_n": count,
            "original_sha256": digest(original),
            "original_bytes": len(original),
            "published_sha256": digest(published),
            "published_bytes": len(published),
            "sanitized_at_utc": timestamp,
        })

    path = ARCHIVE / "cestat_notices.response"
    original = path.read_bytes()
    published, count = sanitize_csrf_markup(original)
    if count:
        manifest_path = ARCHIVE / "manifest.jsonl"
        records = [json.loads(line) for line in manifest_path.read_text().splitlines()]
        matching = [record for record in records if record.get("body") == str(path.relative_to(ROOT))]
        if not matching:
            raise ValueError("CESTAT response has no manifest record")
        for record in matching:
            if record["sha256"] != digest(original) or record["bytes"] != len(original):
                raise ValueError("CESTAT response does not match its recorded download identity")
            record.setdefault("original_download", {"sha256": record["sha256"], "bytes": record["bytes"]})
            record.update(sha256=digest(published), bytes=len(published), sanitized_for_publication=True)
            record["publication_sanitization"] = {
                "action": "redact_csrf_markup_values",
                "redacted_values_n": count,
                "sanitized_at_utc": timestamp,
                "report": REPORT.name,
            }
        path.write_bytes(published)
        manifest_path.write_text("".join(json.dumps(record) + "\n" for record in records))
        report["actions"].append({
            "path": str(path.relative_to(ROOT)),
            "action": "redact_csrf_markup_values",
            "redacted_values_n": count,
            "original_sha256": digest(original),
            "original_bytes": len(original),
            "published_sha256": digest(published),
            "published_bytes": len(published),
            "sanitized_at_utc": timestamp,
        })

    report["removed_set_cookie_headers_n"] = sum(action.get("removed_headers_n", 0) for action in report["actions"])
    report["redacted_csrf_values_n"] = sum(action.get("redacted_values_n", 0) for action in report["actions"])
    report["changed_files_n"] = len({action["path"] for action in report["actions"]})
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("changed_files_n", "removed_set_cookie_headers_n", "redacted_csrf_values_n")}))


if __name__ == "__main__":
    main()
