from __future__ import annotations

from guide_checker.core.constants import STYLE_EXPECTATIONS
from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import approx, compare_style, extract_formal_page_label, get_page_lines
from .common import (
    extract_chapter_headings,
    extract_chapter_toc_entries,
    find_contains_index,
    find_first_pdf_page_with_any_title,
    find_first_pdf_page_with_title,
    find_pdf_page_by_label,
    format_paragraph_location,
    get_cover_titles,
    parse_toc_entries,
    page_contains_chapter_header,
    page_contains_title_near_top,
)


def _structure_components(context: CheckContext) -> list[dict]:
    cn_title, en_title = get_cover_titles(context.paragraphs)
    toc_lookup = {}
    for entry in parse_toc_entries(context.paragraphs):
        page = find_pdf_page_by_label(context.pdf_pages, entry["page_label"] or "")
        if page is not None:
            toc_lookup[entry["title_part"].replace(" ", "")] = page["page_no"]
    items = []

    def push(name: str, page_no: int | None, title: str | None) -> None:
        items.append({"name": name, "page_no": page_no, "title": title or ""})

    push("中文封面", find_first_pdf_page_with_title(context.pdf_pages, cn_title or "", allow_anywhere=True), cn_title)
    push("英文封面", find_first_pdf_page_with_title(context.pdf_pages, en_title or "", allow_anywhere=True), en_title)
    push(
        "名单页",
        find_first_pdf_page_with_title(context.pdf_pages, "学位论文指导小组、公开评阅人和答辩委员会名单"),
        "学位论文指导小组、公开评阅人和答辩委员会名单",
    )
    push("授权说明", find_first_pdf_page_with_title(context.pdf_pages, "关于学位论文使用授权的说明"), "关于学位论文使用授权的说明")
    push("中文摘要", toc_lookup.get("摘要") or find_first_pdf_page_with_any_title(context.pdf_pages, ["摘要", "摘  要"]), "摘要")
    push("英文摘要", toc_lookup.get("Abstract") or find_first_pdf_page_with_title(context.pdf_pages, "Abstract"), "Abstract")
    push("目录", find_first_pdf_page_with_title(context.pdf_pages, "目录"), "目录")
    push("插图清单", toc_lookup.get("插图清单") or find_first_pdf_page_with_title(context.pdf_pages, "插图清单"), "插图清单")
    push("附表清单", toc_lookup.get("附表清单") or find_first_pdf_page_with_title(context.pdf_pages, "附表清单"), "附表清单")
    push("符号和缩略语说明", toc_lookup.get("符号和缩略语说明") or find_first_pdf_page_with_title(context.pdf_pages, "符号和缩略语说明"), "符号和缩略语说明")
    for chapter in extract_chapter_headings(context.paragraphs):
        push(chapter["text"], toc_lookup.get(chapter["text"].replace(" ", "")) or find_first_pdf_page_with_title(context.pdf_pages, chapter["text"]), chapter["text"])
    push("参考文献", toc_lookup.get("参考文献") or find_first_pdf_page_with_title(context.pdf_pages, "参考文献"), "参考文献")
    push("致谢", toc_lookup.get("致谢") or find_first_pdf_page_with_any_title(context.pdf_pages, ["致谢", "致  谢"]), "致谢")
    push("声明", toc_lookup.get("声明") or find_first_pdf_page_with_any_title(context.pdf_pages, ["声明", "声  明"]), "声明")
    push(
        "个人简历、在学期间完成的相关学术成果",
        toc_lookup.get("个人简历、在学期间完成的相关学术成果") or find_first_pdf_page_with_title(context.pdf_pages, "个人简历、在学期间完成的相关学术成果"),
        "个人简历、在学期间完成的相关学术成果",
    )
    push("指导教师评语", toc_lookup.get("指导教师评语") or find_first_pdf_page_with_title(context.pdf_pages, "指导教师评语"), "指导教师评语")
    push("答辩委员会决议书", toc_lookup.get("答辩委员会决议书") or find_first_pdf_page_with_title(context.pdf_pages, "答辩委员会决议书"), "答辩委员会决议书")
    return items


def _first_body_chapter_title(context: CheckContext) -> str | None:
    chapters = extract_chapter_headings(context.paragraphs)
    return chapters[0]["text"] if chapters else None


def _first_body_pdf_page_no(context: CheckContext) -> int | None:
    chapter_entries = extract_chapter_toc_entries(context.paragraphs)
    if not chapter_entries or chapter_entries[0]["page_num"] is None:
        return None
    page = find_pdf_page_by_label(context.pdf_pages, chapter_entries[0]["page_num"])
    return page["page_no"] if page is not None else None


def check_str01(rule: dict, context: CheckContext) -> Result:
    components = _structure_components(context)
    missing = [item["name"] for item in components if item["page_no"] is None]
    if missing:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], f"以下组成部分未在 PDF 中稳定定位：{', '.join(missing[:8])}。", "检查这些部分的标题文字、分页和 PDF 导出结果。")

    ordered_pages = [item["page_no"] for item in components]
    if ordered_pages != sorted(ordered_pages):
        disorder = [f"{item['name']}@p{item['page_no']}" for item in components]
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "组成部分页序未保持严格递增：" + " -> ".join(disorder[:12]), "按指南顺序重排前置部分、正文和末尾材料。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"共定位 {len(components)} 个组成部分，PDF 起始页顺序与指南要求一致。", "无。")


def check_str02(rule: dict, context: CheckContext) -> Result:
    components = _structure_components(context)
    missing = [item["name"] for item in components if item["page_no"] is None]
    if missing:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], f"存在未能定位起始页的组成部分：{', '.join(missing[:8])}。", "先保证各组成部分标题可稳定识别。")

    duplicates = []
    seen_pages = {}
    for item in components:
        page_no = item["page_no"]
        if page_no in seen_pages:
            duplicates.append(f"p{page_no}: {seen_pages[page_no]} / {item['name']}")
        else:
            seen_pages[page_no] = item["name"]

    top_failures = []
    for item in components:
        page = context.pdf_pages[item["page_no"] - 1]
        if item["title"] and not page_contains_title_near_top(page, item["title"], top_n=14):
            top_failures.append(f"{item['name']}@p{item['page_no']}")

    if duplicates or top_failures:
        parts = []
        if duplicates:
            parts.append("起始页重复：" + "；".join(duplicates[:6]))
        if top_failures:
            parts.append("未在页首区域命中标题：" + "；".join(top_failures[:6]))
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], " | ".join(parts), "确保每个组成部分独立起页，且标题出现在对应页的页首区域。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "所有已定位组成部分均占用独立起始页，且标题出现在对应页首区域。", "无。")


def check_str03(rule: dict, context: CheckContext) -> Result:
    failures = []
    for sec in context.sections:
        if sec["page_width_twips"] not in range(11890, 11920) or sec["page_height_twips"] not in range(16820, 16850):
            failures.append(f"section {sec['section_id']} 尺寸不是 A4")
    for page in context.pdf_pages:
        if not approx(page["width_pt"], 595.276, 1.5) or not approx(page["height_pt"], 841.89, 1.5):
            failures.append(f"PDF 第 {page['page_no']} 页尺寸不是 A4")
            break
    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures[:6]), "检查 section 页面设置与 PDF 输出尺寸。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"DOCX 共 {len(context.sections)} 个 section，PDF 共 {len(context.pdf_pages)} 页，页面尺寸均为 A4。", "无。")


def check_str04(rule: dict, context: CheckContext) -> Result:
    abstract_page = find_first_pdf_page_with_any_title(context.pdf_pages, ["摘要", "摘  要"])
    if abstract_page is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能稳定定位中文摘要首页。", "检查摘要标题与 PDF 提取结果。")

    failures = []
    for page in context.pdf_pages[: abstract_page - 1]:
        if extract_formal_page_label(page):
            failures.append(f"p{page['page_no']} 检测到页码 {extract_formal_page_label(page)}")
        if page_contains_chapter_header(page):
            failures.append(f"p{page['page_no']} 检测到篇眉样式文本")

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures[:6]), "中文摘要之前的前四部分不应进入正式篇眉页码体系。", coverage="partial")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"中文摘要前共检查 {abstract_page - 1} 页，未检测到正式页码或正文篇眉。", "单双面留白仍建议人工翻页确认。", coverage="partial")


def check_str05(rule: dict, context: CheckContext) -> Result:
    abstract_page = find_first_pdf_page_with_any_title(context.pdf_pages, ["摘要", "摘  要"])
    body_page = _first_body_pdf_page_no(context)
    if abstract_page is None or body_page is None or body_page <= abstract_page:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能稳定定位中文摘要首页或正文首页。", "检查摘要、第1章标题和 PDF 页首文本。")

    abstract_label = extract_formal_page_label(context.pdf_pages[abstract_page - 1])
    body_label = extract_formal_page_label(context.pdf_pages[body_page - 1])
    failures = []
    if abstract_label != "I":
        failures.append(f"中文摘要首页页码={abstract_label}")
    if body_label != "1":
        failures.append(f"正文首页页码={body_label}")

    for page in context.pdf_pages[abstract_page - 1: body_page - 1]:
        label = extract_formal_page_label(page)
        if not label or not label.isalpha():
            failures.append(f"p{page['page_no']} 未检测到大写罗马页码")
            break

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures[:6]), "中文摘要开始应进入正式双面编排和页眉页码体系，前置部分使用大写罗马页码，正文从 1 开始。", coverage="partial")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"中文摘要首页页码为 {abstract_label}，正文首页页码为 {body_label}，前置正式部分页码切换正常。", "双面起印方向仍建议结合 PDF 可视化复核。", coverage="partial")


def check_body01(rule: dict, context: CheckContext) -> Result:
    chapter_entries = extract_chapter_toc_entries(context.paragraphs)
    if not chapter_entries:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未从目录中提取到章标题起始页。", "检查目录是否完整且可解析。")

    even_starts = [item for item in chapter_entries if item["page_num"] is not None and item["page_num"] % 2 == 0]
    if even_starts:
        chapter_heading_map = {item["chapter_no"]: item for item in extract_chapter_headings(context.paragraphs)}
        detail = "；".join(f"{item['title_part']} 从 {item['page_num']} 起" for item in even_starts[:6])
        locations = []
        for item in even_starts[:6]:
            page = find_pdf_page_by_label(context.pdf_pages, item["page_num"])
            paragraph_id = item["paragraph_id"]
            extra = f"目录页码 {item['page_num']}"
            chapter_heading = chapter_heading_map.get(item["chapter_no"])
            if chapter_heading is not None:
                paragraph_id = chapter_heading["paragraph_id"]
            locations.append(
                format_paragraph_location(
                    context.paragraphs,
                    context.pdf_pages,
                    paragraph_id,
                    page_no=page["page_no"] if page is not None else None,
                    extra=extra,
                )
            )
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            f"检测到偶数页起章：{detail}。",
            "按指南要求将每章调整为右页起章。",
            locations=locations,
        )

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"目录共识别 {len(chapter_entries)} 个章首页，起始页码均为奇数。", "无。")


def _find_content_start_section(sections: list[dict]) -> int | None:
    for sec in sections:
        if sec["page_number_format"] == "upperRoman" and sec["page_number_start"] == 1:
            return sec["section_id"]
    return None


def check_page01(rule: dict, context: CheckContext) -> Result:
    start_section = _find_content_start_section(context.sections)
    if start_section is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未找到前置部分以大写罗马页码起始的 section，无法界定中文摘要开始位置。", "检查 section 页码设置。")

    failures = []
    for sec in context.sections:
        if sec["section_id"] < start_section:
            continue
        checks = {
            "margin_top_cm": 3.0,
            "margin_bottom_cm": 3.0,
            "margin_left_cm": 3.0,
            "margin_right_cm": 3.0,
            "header_distance_cm": 2.2,
            "footer_distance_cm": 2.2,
        }
        for key, target in checks.items():
            if not approx(sec.get(key), target, 0.08):
                failures.append(f"section {sec['section_id']} 的 {key}={sec.get(key)}")
                if len(failures) >= 6:
                    break
        if len(failures) >= 6:
            break

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures), "将中文摘要开始后的 section 统一设置为四边 3.0 cm、页眉页脚 2.2 cm。")
    count = len([sec for sec in context.sections if sec["section_id"] >= start_section])
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"从 section {start_section} 起共检查 {count} 个正式 section，页面参数均符合要求。", "无。")


def check_page02(rule: dict, context: CheckContext) -> Result:
    abstract_page = find_first_pdf_page_with_any_title(context.pdf_pages, ["摘要", "摘  要"])
    body_page = _first_body_pdf_page_no(context)
    ref_page = find_first_pdf_page_with_title(context.pdf_pages, "参考文献")
    if abstract_page is None or body_page is None or ref_page is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能稳定定位摘要、正文或参考文献页。", "检查 PDF 页首文本提取结果。")

    failures = []
    for page in context.pdf_pages[: abstract_page - 1]:
        if extract_formal_page_label(page):
            failures.append(f"p{page['page_no']} 前置部分出现正式页码")
            break

    for page in context.pdf_pages[abstract_page - 1:]:
        if not extract_formal_page_label(page):
            failures.append(f"p{page['page_no']} 未检测到正式页码")
            break

    body_header_missing = []
    for page in context.pdf_pages[body_page - 1: ref_page - 1]:
        if not page_contains_chapter_header(page):
            body_header_missing.append(page["page_no"])
            if len(body_header_missing) >= 5:
                break
    if body_header_missing:
        failures.append("正文页缺少章篇眉：" + ",".join(f"p{page_no}" for page_no in body_header_missing))

    start_checks = [
        ("摘要", abstract_page),
        ("Abstract", find_first_pdf_page_with_title(context.pdf_pages, "Abstract")),
        ("目录", find_first_pdf_page_with_title(context.pdf_pages, "目录")),
        ("插图清单", find_first_pdf_page_with_title(context.pdf_pages, "插图清单")),
        ("附表清单", find_first_pdf_page_with_title(context.pdf_pages, "附表清单")),
        ("符号和缩略语说明", find_first_pdf_page_with_title(context.pdf_pages, "符号和缩略语说明")),
        ("参考文献", ref_page),
    ]
    for title, page_no in start_checks:
        if page_no is None:
            failures.append(f"{title} 起始页未定位")
            continue
        page = context.pdf_pages[page_no - 1]
        if not page_contains_title_near_top(page, title, top_n=12):
            failures.append(f"{title}@p{page_no} 页首未命中标题")

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures[:8]), "修正页眉内容与显示范围，保证前置封面不显示正式页眉页码，摘要之后进入正式体系。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "前置封面页未进入正式篇眉页码体系；摘要至末页均检测到正式页码，正文页章篇眉显示范围正常。", "无。")


def check_page03(rule: dict, context: CheckContext) -> Result:
    content_start = _find_content_start_section(context.sections)
    if content_start is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未找到前置部分的 upperRoman 起始 section。", "检查摘要起始页码设置。")

    later_sections = [sec for sec in context.sections if sec["section_id"] >= content_start]
    body_start = None
    for sec in later_sections:
        if sec["page_number_format"] == "decimal" and sec["page_number_start"] == 1:
            body_start = sec["section_id"]
            break
    if body_start is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未找到正文从阿拉伯数字 1 开始的 section。", "将正文起始 section 设为 decimal 且 start=1。")

    failures = []
    for sec in later_sections:
        if sec["section_id"] < body_start and sec["page_number_format"] != "upperRoman":
            failures.append(f"section {sec['section_id']} 前置部分页码格式={sec['page_number_format']}")
        if sec["section_id"] >= body_start and sec["page_number_format"] != "decimal":
            failures.append(f"section {sec['section_id']} 正文页码格式={sec['page_number_format']}")

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures[:6]), "摘要至符号说明使用 upperRoman，正文起使用 decimal 并从 1 开始。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"前置部分从 section {content_start} 开始使用 upperRoman，正文从 section {body_start} 开始使用 decimal 且 start=1。", "无。")


RULE_CHECKERS = {
    "STR-01": check_str01,
    "STR-02": check_str02,
    "STR-03": check_str03,
    "STR-04": check_str04,
    "STR-05": check_str05,
    "BODY-01": check_body01,
    "PAGE-01": check_page01,
    "PAGE-02": check_page02,
    "PAGE-03": check_page03,
}
