"""Bounded, finite PDF text evidence; coordinates are always unrotated points."""
import math
import re

MAX_LOCATIONS = 60
MAX_FINDINGS = 4096


def validated_locations(locations):
    """Reject unsafe geometry rather than inventing a replacement rectangle."""
    result, truncated = [], False
    if not isinstance(locations, (list, tuple)):
        return result, truncated
    for location in locations:
        if not isinstance(location, dict):
            continue
        page, box, text = location.get('page'), location.get('bbox'), location.get('text')
        if type(page) is not int or page < 1 or not isinstance(text, str):
            continue
        if not isinstance(box, (list, tuple)) or len(box) != 4:
            continue
        try:
            finite = all(type(value) in (int, float) and math.isfinite(value) for value in box)
        except OverflowError:
            finite = False
        if not finite:
            continue
        if not (0 <= box[0] < box[2] and 0 <= box[1] < box[3]):
            continue
        if len(result) == MAX_LOCATIONS:
            truncated = True
            break
        result.append(dict(page=page, bbox=list(box), text=text))
    return result, truncated


def item_locations(page, items):
    return validated_locations([dict(page=page['page_no'], bbox=item.get('bbox'),
                                     text=item.get('text')) for item in items])


def locations_on_page(finding, page_dict, profile=None):
    """Use stored evidence, or conservatively locate a schema-1 local finding.

    Legacy document-wide checks deliberately do not acquire text highlights.
    The caller still clips boxes against the physical page before rendering.
    """
    page_no = page_dict['page_no']
    if 'locations' in finding:
        locations, _ = validated_locations(finding.get('locations'))
        return [location for location in locations if location['page'] == page_no]
    if finding.get('page') != page_no:
        return []
    from .checker import DEFAULT_PROFILE, MM, normalize
    profile = profile or DEFAULT_PROFILE
    rule = finding.get('rule_id')
    evidence = normalize(str(finding.get('anchor') or finding.get('evidence', '')))
    lines, spans = page_dict.get('lines', []), page_dict.get('spans', [])
    items = []
    if rule in {'R_HEADING', 'R_FIGURE', 'R_TABLE', 'R_APPENDIX'}:
        items = [line for line in lines if normalize(line['text']) == evidence]
    elif rule == 'R_NUMBER':
        items = [line for line in lines if line['text'].strip() == evidence
                 and line['bbox'][1] > page_dict['height_pt'] * .88]
    elif rule in {'R_FONT', 'R_COLOR', 'R_MARGIN'}:
        for span in spans:
            text, box = span['text'].strip(), span['bbox']
            if len(text) < 35 or not 30 < box[1] < page_dict['height_pt'] - 35:
                continue
            font = re.sub(r'^[A-Z]{6}\+', '', span['font']).lower().replace(' ', '').replace('-', '')
            wrong = ((not any(name in font for name in ('timesnewroman', 'timesroman'))
                      or abs(span['size'] - profile['font_size']) > .5) if rule == 'R_FONT'
                     else span['color'] != 0 if rule == 'R_COLOR' else
                     (box[0] / MM < profile['margin_left'] - 2 or
                      (page_dict['width_pt'] - box[2]) / MM < profile['margin_right'] - 2 or
                      box[1] / MM < profile['margin_top'] - 2 or
                      (page_dict['height_pt'] - box[3]) / MM < profile['margin_bottom'] - 2))
            if wrong and (rule == 'R_FONT' or normalize(text[:100]) in evidence):
                items.append(span)
    return item_locations(page_dict, items)[0]
