from __future__ import annotations

import re

from guide_checker.core.models import CheckContext, Result
from guide_checker.core.utils import approx
from .common import (
    extract_chapter_headings,
    find_exact_index,
    find_paragraph_by_id,
    find_first_pdf_page_with_title,
    format_paragraph_location,
    get_reference_span,
    locate_text_page_no,
)


LIST_TITLE = "学位论文指导小组、公开评阅人和答辩委员会名单"
LIST_SUBTITLES = ["指导小组名单", "公开评阅人名单", "答辩委员会名单"]
TABLE_CAPTION_RE = re.compile(r"^表\s*\d+\.\d+\s+")


def _paragraph_location(context: CheckContext, paragraph_id: int, *, extra: str | None = None) -> str:
    return format_paragraph_location(
        context.paragraphs,
        context.pdf_pages,
        paragraph_id,
        extra=extra,
    )


def _paragraphs_for_table(context: CheckContext, table_index: int) -> list[dict]:
    return [para for para in context.paragraphs if para.get("table_index") == table_index]


def _table_page_no(context: CheckContext, table: dict) -> int | None:
    paragraph_ids = table.get("paragraph_ids") or []
    if not paragraph_ids:
        return None

    candidates = sorted(
        [para for para in _paragraphs_for_table(context, table["table_index"]) if (para.get("text") or "").strip()],
        key=lambda item: len(item.get("text") or ""),
        reverse=True,
    )
    page_votes = []
    for para in candidates:
        page_no = locate_text_page_no(context.pdf_pages, para.get("text", ""))
        if page_no is not None:
            page_votes.append(page_no)
    if page_votes:
        return max(set(page_votes), key=page_votes.count)

    first_para_id = min(paragraph_ids)
    for para_id in range(first_para_id - 1, max(first_para_id - 6, 0), -1):
        para = find_paragraph_by_id(context.paragraphs, para_id)
        if para is None:
            continue
        text = (para.get("text") or "").strip()
        if not TABLE_CAPTION_RE.match(text):
            continue
        page_no = locate_text_page_no(context.pdf_pages, text)
        if page_no is not None:
            return page_no
    return None


def _body_data_tables(context: CheckContext) -> list[dict]:
    headings = extract_chapter_headings(context.paragraphs)
    body_start_para_id = headings[0]["paragraph_id"] if headings else 1
    ref_start, _ = get_reference_span(context.paragraphs)
    ref_start_para_id = context.paragraphs[ref_start]["paragraph_id"] if ref_start is not None else 10**9

    tables = []
    for table in context.tables:
        paragraph_ids = table.get("paragraph_ids") or []
        if not paragraph_ids:
            continue
        if max(paragraph_ids) < body_start_para_id or min(paragraph_ids) >= ref_start_para_id:
            continue
        if table.get("contains_omml"):
            continue
        if table.get("row_count", 0) < 2 and table.get("cell_count", 0) < 4:
            continue

        paragraphs = [
            para for para in _paragraphs_for_table(context, table["table_index"])
            if (para.get("text") or "").strip()
        ]
        if len(paragraphs) < 2:
            continue
        if all(
            re.fullmatch(r"\(\d+-\d+\)", (para.get("text") or "").strip())
            or not (para.get("text") or "").strip()
            for para in paragraphs
        ):
            continue
        tables.append(table)
    return tables


def check_list01(rule: dict, context: CheckContext) -> Result:
    title_idx = find_exact_index(context.paragraphs, LIST_TITLE)
    auth_idx = find_exact_index(context.paragraphs, "关于学位论文使用授权的说明")
    if title_idx is None or auth_idx is None or auth_idx <= title_idx:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "warning",
            "medium",
            rule["evidence_types"],
            "未能稳定界定名单页范围，当前未执行完整格式检查。",
            "检查名单页标题与授权说明标题的定位结果。",
            coverage="partial",
        )

    title_para = context.paragraphs[title_idx]
    list_page_no = find_first_pdf_page_with_title(context.pdf_pages, LIST_TITLE, allow_anywhere=True)
    title_problems = []
    title_fmt = title_para.get("para_fmt") or {}
    title_run = title_para.get("run_info") or {}
    if title_fmt.get("alignment") != "center":
        title_problems.append("主标题未居中")
    if not approx(title_run.get("size_pt"), 16.0, 0.6):
        title_problems.append(f"主标题字号={title_run.get('size_pt')}")
    if "黑体" not in ((title_run.get("font_eastAsia") or "") + (title_run.get("font_ascii") or "")):
        title_problems.append("主标题未识别到黑体")

    subtitle_problems = []
    for subtitle in LIST_SUBTITLES:
        subtitle_idx = find_exact_index(context.paragraphs, subtitle)
        if subtitle_idx is None or not (title_idx < subtitle_idx < auth_idx):
            subtitle_problems.append(f"缺少子标题“{subtitle}”")
            continue
        para = context.paragraphs[subtitle_idx]
        fmt = para.get("para_fmt") or {}
        run = para.get("run_info") or {}
        if fmt.get("alignment") != "center" or not approx(run.get("size_pt"), 14.0, 0.6):
            subtitle_problems.append(f"{subtitle} 样式异常")

    list_tables = []
    for table in context.tables:
        paragraph_ids = table.get("paragraph_ids") or []
        if not paragraph_ids:
            continue
        if title_para["paragraph_id"] < min(paragraph_ids) < context.paragraphs[auth_idx]["paragraph_id"]:
            list_tables.append(table)

    if len(list_tables) < 3:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"名单页范围内仅识别到 {len(list_tables)} 个表格对象，少于预期的 3 个分栏表。",
            "检查名单页是否仍使用无框线表格承载“指导小组/公开评阅人/答辩委员会”三部分内容。",
            coverage="partial",
            locations=[_paragraph_location(context, title_para["paragraph_id"], extra="名单页主标题")],
        )

    border_failures = [table for table in list_tables if table.get("has_visible_border")]
    content_failures = []
    for table in list_tables:
        for para in _paragraphs_for_table(context, table["table_index"]):
            text = (para.get("text") or "").strip()
            if not text:
                continue
            fmt = para.get("para_fmt") or {}
            run = para.get("run_info") or {}
            if fmt.get("alignment") != "center" or not approx(run.get("size_pt"), 10.5, 0.6):
                content_failures.append((table["table_index"], para["paragraph_id"], text[:20]))
                break

    problems = []
    if title_problems:
        problems.append("主标题样式异常：" + "；".join(title_problems[:3]))
    if subtitle_problems:
        problems.append("子标题异常：" + "；".join(subtitle_problems[:3]))
    if border_failures:
        problems.append("名单表检测到可见边框：" + "、".join(f"表{table['table_index']}" for table in border_failures[:3]))
    if content_failures:
        problems.append("表内文字样式异常：" + "、".join(f"表{item[0]}" for item in content_failures[:3]))

    if problems:
        locations = [_paragraph_location(context, title_para["paragraph_id"], extra="名单页主标题")]
        if border_failures and border_failures[0].get("paragraph_ids"):
            locations.append(
                format_paragraph_location(
                    context.paragraphs,
                    context.pdf_pages,
                    border_failures[0]["paragraph_ids"][0],
                    page_no=list_page_no,
                    extra=f"名单表 {border_failures[0]['table_index']}",
                )
            )
        if content_failures:
            locations.append(
                format_paragraph_location(
                    context.paragraphs,
                    context.pdf_pages,
                    content_failures[0][1],
                    page_no=list_page_no,
                    extra=f"名单表 {content_failures[0][0]}",
                )
            )
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "；".join(problems),
            "将名单页统一为无框线表格，并按模板修正主标题、子标题及表内文字样式。",
            coverage="partial",
            locations=list(dict.fromkeys(locations)),
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"名单页识别到 {len(list_tables)} 个无框线表格对象，主标题、子标题及表内文字样式均符合当前自动检查口径。",
        "无。",
        coverage="partial",
        locations=[_paragraph_location(context, title_para["paragraph_id"], extra="名单页主标题")],
    )


def check_foot01(rule: dict, context: CheckContext) -> Result:
    footnotes = context.footnotes
    ref_count = footnotes.get("reference_count", 0)
    entry_count = footnotes.get("footnote_count", 0)
    references = footnotes.get("references", [])
    settings = footnotes.get("settings", {})

    if ref_count == 0 and entry_count == 0:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            "正文未检测到脚注引用，也未检测到实际脚注正文；当前论文不涉及脚注排版要求。",
            "无。",
            coverage="partial",
        )

    problems = []
    if ref_count != entry_count:
        problems.append(f"脚注引用 {ref_count} 处，但脚注正文仅 {entry_count} 条")

    non_superscript = [item for item in references if not item.get("is_superscript")]
    if non_superscript:
        problems.append(f"{len(non_superscript)} 处脚注引用未识别为上标样式")

    num_restart = settings.get("num_restart")
    if num_restart not in {None, "eachPage"}:
        problems.append(f"脚注编号重启方式={num_restart}")

    if problems:
        locations = [
            _paragraph_location(context, item["paragraph_id"], extra=f"脚注引用 id={item['footnote_id']}")
            for item in (non_superscript[:3] or references[:3])
        ]
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            "；".join(problems),
            "检查脚注引用与脚注正文是否一一对应，并将脚注编号方式设为按页重新编号。",
            coverage="partial",
            locations=list(dict.fromkeys(locations)),
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"共识别 {ref_count} 处脚注引用和 {entry_count} 条脚注正文；当前未发现引用缺失，上标样式正常。",
        "如论文后续新增脚注，仍建议结合 PDF 页脚位置做一次人工复核。",
        coverage="partial",
    )


def check_foot02(rule: dict, context: CheckContext) -> Result:
    entries = context.footnotes.get("entries", [])
    if not entries:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "pass",
            "low",
            rule["evidence_types"],
            "未检测到实际脚注正文，当前论文不涉及脚注正文样式检查。",
            "无。",
            coverage="partial",
        )

    failures = []
    for entry in entries:
        for para in entry.get("paragraphs", []):
            text = (para.get("text") or "").strip()
            if not text:
                continue
            fmt = para.get("para_fmt") or {}
            run = para.get("run_info") or {}
            problems = []
            if not approx(run.get("size_pt"), 9.0, 0.6):
                problems.append(f"字号={run.get('size_pt')}")
            if fmt.get("line_rule") != "auto" or not approx(fmt.get("line_multiple"), 1.0, 0.05):
                problems.append(f"行距={fmt.get('line_rule')}/{fmt.get('line_multiple')}")
            if not approx(fmt.get("space_before_pt"), 0.0, 0.5) or not approx(fmt.get("space_after_pt"), 0.0, 0.5):
                problems.append(f"段前后={fmt.get('space_before_pt')}/{fmt.get('space_after_pt')}")
            if not approx(fmt.get("hanging_pt"), 18.0, 2.0):
                problems.append(f"悬挂缩进={fmt.get('hanging_pt')}")
            if problems:
                failures.append((entry["footnote_id"], para["footnote_paragraph_index"], text[:30], problems))
                break

    if failures:
        failure = failures[0]
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"脚注 {failure[0]} 的正文样式异常：" + "；".join(failure[3]),
            "将脚注正文统一调整为小五、单倍行距、段前段后 0、悬挂 1.5 字符。",
            coverage="partial",
            locations=[f"脚注 {failure[0]} / 段 {failure[1]} / “{failure[2]}”"],
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"共检查 {len(entries)} 条脚注正文，未发现明显的字号、行距或悬挂缩进异常。",
        "无。",
        coverage="partial",
    )


def check_tab02(rule: dict, context: CheckContext) -> Result:
    candidate_tables = _body_data_tables(context)
    if not candidate_tables:
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "warning",
            "medium",
            rule["evidence_types"],
            "未稳定识别到可判定的正文数据表，当前未执行表内文字样式检查。",
            "后续可继续增强“数据表/公式表/前置名单表”的自动区分逻辑。",
            coverage="partial",
        )

    checked_paragraphs = 0
    failures = []
    for table in candidate_tables:
        for para in _paragraphs_for_table(context, table["table_index"]):
            text = (para.get("text") or "").strip()
            if not text:
                continue
            checked_paragraphs += 1
            fmt = para.get("para_fmt") or {}
            run = para.get("run_info") or {}
            problems = []
            if not approx(run.get("size_pt"), 11.0, 0.6):
                problems.append(f"字号={run.get('size_pt')}")
            if fmt.get("line_rule") != "auto" or not approx(fmt.get("line_multiple"), 1.0, 0.05):
                problems.append(f"行距={fmt.get('line_rule')}/{fmt.get('line_multiple')}")
            if not approx(fmt.get("space_before_pt"), 3.0, 0.8) or not approx(fmt.get("space_after_pt"), 3.0, 0.8):
                problems.append(f"段前后={fmt.get('space_before_pt')}/{fmt.get('space_after_pt')}")
            if fmt.get("alignment") not in {None, "left", "center", "both"}:
                problems.append(f"对齐={fmt.get('alignment')}")
            if problems:
                failures.append((table["table_index"], para["paragraph_id"], text[:30], problems))
                if len(failures) >= 8:
                    break
        if len(failures) >= 8:
            break

    if failures:
        table_page_cache = {
            table["table_index"]: _table_page_no(context, table)
            for table in candidate_tables
        }
        locations = [
            format_paragraph_location(
                context.paragraphs,
                context.pdf_pages,
                paragraph_id,
                page_no=table_page_cache.get(table_index),
                extra=f"表格 {table_index}",
            )
            for table_index, paragraph_id, _, _ in failures[:5]
        ]
        examples = "；".join(
            f"表{table_index} 段落 {paragraph_id}：" + "、".join(problems[:3])
            for table_index, paragraph_id, _, problems in failures[:3]
        )
        return Result(
            rule["rule_id"],
            rule["title"],
            rule["priority"],
            "fail",
            "medium",
            rule["evidence_types"],
            f"共检查 {len(candidate_tables)} 个正文数据表、{checked_paragraphs} 个表内段落；发现样式不一致。{examples}",
            "将表内文字统一调整为 11pt、单倍行距、段前段后 3 磅，并检查局部手工改字造成的样式漂移。",
            coverage="partial",
            locations=list(dict.fromkeys(locations)),
        )

    return Result(
        rule["rule_id"],
        rule["title"],
        rule["priority"],
        "pass",
        "low",
        rule["evidence_types"],
        f"共检查 {len(candidate_tables)} 个正文数据表、{checked_paragraphs} 个表内段落，未发现明显的字号、行距或段前段后异常。",
        "无。",
        coverage="partial",
    )


RULE_CHECKERS = {
    "LIST-01": check_list01,
    "FOOT-01": check_foot01,
    "FOOT-02": check_foot02,
    "TAB-02": check_tab02,
}
