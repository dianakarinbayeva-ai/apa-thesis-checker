import hashlib
import tempfile
from pathlib import Path

import pymupdf as fitz
from django.test import SimpleTestCase

from platform_app.checker import check_pdf, parse_pdf_pages


FONT = Path(__file__).resolve().parent.parent / 'platform_app/assets/NotoSans-Regular.ttf'
ANCHOR = 'Unique paragraph about public policy evidence.'


def evidence_pdf(*, target=33, wrong=True, rotate=False, language='en', reflow=False,
                 omit=False, crowded=False):
    labels = {'en': ('Introduction', 'References'), 'ru': ('Введение', 'Список литературы'),
              'kk': ('Кіріспе', 'Пайдаланылған әдебиеттер тізімі')}[language]
    doc = fitz.open()
    for number in range(1, 41 if not crowded else 221):
        page = doc.new_page(width=595.28, height=841.89)
        if number in (2, 39):
            page.insert_font(fontname='noto', fontfile=str(FONT))
            page.insert_text((85, 75), labels[number == 39], fontname='noto', fontsize=14)
        for row in range(4 if not crowded else 24):
            page.insert_text((85, 120 + row * 20),
                             'Regular research examines public administration.',
                             fontname='tiro', fontsize=14 if not crowded else 18,
                             color=(0, 0, 0) if not crowded else (1, 0, 0))
        if number == target and not omit:
            if reflow:
                for row, text in enumerate(('Unique paragraph about', 'public policy evidence.')):
                    page.insert_text((85, 250 + 18 * row), text, fontname='tiro', fontsize=14)
            else:
                page.insert_text((85, 250), ANCHOR, fontname='helv' if wrong else 'tiro',
                                 fontsize=18 if wrong else 14, color=(1, 0, 0) if wrong else (0, 0, 0))
        if number > 1:
            page.insert_text((294, 815), str(number), fontsize=10)
        if number == target and rotate:
            page.set_rotation(90)
    data = doc.tobytes(garbage=4, deflate=True)
    doc.close()
    return data


class EvidenceTests(SimpleTestCase):
    def inspect(self, data, **kwargs):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'evidence.pdf'
            path.write_bytes(data)
            result = check_pdf(path, **kwargs)
            self.assertEqual(path.read_bytes(), data)
            self.assertEqual(result['original_sha256'], hashlib.sha256(data).hexdigest())
            return result

    def test_isolated_wrong_paragraph_has_actual_page33_line_boxes(self):
        result = self.inspect(evidence_pdf())
        self.assertEqual(result['schema_version'], 2)
        for rule in ('R_FONT', 'R_COLOR'):
            matches = [f for f in result['findings'] if f['rule_id'] == rule
                       and f['status'] == 'fail' and f['page'] == 33]
            self.assertEqual(len(matches), 1, rule)
            self.assertEqual(matches[0]['anchor'], ANCHOR)
            location = matches[0]['locations'][0]
            self.assertEqual(location['page'], 33)
            self.assertEqual(location['text'], ANCHOR)
            self.assertAlmostEqual(location['bbox'][0], 85, places=1)
            self.assertLess(location['bbox'][1], 250)
            self.assertGreater(location['bbox'][3], 250)
        for finding in result['findings']:
            if finding['rule_id'] in ('R_SIZE', 'R_LENGTH') or (
                    finding['rule_id'] == 'R_STRUCTURE' and finding['status'] == 'fail'):
                self.assertFalse(finding.get('locations'))

    def test_fixed_paragraph_is_checked_after_page_shift_and_line_reflow(self):
        prior = self.inspect(evidence_pdf())
        result = self.inspect(evidence_pdf(target=34, wrong=False, reflow=True),
                              previous_findings=prior['findings'])
        digest = hashlib.sha256(ANCHOR.casefold().rstrip('.').encode()).hexdigest()
        for rule in ('R_FONT', 'R_COLOR'):
            self.assertIn(digest, result['checked_anchors'][rule])
            self.assertFalse(any(f['rule_id'] == rule and f['status'] == 'fail'
                                 for f in result['findings']))
        deleted = self.inspect(evidence_pdf(omit=True), previous_findings=prior['findings'])
        self.assertNotIn(digest, deleted['checked_anchors']['R_FONT'])

    def test_multilingual_sections_and_rotation_keep_unrotated_geometry(self):
        for language in ('kk', 'ru', 'en'):
            with self.subTest(language=language):
                result = self.inspect(evidence_pdf(language=language, rotate=True), language=language)
                error = next(f for f in result['findings'] if f['rule_id'] == 'R_COLOR' and f['status'] == 'fail')
                self.assertEqual(error['page'], 33)
                self.assertAlmostEqual(error['locations'][0]['bbox'][0], 85, places=1)
                self.assertLess(error['locations'][0]['bbox'][3], 280)
                self.assertFalse(any(f['rule_id'] == 'R_SIZE' and f['status'] == 'fail'
                                     for f in result['findings']))
                present = [f for f in result['findings'] if f['rule_id'] == 'R_STRUCTURE'
                           and f['status'] == 'pass']
                self.assertTrue(all(f.get('locations') for f in present))

    def test_limits_are_explicit_and_every_rule_survives_truncation(self):
        from platform_app.checker import REGISTRY
        result = self.inspect(evidence_pdf(crowded=True))
        self.assertLessEqual(len(result['findings']), 4096)
        self.assertTrue(result['evidence_truncated'])
        self.assertEqual({f['rule_id'] for f in result['findings']}, {r[0] for r in REGISTRY})
        self.assertTrue(all(len(f.get('locations', [])) <= 60 for f in result['findings']))

    def test_locations_reject_invalid_or_nonfinite_geometry_and_limit_count(self):
        from platform_app.evidence import validated_locations
        good = {'page': 1, 'bbox': [1, 2, 30, 40], 'text': 'real line'}
        invalid = [dict(good, bbox=box) for box in (
            [float('nan'), 2, 30, 40], [1, 2, float('inf'), 40], [4, 3, 2, 1],
            [-1, 2, 30, 40], [1, 2, 3], ['1', 2, 3, 4], [True, 2, 3, 4],
            [1, 2, 10 ** 400, 40])]
        invalid += [dict(good, page=0), dict(good, page=True), dict(good, page=1.5)]
        locations, truncated = validated_locations(invalid + [good])
        self.assertEqual(locations, [good])
        self.assertFalse(truncated)
        locations, truncated = validated_locations([good] * 61)
        self.assertEqual(len(locations), 60)
        self.assertTrue(truncated)

    def test_local_rules_expose_true_text_and_global_errors_have_no_boxes(self):
        doc = fitz.open()
        for number in range(1, 5):
            page = doc.new_page(width=595.28, height=841.89)
            page.insert_text((85, 120), 'Research addresses public policy and governance.', fontname='tiro', fontsize=14)
            if number == 2:
                for point, text in (((85, 160), 'Introduction'), ((20, 220), 'A margin intrusion requiring a precise local highlight.'),
                                    ((85, 260), 'Figure 1'), ((85, 300), 'Table 1'),
                                    ((85, 340), 'Initial citation unexpectedly starts at [3].'), ((294, 815), '99')):
                    page.insert_text(point, text, fontname='tiro', fontsize=14)
            elif number == 3:
                page.insert_text((85, 75), 'References', fontname='tiro', fontsize=14)
            elif number == 4:
                page.insert_text((85, 75), 'Appendix A', fontname='tiro', fontsize=14)
        result = self.inspect(doc.tobytes())
        doc.close()
        for rule in ('R_MARGIN', 'R_NUMBER', 'R_HEADING', 'R_FIGURE', 'R_TABLE', 'R_REFERENCE', 'R_APPENDIX'):
            local = next(f for f in result['findings'] if f['rule_id'] == rule and f['status'] == 'fail')
            self.assertTrue(local['locations'], rule)
            self.assertEqual(local['anchor'], local['locations'][0]['text'])
            self.assertEqual(local['page'], local['locations'][0]['page'])

    def test_legacy_localization_uses_real_matches_and_ignores_global_rules(self):
        from platform_app.evidence import locations_on_page
        data = evidence_pdf()
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'legacy.pdf'
            path.write_bytes(data)
            page = parse_pdf_pages(path)[32]
        old = {'rule_id': 'R_COLOR', 'status': 'fail', 'page': 33,
               'evidence': ANCHOR + '; #ff0000'}
        location = locations_on_page(old, page)[0]
        self.assertEqual(location['text'], ANCHOR)
        self.assertEqual(location['page'], 33)
        self.assertEqual(locations_on_page(dict(old, page=32), page), [])
        self.assertEqual(locations_on_page(dict(old, rule_id='R_SIZE'), page), [])
        self.assertEqual(locations_on_page(dict(old, locations=[{'page': 33, 'bbox': [1, 2, float('nan'), 4], 'text': ANCHOR}]), page), [])

    def test_short_wrong_span_inside_body_line_highlights_the_whole_line(self):
        doc = fitz.open(stream=evidence_pdf(wrong=False), filetype='pdf')
        page = doc[32]
        first = 'The findings support a public policy with '
        page.insert_text((85, 350), first, fontname='tiro', fontsize=14)
        x = 85 + fitz.get_text_length(first, fontname='tiro', fontsize=14)
        page.insert_text((x, 350), 'red evidence', fontname='helv', fontsize=18, color=(1, 0, 0))
        result = self.inspect(doc.tobytes())
        doc.close()
        for rule in ('R_FONT', 'R_COLOR'):
            error = next(f for f in result['findings'] if f['rule_id'] == rule and f['status'] == 'fail')
            self.assertEqual(error['page'], 33)
            self.assertIn('red evidence', error['anchor'])
            self.assertIn('The findings', error['anchor'])
            self.assertEqual(error['anchor'], error['locations'][0]['text'])
            self.assertAlmostEqual(error['locations'][0]['bbox'][0], 85, places=1)

    def test_old_anchor_cannot_match_inside_a_different_word(self):
        old = {'rule_id': 'R_FONT', 'anchor': 'nique paragraph about public policy evidence.'}
        result = self.inspect(evidence_pdf(wrong=False), previous_findings=[old])
        digest = hashlib.sha256(b'nique paragraph about public policy evidence').hexdigest()
        self.assertNotIn(digest, result['checked_anchors']['R_FONT'])
