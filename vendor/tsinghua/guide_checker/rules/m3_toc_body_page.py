from __future__ import annotations

from guide_checker.core.constants import STYLE_EXPECTATIONS
from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import compare_style
from .common import extract_chapter_headings, get_toc_entries, parse_toc_entries


def check_toc01(rule: dict, context: CheckContext) -> Result:
    entries = parse_toc_entries(context.paragraphs)
    if not entries:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未找到目录条目。", "确认目录部分存在。")

    max_groups = 0
    offending = []
    for entry in entries:
        text = entry["title_part"]
        match = __import__("re").match(r"^(\d+(?:\.\d+)+)", text)
        if not match:
            continue
        groups = match.group(1).count(".") + 1
        max_groups = max(max_groups, groups)
        if groups > 3:
            offending.append(match.group(1))

    if offending:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], f"目录中检测到超出二级节范围的条目：{', '.join(offending[:5])}。", "目录最多列至二级节标题，例如 2.3.5。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"目录编号最大深度为 {max_groups} 组数字，未超过二级节范围。", "无。")


def check_toc02(rule: dict, context: CheckContext) -> Result:
    entries = parse_toc_entries(context.paragraphs)
    if not entries:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未解析到目录条目。", "检查目录是否存在且可读取。")

    titles_norm = {entry["title_part"].replace(" ", "") for entry in entries}
    required_titles = [
        "摘要",
        "Abstract",
        "插图清单",
        "附表清单",
        "符号和缩略语说明",
        "参考文献",
        "致谢",
        "声明",
        "个人简历、在学期间完成的相关学术成果",
        "指导教师评语",
        "答辩委员会决议书",
    ]
    missing = [title for title in required_titles if title.replace(" ", "") not in titles_norm]

    chapter_missing = []
    for chapter in extract_chapter_headings(context.paragraphs):
        if chapter["text"].replace(" ", "") not in titles_norm:
            chapter_missing.append(chapter["text"])

    if missing or chapter_missing:
        problems = []
        if missing:
            problems.append("缺少固定部分：" + "、".join(missing[:8]))
        if chapter_missing:
            problems.append("缺少章标题：" + "、".join(chapter_missing[:5]))
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], " | ".join(problems), "补齐目录覆盖范围，使前置部分、各章与末尾材料均进入目录。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"目录已覆盖固定前置部分、{len(extract_chapter_headings(context.paragraphs))} 个章标题及末尾材料。", "无。")


def check_toc03(rule: dict, context: CheckContext) -> Result:
    styles = context.styles
    toc1 = styles.get("toc 1")
    toc2 = styles.get("toc 2")
    toc3 = styles.get("toc 3")
    if toc1 is None or toc2 is None or toc3 is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "缺少 toc 1/toc 2/toc 3 样式定义。", "检查目录样式是否存在。", coverage="partial")

    failures = []
    if toc1.get("first_line_indent_pt") not in (None, 0.0):
        failures.append(f"toc 1 首行缩进={toc1.get('first_line_indent_pt')}")
    if toc2.get("first_line_indent_pt") not in (None, 0.0):
        failures.append(f"toc 2 首行缩进={toc2.get('first_line_indent_pt')}")
    if toc3.get("first_line_indent_pt") not in (None, 0.0):
        failures.append(f"toc 3 首行缩进={toc3.get('first_line_indent_pt')}")

    toc1_left = toc1.get("left_indent_pt") or 0.0
    toc2_left = toc2.get("left_indent_pt") or 0.0
    toc3_left = toc3.get("left_indent_pt") or 0.0
    if not (toc1_left < toc2_left < toc3_left):
        failures.append(f"目录层级缩进异常：toc1={toc1_left}, toc2={toc2_left}, toc3={toc3_left}")

    toc_entries = get_toc_entries(context.paragraphs)
    if toc_entries and not all(entry.get("in_sdt") for entry in toc_entries[: min(10, len(toc_entries))]):
        failures.append("部分目录条目不在自动目录结构内")

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "medium", rule["evidence_types"], "；".join(failures[:6]), "修正目录样式层级与悬挂缩进，并优先使用自动目录。", coverage="partial")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "toc 1/toc 2/toc 3 样式层级关系正常，目录条目位于自动目录结构中。", "导点和视觉细节仍建议结合 PDF 快速复核。", coverage="partial")


def check_toc04(rule: dict, context: CheckContext) -> Result:
    entries = get_toc_entries(context.paragraphs)
    if not entries:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未识别到目录条目。", "检查目录是否生成。")
    auto_hits = [entry for entry in entries if (entry.get("style_name") or "").lower().startswith("toc ") and entry.get("in_sdt")]
    if not auto_hits:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "目录条目存在，但未识别到自动目录结构特征。", "建议重新插入 Word 自动目录。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"共识别 {len(auto_hits)} 条自动目录项，目录为自动生成结构。", "无。")


def check_body03(rule: dict, context: CheckContext) -> Result:
    mismatches = []
    for style_name in ("heading 1", "heading 2", "heading 3", "heading 4"):
        actual = context.styles.get(style_name)
        if actual is None:
            mismatches.append(f"缺少样式 {style_name}")
            continue
        problems = compare_style(actual, STYLE_EXPECTATIONS[style_name])
        if problems:
            mismatches.append(f"{style_name}: " + "；".join(problems[:4]))
    if mismatches:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], " | ".join(mismatches[:4]), "统一修正 heading 1-4 的样式定义与局部覆盖。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "heading 1-4 样式定义均符合指南要求。", "无。")


def check_body04(rule: dict, context: CheckContext) -> Result:
    actual = context.styles.get("normal")
    if actual is None:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未找到 Normal 样式。", "检查 styles.xml。")
    problems = compare_style(actual, STYLE_EXPECTATIONS["normal"])
    if problems:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(problems[:6]), "统一修正 Normal 样式定义。")
    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], "Normal 样式定义符合指南要求。", "无。")


RULE_CHECKERS = {
    "TOC-01": check_toc01,
    "TOC-02": check_toc02,
    "TOC-03": check_toc03,
    "TOC-04": check_toc04,
    "BODY-03": check_body03,
    "BODY-04": check_body04,
}
