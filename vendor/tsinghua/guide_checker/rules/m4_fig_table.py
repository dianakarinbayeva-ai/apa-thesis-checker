from __future__ import annotations

from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import get_page_lines, norm
from .common import extract_body_figure_titles, extract_list_entries, find_pdf_page_by_label


def _check_seq(items: list[dict]) -> list[str]:
    failures = []
    chapter_map: dict[int, list[int]] = {}
    for item in items:
        chapter_map.setdefault(item["chapter_no"], []).append(item["seq_no"])
    for chapter_no, seqs in sorted(chapter_map.items()):
        ordered = sorted(seqs)
        expected = list(range(1, len(ordered) + 1))
        if ordered != expected:
            failures.append(f"第 {chapter_no} 章编号序列={ordered}")
    return failures


def check_fig01(rule: dict, context: CheckContext) -> Result:
    body_figures = extract_body_figure_titles(context.paragraphs)
    list_figures = extract_list_entries(context.paragraphs, "图")
    if not body_figures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未从正文中提取到图题。", "检查图题文本与样式。")

    failures = []
    failures.extend(_check_seq(body_figures))
    no_drawing = [item for item in body_figures if not item["preceded_by_drawing"]]
    if no_drawing:
        failures.append("以下图题前未检测到插图段落：" + "、".join(item["number_text"] for item in no_drawing[:6]))
    if list_figures and len(list_figures) != len(body_figures):
        failures.append(f"插图清单 {len(list_figures)} 条，正文图题 {len(body_figures)} 条")

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "；".join(failures[:6]), "统一修正图题编号连续性，并保持图题紧跟在对应图片下方。")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"正文共提取 {len(body_figures)} 条图题，章内编号连续，且图题均位于对应插图之后。", "无。")


def check_tab03(rule: dict, context: CheckContext) -> Result:
    table_entries = extract_list_entries(context.paragraphs, "表")
    if not table_entries:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "high", rule["evidence_types"], "未从附表清单中提取到表题。", "检查附表清单和 PDF 文本提取结果。", coverage="partial")

    failures = []
    failures.extend(_check_seq(table_entries))

    for item in table_entries:
        page = find_pdf_page_by_label(context.pdf_pages, item["page_label"] or "")
        if page is None:
            failures.append(f"{item['number_text']} 未映射到 PDF 页码 {item['page_label']}")
            continue
        lines = get_page_lines(page)
        target_norm = norm(item["number_text"])
        title_norm = norm(item["title"])
        title_idx = None
        title_window = ""
        for idx, line in enumerate(lines):
            line_norm = norm(line)
            if target_norm == line_norm:
                title_idx = idx
                title_window = "".join(lines[idx + 1: idx + 4])
                break
        if title_idx is None:
            failures.append(f"{item['number_text']} 未在 PDF p{page['page_no']} 中命中")
            continue
        if title_norm and title_norm not in norm(title_window):
            failures.append(f"{item['number_text']} 的表题文本未在 PDF p{page['page_no']} 中紧邻编号出现")

    if failures:
        return Result(rule["rule_id"], rule["title"], rule["priority"], "fail", "medium", rule["evidence_types"], "；".join(failures[:8]), "保持表题章内连续编号，并确保表题位于表格上方且与附表清单一致。", coverage="partial")

    return Result(rule["rule_id"], rule["title"], rule["priority"], "pass", "low", rule["evidence_types"], f"附表清单共提取 {len(table_entries)} 条表题，章内编号连续，且 PDF 中均能定位到“编号在上、表格内容在下”的结构。", "无。", coverage="partial")


RULE_CHECKERS = {
    "FIG-01": check_fig01,
    "TAB-03": check_tab03,
}
