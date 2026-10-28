import io
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether

from .i18n import strings, finding_text


def pdf_report(job, lang):
    t = strings(lang)
    font = Path(__file__).parent / "assets" / "NotoSans-Regular.ttf"
    if "NotoSans" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("NotoSans", str(font)))
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=(595.28, 841.89), leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42,
                            title=t["report"], author="APA Thesis Checker")
    body = ParagraphStyle("body", fontName="NotoSans", fontSize=9, leading=14, spaceAfter=7, alignment=TA_LEFT)
    heading = ParagraphStyle("heading", parent=body, fontSize=16, leading=22, spaceAfter=15, textColor=colors.HexColor("#274476"))
    label = ParagraphStyle("label", parent=body, fontSize=11, leading=16, textColor=colors.HexColor("#274476"))
    p = lambda value, style=body: Paragraph(escape(str(value)), style)
    flow = [p(t["report"], heading), p(job.title, label), p(t["academy"]),
            p(f"{t['profile']}: {job.profile['name']} / {job.profile['version']}"),
            p(f"{t['pages']}: {job.result['page_count']} · {t['body_pages']}: {job.result['body_pages']}"),
            p(t["limits_text"]), p("SHA-256: " + job.result["original_sha256"]), Spacer(1, 12)]
    for finding in job.result["findings"]:
        f = finding_text(finding, lang)
        flow.append(p(f"{f['rule_id']} · {f['title']} — {f['status_label']}", label))
        if f["page"]:
            flow.append(p(f"{t['page']}: {f['page']}"))
        flow += [p(f["explanation"]), p(f"{t['evidence']}: {f['evidence'] or '—'}"),
                 p(f"{t['method']}: {f['method_label']}"), p(f"{t['source_clause']}: {f['clause']}"),
                 p(f"{t['recommendation']}: {f['recommendation']}"), Spacer(1, 8)]
    flow += [p(t["requirements"], label), p(job.profile["source_url"])]

    def footer(canvas, document):
        canvas.setFont("NotoSans", 8)
        canvas.setFillColor(colors.HexColor("#667085"))
        canvas.drawString(42, 24, "APA Thesis Checker · v0.1.0")
        canvas.drawRightString(553, 24, str(document.page))
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
