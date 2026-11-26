import copy
import hashlib

from django.test import SimpleTestCase

from platform_app.checker import DEFAULT_PROFILE, normalize


def finding(rule="R_MARGIN", status="fail", anchor="Unchanged research sentence", page=3, **extra):
    return dict(rule_id=rule, status=status, anchor=anchor, page=page, evidence=anchor, **extra)


def result(findings, checked=None, **extra):
    value = dict(schema_version=1, engine="apa-pdf-0.1.0", profile=DEFAULT_PROFILE.copy(),
                 duration="1", language="en", findings=findings, checked_anchors=checked or {})
    value.update(extra)
    return value


def inspected(rule, *anchors):
    return {rule: [hashlib.sha256(normalize(anchor).encode()).hexdigest() for anchor in anchors]}


class GuidanceTests(SimpleTestCase):
    def guide(self, *args, **kwargs):
        try:
            from platform_app.guidance import guidance_for
        except ImportError:
            self.fail("Localized correction guidance has not been implemented")
        return guidance_for(*args, **kwargs)

    def test_profile_values_drive_font_margins_and_duration_minimum(self):
        profile = dict(DEFAULT_PROFILE, font_size=12.5, margin_left=32, margin_right=11,
                       margin_top=21, margin_bottom=22, min_pages_one=45, min_pages_long=65)
        for language in ("kk", "ru", "en"):
            font = self.guide(finding("R_FONT"), profile, language=language)
            self.assertIn("12.5", font["expected"])
            margins = self.guide(finding(), profile, language=language)
            for measurement in ("32", "11", "21", "22"):
                self.assertIn(measurement, margins["expected"])
            self.assertIn("45", self.guide(finding("R_LENGTH"), profile, "1", language)["expected"])
            self.assertIn("65", self.guide(finding("R_LENGTH"), profile, "1.5", language)["expected"])
            self.assertIn("65", self.guide(finding("R_LENGTH"), profile, "2", language)["expected"])

    def test_all_rules_have_localized_action_and_safe_formatting_example(self):
        from platform_app.checker import REGISTRY
        for rule, _, _ in REGISTRY:
            localized = []
            for language in ("kk", "ru", "en"):
                guide = self.guide(finding(rule, anchor="Private substantive research claim"), DEFAULT_PROFILE,
                                   language=language)
                self.assertEqual(set(guide), {"expected", "recommendation", "correct_example"})
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in guide.values()))
                self.assertNotIn("Private substantive research claim", str(guide))
                localized.append(guide["recommendation"])
            self.assertEqual(len(set(localized)), 3, rule)


class ComparisonTests(SimpleTestCase):
    def compare(self, *args):
        try:
            from platform_app.comparison import compare_results
        except ImportError:
            self.fail("Conservative revision comparison has not been implemented")
        return compare_results(*args)

    def assert_counts(self, value, fixed=0, remaining=0, new=0, unverified=0):
        self.assertTrue(value["comparable"])
        self.assertEqual(value["counts"], dict(fixed=fixed, remaining=remaining, new=new, unverified=unverified))
        self.assertEqual(len(value["rows"]), fixed + remaining + new + unverified)

    def test_identical_error_remains_after_page_shift_and_case_whitespace_normalization(self):
        value = self.compare(result([finding(anchor="Research   SENTENCE.")]),
                             result([finding(anchor="research sentence", page=19)]))
        self.assert_counts(value, remaining=1)
        self.assertEqual(value["rows"][0]["previous"]["page"], 3)
        self.assertEqual(value["rows"][0]["current"]["page"], 19)

    def test_disappearing_changed_or_deleted_text_is_unverified(self):
        for current in (result([]), result([finding(anchor="Different sentence")] ),
                        result([finding(status="pass", anchor="Different sentence")])):
            value = self.compare(result([finding()]), current)
            self.assert_counts(value, new=int(any(f["status"] == "fail" for f in current["findings"])), unverified=1)

    def test_inspection_of_same_anchor_proves_fixed_without_physical_page_identity(self):
        value = self.compare(result([finding()]), result([], inspected("R_MARGIN", "Unchanged research sentence")))
        self.assert_counts(value, fixed=1)

    def test_uncertain_same_anchor_is_unverified_even_when_checked(self):
        value = self.compare(result([finding()]), result([finding(status="uncertain")],
                             inspected("R_MARGIN", "Unchanged research sentence")))
        self.assert_counts(value, unverified=1)

    def test_general_uncertain_rule_blocks_disappearance_fix(self):
        value = self.compare(result([finding()]), result([finding(status="uncertain", anchor="")],
                             inspected("R_MARGIN", "Unchanged research sentence")))
        self.assert_counts(value, unverified=1)

    def test_repeated_errors_match_one_to_one(self):
        previous = result([finding(page=3), finding(page=4)])
        current = result([finding(page=12)], inspected("R_MARGIN", "Unchanged research sentence"))
        self.assert_counts(self.compare(previous, current), remaining=1, unverified=1)
        self.assert_counts(self.compare(result([finding()]), result([finding(), finding(page=4)])),
                           remaining=1, new=1)

    def test_checked_anchors_do_not_cross_rules(self):
        self.assert_counts(self.compare(result([finding()]),
                           result([], inspected("R_FONT", "Unchanged research sentence"))), unverified=1)

    def test_only_genuinely_global_passes_fix_legacy_failures(self):
        for rule in ("R_LENGTH", "R_SIZE", "R_NUMBER"):
            old = finding(rule); old.pop("anchor")
            new = finding(rule, "pass", anchor="different aggregate measurement")
            self.assert_counts(self.compare(result([old]), result([new])), fixed=1)
        for rule in ("R_FONT", "R_COLOR", "R_MARGIN", "R_SPACING", "R_REFERENCE"):
            self.assert_counts(self.compare(result([finding(rule)]),
                               result([finding(rule, "pass", anchor="different text")])), unverified=1)

    def test_section_identity_can_fix_missing_section_but_other_section_pass_cannot(self):
        old = dict(rule_id="R_STRUCTURE", status="fail", evidence="introduction", page=None)
        correct = dict(old, status="pass", page=4)
        unrelated = dict(correct, evidence="conclusion")
        self.assert_counts(self.compare(result([old]), result([correct])), fixed=1)
        self.assert_counts(self.compare(result([old]), result([unrelated])), unverified=1)

    def test_legacy_equal_evidence_can_remain_but_disappearance_is_unverified(self):
        old = finding(); old.pop("anchor")
        current = dict(old, page=25)
        self.assert_counts(self.compare(result([old]), result([current])), remaining=1)
        self.assert_counts(self.compare(result([old]), result([])), unverified=1)

    def test_metadata_differences_and_invalid_results_fail_closed(self):
        valid = result([finding()])
        altered_profile = dict(DEFAULT_PROFILE, font_size=12)
        cases = [None, {}, result([], profile=altered_profile), result([], duration="2"),
                 result([], language="kk"), result([], schema_version=42), result([{"status": "fail"}]),
                 result([finding(status="maybe")]), result([], checked_anchors={"R_MARGIN": [False]}),
                 result([finding(rule=[])]), result([], profile=dict(DEFAULT_PROFILE, font_size=float("nan"))),
                 result([], profile=dict(DEFAULT_PROFILE, min_pages_one=True))]
        for changed in cases:
            with self.subTest(changed=changed):
                comparison = self.compare(valid, changed)
                self.assertFalse(comparison["comparable"])
                self.assertTrue(comparison["reason"])
                self.assertEqual(comparison["counts"]["fixed"], 0)

    def test_each_checked_occurrence_can_only_prove_one_repeated_error_fixed(self):
        previous = result([finding(page=3), finding(page=4)])
        once = result([], inspected("R_MARGIN", "Unchanged research sentence"))
        twice = result([], inspected("R_MARGIN", "Unchanged research sentence", "Unchanged research sentence"))
        self.assert_counts(self.compare(previous, once), fixed=1, unverified=1)
        self.assert_counts(self.compare(previous, twice), fixed=2)

    def test_truncated_current_evidence_cannot_prove_a_correction(self):
        current = result([], inspected("R_MARGIN", "Unchanged research sentence"), evidence_truncated=True)
        self.assert_counts(self.compare(result([finding()]), current), unverified=1)

    def test_reflowed_failing_fragment_blocks_fix_credit_for_checked_full_text(self):
        current = result([finding(anchor="Unchanged research")], inspected("R_MARGIN", "Unchanged research sentence"))
        self.assert_counts(self.compare(result([finding()]), current), new=1, unverified=1)

    def test_reflow_with_prefix_and_suffix_cannot_hide_overlapping_failure(self):
        old_anchor = "alpha beta gamma delta"
        for status in ("fail", "uncertain"):
            for current_anchor in ("prefix alpha beta", "gamma delta suffix"):
                with self.subTest(status=status, current_anchor=current_anchor):
                    current = result([finding(status=status, anchor=current_anchor)], inspected("R_MARGIN", old_anchor))
                    self.assert_counts(self.compare(result([finding(anchor=old_anchor)]), current),
                                       unverified=1, new=int(status == "fail"))

    def test_present_introduction_is_fixed_while_separate_references_section_remains_missing(self):
        old = [dict(rule_id="R_STRUCTURE", status=status, evidence=section, page=page)
               for section, status, page in (("contents", "pass", 2), ("introduction", "fail", None),
                                             ("conclusion", "pass", 35), ("references", "fail", None))]
        current = [dict(item, status="pass", page=3) if item["evidence"] == "introduction" else dict(item)
                   for item in old]
        self.assert_counts(self.compare(result(old), result(current)), fixed=1, remaining=1)
        self.assert_counts(self.compare(result(old), result(current, evidence_truncated=True)),
                           unverified=1, remaining=1)

    def test_comparison_does_not_mutate_results_or_count_old_uncertainty_as_fixed(self):
        previous = result([finding(status="uncertain")]); current = result([finding()])
        snapshot = copy.deepcopy((previous, current))
        self.assert_counts(self.compare(previous, current), new=1)
        self.assertEqual((previous, current), snapshot)
