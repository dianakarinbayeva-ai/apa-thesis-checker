from __future__ import annotations

import re

from guide_checker.core.constants import STYLE_EXPECTATIONS, TRIGGER_WORDS, VALID_TYPE_CODES
from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import compare_style
from .common import extract_body_citation_numbers, find_exact_index, format_paragraph_location, get_reference_entries, get_reference_span


def check_refsec01(rule: dict, context: CheckContext) -> Result:
    ref_start, _ = get_reference_span(context.paragraphs)
    if ref_start is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未找到参考文献标题。", "确认文档包含“参考文献”章节。")

    entries = get_reference_entries(context.paragraphs)
    if not entries:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "找到参考文献标题，但未提取到文献条目。", "检查参考文献段落样式或标题位置。")

    title_style_name = (context.paragraphs[ref_start].get("style_name") or "").lower()
    title_style = context.styles.get(title_style_name) if title_style_name else None
    ref_style = context.styles.get("参考文献".lower())

    failures = []
    if title_style is None:
        failures.append("未找到参考文献标题样式定义")
    else:
        title_problems = compare_style(title_style, STYLE_EXPECTATIONS["heading 1"])
        if title_problems:
            failures.append("参考文献标题样式异常：" + "；".join(title_problems[:4]))

    if ref_style is None:
        failures.append("未找到“参考文献”段落样式定义")
    else:
        ref_checks = {
            "font_ascii": "Times New Roman",
            "size_pt": 10.5,
            "line_rule": "exact",
            "line_pt": 16.0,
            "space_before_pt": 3.0,
            "left_indent_pt": 28.35,
            "hanging_pt": 28.35,
        }
        ref_problems = compare_style(ref_style, ref_checks)
        if ref_problems:
            failures.append("参考文献条目样式异常：" + "；".join(ref_problems[:6]))

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], " | ".join(failures), "统一修正参考文献标题样式与“参考文献”段落样式。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"参考文献节定位正常，文献条目共 {len(entries)} 条，标题样式和条目样式符合当前检查范围。", "无。")


def check_bib03(rule: dict, context: CheckContext) -> Result:
    entries = get_reference_entries(context.paragraphs)
    if not entries:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未提取到参考文献条目，无法检查著录结构。", "检查参考文献节定位。")

    no_seq = []
    no_type = []
    no_year = []
    no_split = []
    fail_para_ids: list[int] = []
    for para in entries:
        text = (para.get("text") or "").strip()
        if not re.match(r"^\[(\d+)\]", text):
            no_seq.append(text[:80])
            fail_para_ids.append(para["paragraph_id"])
        if not VALID_TYPE_CODES.search(text):
            no_type.append(text[:80])
            fail_para_ids.append(para["paragraph_id"])
        if not re.search(r"(?<!\d)(19|20)\d{2}(?!\d)", text):
            no_year.append(text[:80])
            fail_para_ids.append(para["paragraph_id"])
        text_wo_seq = re.sub(r"^\[(\d+)\]", "", text).strip()
        if ". " not in text_wo_seq:
            no_split.append(text[:80])
            fail_para_ids.append(para["paragraph_id"])

    problems = []
    if no_seq:
        problems.append(f"{len(no_seq)} 条缺少 [序号]")
    if no_type:
        problems.append(f"{len(no_type)} 条缺少文献类型标识")
    if no_year:
        problems.append(f"{len(no_year)} 条缺少四位年份")
    if no_split:
        problems.append(f"{len(no_split)} 条未识别到作者/题名基本分隔")

    if problems:
        examples = []
        for label, items in (("缺年份", no_year), ("缺类型", no_type), ("缺序号", no_seq), ("缺分隔", no_split)):
            if items:
                examples.append(f"{label}示例：{items[0]}")
        fail_locations = [
            format_paragraph_location(context.paragraphs, context.pdf_pages, para_id)
            for para_id in sorted(set(fail_para_ids))[:4]
        ]
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            "；".join(problems + examples[:2]),
            "逐条补齐最小著录结构：序号、类型标识、年份，以及作者/题名基本分隔。",
            locations=fail_locations,
        )

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"参考文献共 {len(entries)} 条，全部满足当前自动检查的最小著录结构。", "无。")


def check_bib04(rule: dict, context: CheckContext) -> Result:
    ref_start, _ = get_reference_span(context.paragraphs)
    body_paragraphs = context.paragraphs[:ref_start] if ref_start is not None else context.paragraphs
    body_text = "\n".join(para.get("text", "") for para in body_paragraphs if para.get("text", "").strip())

    square_count = len(re.findall(r"\[(\d+(?:\s*[-,，]\s*\d+)*)\]", body_text))
    author_year_count = len(re.findall(r"[（(][^()\n]{0,24}(19|20)\d{2}[a-z]?[)）]", body_text))

    if square_count > 0 and author_year_count > 0:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], f"正文同时检测到顺序编码制引用 {square_count} 处和著者-出版年式样 {author_year_count} 处。", "正文引用只能选择一种制式，并全文统一。")
    if square_count > 0:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"正文检测到顺序编码制引用 {square_count} 处，未发现著者-出版年制混用。", "无。")
    if author_year_count > 0:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"正文检测到著者-出版年制样式 {author_year_count} 处，未发现顺序编码制混用。", "无。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "warning", "medium", rule["evidence_types"], "未在正文中稳定识别到引用标注，当前规则未能给出制式判断。", "增强正文引用模式识别，或人工复核正文标注方式。", coverage="partial")


def check_bib08(rule: dict, context: CheckContext) -> Result:
    entries = get_reference_entries(context.paragraphs)
    ref_numbers = []
    duplicate_numbers = []
    seen = set()
    for para in entries:
        match = re.match(r"^\[(\d+)\]", (para.get("text") or "").strip())
        if not match:
            continue
        number = int(match.group(1))
        ref_numbers.append(number)
        if number in seen:
            duplicate_numbers.append(number)
        seen.add(number)

    ref_number_set = set(ref_numbers)
    max_ref_num = max(ref_number_set) if ref_number_set else None
    cited_numbers = extract_body_citation_numbers(context.paragraphs, max_ref_num=max_ref_num)

    missing_in_refs = sorted(cited_numbers - ref_number_set)
    uncited_refs = sorted(ref_number_set - cited_numbers)
    artifacts = {
        "reference_index": {
            "reference_count": len(entries),
            "reference_numbers": ref_numbers,
            "cited_numbers": sorted(cited_numbers),
            "missing_in_refs": missing_in_refs,
            "uncited_refs": uncited_refs,
            "duplicate_reference_numbers": sorted(set(duplicate_numbers)),
        }
    }

    problems = []
    if duplicate_numbers:
        problems.append(f"重复编号 {sorted(set(duplicate_numbers))[:5]}")
    if missing_in_refs:
        problems.append(f"正文引用但文献表缺失 {missing_in_refs[:8]}")
    if uncited_refs:
        problems.append(f"文献表存在但正文未引用 {uncited_refs[:8]}")

    if problems:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(problems), "使正文引用与参考文献表严格一一对应，并检查文献编号连续性。", artifacts=artifacts)

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"正文引用编号与参考文献表一一对应，文献表共 {len(entries)} 条，正文命中 {len(cited_numbers)} 个编号。", "无。", artifacts=artifacts)


def check_wr08(rule: dict, context: CheckContext) -> Result:
    ref_idx = find_exact_index(context.paragraphs, "参考文献")
    chapter_candidates = [
        idx for idx, para in enumerate(context.paragraphs)
        if (para.get("style_name") or "").lower() == "heading 1" and ("总结" in para.get("text", "") or "结论" in para.get("text", "") or "展望" in para.get("text", ""))
    ]
    if not chapter_candidates or ref_idx is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "warning", "medium", rule["evidence_types"], "未能稳定定位结论/总结部分，未执行夸大词扫描。", "后续可增强结论节定位逻辑。", coverage="partial")

    start_idx = chapter_candidates[-1]
    end_idx = ref_idx if ref_idx > start_idx else len(context.paragraphs)
    text = "\n".join((para.get("text") or "").strip() for para in context.paragraphs[start_idx:end_idx] if (para.get("text") or "").strip())
    hits = [word for word in TRIGGER_WORDS if word in text]
    if hits:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "warning", "medium", rule["evidence_types"], f"结论部分命中高风险词：{', '.join(hits)}。", "人工核对这些表述是否有充分证据支撑。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "结论部分未命中“首次/领先/填补空白”等高风险词。", "无。")


RULE_CHECKERS = {
    "REFSEC-01": check_refsec01,
    "BIB-03": check_bib03,
    "BIB-04": check_bib04,
    "BIB-08": check_bib08,
    "WR-08": check_wr08,
}
