from __future__ import annotations

from collections import defaultdict

from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import norm
from .common import (
    extract_body_acronyms,
    extract_display_equations,
    find_abbr_section,
    format_paragraph_location,
    scan_unit_pair_mixes,
)


def _format_acronym_examples(items: list[dict], limit: int = 5) -> str:
    if not items:
        return "无高频缩略语样本"
    return "，".join(f"{item['token']}×{item['count']}" for item in items[:limit])


def _format_unit_examples(examples: list[dict], limit: int = 2) -> str:
    if not examples:
        return ""
    return "；".join(example["match"] for example in examples[:limit])


def _build_equation_artifact(equations: list[dict], page_hits: dict[str, list[int]] | None = None) -> dict:
    chapter_map: dict[int, list[int]] = defaultdict(list)
    for equation in equations:
        chapter_map[equation["chapter_no"]].append(equation["seq_no"])
    chapter_summary = {
        str(chapter_no): {
            "count": len(seqs),
            "min_seq": min(seqs),
            "max_seq": max(seqs),
            "sequences": sorted(seqs),
        }
        for chapter_no, seqs in sorted(chapter_map.items())
    }
    artifact = {
        "equation_count": len(equations),
        "chapter_summary": chapter_summary,
        "equations": equations,
    }
    if page_hits is not None:
        artifact["pdf_page_hits"] = page_hits
    return artifact


def check_abbr01(rule: dict, context: CheckContext) -> Result:
    abbr_section = find_abbr_section(context.paragraphs)
    acronym_items = extract_body_acronyms(context.paragraphs, min_count=2, top_n=20)
    frequent_items = [item for item in acronym_items if item["count"] >= 3]
    artifacts = {
        "abbreviation_index": {
            "section": abbr_section,
            "top_acronyms": acronym_items,
        }
    }

    if abbr_section is not None:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            (
                f"已识别到“符号和缩略语说明”节，节内共 {abbr_section['item_count']} 条说明项；"
                f"正文高频缩略语抽样为 {_format_acronym_examples(frequent_items or acronym_items)}。"
            ),
            "无。",
            coverage="partial",
            artifacts=artifacts,
        )

    if len(frequent_items) >= 6:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            (
                f"正文识别到 {len(frequent_items)} 个高频缩略语，但未找到专门说明节；"
                f"抽样包括 {_format_acronym_examples(frequent_items)}。"
            ),
            "补充“符号和缩略语说明”节，或至少在首次出现处对高频缩略语逐一解释。",
            coverage="partial",
            artifacts=artifacts,
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "warning",
        "medium",
        rule["evidence_types"],
        (
            "未找到“符号和缩略语说明”节；"
            f"当前仅识别到少量重复缩略语样本：{_format_acronym_examples(acronym_items)}。"
        ),
        "若后续缩略语继续增多，建议补充专门说明节；否则需逐一检查首次出现处是否已随文解释。",
        coverage="partial",
        artifacts=artifacts,
    )


def check_unit01(rule: dict, context: CheckContext) -> Result:
    unit_scan = scan_unit_pair_mixes(context.paragraphs)
    artifacts = {"unit_scan": unit_scan}

    if unit_scan["symbol_total"] > 0 and unit_scan["chinese_total"] > 0:
        mixed_pair = unit_scan["mixed_pairs"][0] if unit_scan["mixed_pairs"] else None
        fail_locations = []
        if mixed_pair is not None:
            detail = (
                f"{mixed_pair['symbol']}/{mixed_pair['cn']} 同时出现，"
                f"符号示例：{_format_unit_examples(mixed_pair['symbol_examples'])}，"
                f"中文示例：{_format_unit_examples(mixed_pair['cn_examples'])}。"
            )
            for sample in mixed_pair["symbol_examples"][:2] + mixed_pair["cn_examples"][:2]:
                para_id = sample.get("paragraph_id")
                if para_id is not None:
                    fail_locations.append(
                        format_paragraph_location(context.paragraphs, context.pdf_pages, para_id)
                    )
            fail_locations = list(dict.fromkeys(fail_locations))
        else:
            detail = (
                f"国际符号共 {unit_scan['symbol_total']} 处，中文单位名称共 {unit_scan['chinese_total']} 处。"
            )
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            f"检测到数值单位混用国际符号与中文名称：{detail}",
            "同一篇论文中单位表达应统一为一种书写体系，建议统一改为国际符号或统一改为中文名称。",
            coverage="partial",
            locations=fail_locations,
            artifacts=artifacts,
        )

    if unit_scan["symbol_total"] > 0:
        active_pairs = [item["symbol"] for item in unit_scan["pairs"] if item["symbol_count"] > 0]
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            f"正文数值单位当前统一采用国际符号，共识别 {unit_scan['symbol_total']} 处；涉及 {', '.join(active_pairs[:6])} 等单位，未发现中文单位名称混用。",
            "无。",
            coverage="partial",
            artifacts=artifacts,
        )

    if unit_scan["chinese_total"] > 0:
        active_pairs = [item["cn"] for item in unit_scan["pairs"] if item["cn_count"] > 0]
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            f"正文数值单位当前统一采用中文名称，共识别 {unit_scan['chinese_total']} 处；涉及 {', '.join(active_pairs[:6])} 等单位，未发现国际符号混用。",
            "无。",
            coverage="partial",
            artifacts=artifacts,
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "warning",
        "medium",
        rule["evidence_types"],
        "未稳定识别到“数值 + 单位”样本，当前规则未能给出一致性结论。",
        "后续可继续扩充单位词典，或结合 PDF 可视化对参数表、实验配置表进行人工复核。",
        coverage="partial",
        artifacts=artifacts,
    )


def check_eq01(rule: dict, context: CheckContext) -> Result:
    equations = extract_display_equations(context.paragraphs)
    artifacts = {"display_equation_index": _build_equation_artifact(equations)}
    if not equations:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            "未从 DOCX 结构中提取到显示公式对象。",
            "检查公式是否仍采用 Word 公式对象，或补充新的显示公式抽取逻辑。",
            coverage="partial",
            artifacts=artifacts,
        )

    missing_formula = [item["number_text"] for item in equations if item["formula_para_id"] is None]
    explicit_alignments = sorted({item["formula_alignment"] for item in equations if item["formula_alignment"] is not None})
    unsupported_alignments = [
        item["number_text"]
        for item in equations
        if item["formula_alignment"] not in (None, "center", "left", "both")
    ]

    if missing_formula:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            f"以下公式编号未成功绑定到对应公式主体：{', '.join(missing_formula[:8])}。",
            "检查这些公式是否仍采用统一的表格型显示公式结构。",
            coverage="partial",
            artifacts=artifacts,
        )

    if unsupported_alignments:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            f"检测到非预期公式对齐模式，涉及 {', '.join(unsupported_alignments[:8])}。",
            "显示公式建议统一为居中或统一缩进；若采用特殊段落样式，需同步增强抽取规则。",
            coverage="partial",
            artifacts=artifacts,
        )

    if len(explicit_alignments) > 1:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            f"显示公式显式对齐模式存在混用：{', '.join(explicit_alignments)}。",
            "全文显示公式建议统一采用一种排版模式，避免部分居中、部分缩进并存。",
            coverage="partial",
            artifacts=artifacts,
        )

    explicit_count = sum(1 for item in equations if item["formula_alignment"] is not None)
    if explicit_alignments:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            (
                f"共提取 {len(equations)} 个显示公式对象，其中 {explicit_count} 个显式记录为 {explicit_alignments[0]} 对齐；"
                "未发现显式排版模式混用。"
            ),
            "无。",
            coverage="partial",
            artifacts=artifacts,
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "warning",
        "medium",
        rule["evidence_types"],
        f"共提取 {len(equations)} 个显示公式对象，但段落级对齐值均未显式记录，当前只能确认其显示公式结构稳定存在。",
        "建议结合 PDF 可视化快速复核公式主体是否统一居中或统一缩进。",
        coverage="partial",
        artifacts=artifacts,
    )


def check_eq02(rule: dict, context: CheckContext) -> Result:
    equations = extract_display_equations(context.paragraphs)
    page_hits: dict[str, list[int]] = {}
    for equation in equations:
        target = norm(equation["number_text"])
        hits = [
            page["page_no"]
            for page in context.pdf_pages
            if target and target in norm(page.get("text", ""))
        ]
        page_hits[equation["number_text"]] = hits

    artifacts = {"display_equation_index": _build_equation_artifact(equations, page_hits=page_hits)}
    if not equations:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            "未提取到可检查的显示公式编号。",
            "检查 DOCX 中公式编号是否仍保留为独立段落，或补充新的编号抽取逻辑。",
            coverage="partial",
            artifacts=artifacts,
        )

    invalid_format = [item["number_text"] for item in equations if not item["number_text"].startswith("(") or not item["number_text"].endswith(")")]
    wrong_alignment = [item["number_text"] for item in equations if item["number_alignment"] != "right"]
    pdf_missing = [number_text for number_text, hits in page_hits.items() if not hits]

    seq_failures = []
    chapter_map: dict[int, list[int]] = defaultdict(list)
    for equation in equations:
        chapter_map[equation["chapter_no"]].append(equation["seq_no"])
    for chapter_no, seqs in sorted(chapter_map.items()):
        ordered = sorted(seqs)
        expected = list(range(1, len(ordered) + 1))
        if ordered != expected:
            seq_failures.append(f"第{chapter_no}章编号序列={ordered}")

    problems = []
    if invalid_format:
        problems.append(f"括号编号格式异常：{', '.join(invalid_format[:8])}")
    if wrong_alignment:
        problems.append(f"编号未右对齐：{', '.join(wrong_alignment[:8])}")
    if seq_failures:
        problems.extend(seq_failures[:4])
    if pdf_missing:
        problems.append(f"PDF 文本未命中：{', '.join(pdf_missing[:8])}")

    if problems:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "high",
            rule["evidence_types"],
            "；".join(problems),
            "统一调整公式编号格式为“(章序号-公式序号)”并右对齐，同时复核 PDF 渲染结果。",
            coverage="partial",
            artifacts=artifacts,
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"共检查 {len(equations)} 个显示公式编号，章内序号连续，编号段落均为右对齐，且 PDF 文本均可定位到对应公式号。",
        "无。",
        coverage="partial",
        artifacts=artifacts,
    )


RULE_CHECKERS = {
    "ABBR-01": check_abbr01,
    "UNIT-01": check_unit01,
    "EQ-01": check_eq01,
    "EQ-02": check_eq02,
}
