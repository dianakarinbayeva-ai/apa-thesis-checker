from __future__ import annotations

from collections import Counter
from datetime import datetime
import re
from typing import Any

from guide_checker.core.constants import IMPLEMENTED_RULE_IDS
from guide_checker.core.models import CheckContext, Result
from guide_checker.rules.common import (
    extract_body_acronyms,
    extract_body_figure_titles,
    extract_chapter_headings,
    extract_chapter_toc_entries,
    extract_keyword_items,
    find_abbr_section,
    find_exact_index,
    find_first_pdf_page_with_any_title,
    find_first_pdf_page_with_title,
    find_pdf_page_by_label,
    format_paragraph_location,
    format_paragraph_range_location,
    get_abstract_indices,
    get_body_paragraphs,
    get_reference_entries,
    get_reference_span,
    locate_text_page_no,
)


REVIEW_MODE_SCRIPT_SOP = "script_plus_sop"
REVIEW_MODE_PURE_SOP = "pure_sop"
REVIEW_MODE_LABELS = {
    REVIEW_MODE_SCRIPT_SOP: "脚本+SOP",
    REVIEW_MODE_PURE_SOP: "纯SOP",
}

MANUAL_RULE_POLICIES = {
    "ABS-07": {
        "review_mode": REVIEW_MODE_PURE_SOP,
        "classification_reason": "中英文摘要是否语义对应，最终仍需人工逐项比对对象、方法、结果与结论。",
        "sop_steps": [
            "对照中文摘要与英文摘要，逐项核对研究对象、核心方法、实验结果和结论是否一一对应。",
            "检查英文摘要是否存在明显漏译、增译、错译，尤其关注数值、数据集名称和方法名称。",
            "结合中英文关键词，确认两者主题一致；若不一致，在结果文件中记录缺漏点和对应段落。",
        ],
    },
    "REFSEC-02": {
        "review_mode": REVIEW_MODE_SCRIPT_SOP,
        "classification_reason": "可先用脚本筛出长条目和页码不稳的参考文献，再人工翻 PDF 判断是否跨页。",
        "sop_steps": [
            "优先检查脚本标出的长条目和页码不稳条目，打开对应 PDF 页面查看条目是否断到下一页。",
            "若单条参考文献跨页，记录其参考文献编号和跨页起止页，并判断是否需要通过压缩段落或微调分页处理。",
            "仅在跨页明显影响阅读时记为 fail；若仅个别长条目轻微跨页，可记为 warning 并备注。",
        ],
    },
    "FIG-03": {
        "review_mode": REVIEW_MODE_SCRIPT_SOP,
        "classification_reason": "脚本可以筛出首次引用、图题和页码的相对位置，但是否“紧跟引用”仍需结合 PDF 人工判断。",
        "sop_steps": [
            "按脚本给出的候选图编号，先看正文首次引用段，再看图题所在页，核对图是否紧跟首次引用。",
            "若图与首次引用相隔超过 1 页，或明显提前/滞后，记录图号和对应页码。",
            "若图很大必须跨页或旋转排版，结合版面可读性判断是否接受，并在结果中说明。",
        ],
    },
    "TAB-01": {
        "review_mode": REVIEW_MODE_SCRIPT_SOP,
        "classification_reason": "脚本可以先提取表格边框和基本位置，人工再判断是否满足三线表和自明性要求。",
        "sop_steps": [
            "优先检查脚本标出的可见边框较多的表格，确认是否为三线表，或是否属于必要的复杂表格例外。",
            "检查表头是否自明，量纲和单位是否标注完整；若仅靠正文才能理解，则记为问题。",
            "对复杂表格可记录为 warning，并说明属于版式复杂但可接受，还是需要进一步简化。",
        ],
    },
    "G-06": {
        "review_mode": REVIEW_MODE_SCRIPT_SOP,
        "classification_reason": "脚本可筛出高频缩写和首次出现位置，人工再判断首次出现处是否已解释清楚。",
        "sop_steps": [
            "按脚本列出的高频缩写，逐项检查首次出现段落是否给出中文全称、英文全称或必要解释。",
            "若缩写在“符号和缩略语说明”中出现，但正文首次出现处完全无引导，可记为 warning；若两处都无解释，则记为 fail。",
            "对领域内公认通用缩写，可在结果中注明“可接受”并保留 pass。",
        ],
    },
    "WR-04": {
        "review_mode": REVIEW_MODE_SCRIPT_SOP,
        "classification_reason": "脚本可以先筛出摘要中的章节提纲式表述，最终是否构成问题需人工通读判断。",
        "sop_steps": [
            "先看脚本命中的摘要段落，判断是否出现“第1章……第2章……”或类似章节提纲式写法。",
            "若只是正常的研究步骤描述而非按章罗列，可保留 pass；若明确按章概述全文结构，应记为 fail。",
            "若表述介于两者之间，可记为 warning，并建议改写成研究目标、方法和结论导向的摘要表述。",
        ],
    },
    "WR-05": {
        "review_mode": REVIEW_MODE_SCRIPT_SOP,
        "classification_reason": "脚本可先给出引言要素命中情况，是否真正覆盖‘问题、背景、综述、方法、结构’仍需人工判断。",
        "sop_steps": [
            "先看脚本给出的引言段范围和要素命中概览，再通读引言，确认是否覆盖问题提出、背景意义、文献综述、研究方法和结构安排。",
            "若只是出现关键词但没有形成完整论述，不应直接判为通过，应在结果中说明缺失的是“无”还是“弱”。",
            "对结构安排如已融入章节结尾或段尾说明，可接受，但需在结果中注明所在段落。",
        ],
    },
    "WR-07": {
        "review_mode": REVIEW_MODE_SCRIPT_SOP,
        "classification_reason": "脚本可先筛出结论部分的贡献、局限和展望锚点，最终覆盖度需人工确认。",
        "sop_steps": [
            "先看脚本标出的结论段范围，确认是否包含核心结论、贡献总结、局限不足和未来工作等要素。",
            "若结论只是逐章重复小结，且没有提炼核心结论或未来工作，应记为 fail 或 warning。",
            "若局限与展望写得较弱但并非完全缺失，可记为 warning，并在结果中指出需要加强的部分。",
        ],
    },
}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _rule_sort_key(item: dict) -> tuple[int, str]:
    order = 0 if item["review_mode"] == REVIEW_MODE_SCRIPT_SOP else 1
    return order, item["rule_id"]


def _range_location(context: CheckContext, paragraphs: list[dict], *, page_no: int | None = None, extra: str | None = None) -> str | None:
    if not paragraphs:
        return None
    return format_paragraph_range_location(
        context.paragraphs,
        context.pdf_pages,
        paragraphs[0]["paragraph_id"],
        paragraphs[-1]["paragraph_id"],
        page_no=page_no,
        extra=extra,
    )


def _para_location(context: CheckContext, paragraph_id: int, *, page_no: int | None = None, extra: str | None = None) -> str:
    return format_paragraph_location(
        context.paragraphs,
        context.pdf_pages,
        paragraph_id,
        page_no=page_no,
        extra=extra,
    )


def _cn_en_abstract_bodies(context: CheckContext) -> tuple[list[dict], list[dict]]:
    cn_idx, en_idx = get_abstract_indices(context.paragraphs)
    toc_idx = find_exact_index(context.paragraphs, "目录")
    if cn_idx is None or en_idx is None:
        return [], []

    cn_body = [
        para
        for para in context.paragraphs[cn_idx + 1:en_idx]
        if (para.get("text") or "").strip() and not (para.get("text") or "").strip().startswith("关键词")
    ]
    en_end_idx = toc_idx if toc_idx is not None and toc_idx > en_idx else len(context.paragraphs)
    en_body = [
        para
        for para in context.paragraphs[en_idx + 1:en_end_idx]
        if (para.get("text") or "").strip() and not (para.get("text") or "").strip().startswith("Keywords")
    ]
    return cn_body, en_body


def _extract_line_by_prefix(paragraphs: list[dict], prefix: str) -> str:
    for para in paragraphs:
        text = (para.get("text") or "").strip()
        if text.startswith(prefix):
            return text
    return ""


def _abstract_prefill(context: CheckContext) -> dict[str, Any]:
    cn_body, en_body = _cn_en_abstract_bodies(context)
    cn_text = "\n".join((para.get("text") or "").strip() for para in cn_body)
    en_text = "\n".join((para.get("text") or "").strip() for para in en_body)
    cn_chars = len(re.findall(r"[\u4e00-\u9fff]", cn_text))
    en_words = len(re.findall(r"[A-Za-z]+", en_text))
    cn_page = find_first_pdf_page_with_any_title(context.pdf_pages, ["摘要", "摘  要"])
    en_page = find_first_pdf_page_with_title(context.pdf_pages, "Abstract")
    cn_keywords = extract_keyword_items(_extract_line_by_prefix(context.paragraphs, "关键词"), "cn")
    en_keywords = extract_keyword_items(_extract_line_by_prefix(context.paragraphs, "Keywords"), "en")

    locations = []
    cn_loc = _range_location(context, cn_body, page_no=cn_page, extra="中文摘要正文")
    en_loc = _range_location(context, en_body, page_no=en_page, extra="英文摘要正文")
    if cn_loc:
        locations.append(cn_loc)
    if en_loc:
        locations.append(en_loc)

    return {
        "summary": (
            f"已提取中文摘要约 {cn_chars} 个汉字、英文摘要约 {en_words} 个英文词；"
            f"中文关键词 {len(cn_keywords)} 个，英文关键词 {len(en_keywords)} 个。"
        ),
        "locations": locations,
        "artifacts": {
            "cn_char_count": cn_chars,
            "en_word_count": en_words,
            "cn_keywords": cn_keywords,
            "en_keywords": en_keywords,
            "cn_excerpt": cn_text[:240],
            "en_excerpt": en_text[:240],
        },
    }


def _build_abs07_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    return _abstract_prefill(context)


def _build_refsec02_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    entries = get_reference_entries(context.paragraphs)
    risk_items = []
    for para in entries:
        text = (para.get("text") or "").strip()
        if not text:
            continue
        page_no = locate_text_page_no(context.pdf_pages, text)
        risk_score = len(text)
        if page_no is None:
            risk_score += 1000
        risk_items.append(
            {
                "paragraph_id": para["paragraph_id"],
                "text": text,
                "page_no": page_no,
                "length": len(text),
                "risk_score": risk_score,
            }
        )
    risk_items.sort(key=lambda item: (-item["risk_score"], item["paragraph_id"]))
    flagged = [item for item in risk_items if item["length"] >= 170 or item["page_no"] is None]
    locations = [
        _para_location(context, item["paragraph_id"], page_no=item["page_no"])
        for item in flagged[:6]
    ]
    summary = (
        f"共识别参考文献 {len(entries)} 条；其中高风险长条目/页码不稳条目 {len(flagged)} 条，"
        "建议优先人工核查这些条目是否跨页。"
    )
    return {
        "summary": summary,
        "locations": locations,
        "artifacts": {
            "reference_count": len(entries),
            "flagged_count": len(flagged),
            "flagged_items": flagged[:12],
        },
    }


def _build_fig03_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    figures = extract_body_figure_titles(context.paragraphs)
    body_paragraphs = get_body_paragraphs(context.paragraphs)
    risks = []

    for figure in figures:
        figure_para = next((para for para in context.paragraphs if para["paragraph_id"] == figure["paragraph_id"]), None)
        if figure_para is None:
            continue
        caption_text = (figure_para.get("text") or "").strip()
        figure_page = locate_text_page_no(context.pdf_pages, caption_text)
        citation_para = None
        for para in body_paragraphs:
            if para["paragraph_id"] >= figure["paragraph_id"]:
                break
            if figure["number_text"] in (para.get("text") or ""):
                citation_para = para
                break
        citation_page = locate_text_page_no(context.pdf_pages, citation_para.get("text", "")) if citation_para else None
        page_gap = None
        if citation_page is not None and figure_page is not None:
            page_gap = figure_page - citation_page
        if citation_para is None or page_gap is None or abs(page_gap) > 1:
            risks.append(
                {
                    "number_text": figure["number_text"],
                    "caption_para_id": figure["paragraph_id"],
                    "caption_page": figure_page,
                    "citation_para_id": citation_para["paragraph_id"] if citation_para else None,
                    "citation_page": citation_page,
                    "page_gap": page_gap,
                }
            )

    locations = []
    for item in risks[:5]:
        if item["citation_para_id"] is not None:
            locations.append(
                _para_location(
                    context,
                    item["citation_para_id"],
                    page_no=item["citation_page"],
                    extra=f"{item['number_text']} 首次引用",
                )
            )
        locations.append(
            _para_location(
                context,
                item["caption_para_id"],
                page_no=item["caption_page"],
                extra=f"{item['number_text']} 图题",
            )
        )

    return {
        "summary": f"共识别正文图题 {len(figures)} 条；脚本初筛出 {len(risks)} 条疑似未紧跟首次引用或页差较大的图。",
        "locations": locations[:8],
        "artifacts": {
            "figure_count": len(figures),
            "risk_count": len(risks),
            "risk_items": risks[:12],
        },
    }


def _body_table_candidates(context: CheckContext) -> list[dict]:
    chapter_headings = extract_chapter_headings(context.paragraphs)
    first_body_para_id = chapter_headings[0]["paragraph_id"] if chapter_headings else 1
    ref_start, _ = get_reference_span(context.paragraphs)
    ref_para_id = context.paragraphs[ref_start]["paragraph_id"] if ref_start is not None else 10**9
    tables = []
    for table in context.tables:
        paragraph_ids = table.get("paragraph_ids") or []
        if not paragraph_ids:
            continue
        if min(paragraph_ids) < first_body_para_id or min(paragraph_ids) >= ref_para_id:
            continue
        if table.get("contains_omml"):
            continue
        if table.get("row_count", 0) < 2:
            continue
        tables.append(table)
    return tables


def _build_tab01_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    candidates = _body_table_candidates(context)
    flagged = []
    for table in candidates:
        paragraph_ids = table.get("paragraph_ids") or []
        if not paragraph_ids:
            continue
        if table.get("has_visible_border"):
            flagged.append(
                {
                    "table_index": table["table_index"],
                    "paragraph_id": paragraph_ids[0],
                    "row_count": table.get("row_count"),
                    "cell_count": table.get("cell_count"),
                    "table_border_values": table.get("table_border_values"),
                    "cell_border_values": table.get("cell_border_values"),
                    "first_text": table.get("first_text"),
                }
            )
    locations = [
        _para_location(context, item["paragraph_id"], extra=f"表格 {item['table_index']}")
        for item in flagged[:6]
    ]
    return {
        "summary": f"正文中共识别候选数据表 {len(candidates)} 个；其中 {len(flagged)} 个表格检测到明显可见边框，建议优先核查是否为三线表或必要例外。",
        "locations": locations,
        "artifacts": {
            "candidate_table_count": len(candidates),
            "flagged_count": len(flagged),
            "flagged_tables": flagged[:12],
        },
    }


def _build_g06_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    body_paragraphs = get_body_paragraphs(context.paragraphs)
    abbr_section = find_abbr_section(body_paragraphs)
    abbr_span = None
    if abbr_section is not None:
        abbr_span = (abbr_section["start_idx"], abbr_section["end_idx"])

    tokens = extract_body_acronyms(context.paragraphs, min_count=2, top_n=12)
    first_hits = []
    for item in tokens:
        token = item["token"]
        for idx, para in enumerate(body_paragraphs):
            if abbr_span is not None and abbr_span[0] <= idx < abbr_span[1]:
                continue
            if token in (para.get("text") or ""):
                first_hits.append(
                    {
                        "token": token,
                        "count": item["count"],
                        "paragraph_id": para["paragraph_id"],
                        "text": (para.get("text") or "")[:120],
                    }
                )
                break
    locations = [
        _para_location(context, item["paragraph_id"], extra=f"{item['token']} 首次出现")
        for item in first_hits[:6]
    ]
    return {
        "summary": f"正文中筛出高频缩写/术语 {len(tokens)} 个，已定位其首次出现位置；需人工核对首次出现处是否已解释。",
        "locations": locations,
        "artifacts": {
            "token_count": len(tokens),
            "first_hits": first_hits,
        },
    }


def _build_wr04_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    cn_body, _ = _cn_en_abstract_bodies(context)
    patterns = [
        re.compile(r"第[一二三四五六七八九十0-9]+章"),
        re.compile(r"第[一二三四五六七八九十0-9]+节"),
        re.compile(r"本文(首先|先).*?(然后|其次|最后)"),
    ]
    hits = []
    for para in cn_body:
        text = (para.get("text") or "").strip()
        matched = [pat.pattern for pat in patterns if pat.search(text)]
        if matched:
            hits.append(
                {
                    "paragraph_id": para["paragraph_id"],
                    "text": text[:120],
                    "matched_patterns": matched,
                }
            )
    cn_page = find_first_pdf_page_with_any_title(context.pdf_pages, ["摘要", "摘  要"])
    locations = [
        _para_location(context, item["paragraph_id"], page_no=cn_page, extra="摘要提纲式风险段落")
        for item in hits[:6]
    ]
    return {
        "summary": f"中文摘要正文共筛出 {len(hits)} 处疑似章节提纲式表述，需人工确认是否真的按章罗列。",
        "locations": locations,
        "artifacts": {
            "hit_count": len(hits),
            "hits": hits,
        },
    }


def _heading_span(context: CheckContext, keywords: list[str]) -> tuple[dict | None, list[dict]]:
    heading = None
    for para in context.paragraphs:
        text = (para.get("text") or "").strip()
        style = (para.get("style_name") or "").lower()
        if style != "heading 1":
            continue
        if any(keyword in text for keyword in keywords):
            heading = para
            break
    if heading is None:
        return None, []

    start_idx = next(idx for idx, para in enumerate(context.paragraphs) if para["paragraph_id"] == heading["paragraph_id"])
    end_idx = len(context.paragraphs)
    for idx in range(start_idx + 1, len(context.paragraphs)):
        if (context.paragraphs[idx].get("style_name") or "").lower() == "heading 1":
            end_idx = idx
            break
    body = [para for para in context.paragraphs[start_idx + 1:end_idx] if (para.get("text") or "").strip()]
    return heading, body


def _chapter_heading_page_no(context: CheckContext, heading_text: str) -> int | None:
    target = "".join((heading_text or "").split())
    for entry in extract_chapter_toc_entries(context.paragraphs):
        if "".join((entry.get("title_part") or "").split()) != target:
            continue
        page = find_pdf_page_by_label(context.pdf_pages, entry.get("page_num"))
        if page is not None:
            return page["page_no"]
    return find_first_pdf_page_with_title(context.pdf_pages, heading_text)


def _anchor_hits(paragraphs: list[dict], anchor_groups: dict[str, list[str]]) -> dict[str, list[dict]]:
    hits: dict[str, list[dict]] = {group: [] for group in anchor_groups}
    for para in paragraphs:
        text = para.get("text") or ""
        for group, keywords in anchor_groups.items():
            if any(keyword in text for keyword in keywords):
                hits[group].append(
                    {
                        "paragraph_id": para["paragraph_id"],
                        "text": text[:120],
                    }
                )
    return hits


def _build_wr05_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    heading, intro_body = _heading_span(context, ["引言", "绪论"])
    if heading is None:
        chapter_heading = next(
            (para for para in context.paragraphs if (para.get("style_name") or "").lower() == "heading 1" and "第1章" in (para.get("text") or "")),
            None,
        )
        if chapter_heading is not None:
            heading, intro_body = _heading_span(context, [chapter_heading.get("text", "")])

    if heading is None:
        return {
            "summary": "未稳定定位到引言/绪论章节，当前无法生成引言要素预填证据。",
            "locations": [],
            "artifacts": {"anchor_hits": {}},
        }

    anchor_groups = {
        "问题提出": ["问题", "挑战", "需求", "研究问题"],
        "背景意义": ["背景", "意义", "重要性", "应用价值"],
        "文献综述": ["研究现状", "相关工作", "文献综述", "已有研究"],
        "研究方法": ["本文提出", "本文设计", "方法", "技术路线"],
        "结构安排": ["本文结构", "全文结构", "章节安排", "本文内容安排"],
    }
    hits = _anchor_hits(intro_body, anchor_groups)
    missing = [group for group, items in hits.items() if not items]
    heading_page = _chapter_heading_page_no(context, heading.get("text", ""))
    locations = [_para_location(context, heading["paragraph_id"], page_no=heading_page, extra="引言/绪论标题")]
    for group, items in hits.items():
        if items:
            locations.append(_para_location(context, items[0]["paragraph_id"], extra=group))
    return {
        "summary": f"已定位引言/绪论范围，共 {len(intro_body)} 段；脚本锚点显示缺失要素 {len(missing)} 项：{', '.join(missing) if missing else '无'}。",
        "locations": locations[:8],
        "artifacts": {
            "heading_paragraph_id": heading["paragraph_id"],
            "paragraph_count": len(intro_body),
            "missing_groups": missing,
            "anchor_hits": hits,
        },
    }


def _build_wr07_prefill(context: CheckContext, rule: dict) -> dict[str, Any]:
    heading, body = _heading_span(context, ["总结", "结论", "展望"])
    if heading is None:
        return {
            "summary": "未稳定定位到结论/总结章节，当前无法生成结论要素预填证据。",
            "locations": [],
            "artifacts": {"anchor_hits": {}},
        }

    anchor_groups = {
        "核心结论": ["本文", "研究表明", "结果表明", "实现了"],
        "主要贡献": ["贡献", "创新", "提出了"],
        "局限不足": ["不足", "局限", "仍存在", "尚有"],
        "未来工作": ["未来", "后续", "展望", "下一步"],
    }
    hits = _anchor_hits(body, anchor_groups)
    missing = [group for group, items in hits.items() if not items]
    heading_page = _chapter_heading_page_no(context, heading.get("text", ""))
    locations = [_para_location(context, heading["paragraph_id"], page_no=heading_page, extra="结论/总结标题")]
    for group, items in hits.items():
        if items:
            locations.append(_para_location(context, items[0]["paragraph_id"], extra=group))
    return {
        "summary": f"已定位结论/总结范围，共 {len(body)} 段；脚本锚点显示缺失要素 {len(missing)} 项：{', '.join(missing) if missing else '无'}。",
        "locations": locations[:8],
        "artifacts": {
            "heading_paragraph_id": heading["paragraph_id"],
            "paragraph_count": len(body),
            "missing_groups": missing,
            "anchor_hits": hits,
        },
    }


PREFILL_BUILDERS = {
    "ABS-07": _build_abs07_prefill,
    "REFSEC-02": _build_refsec02_prefill,
    "FIG-03": _build_fig03_prefill,
    "TAB-01": _build_tab01_prefill,
    "G-06": _build_g06_prefill,
    "WR-04": _build_wr04_prefill,
    "WR-05": _build_wr05_prefill,
    "WR-07": _build_wr07_prefill,
}


def classify_remaining_rule(rule: dict) -> dict[str, Any]:
    policy = MANUAL_RULE_POLICIES.get(rule["rule_id"])
    if policy is not None:
        return policy
    if "pdf_visual" in rule.get("evidence_types", []) or "docx_xml" in rule.get("evidence_types", []):
        return {
            "review_mode": REVIEW_MODE_SCRIPT_SOP,
            "classification_reason": "存在可自动抽取的结构或版式证据，适合先脚本预筛再按 SOP 人工确认。",
            "sop_steps": [
                "先查看脚本预填的候选位置和风险摘要。",
                "再结合 PDF 或 DOCX 可视化结果进行人工确认。",
                "将最终结论写回 manual_review_results.json 并重跑总报告。",
            ],
        }
    return {
        "review_mode": REVIEW_MODE_PURE_SOP,
        "classification_reason": "当前缺少稳定可判的结构证据，建议直接按 SOP 人工复核。",
        "sop_steps": [
            "根据规则要求直接对论文正文和 PDF 进行人工复核。",
            "将结论、位置和修改建议写回 manual_review_results.json。",
            "重跑总报告并确认人工结论已整合。",
        ],
    }


def build_manual_review_items(context: CheckContext, registry: dict, auto_results: list[Result]) -> list[dict]:
    implemented = set(IMPLEMENTED_RULE_IDS)
    items = []
    for rule in registry["rules"]:
        if rule["rule_id"] in implemented:
            continue
        policy = classify_remaining_rule(rule)
        prefill_builder = PREFILL_BUILDERS.get(rule["rule_id"])
        prefill = (
            prefill_builder(context, rule)
            if prefill_builder is not None
            else {"summary": "当前未配置脚本预填证据。", "locations": [], "artifacts": {}}
        )
        items.append(
            {
                "rule_id": rule["rule_id"],
                "title": rule["title"],
                "priority": rule["priority"],
                "automation": rule["automation"],
                "source_section": rule["source_section"],
                "source_pages": rule["source_pages"],
                "requirement_summary": rule["requirement_summary"],
                "evidence_types": rule["evidence_types"],
                "sop_refs": rule["sop_refs"],
                "review_mode": policy["review_mode"],
                "review_mode_label": REVIEW_MODE_LABELS[policy["review_mode"]],
                "classification_reason": policy["classification_reason"],
                "sop_steps": policy["sop_steps"],
                "prefill_summary": prefill["summary"],
                "prefill_locations": prefill["locations"],
                "prefill_artifacts": prefill["artifacts"],
                "status": "pending",
                "reviewer": "",
                "checked_at": "",
                "finding": "",
                "decision_reason": "",
                "follow_up": "",
                "confirmed_locations": [],
            }
        )
    items.sort(key=_rule_sort_key)
    return items


def build_manual_review_payload(context: CheckContext, registry: dict, auto_results: list[Result]) -> dict[str, Any]:
    items = build_manual_review_items(context, registry, auto_results)
    counter = Counter(item["review_mode"] for item in items)
    return {
        "meta": {
            "generated_at": _now_iso(),
            "docx": context.docx_path.name,
            "pdf": context.pdf_path.name,
            "auto_rule_count": len(auto_results),
            "manual_rule_count": len(items),
            "script_plus_sop_count": counter.get(REVIEW_MODE_SCRIPT_SOP, 0),
            "pure_sop_count": counter.get(REVIEW_MODE_PURE_SOP, 0),
        },
        "rules": items,
    }


def merge_manual_review_payload(template_payload: dict[str, Any], existing_payload: dict[str, Any] | None) -> dict[str, Any]:
    if not existing_payload:
        return template_payload

    existing_map = {item["rule_id"]: item for item in existing_payload.get("rules", [])}
    merged_rules = []
    for item in template_payload["rules"]:
        existing = existing_map.get(item["rule_id"])
        if existing is None:
            merged_rules.append(item)
            continue
        merged = dict(item)
        for key in [
            "status",
            "reviewer",
            "checked_at",
            "finding",
            "decision_reason",
            "follow_up",
            "confirmed_locations",
        ]:
            if key in existing:
                merged[key] = existing[key]
        merged_rules.append(merged)

    return {
        "meta": {
            **template_payload["meta"],
            "merged_at": _now_iso(),
        },
        "rules": merged_rules,
    }
