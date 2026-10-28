from __future__ import annotations

import re

from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import approx
from .common import (
    extract_keyword_items,
    find_contains_index,
    find_exact_index,
    find_first_pdf_page_with_any_title,
    find_first_pdf_page_with_title,
    format_paragraph_range_location,
    get_abstract_indices,
    get_cover_titles,
)


def _match_body_para(para: dict) -> list[str]:
    fmt = para.get("para_fmt", {})
    problems = []
    if fmt.get("alignment") != "both":
        problems.append(f"alignment={fmt.get('alignment')}")
    if fmt.get("line_rule") != "exact" or not approx(fmt.get("line_pt"), 20.0, 0.8):
        problems.append(f"line={fmt.get('line_rule')}/{fmt.get('line_pt')}")
    if not approx(fmt.get("first_line_indent_pt"), 24.0, 1.2):
        problems.append(f"indent={fmt.get('first_line_indent_pt')}")
    return problems


def check_cover01(rule: dict, context: CheckContext) -> Result:
    chinese_title, _ = get_cover_titles(context.paragraphs)
    front = context.paragraphs[:40]
    required_labels = ["培养单位", "专业领域", "申请人", "指导教师"]
    missing = [label for label in required_labels if not any(label in para.get("text", "") for para in front)]
    has_date = any(re.search(r"(二○|二〇|\d{4}).{0,4}年.{0,2}月", para.get("text", "")) for para in context.paragraphs[:60])

    problems = []
    if not chinese_title:
        problems.append("未识别到中文封面题名")
    if missing:
        problems.append("缺少字段：" + "、".join(missing))
    if not has_date:
        problems.append("未识别到封面日期")

    if problems:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(problems), "补齐中文封面的题名、培养单位、专业领域、申请人、指导教师和日期信息。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "中文封面已识别到题名、培养单位、专业领域、申请人、指导教师和日期等关键信息。", "无。")


def check_cover02(rule: dict, context: CheckContext) -> Result:
    chinese_title, _ = get_cover_titles(context.paragraphs)
    if not chinese_title:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能识别中文题名。", "检查中文封面题名位置。")
    char_count = len(re.findall(r"[\u4e00-\u9fff]", chinese_title))
    if char_count > 25:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], f"中文题名约 {char_count} 个汉字，超过 25 字。", "压缩中文题名长度。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"中文题名约 {char_count} 个汉字，满足不超过 25 字的当前检查口径。", "无。")


def check_cover04(rule: dict, context: CheckContext) -> Result:
    if len(context.sections) < 3:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "section 数量不足，无法稳定识别中英文封面页边距。", "检查 section 提取逻辑。")

    cn_cover = context.sections[0]
    en_cover = context.sections[2]
    failures = []
    cn_expected = {"margin_top_cm": 6.0, "margin_bottom_cm": 6.0, "margin_left_cm": 4.0, "margin_right_cm": 4.0}
    en_expected = {"margin_top_cm": 5.5, "margin_bottom_cm": 5.0, "margin_left_cm": 3.6, "margin_right_cm": 3.6}

    for key, target in cn_expected.items():
        if not approx(cn_cover.get(key), target, 0.15):
            failures.append(f"中文封面 {key}={cn_cover.get(key)}")
    for key, target in en_expected.items():
        if not approx(en_cover.get(key), target, 0.2):
            failures.append(f"英文封面 {key}={en_cover.get(key)}")

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures[:8]), "按模板修正中英文封面 section 的页边距参数。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "按当前 section 抽取结果，中英文封面页边距与模板参数一致。", "无。")


def check_abs01(rule: dict, context: CheckContext) -> Result:
    cn_idx, en_idx = get_abstract_indices(context.paragraphs)
    if cn_idx is None or en_idx is None or en_idx <= cn_idx:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能稳定定位中文摘要与英文摘要。", "检查“摘要”和“Abstract”标题。")

    failures = []
    if context.paragraphs[cn_idx].get("style_name", "").lower() != "heading 1":
        failures.append("中文摘要标题未使用 heading 1")
    if context.paragraphs[en_idx].get("style_name", "").lower() != "heading 1":
        failures.append("Abstract 标题未使用 heading 1")

    cn_body = []
    for para in context.paragraphs[cn_idx + 1:en_idx]:
        text = (para.get("text") or "").strip()
        if not text or text.startswith("关键词"):
            continue
        cn_body.append(para)
    en_body = []
    for para in context.paragraphs[en_idx + 1:]:
        text = (para.get("text") or "").strip()
        if not text:
            continue
        if text.startswith("Keywords"):
            break
        if find_exact_index(context.paragraphs, "目录") is not None and para["paragraph_id"] >= context.paragraphs[find_exact_index(context.paragraphs, "目录")]["paragraph_id"]:
            break
        en_body.append(para)

    for label, body in (("中文摘要正文", cn_body[:4]), ("英文摘要正文", en_body[:4])):
        for para in body:
            problems = _match_body_para(para)
            if problems:
                failures.append(f"{label}段落 {para['paragraph_id']} 异常：" + "；".join(problems))
                break

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], " | ".join(failures[:6]), "统一修正中英文摘要标题和正文段落格式。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "中英文摘要标题和正文段落样式符合当前自动检查范围。", "无。")


def check_abs02(rule: dict, context: CheckContext) -> Result:
    cn_idx, en_idx = get_abstract_indices(context.paragraphs)
    if cn_idx is None or en_idx is None or en_idx <= cn_idx:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能正确定位中文摘要与 Abstract 边界。", "检查摘要与 Abstract 标题是否存在且顺序正确。")

    body = []
    for para in context.paragraphs[cn_idx + 1:en_idx]:
        text = (para.get("text") or "").strip()
        if not text or text.startswith("关键词"):
            continue
        body.append(text)
    char_count = len(re.findall(r"[\u4e00-\u9fff]", "".join(body)))

    cn_page = find_first_pdf_page_with_any_title(context.pdf_pages, ["摘要", "摘  要"])
    en_page = find_first_pdf_page_with_title(context.pdf_pages, "Abstract")
    page_span = (en_page - cn_page) if cn_page and en_page else None

    problems = []
    if not (800 <= char_count <= 1000):
        problems.append(f"中文摘要约 {char_count} 个汉字，不在 800-1000 范围内")
    if page_span is not None and page_span != 1:
        problems.append(f"PDF 中中文摘要跨越 {page_span} 页")

    if problems:
        body_paragraphs = [
            para
            for para in context.paragraphs[cn_idx + 1:en_idx]
            if (para.get("text") or "").strip() and not (para.get("text") or "").strip().startswith("关键词")
        ]
        content_para_ids = [para["paragraph_id"] for para in body_paragraphs]
        start_para_id = content_para_ids[0] if content_para_ids else context.paragraphs[cn_idx]["paragraph_id"]
        end_para_id = content_para_ids[-1] if content_para_ids else context.paragraphs[cn_idx]["paragraph_id"]
        locations = [
            format_paragraph_range_location(
                context.paragraphs,
                context.pdf_pages,
                start_para_id,
                end_para_id,
                page_no=cn_page,
                extra="中文摘要范围",
            )
        ]
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            "；".join(problems),
            "压缩或补足摘要内容，并确认中文摘要只占 1 页。",
            locations=locations,
        )

    page_note = "PDF 中中文摘要占 1 页" if page_span == 1 else "未能从 PDF 稳定判断摘要页数"
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"中文摘要约 {char_count} 个汉字；{page_note}。", "无。")


def check_abs03(rule: dict, context: CheckContext) -> Result:
    cn_idx, en_idx = get_abstract_indices(context.paragraphs)
    if cn_idx is None or en_idx is None or en_idx <= cn_idx:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能正确定位中文摘要范围。", "检查摘要与 Abstract 标题。")

    drawing_hits = []
    table_hits = []
    for para in context.paragraphs[cn_idx + 1:en_idx]:
        if para.get("has_drawing"):
            drawing_hits.append(para["paragraph_id"])
        if para.get("has_table"):
            table_hits.append(para["paragraph_id"])

    if drawing_hits or table_hits:
        parts = []
        if drawing_hits:
            parts.append(f"drawing 段落 {drawing_hits[:5]}")
        if table_hits:
            parts.append(f"table 段落 {table_hits[:5]}")
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "摘要范围内检测到 " + "；".join(parts) + "。", "删除摘要中的图、表或其他插图材料。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "摘要范围内未检测到 drawing 或 table。", "无。")


def check_abs04(rule: dict, context: CheckContext) -> Result:
    cn_idx, en_idx = get_abstract_indices(context.paragraphs)
    if cn_idx is None or en_idx is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能定位摘要区域。", "检查摘要标题。")

    keyword_line = next((para.get("text", "").strip() for para in context.paragraphs[cn_idx:en_idx] if para.get("text_norm", "").startswith("关键词")), "")
    if not keyword_line:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未找到中文关键词行。", "补充“关键词：”行。")

    delimiter_ok = "；" in keyword_line or ";" in keyword_line
    items = extract_keyword_items(keyword_line, "cn")
    if len(items) > 5 or not delimiter_ok:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], f"中文关键词共 {len(items)} 个，分隔符状态={delimiter_ok}。", "将中文关键词控制在 5 个以内，并使用分号分隔。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"中文关键词共 {len(items)} 个，分号分隔正常。", "无。")


def check_abs06(rule: dict, context: CheckContext) -> Result:
    cn_idx, en_idx = get_abstract_indices(context.paragraphs)
    toc_idx = find_exact_index(context.paragraphs, "目录")
    if cn_idx is None or en_idx is None or toc_idx is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未能稳定定位摘要、Abstract 或目录边界。", "检查摘要相关标题。")

    cn_line = next((para.get("text", "").strip() for para in context.paragraphs[cn_idx:en_idx] if para.get("text_norm", "").startswith("关键词")), "")
    en_line = next((para.get("text", "").strip() for para in context.paragraphs[en_idx:toc_idx] if para.get("text", "").strip().startswith("Keywords")), "")
    if not cn_line or not en_line:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未同时识别到中英文关键词行。", "补齐中文“关键词：”和英文“Keywords:”行。")

    cn_items = extract_keyword_items(cn_line, "cn")
    en_items = extract_keyword_items(en_line, "en")
    delimiter_ok = ";" in en_line
    if len(en_items) > 5 or not delimiter_ok or len(cn_items) != len(en_items):
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], f"中文关键词 {len(cn_items)} 个，英文关键词 {len(en_items)} 个，英文分号分隔={delimiter_ok}。", "保证英文关键词不超过 5 个、使用分号分隔，并与中文关键词数量对应。", coverage="partial")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"中英文关键词数量一致，均为 {len(en_items)} 个，英文关键词分号分隔正常。", "语义对应关系仍建议人工快速复核。", coverage="partial")


RULE_CHECKERS = {
    "COVER-01": check_cover01,
    "COVER-02": check_cover02,
    "COVER-04": check_cover04,
    "ABS-01": check_abs01,
    "ABS-02": check_abs02,
    "ABS-03": check_abs03,
    "ABS-04": check_abs04,
    "ABS-06": check_abs06,
}
