"""PDF-only adaptation of Tsinghua's page-evidence / registry / finding workflow.

Upstream: jacky-rui/tsinghua-thesis-format-checker-skill, MIT,
f19b8392a111eacff7b6e80211560298abca852e. Original retained in vendor/tsinghua.
The page parser below extends upstream guide_checker/extractors/pdf.py with
font and coordinate evidence. Academy rules replace the upstream Chinese rules.
"""
import hashlib
import re
from collections import Counter
from pathlib import Path

import pymupdf as fitz

SOURCE = "https://www.apa.kz/wp-content/uploads/2024/09/Приложение-1-Требования-к-оформлению.docx"
DEFAULT_PROFILE = dict(code="apa-2024", name="APA 2024 · № 586", source_url=SOURCE,
                       version="2024-09-13", min_pages_one=40, min_pages_long=60,
                       font_size=14, margin_left=30, margin_right=10, margin_top=20, margin_bottom=20)
MAX_SIZE = 30 * 1024 * 1024
MAX_PAGES = 300
MM = 72 / 25.4
ALIASES = {
    "contents": r"(?:содержание|мазмұны|contents|table of contents)",
    "introduction": r"(?:введение|кіріспе|introduction)",
    "conclusion": r"(?:заключение|қорытынды|conclusion|conclusions)",
    "references": r"(?:список (?:использованных )?(?:источников|литературы)|пайдаланылған (?:дереккөздер|әдебиеттер)(?: тізімі)?|әдебиеттер тізімі|references|bibliography)",
    "appendix": r"(?:приложение|қосымша|appendix|appendices)(?:\s+\S+)?",
}
REGISTRY = [
    ("R_SIZE", "5.1.1", "geometry"), ("R_LENGTH", "Объём работы / Жұмыс көлемі / Work length", "text_method"),
    ("R_FONT", "5.1.2", "font_method"), ("R_COLOR", "5.1.2", "font_method"),
    ("R_MARGIN", "5.1.2", "geometry"), ("R_NUMBER", "5.3.1–5.3.5", "geometry"),
    ("R_STRUCTURE", "4; 5.2.1", "text_method"), ("R_HEADING", "5.2.1–5.2.4; 5.3.4", "text_method"),
    ("R_FIGURE", "5.4.1–5.4.7", "text_method"), ("R_TABLE", "5.5.1–5.5.8", "text_method"),
    ("R_REFERENCE", "5.7.3–5.8.1", "text_method"), ("R_APPENDIX", "5.9.1–5.9.6", "text_method"),
    ("R_SPACING", "5.1.2", "inference_method"), ("R_VISUAL", "4; 5.4.8; 5.5.8", "inference_method"),
]


class PDFError(ValueError):
    pass


def normalize(text):
    return re.sub(r"\s+", " ", text.casefold()).strip().rstrip(".")


def parse_pdf_pages(path):
    """Preserve page numbers, dimensions and lines from upstream's page contract."""
    if Path(path).stat().st_size > MAX_SIZE:
        raise PDFError("too_large")
    try:
        # Byte streams avoid an OS-handle leak on MuPDF's failed-open path
        # for malformed documents on Windows.
        doc = fitz.open(stream=Path(path).read_bytes(), filetype="pdf")
    except Exception as exc:
        raise PDFError("bad_pdf") from exc
    with doc:
        if not doc.is_pdf:
            raise PDFError("bad_pdf")
        if doc.is_encrypted:
            raise PDFError("encrypted")
        if not 1 <= len(doc) <= MAX_PAGES:
            raise PDFError("too_many_pages")
        pages = []
        for idx, page in enumerate(doc):
            spans, lines = [], []
            for block in page.get_text("dict")["blocks"]:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    text = "".join(s["text"] for s in line["spans"]).strip()
                    if text:
                        lines.append(dict(text=text, bbox=list(line["bbox"])))
                    for span in line["spans"]:
                        if span["text"].strip():
                            spans.append({key: span[key] for key in ("text", "font", "size", "color", "flags", "bbox")})
            text = page.get_text("text")
            pages.append(dict(page_no=idx + 1, width_pt=page.rect.width, height_pt=page.rect.height,
                              text=text, lines=lines, spans=spans, images=len(page.get_image_info())))
        readable = sum(len(p["text"].strip()) >= 20 for p in pages)
        if not readable or readable / len(pages) < 0.5:
            raise PDFError("scan")
        return pages


def heading_pages(pages, key):
    pattern = re.compile(r"^(?:\d+(?:\.\d+)*\.?\s+)?" + ALIASES[key] + r"$", re.I)
    return [(p, line) for p in pages for line in p["lines"] if pattern.fullmatch(normalize(line["text"]))]


def check_pdf(path, *, duration="1", language="kk", profile=None):
    profile = profile or DEFAULT_PROFILE.copy()
    pages = parse_pdf_pages(path)
    findings = []
    registry = {rid: (clause, method) for rid, clause, method in REGISTRY}

    def add(rid, status, page=None, evidence="", message="observed"):
        clause, method = registry[rid]
        findings.append(dict(rule_id=rid, status=status, page=page, evidence=str(evidence)[:700],
                             message=message, clause=clause, method=method,
                             source_url=profile["source_url"]))

    bad_size = [p for p in pages if abs(min(p["width_pt"], p["height_pt"]) / MM - 210) > 1
                or abs(max(p["width_pt"], p["height_pt"]) / MM - 297) > 1]
    if bad_size:
        for p in bad_size:
            add("R_SIZE", "fail", p["page_no"], f'{p["width_pt"]/MM:.1f} × {p["height_pt"]/MM:.1f} mm; A4: 210 × 297 mm')
    else:
        add("R_SIZE", "pass", evidence="A4: 210 × 297 mm; ±1 mm")

    intro = heading_pages(pages, "introduction")
    refs = heading_pages(pages, "references")
    appendix = [(p, line) for p, line in heading_pages(pages, "appendix")
                if p["page_no"] > (refs[0][0]["page_no"] if refs else (intro[0][0]["page_no"] if intro else 2))]
    appendix_start = appendix[0][0]["page_no"] if appendix else None
    body_pages = appendix_start - 1 if appendix_start else len(pages)
    minimum = profile["min_pages_one"] if duration == "1" else profile["min_pages_long"]
    length_status = "pass" if body_pages >= minimum else "fail"
    # Unrecognised appendix boundaries cannot establish compliance for long files.
    if not appendix and re.search(ALIASES["appendix"], "\n".join(p["text"] for p in pages[-10:]), re.I):
        length_status = "uncertain"
    add("R_LENGTH", length_status, evidence=f"{body_pages} / ≥{minimum}",
        message="not_measurable" if length_status == "uncertain" else "observed")

    first_body = intro[0][0]["page_no"] if intro else 2
    last_body = refs[0][0]["page_no"] if refs else body_pages
    candidates = []
    for p in pages:
        if not first_body <= p["page_no"] <= last_body:
            continue
        for s in p["spans"]:
            if len(s["text"].strip()) >= 35 and 30 < s["bbox"][1] < p["height_pt"] - 35:
                candidates.append((p, s))
    if not candidates:
        add("R_FONT", "uncertain", message="no_evidence")
        add("R_COLOR", "uncertain", message="no_evidence")
    else:
        weights = Counter()
        for _, s in candidates:
            font = re.sub(r"^[A-Z]{6}\+", "", s["font"]).lower().replace(" ", "").replace("-", "")
            weights[(font, round(s["size"], 1))] += len(s["text"])
        dominant, weight = weights.most_common(1)[0]
        known_font = any(f in dominant[0] for f in ("timesnewroman", "timesroman"))
        confidence = weight / sum(weights.values())
        status = "pass" if known_font and abs(dominant[1] - profile["font_size"]) <= 0.5 else "fail"
        if confidence < 0.5:
            status = "uncertain"
        sample = next((p, s) for p, s in candidates if round(s["size"], 1) == dominant[1])
        add("R_FONT", status, sample[0]["page_no"],
            f"{dominant[0]}, {dominant[1]} pt; ≥50%: {confidence:.0%}; Times New Roman {profile['font_size']} pt")
        # A dominant font check does not establish that every body span complies.
        if status == "pass" and len(weights) > 1:
            add("R_FONT", "uncertain", evidence="; ".join(f"{f} {size} pt" for f, size in weights if (f, size) != dominant)[:500])
        colored = [(p, s) for p, s in candidates if s["color"] != 0]
        if colored:
            p, s = colored[0]
            add("R_COLOR", "fail", p["page_no"], s["text"][:180] + f"; #{s['color']:06x}")
        else:
            add("R_COLOR", "pass", evidence="#000000")

    # Measure occupied text boxes. Values close to the target demonstrate the
    # rendered text envelope, never the source Word section settings.
    intrusions = []
    margins = []
    for p, s in candidates:
        x0, y0, x1, y1 = s["bbox"]
        margins.append((x0/MM, (p["width_pt"]-x1)/MM, y0/MM, (p["height_pt"]-y1)/MM))
        if (x0 / MM < profile["margin_left"] - 2 or
            (p["width_pt"] - x1) / MM < profile["margin_right"] - 2 or
            y0 / MM < profile["margin_top"] - 2 or
            (p["height_pt"] - y1) / MM < profile["margin_bottom"] - 2):
            intrusions.append((p, s))
    for p, s in intrusions[:20]:
        add("R_MARGIN", "fail", p["page_no"], s["text"][:160])
    if not intrusions:
        if margins:
            measured = [min(row[i] for row in margins) for i in range(4)]
            expected = [profile['margin_left'],profile['margin_right'],profile['margin_top'],profile['margin_bottom']]
            exact = all(abs(a-b) <= 2 for a,b in zip(measured,expected))
            add("R_MARGIN", "pass" if exact else "uncertain", evidence=" / ".join(f"{v:.1f}" for v in measured)+" mm; ±2 mm",
                message="observed" if exact else "not_measurable")
        else:
            add("R_MARGIN", "uncertain", message="no_evidence")

    numbers = []
    for p in pages:
        footer = [line for line in p["lines"] if line["bbox"][1] > p["height_pt"] * .88
                  and re.fullmatch(r"\d{1,3}", line["text"].strip())]
        centered = [line for line in footer if abs((line["bbox"][0] + line["bbox"][2]) / 2 - p["width_pt"] / 2) < 8 * MM]
        if centered:
            numbers.append((p["page_no"], int(centered[0]["text"])))
    bad_numbers = [(physical, visible) for physical, visible in numbers if physical == 1 or physical != visible]
    if bad_numbers:
        for physical, visible in bad_numbers[:20]:
            add("R_NUMBER", "fail", physical, str(visible), "number_order")
    elif len(numbers) == len(pages) - 1 and all(p != 1 for p, _ in numbers):
        add("R_NUMBER", "pass", message="number_order")
    else:
        add("R_NUMBER", "uncertain", evidence=f"{len(numbers)} / {len(pages)-1}", message="number_order")

    section_locations = {}
    for key in ("contents", "introduction", "conclusion", "references"):
        matches = heading_pages(pages, key)
        section_locations[key] = matches[0][0]["page_no"] if matches else None
        add("R_STRUCTURE", "pass" if matches else "fail", section_locations[key], key,
            "observed" if matches else "no_evidence")
    located = [p for p in section_locations.values() if p]
    if located != sorted(located):
        add("R_STRUCTURE", "uncertain", evidence=str(section_locations), message="not_measurable")
    for key in ("introduction", "conclusion", "references"):
        matches = heading_pages(pages, key)
        for p, line in matches[:1]:
            bold = any(s["flags"] & 16 for s in p["spans"] if normalize(s["text"]) == normalize(line["text"]))
            add("R_HEADING", "pass" if bold else "uncertain", p["page_no"], line["text"])
            body_lines = [item for item in p['lines'] if item['bbox'][1] > 30]
            if body_lines and normalize(body_lines[0]['text']) != normalize(line['text']):
                add("R_HEADING", "fail", p['page_no'], line['text'])

    for rid, pattern in (("R_FIGURE", r"^(?:рисунок|рис\.|сурет|figure|fig\.)\s*(\d+(?:\.\d+)*)\s*[-–—.:]?\s*(.*)$"),
                         ("R_TABLE", r"^(?:таблица|кесте|table)\s*(\d+(?:\.\d+)*)\s*[-–—.:]?\s*(.*)$")):
        captions = [(p, line, re.match(pattern, line["text"], re.I)) for p in pages for line in p["lines"]
                    if re.match(pattern, line["text"], re.I)]
        for p, line, match in captions[:40]:
            # A caption must have a number and a non-empty title.
            add(rid, "pass" if match.group(2).strip() else "fail", p["page_no"], line["text"])
        if not captions:
            add(rid, "uncertain", message="no_evidence")

    ref_page = section_locations["references"]
    body_text = "\n".join(p["text"] for p in pages if p["page_no"] < (ref_page or len(pages) + 1))
    citations = re.findall(r"\[\s*\d+(?:\s*[,;–\-]\s*[^\]\n]+)?\s*\]", body_text)
    if citations:
        cited = [int(re.search(r'\d+', c).group()) for c in citations]
        first_seen = list(dict.fromkeys(cited))
        ordered = first_seen == sorted(first_seen) and first_seen[0] == 1
        add("R_REFERENCE", "pass" if ordered and ref_page else "fail", evidence="; ".join(citations[:20]))
    else:
        add("R_REFERENCE", "uncertain", message="no_evidence")
    if appendix:
        for p, line in appendix[:20]:
            suffix = line["text"].split()[-1]
            add("R_APPENDIX", "pass" if suffix.isdigit() else "fail", p["page_no"], line["text"])
        add("R_APPENDIX", "uncertain", message="not_measurable")
    else:
        add("R_APPENDIX", "uncertain", message="no_evidence")
    from statistics import median
    ratios = []
    for p in pages:
        lines = [line for line in p['lines'] if len(line['text']) >= 35]
        lines.sort(key=lambda item:item['bbox'][1])
        for a,b in zip(lines,lines[1:]):
            delta = b['bbox'][1]-a['bbox'][1]
            if abs(a['bbox'][0]-b['bbox'][0]) < 15 and 8 < delta < 35:
                ratios.append(delta/profile['font_size'])
    if len(ratios) >= 5:
        ratio = median(ratios)
        add('R_SPACING','pass' if 0.95 <= ratio <= 1.3 else 'fail',evidence=f'{ratio:.2f} × {profile["font_size"]} pt; median')
    else:
        add('R_SPACING','uncertain',message='no_evidence')
    # Text-only PDFs have no detected raster illustration area; vector figures
    # and complex tables are explicitly outside this estimate.
    image_pages = [p for p in pages if p['images']]
    add('R_VISUAL','uncertain' if image_pages else 'na', evidence=f"Raster illustrations: {sum(p['images'] for p in pages)}",
        message='not_measurable' if image_pages else 'observed')
    for p in pages:
        if len(p["text"].strip()) < 20:
            add("R_VISUAL", "uncertain", p["page_no"], message="mixed_scans")
    counts = Counter(f["status"] for f in findings)
    return dict(schema_version=1, engine="apa-pdf-0.1.0", profile=profile, language=language, duration=duration,
                page_count=len(pages), body_pages=body_pages, appendix_start=appendix_start,
                original_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                counts={s: counts[s] for s in ("pass", "fail", "uncertain", "na")}, findings=findings)
