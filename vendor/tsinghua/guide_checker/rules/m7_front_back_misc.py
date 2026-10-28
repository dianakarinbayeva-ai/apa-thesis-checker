from __future__ import annotations

import re

from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import get_page_lines, norm
from .common import (
    extract_body_figure_titles,
    extract_chapter_headings,
    extract_list_entries,
    find_exact_index,
    find_first_pdf_page_with_any_title,
    find_first_pdf_page_with_title,
    find_pdf_page_by_label,
    get_body_paragraphs,
    parse_toc_entries,
    split_entry_tail_page,
)


AUTH_TEMPLATE_ANCHORS = [
    "本人完全了解清华大学有关保留、使用学位论文的规定，即：",
    "清华大学拥有在著作权法规定范围内学位论文的使用权，其",
    "中包括：（1）已获学位的研究生必须按学校规定提交学位论文，",
    "学校可以采用影印、缩印或其他复制手段保存研究生上交的学位",
    "论文；（2）为教学和科研目的，学校可以将公开的学位论文作",
    "为资料在图书馆、资料室等场所供校内师生阅读，或在校园网上",
    "供校内师生浏览部分内容；（3）按照上级教育主管部门督导、",
    "抽查等要求，报送相应的学位论文。",
    "本人保证遵守上述规定。",
    "作者签名：",
    "导师签名：",
]

TRADITIONAL_HINTS = set("學術與為體這對於實際說發現級過現書國測圖關專術獻錄優讓還許體應將產設備")


def _find_toc_page_no(context: CheckContext, title: str) -> int | None:
    target = norm(title)
    for entry in parse_toc_entries(context.paragraphs):
        if norm(entry["title_part"]) == target and entry["page_label"]:
            page = find_pdf_page_by_label(context.pdf_pages, entry["page_label"])
            if page is not None:
                return page["page_no"]
    return None


def _content_pages_between(context: CheckContext, start_page_no: int, end_page_no: int) -> list[dict]:
    pages = []
    for page in context.pdf_pages:
        if start_page_no <= page["page_no"] < end_page_no and (page.get("text") or "").strip():
            pages.append(page)
    return pages


def _paragraph_location(paragraphs: list[dict], idx: int | None) -> str | None:
    if idx is None:
        return None
    para = paragraphs[idx]
    return f"DOCX 段落 {para['paragraph_id']}"


def _page_location(page_no: int | None, title: str | None = None) -> str | None:
    if page_no is None:
        return None
    if title:
        return f"PDF p{page_no}（{title}）"
    return f"PDF p{page_no}"


def _pdf_page_by_no(context: CheckContext, page_no: int | None) -> dict | None:
    if page_no is None or page_no < 1 or page_no > len(context.pdf_pages):
        return None
    return context.pdf_pages[page_no - 1]


def check_list02(rule: dict, context: CheckContext) -> Result:
    list_page_no = find_first_pdf_page_with_title(context.pdf_pages, "学位论文指导小组、公开评阅人和答辩委员会名单", allow_anywhere=True)
    auth_page_no = find_first_pdf_page_with_title(context.pdf_pages, "关于学位论文使用授权的说明", allow_anywhere=True)
    if list_page_no is None or auth_page_no is None:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "warning",
            "medium",
            rule["evidence_types"],
            "未能稳定定位名单页或授权说明页，当前无法判断名单页占用页数。",
            "增强 PDF 页首标题定位逻辑后再复核。",
            coverage="partial",
            locations=[loc for loc in [
                _page_location(list_page_no, "学位论文指导小组、公开评阅人和答辩委员会名单"),
                _page_location(auth_page_no, "关于学位论文使用授权的说明"),
            ] if loc],
        )

    content_pages = _content_pages_between(context, list_page_no, auth_page_no)
    if len(content_pages) > 1:
        continuation_titles = []
        for page in content_pages[1:]:
            top_text = norm("".join(get_page_lines(page)[:8]))
            if any(title in top_text for title in ("指导小组名单", "公开评阅人名单", "答辩委员会名单")):
                continuation_titles.append(f"p{page['page_no']}")
        if not continuation_titles:
            return Result(
                rule["rule_id"],
                rule["title"],
                rule["priority"],
                "fail",
                "medium",
                rule["evidence_types"],
                f"名单页占用 {len(content_pages)} 个内容页，未看到拆页后的标题变化。",
                "若名单页确需拆页，应按页面内容改写标题，并保证页序清晰。",
                coverage="partial",
                locations=[_page_location(content_pages[0]["page_no"], "学位论文指导小组、公开评阅人和答辩委员会名单")],
            )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"名单页当前占用 {len(content_pages)} 个内容页，未超过 1 页。",
        "无。",
        coverage="partial",
        locations=[_page_location(list_page_no, "学位论文指导小组、公开评阅人和答辩委员会名单")],
    )


def check_auth01(rule: dict, context: CheckContext) -> Result:
    title_idx = find_exact_index(context.paragraphs, "关于学位论文使用授权的说明")
    abstract_idx = find_exact_index(context.paragraphs, "摘要")
    if title_idx is None or abstract_idx is None or abstract_idx <= title_idx:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            "未能稳定定位授权说明正文。",
            "检查授权说明标题及其后正文。",
            coverage="partial",
            locations=[loc for loc in [_paragraph_location(context.paragraphs, title_idx)] if loc],
        )

    body_text = norm("".join(
        (para.get("text") or "")
        for para in context.paragraphs[title_idx + 1:abstract_idx]
        if (para.get("text") or "").strip()
    ))
    missing = []
    for anchor in AUTH_TEMPLATE_ANCHORS:
        if norm(anchor) not in body_text:
            missing.append(anchor)

    if missing:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            f"授权说明正文缺少模板关键语句：{missing[0][:18]}…",
            "按学校模板统一修正授权说明正文内容与署名栏。",
            coverage="partial",
            locations=[loc for loc in [_paragraph_location(context.paragraphs, title_idx)] if loc],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        "授权说明正文与当前模板锚点一致。",
        "无。",
        coverage="partial",
        locations=[loc for loc in [_paragraph_location(context.paragraphs, title_idx)] if loc],
    )


def check_abs05(rule: dict, context: CheckContext) -> Result:
    abs_idx = find_exact_index(context.paragraphs, "Abstract")
    toc_idx = find_exact_index(context.paragraphs, "目录")
    if abs_idx is None or toc_idx is None or toc_idx <= abs_idx:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            "未能稳定定位英文摘要范围。",
            "检查 Abstract 与目录边界。",
            coverage="partial",
            locations=[loc for loc in [_paragraph_location(context.paragraphs, abs_idx)] if loc],
        )

    body_paragraphs = []
    for para in context.paragraphs[abs_idx + 1:toc_idx]:
        text = (para.get("text") or "").strip()
        if not text or text.startswith("Keywords"):
            continue
        body_paragraphs.append(para)

    body_text = "\n".join(para.get("text", "") for para in body_paragraphs)
    chinese_punc = re.findall(r"[，。；：、（）【】“”‘’《》？！]", body_text)
    ascii_punc = re.findall(r"[,.;:()?!]", body_text)
    style_issues = []
    for para in body_paragraphs[:4]:
        fmt = para.get("para_fmt", {})
        if fmt.get("alignment") != "both":
            style_issues.append(f"段落 {para['paragraph_id']} 对齐={fmt.get('alignment')}")
            break

    if len(chinese_punc) > 0 or len(ascii_punc) == 0:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"英文摘要检测到中文全角标点 {len(chinese_punc)} 处，英文标点 {len(ascii_punc)} 处。",
            "英文摘要正文建议优先使用英文标点，并保持段落样式统一。",
            coverage="partial",
            locations=[_page_location(find_first_pdf_page_with_title(context.pdf_pages, "Abstract"), "Abstract")],
        )

    if style_issues:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "；".join(style_issues),
            "统一修正英文摘要正文段落样式。",
            coverage="partial",
            locations=[_paragraph_location(context.paragraphs, abs_idx)],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"英文摘要正文未检测到中文全角标点，英文标点使用正常，共识别英文标点 {len(ascii_punc)} 处。",
        "无。",
        coverage="partial",
        locations=[_page_location(find_first_pdf_page_with_title(context.pdf_pages, "Abstract"), "Abstract")],
    )


def check_lot01(rule: dict, context: CheckContext) -> Result:
    body_figures = extract_body_figure_titles(context.paragraphs)
    body_table_count = sum(
        1
        for para in get_body_paragraphs(context.paragraphs)
        if re.match(r"^表\s*\d+\.\d+\s+", (para.get("text") or "").strip())
    )
    figure_threshold = len(body_figures) >= 5
    table_threshold = body_table_count >= 5
    need_lists = figure_threshold or table_threshold or (len(body_figures) + body_table_count >= 10)

    toc_page = find_first_pdf_page_with_title(context.pdf_pages, "目录", allow_anywhere=True)
    figure_list_page = None
    table_list_page = None
    for entry in parse_toc_entries(context.paragraphs):
        title_norm = norm(entry["title_part"])
        if title_norm == norm("插图清单") and entry["page_label"]:
            page = find_pdf_page_by_label(context.pdf_pages, entry["page_label"])
            figure_list_page = page["page_no"] if page else None
        if title_norm == norm("附表清单") and entry["page_label"]:
            page = find_pdf_page_by_label(context.pdf_pages, entry["page_label"])
            table_list_page = page["page_no"] if page else None

    if not need_lists:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            f"正文图表规模暂未达到必须设置图表清单的自动检查阈值（图 {len(body_figures)} 条、表 {body_table_count} 条）。",
            "无。",
            coverage="partial",
        )

    missing = []
    if figure_threshold and figure_list_page is None:
        missing.append("插图清单")
    if table_threshold and table_list_page is None:
        missing.append("附表清单")
    if missing:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"图表数量较多，但未稳定识别到 {', '.join(missing)}。",
            "补充图表清单，并放在目录之后、正文之前。",
            coverage="partial",
            locations=[loc for loc in [
                _page_location(toc_page, "目录"),
                _page_location(figure_list_page, "插图清单") if figure_list_page else None,
                _page_location(table_list_page, "附表清单") if table_list_page else None,
            ] if loc],
        )

    if toc_page is not None and ((figure_list_page is not None and figure_list_page <= toc_page) or (table_list_page is not None and table_list_page <= toc_page)):
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "图表清单已识别到，但其页码未位于目录之后。",
            "将图表清单统一放在目录之后、正文之前。",
            coverage="partial",
            locations=[loc for loc in [
                _page_location(toc_page, "目录"),
                _page_location(figure_list_page, "插图清单") if figure_list_page else None,
                _page_location(table_list_page, "附表清单") if table_list_page else None,
            ] if loc],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"正文图表数量较多，插图清单与附表清单均已位于目录之后，当前结构符合自动检查范围。",
        "无。",
        coverage="partial",
        locations=[loc for loc in [
            _page_location(toc_page, "目录"),
            _page_location(figure_list_page, "插图清单") if figure_list_page else None,
            _page_location(table_list_page, "附表清单") if table_list_page else None,
        ] if loc],
    )


def check_ack01(rule: dict, context: CheckContext) -> Result:
    ack_page = _find_toc_page_no(context, "致谢")
    dec_page = _find_toc_page_no(context, "声明")
    if ack_page is None or dec_page is None:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "未能稳定定位致谢或声明的目录页码。",
            "检查目录中致谢与声明条目。",
            coverage="partial",
            locations=[loc for loc in [_page_location(ack_page, "致谢"), _page_location(dec_page, "声明")] if loc],
        )

    pdf_ack_page = _pdf_page_by_no(context, ack_page)
    pdf_dec_page = _pdf_page_by_no(context, dec_page)
    if pdf_ack_page is None or pdf_dec_page is None:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "无法映射致谢或声明的 PDF 物理页。",
            "检查目录页码与 PDF 页码标签是否一致。",
            coverage="partial",
            locations=[loc for loc in [_page_location(ack_page, "致谢"), _page_location(dec_page, "声明")] if loc],
        )

    ack_content_pages = _content_pages_between(context, pdf_ack_page["page_no"], pdf_dec_page["page_no"])
    if len(ack_content_pages) > 1:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"致谢占用 {len(ack_content_pages)} 个内容页，超过 1 页。",
            "将致谢压缩为单页，并保持篇眉为“致谢”。",
            coverage="partial",
            locations=[_page_location(ack_content_pages[0]["page_no"], "致谢")],
        )

    page_text = "".join(get_page_lines(pdf_ack_page)[:6])
    if "致谢" not in norm(page_text):
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "致谢页的页首文本未稳定识别到“致谢”。",
            "检查致谢页篇眉或页首标题。",
            coverage="partial",
            locations=[_page_location(pdf_ack_page["page_no"], "致谢")],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        "致谢页为单页，且页首识别到“致谢”。",
        "无。",
        coverage="partial",
        locations=[_page_location(pdf_ack_page["page_no"], "致谢")],
    )


def check_dec01(rule: dict, context: CheckContext) -> Result:
    ack_page = _find_toc_page_no(context, "致谢")
    dec_page = _find_toc_page_no(context, "声明")
    cv_page = _find_toc_page_no(context, "个人简历、在学期间完成的相关学术成果")
    if ack_page is None or dec_page is None or cv_page is None:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "未能稳定定位致谢、声明或个人简历的目录页码。",
            "检查目录后置部分条目。",
            coverage="partial",
            locations=[loc for loc in [_page_location(ack_page, "致谢"), _page_location(dec_page, "声明"), _page_location(cv_page, "个人简历、在学期间完成的相关学术成果")] if loc],
        )

    dec_pdf_page = _pdf_page_by_no(context, dec_page)
    cv_pdf_page = _pdf_page_by_no(context, cv_page)
    if dec_pdf_page is None or cv_pdf_page is None or dec_pdf_page["page_no"] >= cv_pdf_page["page_no"]:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "声明页未能稳定排在致谢之后、个人简历之前。",
            "将声明单独成页，并排在致谢之后。",
            coverage="partial",
            locations=[loc for loc in [_page_location(dec_pdf_page["page_no"] if dec_pdf_page else None, "声明"), _page_location(cv_pdf_page["page_no"] if cv_pdf_page else None, "个人简历、在学期间完成的相关学术成果")] if loc],
        )

    dec_content_pages = _content_pages_between(context, dec_pdf_page["page_no"], cv_pdf_page["page_no"])
    if len(dec_content_pages) > 1:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"声明占用 {len(dec_content_pages)} 个内容页，超过 1 页。",
            "将声明压缩为单页，并保持其位于致谢之后。",
            coverage="partial",
            locations=[_page_location(dec_pdf_page["page_no"], "声明")],
        )

    page_text = norm("".join(get_page_lines(dec_pdf_page)))
    if "声明" not in page_text:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "声明页页首未稳定识别到“声明”。",
            "检查声明页标题与页眉。",
            coverage="partial",
            locations=[_page_location(dec_pdf_page["page_no"], "声明")],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        "声明页位于致谢之后，且为单页，页首识别到“声明”。",
        "无。",
        coverage="partial",
        locations=[_page_location(dec_pdf_page["page_no"], "声明")],
    )


def check_cv01(rule: dict, context: CheckContext) -> Result:
    cv_page_no = _find_toc_page_no(context, "个人简历、在学期间完成的相关学术成果")
    if cv_page_no is None:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "未能在目录中定位个人简历部分。",
            "检查目录后置条目。",
            coverage="partial",
        )

    cv_pdf_page = _pdf_page_by_no(context, cv_page_no)
    if cv_pdf_page is None:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "未能将个人简历目录页码映射到 PDF 页面。",
            "检查页码标签。",
            coverage="partial",
            locations=[_page_location(cv_page_no, "个人简历、在学期间完成的相关学术成果")],
        )

    text = norm(cv_pdf_page.get("text", ""))
    has_basic = any(key in text for key in ("出生于", "考入", "毕业", "攻读", "至今"))
    has_sections = all(key in text for key in ("个人简历", "在学期间完成的相关学术成果"))
    has_articles = "学术论文" in text or "专利" in text or "软件著作" in text or "无" in text

    if not has_basic or not has_sections or not has_articles:
        missing = []
        if not has_basic:
            missing.append("基础信息")
        if not has_sections:
            missing.append("成果分节")
        if not has_articles:
            missing.append("成果类型")
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"个人简历部分缺少：{', '.join(missing)}。",
            "补足个人简历基础信息与成果分类型列示。",
            coverage="partial",
            locations=[_page_location(cv_pdf_page["page_no"], "个人简历、在学期间完成的相关学术成果")],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        "个人简历含基础信息，成果按类型列示，当前未见缺项。",
        "无。",
        coverage="partial",
        locations=[_page_location(cv_pdf_page["page_no"], "个人简历、在学期间完成的相关学术成果")],
    )


def _appendix_headings(paragraphs: list[dict]) -> list[dict]:
    items = []
    for para in paragraphs:
        text = (para.get("text") or "").strip()
        if not text.startswith("附录"):
            continue
        match = re.match(r"^附录\s*([A-Z])", text)
        items.append(
            {
                "paragraph_id": para["paragraph_id"],
                "text": text,
                "letter": match.group(1) if match else None,
                "style_name": para.get("style_name"),
            }
        )
    return items


def check_app01(rule: dict, context: CheckContext) -> Result:
    headings = _appendix_headings(context.paragraphs)
    if not headings:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            "当前文档未检测到附录标题，不适用。",
            "无。",
            coverage="partial",
        )

    letters = [item["letter"] for item in headings if item["letter"]]
    if not letters:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "检测到附录标题，但未能识别附录字母编号。",
            "附录应写作“附录 A/B/C…”。",
            coverage="partial",
            locations=[f"DOCX 段落 {headings[0]['paragraph_id']}"],
        )

    expected = [chr(ord("A") + idx) for idx in range(len(letters))]
    if letters != expected:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"附录编号顺序异常：{letters}。",
            "将附录标题统一编号为 A/B/C… 并按顺序排列。",
            coverage="partial",
            locations=[f"DOCX 段落 {headings[0]['paragraph_id']}"],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"识别到 {len(headings)} 个附录标题，编号顺序为 {', '.join(letters)}。",
        "无。",
        coverage="partial",
        locations=[f"DOCX 段落 {headings[0]['paragraph_id']}"],
    )


def check_app02(rule: dict, context: CheckContext) -> Result:
    headings = _appendix_headings(context.paragraphs)
    if not headings:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            "当前文档未检测到附录，不适用。",
            "无。",
            coverage="partial",
        )

    appendix_start_idx = min(
        idx for idx, para in enumerate(context.paragraphs)
        if (para.get("text") or "").strip().startswith("附录")
    )
    appendix_paragraphs = context.paragraphs[appendix_start_idx:]
    bad_captions = []
    for para in appendix_paragraphs:
        text = (para.get("text") or "").strip()
        if re.match(r"^图\s*[A-Z]\.\d+", text) or re.match(r"^表\s*[A-Z]\.\d+", text) or re.match(r"^\([A-Z]-\d+\)$", text):
            continue
        if re.match(r"^(图|表)\s*\d+\.\d+", text) or re.match(r"^\(\d+-\d+\)$", text):
            bad_captions.append((para["paragraph_id"], text[:60]))

    if bad_captions:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"附录中检测到未带字母前缀的编号样式：{bad_captions[0][1]}。",
            "附录中的图、表、式编号应独立并带附录字母前缀。",
            coverage="partial",
            locations=[f"DOCX 段落 {bad_captions[0][0]}"],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        "附录中的编号样式未检测到明显的正文编号混用。",
        "无。",
        coverage="partial",
        locations=[f"DOCX 段落 {headings[0]['paragraph_id']}"],
    )


def check_g03(rule: dict, context: CheckContext) -> Result:
    body_paragraphs = get_body_paragraphs(context.paragraphs)
    suspicious = []
    for para in body_paragraphs:
        text = para.get("text") or ""
        hits = [ch for ch in text if ch in TRADITIONAL_HINTS]
        if hits:
            suspicious.append((para["paragraph_id"], "".join(sorted(set(hits)))[:20], text[:60]))
    if suspicious:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "warning",
            "medium",
            rule["evidence_types"],
            f"疑似繁简混用或传统字形样本 {len(suspicious)} 处。",
            "逐处人工复核这些字符是否为规范简体字或特定专名保留写法。",
            coverage="partial",
            locations=[f"DOCX 段落 {suspicious[0][0]}：{suspicious[0][2]}"],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        "未检测到明显的繁简混用或异常字符样本。",
        "无。",
        coverage="partial",
    )


RULE_CHECKERS = {
    "LIST-02": check_list02,
    "AUTH-01": check_auth01,
    "ABS-05": check_abs05,
    "LOT-01": check_lot01,
    "ACK-01": check_ack01,
    "DEC-01": check_dec01,
    "CV-01": check_cv01,
    "APP-01": check_app01,
    "APP-02": check_app02,
    "G-03": check_g03,
}
