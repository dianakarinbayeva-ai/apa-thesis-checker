"""Only complete, renderable checker results can be treated as a pass."""
from collections import Counter
import re
from .checker import REGISTRY, MAX_PAGES
from .i18n import TEXT

STATUSES = {"pass", "fail", "uncertain", "na"}
RULES = {row[0] for row in REGISTRY}
METHODS = {row[2] for row in REGISTRY}


def valid_result(result, profile):
    if not isinstance(result, dict) or not isinstance(profile, dict):
        return False
    if any(not isinstance(profile.get(key), str) or not profile[key] for key in ("name", "version", "source_url")):
        return False
    if not profile["source_url"].startswith(("https://", "http://")):
        return False
    page_count, body_pages = result.get("page_count"), result.get("body_pages")
    if type(page_count) is not int or not 1 <= page_count <= MAX_PAGES:
        return False
    if type(body_pages) is not int or not 0 <= body_pages <= page_count:
        return False
    if not isinstance(result.get("original_sha256"), str) or not re.fullmatch(r"[0-9a-fA-F]{64}", result["original_sha256"]):
        return False
    findings, counts = result.get("findings"), result.get("counts")
    if not isinstance(findings, list) or not findings or not isinstance(counts, dict) or set(counts) != STATUSES:
        return False
    actual, rules = Counter(), set()
    for finding in findings:
        if not isinstance(finding, dict):
            return False
        for key in ("rule_id", "status", "method", "evidence", "clause", "source_url"):
            if not isinstance(finding.get(key), str):
                return False
        if finding["rule_id"] not in RULES or finding["status"] not in STATUSES or finding["method"] not in METHODS:
            return False
        message = finding.get("message", "observed")
        if not isinstance(message, str) or message not in TEXT["en"]:
            return False
        if "page" not in finding:
            return False
        page = finding["page"]
        if page is not None and (type(page) is not int or not 1 <= page <= MAX_PAGES):
            return False
        if not finding["source_url"].startswith(("https://", "http://")):
            return False
        actual[finding["status"]] += 1
        rules.add(finding["rule_id"])
    # The current checker emits heading findings only when it finds one of
    # these section headings. Missing headings still produce structure failures.
    headings_found = any(f["rule_id"] == "R_STRUCTURE" and f["status"] == "pass" and
                         f["evidence"] in ("introduction", "conclusion", "references") for f in findings)
    required = RULES if headings_found else RULES - {"R_HEADING"}
    return required <= rules and all(type(counts[key]) is int and counts[key] == actual[key] for key in STATUSES)
