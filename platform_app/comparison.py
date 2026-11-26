"""Conservative, content-based comparison of completed PDF checks.

Pages locate evidence but never identify it. Missing findings alone do not prove
a correction: local text must have been rechecked, or a conclusive document-wide
requirement must now pass. Legacy reports without anchors remain readable.
"""
import hashlib
import math
import re
from collections import Counter, defaultdict, deque

from .checker import DEFAULT_PROFILE, REGISTRY, normalize


_RULES = {row[0] for row in REGISTRY}
_GLOBAL = {"R_SIZE", "R_LENGTH", "R_NUMBER"}
_SECTIONS = {"contents", "introduction", "conclusion", "references"}
_STATES = ("fixed", "remaining", "new", "unverified")


def _valid(value):
    if not isinstance(value, dict) or type(value.get("schema_version")) is not int or value["schema_version"] not in (1, 2):
        return False
    profile = value.get("profile")
    if not isinstance(profile, dict) or not set(DEFAULT_PROFILE).issubset(profile):
        return False
    for key in ("code", "name", "source_url", "version"):
        if not isinstance(profile[key], str) or not profile[key].strip():
            return False
    for key in ("min_pages_one", "min_pages_long", "font_size", "margin_left", "margin_right", "margin_top", "margin_bottom"):
        number = profile[key]
        if type(number) not in (float, int) or not math.isfinite(number) or number < 0:
            return False
    if any(type(profile[key]) is not int or profile[key] < 1 for key in ("min_pages_one", "min_pages_long")) or profile["font_size"] <= 0:
        return False
    if value.get("duration") not in ("1", "1.5", "2") or value.get("language") not in ("kk", "ru", "en"):
        return False
    findings = value.get("findings")
    if not isinstance(findings, list):
        return False
    for finding in findings:
        if not isinstance(finding, dict) or not isinstance(finding.get("rule_id"), str) or finding["rule_id"] not in _RULES:
            return False
        if finding.get("status") not in ("pass", "fail", "uncertain", "na"):
            return False
        if any(key in finding and not isinstance(finding[key], str) for key in ("anchor", "evidence")):
            return False
    checked = value.get("checked_anchors", {})
    return (isinstance(checked, dict) and all(
        rule in _RULES and isinstance(hashes, list) and all(
            isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest) for digest in hashes)
        for rule, hashes in checked.items()))


def _anchor(finding):
    return normalize(finding.get("anchor", ""))


def _key(finding):
    # Legacy evidence supports "remaining", never proof that a local error was fixed.
    text = _anchor(finding) or normalize(finding.get("evidence", ""))
    return finding["rule_id"], text


def _overlaps(first, second):
    """Keep rewrapped errors inconclusive when two consecutive words survive.

    A line may gain both a prefix and suffix after reflow, so neither complete
    line needs to contain the other. Common phrases can conservatively withhold
    fixed credit; this overlap is never sufficient to assert a correction.
    """
    if first in second or second in first:
        return True
    first_words, second_words = re.findall(r"\w+", first), re.findall(r"\w+", second)
    first_pairs = set(zip(first_words, first_words[1:]))
    return any(pair in first_pairs for pair in zip(second_words, second_words[1:]))


def compare_results(previous, current):
    """Return ``{comparable, reason, counts, rows}`` without changing inputs.

    Counts refer to failed findings, not rules. Rows have ``status``, ``rule_id``,
    ``previous`` / ``current`` finding (or None), and a stable reason code. Uncertain
    findings prevent unsupported corrections but never become "fixed" themselves.
    Repeated failures are matched one to one; coordinates and page shifts are ignored.
    """
    output = dict(comparable=False, reason="invalid_result", counts={key: 0 for key in _STATES}, rows=[])
    if not _valid(previous) or not _valid(current):
        return output
    for key in ("profile", "duration", "language"):
        if previous[key] != current[key]:
            output["reason"] = key + "_changed"
            return output
    output.update(comparable=True, reason="same_settings")
    prior_failures = [finding for finding in previous["findings"] if finding["status"] == "fail"]
    current_failures = [finding for finding in current["findings"] if finding["status"] == "fail"]
    indexed = defaultdict(deque)
    for index, finding in enumerate(current_failures):
        indexed[_key(finding)].append(index)
    used = set()
    by_rule = defaultdict(list)
    for finding in current["findings"]:
        by_rule[finding["rule_id"]].append(finding)
    checked = {rule: Counter(hashes) for rule, hashes in current.get("checked_anchors", {}).items()}

    def append(status, old=None, new=None, reason=""):
        output["counts"][status] += 1
        output["rows"].append(dict(status=status, rule_id=(old or new)["rule_id"],
                                   previous=old, current=new, reason=reason))

    for old in prior_failures:
        key = _key(old)
        if key[1] and indexed[key]:
            index = indexed[key].popleft()
            used.add(index)
            append("remaining", old, current_failures[index], "same_evidence")
            continue
        rule = old["rule_id"]
        rule_findings = by_rule[rule]
        anchor = _anchor(old)
        if current.get("evidence_truncated"):
            append("unverified", old, reason="current_evidence_inconclusive")
            continue
        if rule == "R_STRUCTURE":
            section = normalize(old.get("evidence", ""))
            section_findings = [f for f in rule_findings if normalize(f.get("evidence", "")) == section]
            passed = next((f for f in section_findings if f["status"] == "pass"), None)
            if (section in _SECTIONS and passed
                    and not any(f["status"] in ("fail", "uncertain") for f in section_findings)):
                append("fixed", old, passed, "section_now_present")
                continue
        # An uncertain finding without a text anchor cannot establish which text
        # was checked reliably. A failure on the same repeated text also blocks
        # credit for unmatched duplicates, even after one-to-one matching.
        blocking = [finding for finding in rule_findings if finding["status"] in ("fail", "uncertain")
                    and (not _anchor(finding) or (anchor and _overlaps(anchor, _anchor(finding))))]
        if blocking:
            append("unverified", old, reason="current_evidence_inconclusive")
            continue
        if rule in _GLOBAL and rule_findings and all(f["status"] == "pass" for f in rule_findings):
            append("fixed", old, next(iter(rule_findings)), "global_requirement_passed")
            continue
        digest = hashlib.sha256(anchor.encode()).hexdigest() if anchor else None
        rule_checked = checked.get(rule, Counter())
        if digest and rule_checked[digest] > 0:
            rule_checked[digest] -= 1
            append("fixed", old, reason="same_text_rechecked")
        else:
            append("unverified", old, reason="text_not_rechecked")
    for index, finding in enumerate(current_failures):
        if index not in used:
            append("new", new=finding, reason="new_failure")
    return output
