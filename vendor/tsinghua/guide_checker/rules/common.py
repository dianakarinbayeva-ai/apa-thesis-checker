from __future__ import annotations

from collections import Counter
import re

from guide_checker.core.utils import extract_formal_page_label, get_page_lines, norm


CHAPTER_RE = re.compile(r"^第\s*(\d+)\s*章")
FIGURE_RE = re.compile(r"^图\s*(\d+)\.(\d+)\s+(.+)$")
TABLE_RE = re.compile(r"^表\s*(\d+)\.(\d+)\s+(.+)$")
ENTRY_TAIL_RE = re.compile(r"(.+?)([IVXLCDM]+|\d+)$")
ABBR_SECTION_TITLE = "符号和缩略语说明"
DISPLAY_EQ_NUM_RE = re.compile(r"^\((\d+)-(\d+)\)$")
ACRONYM_RE = re.compile(r"\b(?:[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+|[A-Z]{2,}[A-Z0-9]*)\b")
UNIT_SPECS = [
    ("m", "米"),
    ("cm", "厘米"),
    ("mm", "毫米"),
    ("km", "千米"),
    ("s", "秒"),
    ("ms", "毫秒"),
    ("h", "小时"),
    ("kg", "千克"),
    ("kn", "节"),
    ("nm", "海里"),
]


def find_exact_index(paragraphs: list[dict], title: str) -> int | None:
    target = norm(title)
    for idx, para in enumerate(paragraphs):
        if para.get("text_norm") == target:
            return idx
    return None


def find_contains_index(paragraphs: list[dict], keyword: str) -> int | None:
    for idx, para in enumerate(paragraphs):
        text = para.get("text", "")
        if keyword in text and len(text.strip()) < 120:
            return idx
    return None


def is_heading_like(style_name: str) -> bool:
    return (style_name or "").strip().lower() in {"heading 1", "标题1"}


def find_first_pdf_page_with_title(
    pages: list[dict],
    title: str,
    *,
    top_n: int = 12,
    allow_anywhere: bool = False,
) -> int | None:
    target_norm = norm(title)
    for page in pages:
        lines = get_page_lines(page)
        top_norm = norm("".join(lines[:top_n]))
        if target_norm and target_norm in top_norm:
            return page["page_no"]
        if allow_anywhere and target_norm and target_norm in norm(page.get("text", "")):
            return page["page_no"]
    return None


def find_first_pdf_page_with_any_title(
    pages: list[dict],
    titles: list[str],
    *,
    top_n: int = 12,
    allow_anywhere: bool = False,
) -> int | None:
    for title in titles:
        page_no = find_first_pdf_page_with_title(pages, title, top_n=top_n, allow_anywhere=allow_anywhere)
        if page_no is not None:
            return page_no
    return None


def find_pdf_page_by_label(pages: list[dict], label: str | int) -> dict | None:
    target = str(label)
    for page in pages:
        if str(page.get("page_label") or "") == target:
            return page
    return None


def get_abstract_indices(paragraphs: list[dict]) -> tuple[int | None, int | None]:
    return find_exact_index(paragraphs, "摘要"), find_exact_index(paragraphs, "Abstract")


def get_body_paragraphs(paragraphs: list[dict]) -> list[dict]:
    ref_start, _ = get_reference_span(paragraphs)
    return paragraphs[:ref_start] if ref_start is not None else paragraphs


def find_paragraph_by_id(paragraphs: list[dict], paragraph_id: int) -> dict | None:
    for para in paragraphs:
        if para.get("paragraph_id") == paragraph_id:
            return para
    return None


def locate_text_page_no(pdf_pages: list[dict], text: str, *, min_chars: int = 5, max_chars: int = 10) -> int | None:
    clean = norm(text)
    if not clean:
        return None
    for length in range(min(max_chars, len(clean)), min_chars - 1, -1):
        snippet = clean[:length]
        hits = [page["page_no"] for page in pdf_pages if snippet in norm(page.get("text", ""))]
        if len(hits) == 1:
            return hits[0]
        if hits:
            return hits[0]
    return None


def paragraph_head_snippet(text: str, *, max_chars: int = 10) -> str:
    clean = "".join((text or "").split())
    return clean[:max_chars]


def format_paragraph_location(paragraphs: list[dict], pdf_pages: list[dict], paragraph_id: int, *, page_no: int | None = None, snippet_chars: int = 10, extra: str | None = None) -> str:
    para = find_paragraph_by_id(paragraphs, paragraph_id)
    if para is None:
        return f"DOCX 段落 {paragraph_id}"
    actual_page_no = page_no if page_no is not None else locate_text_page_no(pdf_pages, para.get("text", ""))
    snippet = paragraph_head_snippet(para.get("text", ""), max_chars=snippet_chars)
    parts = [f"DOCX 段落 {paragraph_id}"]
    if actual_page_no is not None:
        parts.append(f"PDF p{actual_page_no}")
    if extra:
        parts.append(extra)
    if snippet:
        parts.append(f"“{snippet}”")
    return " / ".join(parts)


def format_paragraph_range_location(paragraphs: list[dict], pdf_pages: list[dict], start_id: int, end_id: int, *, page_no: int | None = None, snippet_chars: int = 10, extra: str | None = None) -> str:
    start_para = find_paragraph_by_id(paragraphs, start_id)
    end_para = find_paragraph_by_id(paragraphs, end_id)
    if start_para is None or end_para is None:
        return f"DOCX 段落 {start_id}-{end_id}"
    actual_page_no = page_no if page_no is not None else locate_text_page_no(pdf_pages, start_para.get("text", ""))
    snippet = paragraph_head_snippet(start_para.get("text", ""), max_chars=snippet_chars)
    parts = [f"DOCX 段落 {start_id}-{end_id}"]
    if actual_page_no is not None:
        parts.append(f"PDF p{actual_page_no}")
    if extra:
        parts.append(extra)
    if snippet:
        parts.append(f"“{snippet}”")
    return " / ".join(parts)


def split_entry_tail_page(text: str) -> tuple[str, str | None]:
    clean = (text or "").strip()
    match = ENTRY_TAIL_RE.search(clean)
    if not match:
        return clean, None
    title = match.group(1).rstrip(".· ").rstrip()
    return title, match.group(2)


def parse_chapter_number(text: str) -> int | None:
    match = CHAPTER_RE.match((text or "").strip())
    return int(match.group(1)) if match else None


def get_toc_entries(paragraphs: list[dict]) -> list[dict]:
    toc_idx = find_exact_index(paragraphs, "目录")
    if toc_idx is None:
        return []
    entries = []
    started = False
    for para in paragraphs[toc_idx + 1:]:
        style = (para.get("style_name") or "").lower()
        if style.startswith("toc "):
            entries.append(para)
            started = True
            continue
        if started and not para.get("in_sdt"):
            break
    return entries


def parse_toc_entries(paragraphs: list[dict]) -> list[dict]:
    items = []
    for para in get_toc_entries(paragraphs):
        style = (para.get("style_name") or "").lower()
        match = re.search(r"(\d+)$", style)
        level = int(match.group(1)) if match else None
        title_part, page_label = split_entry_tail_page(para.get("text", "").strip())
        items.append(
            {
                "paragraph_id": para["paragraph_id"],
                "level": level,
                "text": para.get("text", "").strip(),
                "title_part": title_part,
                "page_label": page_label,
            }
        )
    return items


def extract_chapter_headings(paragraphs: list[dict]) -> list[dict]:
    items = []
    for para in paragraphs:
        if para.get("in_sdt"):
            continue
        text = (para.get("text") or "").strip()
        chapter_no = parse_chapter_number(text)
        if chapter_no is None:
            continue
        if is_heading_like(para.get("style_name", "")):
            items.append({"chapter_no": chapter_no, "text": text, "paragraph_id": para["paragraph_id"]})
    dedup = {}
    for item in items:
        dedup.setdefault(item["chapter_no"], item)
    return [dedup[key] for key in sorted(dedup)]


def extract_chapter_toc_entries(paragraphs: list[dict]) -> list[dict]:
    items = []
    for entry in parse_toc_entries(paragraphs):
        chapter_no = parse_chapter_number(entry["title_part"])
        if chapter_no is None:
            continue
        page_num = int(entry["page_label"]) if entry["page_label"] and entry["page_label"].isdigit() else None
        items.append({**entry, "chapter_no": chapter_no, "page_num": page_num})
    return items


def get_reference_span(paragraphs: list[dict]) -> tuple[int | None, int | None]:
    ref_start = find_exact_index(paragraphs, "参考文献")
    if ref_start is None:
        return None, None
    ref_end = len(paragraphs)
    for idx in range(ref_start + 1, len(paragraphs)):
        para = paragraphs[idx]
        if para.get("text", "").strip() and is_heading_like(para.get("style_name", "")):
            ref_end = idx
            break
    return ref_start, ref_end


def get_reference_entries(paragraphs: list[dict]) -> list[dict]:
    ref_start, ref_end = get_reference_span(paragraphs)
    if ref_start is None:
        return []
    entries = []
    for para in paragraphs[ref_start + 1:ref_end]:
        text = (para.get("text") or "").strip()
        if not text:
            continue
        if para.get("style_name") == "参考文献" or re.match(r"^\[\d+\]", text):
            entries.append(para)
    return entries


def parse_citation_token(token: str, max_ref_num: int | None = None) -> list[int]:
    numbers: list[int] = []
    for raw_part in re.split(r"[，,]", token):
        part = raw_part.strip()
        if not part:
            continue
        if "-" in part:
            left, right = [item.strip() for item in part.split("-", 1)]
            if left.isdigit() and right.isdigit():
                start, end = int(left), int(right)
                if start < 1 or end < start:
                    return []
                if max_ref_num is not None and end > max_ref_num:
                    return []
                numbers.extend(range(start, end + 1))
                continue
            return []
        if not part.isdigit():
            return []
        value = int(part)
        if value < 1:
            return []
        if max_ref_num is not None and value > max_ref_num:
            return []
        numbers.append(value)
    return numbers


def extract_body_citation_numbers(paragraphs: list[dict], max_ref_num: int | None = None) -> set[int]:
    body_paragraphs = get_body_paragraphs(paragraphs)
    body_text = "\n".join(para.get("text", "") for para in body_paragraphs if para.get("text", "").strip())
    citation_numbers: set[int] = set()
    for match in re.finditer(r"\[(\d+(?:\s*[-,，]\s*\d+)*)\]", body_text):
        citation_numbers.update(parse_citation_token(match.group(1), max_ref_num=max_ref_num))
    return citation_numbers


def extract_list_entries(paragraphs: list[dict], prefix: str) -> list[dict]:
    pattern = FIGURE_RE if prefix == "图" else TABLE_RE
    items = []
    for para in paragraphs:
        if para.get("style_name") != "table of figures":
            continue
        text = (para.get("text") or "").strip()
        if not text.startswith(prefix):
            continue
        title_part, page_label = split_entry_tail_page(text)
        match = pattern.match(title_part)
        if not match:
            continue
        items.append(
            {
                "paragraph_id": para["paragraph_id"],
                "chapter_no": int(match.group(1)),
                "seq_no": int(match.group(2)),
                "number_text": f"{prefix}{match.group(1)}.{match.group(2)}",
                "title": match.group(3).strip(),
                "page_label": page_label,
            }
        )
    return items


def extract_body_figure_titles(paragraphs: list[dict]) -> list[dict]:
    body_paragraphs = get_body_paragraphs(paragraphs)
    body_end = len(body_paragraphs)
    chapter_headings = extract_chapter_headings(paragraphs)
    chapter_start = (chapter_headings[0]["paragraph_id"] - 1) if chapter_headings else 0
    items = []
    for idx in range(chapter_start, body_end):
        para = body_paragraphs[idx]
        if para.get("in_sdt"):
            continue
        text = (para.get("text") or "").strip()
        match = FIGURE_RE.match(text)
        if not match:
            continue
        items.append(
            {
                "paragraph_id": para["paragraph_id"],
                "chapter_no": int(match.group(1)),
                "seq_no": int(match.group(2)),
                "number_text": f"图{match.group(1)}.{match.group(2)}",
                "title": match.group(3).strip(),
                "preceded_by_drawing": any(
                    paragraphs[j].get("has_drawing") for j in range(max(chapter_start, idx - 2), idx)
                ),
            }
        )
    return items


def extract_keyword_items(line: str, lang: str) -> list[str]:
    if not line:
        return []
    if lang == "cn":
        parts = re.split(r"[：:]", line, maxsplit=1)
        payload = parts[-1]
        return [item.strip() for item in re.split(r"[;；]", payload) if item.strip()]
    parts = re.split(r"[：:]", line, maxsplit=1)
    payload = parts[-1]
    return [item.strip() for item in payload.split(";") if item.strip()]


def get_cover_titles(paragraphs: list[dict]) -> tuple[str | None, str | None]:
    list_idx = find_contains_index(paragraphs, "学位论文指导小组、公开评阅人和答辩委员会名单") or 80
    chinese_title = None
    english_title = None
    for para in paragraphs[:list_idx]:
        text = (para.get("text") or "").strip()
        if not text:
            continue
        if chinese_title is None and len(re.findall(r"[\u4e00-\u9fff]", text)) >= 8:
            chinese_title = text
            continue
        if english_title is None and len(re.findall(r"[A-Za-z]", text)) >= 20:
            english_title = text
            continue
        if chinese_title and english_title:
            break
    return chinese_title, english_title


def get_current_part_title_candidates() -> list[str]:
    return [
        "摘要",
        "Abstract",
        "目录",
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


def page_contains_chapter_header(page: dict) -> bool:
    lines = get_page_lines(page)[:4]
    joined = "".join(lines)
    return "第" in joined and "章" in joined


def page_contains_title_near_top(page: dict, title: str, *, top_n: int = 12) -> bool:
    target_norm = norm(title)
    top_norm = norm("".join(get_page_lines(page)[:top_n]))
    return bool(target_norm) and target_norm in top_norm


def first_nonempty_page_line(page: dict) -> str:
    lines = get_page_lines(page)
    return lines[0] if lines else ""


def first_heading_after(paragraphs: list[dict], start_idx: int) -> int | None:
    for idx in range(start_idx + 1, len(paragraphs)):
        if is_heading_like(paragraphs[idx].get("style_name", "")):
            return idx
    return None


def find_abbr_section(paragraphs: list[dict]) -> dict | None:
    for idx, para in enumerate(paragraphs):
        if para.get("in_sdt"):
            continue
        if norm(para.get("text", "")) != norm(ABBR_SECTION_TITLE):
            continue
        if not is_heading_like(para.get("style_name", "")):
            continue

        end_idx = len(paragraphs)
        for next_idx in range(idx + 1, len(paragraphs)):
            if is_heading_like(paragraphs[next_idx].get("style_name", "")):
                end_idx = next_idx
                break

        item_count = sum(1 for para_item in paragraphs[idx + 1:end_idx] if (para_item.get("text") or "").strip())
        return {
            "start_idx": idx,
            "end_idx": end_idx,
            "paragraph_id": para["paragraph_id"],
            "title": ABBR_SECTION_TITLE,
            "item_count": item_count,
        }
    return None


def extract_body_acronyms(paragraphs: list[dict], *, min_count: int = 2, top_n: int = 20) -> list[dict]:
    body_paragraphs = get_body_paragraphs(paragraphs)
    abbr_section = find_abbr_section(body_paragraphs)
    spans = []
    if abbr_section is not None:
        spans.append((abbr_section["start_idx"], abbr_section["end_idx"]))

    filtered_text_parts = []
    for idx, para in enumerate(body_paragraphs):
        if any(start <= idx < end for start, end in spans):
            continue
        text = (para.get("text") or "").strip()
        if text:
            filtered_text_parts.append(text)

    counts = Counter()
    for token in ACRONYM_RE.findall("\n".join(filtered_text_parts)):
        if re.fullmatch(r"[IVXLCDM]+", token):
            continue
        counts[token] += 1

    items = [
        {"token": token, "count": count}
        for token, count in counts.items()
        if count >= min_count
    ]
    items.sort(key=lambda item: (-item["count"], item["token"]))
    return items[:top_n]


def scan_unit_pair_mixes(paragraphs: list[dict]) -> dict:
    body_paragraphs = get_body_paragraphs(paragraphs)
    abbr_section = find_abbr_section(body_paragraphs)
    spans = []
    if abbr_section is not None:
        spans.append((abbr_section["start_idx"], abbr_section["end_idx"]))

    def in_excluded_span(idx: int) -> bool:
        return any(start <= idx < end for start, end in spans)

    pair_state: dict[str, dict] = {
        symbol: {
            "symbol": symbol,
            "cn": cn,
            "symbol_count": 0,
            "cn_count": 0,
            "symbol_examples": [],
            "cn_examples": [],
        }
        for symbol, cn in UNIT_SPECS
    }

    for idx, para in enumerate(body_paragraphs):
        if in_excluded_span(idx):
            continue
        text = para.get("text") or ""
        if not text.strip():
            continue
        for symbol, cn in UNIT_SPECS:
            sym_re = re.compile(rf"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*{re.escape(symbol)}(?![A-Za-z])")
            if cn == "节":
                cn_re = re.compile(rf"(?<![A-Za-z0-9第.．])(\d+)\s*{re.escape(cn)}(?![A-Za-z0-9])")
            else:
                cn_re = re.compile(rf"(?<![A-Za-z0-9])(\d+(?:\.\d+)?)\s*{re.escape(cn)}(?![A-Za-z])")
            state = pair_state[symbol]
            for match in sym_re.finditer(text):
                state["symbol_count"] += 1
                if len(state["symbol_examples"]) < 3:
                    state["symbol_examples"].append(
                        {
                            "paragraph_id": para["paragraph_id"],
                            "snippet": text[:120],
                            "match": match.group(0),
                        }
                    )
            for match in cn_re.finditer(text):
                state["cn_count"] += 1
                if len(state["cn_examples"]) < 3:
                    state["cn_examples"].append(
                        {
                            "paragraph_id": para["paragraph_id"],
                            "snippet": text[:120],
                            "match": match.group(0),
                        }
                    )

    symbol_total = sum(item["symbol_count"] for item in pair_state.values())
    chinese_total = sum(item["cn_count"] for item in pair_state.values())
    mixed_pairs = [
        {
            "symbol": item["symbol"],
            "cn": item["cn"],
            "symbol_count": item["symbol_count"],
            "cn_count": item["cn_count"],
            "symbol_examples": item["symbol_examples"],
            "cn_examples": item["cn_examples"],
        }
        for item in pair_state.values()
        if item["symbol_count"] > 0 and item["cn_count"] > 0
    ]

    return {
        "symbol_total": symbol_total,
        "chinese_total": chinese_total,
        "mixed_pairs": mixed_pairs,
        "pairs": list(pair_state.values()),
    }


def extract_display_equations(paragraphs: list[dict]) -> list[dict]:
    body_paragraphs = get_body_paragraphs(paragraphs)
    items = []
    for idx, para in enumerate(body_paragraphs):
        text = (para.get("text") or "").strip()
        if not para.get("has_table"):
            continue
        match = DISPLAY_EQ_NUM_RE.fullmatch(text)
        if not match:
            continue

        formula_idx = None
        direction = None
        for delta in range(1, 4):
            prev_idx = idx - delta
            if prev_idx < 0:
                break
            prev_para = body_paragraphs[prev_idx]
            if prev_para.get("has_table") and prev_para.get("has_omml"):
                formula_idx = prev_idx
                direction = "backward"
                break
        if formula_idx is None:
            for delta in range(1, 4):
                next_idx = idx + delta
                if next_idx >= len(body_paragraphs):
                    break
                next_para = body_paragraphs[next_idx]
                if next_para.get("has_table") and next_para.get("has_omml"):
                    formula_idx = next_idx
                    direction = "forward"
                    break

        formula_para = body_paragraphs[formula_idx] if formula_idx is not None else None
        items.append(
            {
                "number_text": text,
                "chapter_no": int(match.group(1)),
                "seq_no": int(match.group(2)),
                "number_para_id": para["paragraph_id"],
                "formula_para_id": formula_para["paragraph_id"] if formula_para is not None else None,
                "number_alignment": (para.get("para_fmt") or {}).get("alignment"),
                "formula_alignment": (formula_para.get("para_fmt") or {}).get("alignment") if formula_para is not None else None,
                "formula_text": (formula_para.get("text") or "").strip() if formula_para is not None else "",
                "table_based": bool(formula_para is not None and formula_para.get("has_table")),
                "pair_direction": direction,
            }
        )
    return items
