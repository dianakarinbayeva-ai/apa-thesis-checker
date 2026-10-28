from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

from lxml import etree

from guide_checker.core.constants import NS
from guide_checker.core.utils import half_points_to_pt, qn, twips_to_cm, twips_to_pt


INVISIBLE_BORDER_VALUES = {"nil", "none"}


def _local_name(node) -> str:
    return etree.QName(node).localname


def _get_text(elem) -> str:
    return "".join((node.text or "") for node in elem.iter(qn("t")))


def _style_name_by_id(styles: dict[str, dict]) -> dict[str, str]:
    return {value["style_id"]: value["style_name"] for value in styles.values() if value["style_id"]}


def _collect_border_values(border_parent) -> list[str]:
    if border_parent is None:
        return []
    values = []
    for child in border_parent:
        value = child.get(qn("val"))
        if value:
            values.append(value)
    return values


def _has_visible_border(values: list[str]) -> bool:
    return any(value not in INVISIBLE_BORDER_VALUES for value in values)


def _first_nonempty_run_info(node) -> dict:
    for run in node.findall(qn("r")):
        run_text = _get_text(run).strip()
        if not run_text:
            continue
        rpr = run.find(qn("rPr"))
        if rpr is None:
            return {}
        rfonts = rpr.find(qn("rFonts"))
        sz = rpr.find(qn("sz"))
        return {
            "font_ascii": rfonts.get(qn("ascii")) if rfonts is not None else None,
            "font_eastAsia": rfonts.get(qn("eastAsia")) if rfonts is not None else None,
            "size_pt": half_points_to_pt(sz.get(qn("val"))) if sz is not None else None,
        }
    return {}


def _extract_para_format(ppr) -> tuple[str, bool, dict]:
    style_id = ""
    page_break_before = False
    para_fmt: dict[str, float | str | None] = {}
    if ppr is None:
        return style_id, page_break_before, para_fmt

    pstyle = ppr.find(qn("pStyle"))
    if pstyle is not None:
        style_id = pstyle.get(qn("val")) or ""

    page_break_before = ppr.find(qn("pageBreakBefore")) is not None
    jc = ppr.find(qn("jc"))
    spacing = ppr.find(qn("spacing"))
    ind = ppr.find(qn("ind"))
    para_fmt["alignment"] = jc.get(qn("val")) if jc is not None else None

    if spacing is not None:
        para_fmt["line_rule"] = spacing.get(qn("lineRule"), "auto")
        line_raw = spacing.get(qn("line"))
        if line_raw is not None:
            if para_fmt["line_rule"] == "auto":
                para_fmt["line_multiple"] = round(int(line_raw) / 240.0, 3)
            else:
                para_fmt["line_pt"] = twips_to_pt(line_raw)
        para_fmt["space_before_pt"] = twips_to_pt(spacing.get(qn("before")))
        para_fmt["space_after_pt"] = twips_to_pt(spacing.get(qn("after")))

    if ind is not None:
        para_fmt["first_line_indent_pt"] = twips_to_pt(ind.get(qn("firstLine")))
        para_fmt["left_indent_pt"] = twips_to_pt(ind.get(qn("left")))
        para_fmt["hanging_pt"] = twips_to_pt(ind.get(qn("hanging")))

    return style_id, page_break_before, para_fmt


def _extract_paragraph_record(
    node,
    *,
    styles: dict[str, dict],
    paragraph_id: int,
    inside_table: bool,
    inside_sdt: bool,
    body_index: int | None,
    table_index: int | None,
    row_index: int | None = None,
    cell_index: int | None = None,
) -> dict:
    style_name_by_id = _style_name_by_id(styles)
    ppr = node.find(qn("pPr"))
    style_id, page_break_before, para_fmt = _extract_para_format(ppr)
    text = _get_text(node)
    instr_text = "".join((item.text or "") for item in node.iter(qn("instrText")))
    return {
        "paragraph_id": paragraph_id,
        "style_id": style_id,
        "style_name": style_name_by_id.get(style_id, ""),
        "text": text,
        "text_norm": "".join(text.split()),
        "has_drawing": bool(node.xpath(".//*[local-name()='drawing']")),
        "has_table": inside_table,
        "has_omml": bool(node.xpath(".//*[local-name()='oMath' or local-name()='oMathPara']")),
        "field_type": "toc" if "TOC" in instr_text else "",
        "page_break_before": page_break_before,
        "in_sdt": inside_sdt,
        "body_index": body_index,
        "table_index": table_index,
        "row_index": row_index,
        "cell_index": cell_index,
        "para_fmt": para_fmt,
        "run_info": _first_nonempty_run_info(node),
    }


def _open_xml(zf: ZipFile, member: str):
    return etree.fromstring(zf.read(member))


def _get_body(doc_root):
    return doc_root.find(qn("body"))


def _body_index_lookup(body) -> tuple[dict[str, int], etree._ElementTree]:
    tree = body.getroottree()
    block_nodes = []
    for child in body:
        if _local_name(child) in {"p", "tbl", "sdt"}:
            block_nodes.append(child)
    return {tree.getpath(node): idx + 1 for idx, node in enumerate(block_nodes)}, tree


def _top_level_body_child(node, body):
    current = node
    while current is not None and current.getparent() is not body:
        current = current.getparent()
    if current is not None and current.getparent() is body:
        return current
    return None


def parse_styles(docx_path: Path) -> dict[str, dict]:
    with ZipFile(docx_path) as zf:
        root = _open_xml(zf, "word/styles.xml")

    styles: dict[str, dict] = {}
    for style in root.findall(".//w:style", namespaces=NS):
        if style.get(qn("type")) != "paragraph":
            continue
        style_id = style.get(qn("styleId")) or ""
        name_el = style.find("w:name", namespaces=NS)
        name = (name_el.get(qn("val")) if name_el is not None else style_id or "").strip()
        key = name.lower()

        ppr = style.find("w:pPr", namespaces=NS)
        rpr = style.find("w:rPr", namespaces=NS)

        alignment = None
        line_rule = None
        line_pt = None
        line_multiple = None
        space_before_pt = None
        space_after_pt = None
        first_line_indent_pt = None
        left_indent_pt = None
        hanging_pt = None

        if ppr is not None:
            jc = ppr.find("w:jc", namespaces=NS)
            if jc is not None:
                alignment = jc.get(qn("val"))
            spacing = ppr.find("w:spacing", namespaces=NS)
            if spacing is not None:
                line_rule = spacing.get(qn("lineRule"), "auto")
                line_raw = spacing.get(qn("line"))
                if line_raw is not None:
                    if line_rule == "auto":
                        line_multiple = round(int(line_raw) / 240.0, 3)
                    else:
                        line_pt = twips_to_pt(line_raw)
                space_before_pt = twips_to_pt(spacing.get(qn("before")))
                space_after_pt = twips_to_pt(spacing.get(qn("after")))
            ind = ppr.find("w:ind", namespaces=NS)
            if ind is not None:
                first_line_indent_pt = twips_to_pt(ind.get(qn("firstLine")))
                left_indent_pt = twips_to_pt(ind.get(qn("left")))
                hanging_pt = twips_to_pt(ind.get(qn("hanging")))

        font_ascii = None
        font_east_asia = None
        size_pt = None
        if rpr is not None:
            rfonts = rpr.find("w:rFonts", namespaces=NS)
            if rfonts is not None:
                font_ascii = rfonts.get(qn("ascii"))
                font_east_asia = rfonts.get(qn("eastAsia"))
            sz = rpr.find("w:sz", namespaces=NS)
            if sz is not None:
                size_pt = half_points_to_pt(sz.get(qn("val")))

        styles[key] = {
            "style_id": style_id,
            "style_name": name,
            "alignment": alignment,
            "line_rule": line_rule,
            "line_pt": line_pt,
            "line_multiple": line_multiple,
            "space_before_pt": space_before_pt,
            "space_after_pt": space_after_pt,
            "first_line_indent_pt": first_line_indent_pt,
            "left_indent_pt": left_indent_pt,
            "hanging_pt": hanging_pt,
            "font_ascii": font_ascii,
            "font_eastAsia": font_east_asia,
            "size_pt": size_pt,
        }
    return styles


def parse_docx_logic(docx_path: Path, styles: dict[str, dict]) -> list[dict]:
    with ZipFile(docx_path) as zf:
        root = _open_xml(zf, "word/document.xml")

    body = _get_body(root)
    if body is None:
        return []

    body_index_map, tree = _body_index_lookup(body)
    table_nodes = body.xpath(".//w:tbl", namespaces=NS)
    table_index_map = {tree.getpath(node): idx + 1 for idx, node in enumerate(table_nodes)}

    paragraphs: list[dict] = []
    paragraph_nodes = body.xpath(".//w:p", namespaces=NS)
    for paragraph_id, node in enumerate(paragraph_nodes, start=1):
        nearest_table = node.xpath("ancestor::w:tbl[1]", namespaces=NS)
        nearest_row = node.xpath("ancestor::w:tr[1]", namespaces=NS)
        nearest_cell = node.xpath("ancestor::w:tc[1]", namespaces=NS)
        top_level = _top_level_body_child(node, body)

        table_index = None
        row_index = None
        cell_index = None
        inside_table = bool(nearest_table)
        if inside_table:
            table_path = tree.getpath(nearest_table[0])
            table_index = table_index_map.get(table_path)
        if nearest_row:
            row_index = len(list(nearest_row[0].itersiblings(preceding=True))) + 1
        if nearest_cell:
            cell_index = len(list(nearest_cell[0].itersiblings(preceding=True))) + 1

        body_index = body_index_map.get(tree.getpath(top_level)) if top_level is not None else None
        paragraphs.append(
            _extract_paragraph_record(
                node,
                styles=styles,
                paragraph_id=paragraph_id,
                inside_table=inside_table,
                inside_sdt=bool(node.xpath("ancestor::w:sdt", namespaces=NS)),
                body_index=body_index,
                table_index=table_index,
                row_index=row_index,
                cell_index=cell_index,
            )
        )
    return paragraphs


def parse_docx_layout(docx_path: Path) -> list[dict]:
    with ZipFile(docx_path) as zf:
        root = _open_xml(zf, "word/document.xml")

    sections: list[dict] = []
    for idx, sect in enumerate(root.xpath(".//w:sectPr", namespaces=NS), start=1):
        pg_sz = sect.find("w:pgSz", namespaces=NS)
        pg_mar = sect.find("w:pgMar", namespaces=NS)
        pg_num = sect.find("w:pgNumType", namespaces=NS)

        sections.append(
            {
                "section_id": idx,
                "page_width_twips": int(pg_sz.get(qn("w"))) if pg_sz is not None and pg_sz.get(qn("w")) else None,
                "page_height_twips": int(pg_sz.get(qn("h"))) if pg_sz is not None and pg_sz.get(qn("h")) else None,
                "page_width_cm": twips_to_cm(pg_sz.get(qn("w"))) if pg_sz is not None else None,
                "page_height_cm": twips_to_cm(pg_sz.get(qn("h"))) if pg_sz is not None else None,
                "margin_top_cm": twips_to_cm(pg_mar.get(qn("top"))) if pg_mar is not None else None,
                "margin_bottom_cm": twips_to_cm(pg_mar.get(qn("bottom"))) if pg_mar is not None else None,
                "margin_left_cm": twips_to_cm(pg_mar.get(qn("left"))) if pg_mar is not None else None,
                "margin_right_cm": twips_to_cm(pg_mar.get(qn("right"))) if pg_mar is not None else None,
                "header_distance_cm": twips_to_cm(pg_mar.get(qn("header"))) if pg_mar is not None else None,
                "footer_distance_cm": twips_to_cm(pg_mar.get(qn("footer"))) if pg_mar is not None else None,
                "page_number_format": pg_num.get(qn("fmt")) if pg_num is not None else None,
                "page_number_start": int(pg_num.get(qn("start"))) if pg_num is not None and pg_num.get(qn("start")) else None,
            }
        )
    return sections


def parse_docx_tables(docx_path: Path, paragraphs: list[dict] | None = None) -> list[dict]:
    with ZipFile(docx_path) as zf:
        root = _open_xml(zf, "word/document.xml")

    body = _get_body(root)
    if body is None:
        return []

    body_index_map, tree = _body_index_lookup(body)
    paragraph_ids_by_table: dict[int, list[int]] = {}
    if paragraphs is not None:
        for para in paragraphs:
            table_index = para.get("table_index")
            if table_index is None:
                continue
            paragraph_ids_by_table.setdefault(table_index, []).append(para["paragraph_id"])

    tables: list[dict] = []
    for table_index, node in enumerate(body.xpath(".//w:tbl", namespaces=NS), start=1):
        tbl_pr = node.find("w:tblPr", namespaces=NS)
        tbl_style = tbl_pr.find("w:tblStyle", namespaces=NS) if tbl_pr is not None else None
        tbl_borders = tbl_pr.find("w:tblBorders", namespaces=NS) if tbl_pr is not None else None
        table_border_values = _collect_border_values(tbl_borders)

        cell_border_values: list[str] = []
        for tc_borders in node.xpath(".//w:tcPr/w:tcBorders", namespaces=NS):
            cell_border_values.extend(_collect_border_values(tc_borders))

        row_nodes = node.findall("w:tr", namespaces=NS)
        row_count = len(row_nodes)
        cell_count = sum(len(row.findall("w:tc", namespaces=NS)) for row in row_nodes)
        paragraph_texts = [_get_text(p).strip() for p in node.findall(".//w:p", namespaces=NS)]
        nonempty_paragraph_texts = [text for text in paragraph_texts if text]
        top_level = _top_level_body_child(node, body)
        body_index = body_index_map.get(tree.getpath(top_level)) if top_level is not None else None

        tables.append(
            {
                "table_index": table_index,
                "body_index": body_index,
                "inside_sdt": bool(node.xpath("ancestor::w:sdt", namespaces=NS)),
                "style_id": tbl_style.get(qn("val")) if tbl_style is not None else None,
                "table_border_values": sorted(set(table_border_values)),
                "cell_border_values": sorted(set(cell_border_values)),
                "has_visible_border": _has_visible_border(table_border_values + cell_border_values),
                "row_count": row_count,
                "cell_count": cell_count,
                "paragraph_count": len(paragraph_texts),
                "nonempty_paragraph_count": len(nonempty_paragraph_texts),
                "contains_omml": bool(node.xpath(".//*[local-name()='oMath' or local-name()='oMathPara']")),
                "first_text": nonempty_paragraph_texts[0][:80] if nonempty_paragraph_texts else "",
                "text": "\n".join(nonempty_paragraph_texts[:20]),
                "paragraph_ids": paragraph_ids_by_table.get(table_index, []),
            }
        )
    return tables


def parse_docx_footnotes(docx_path: Path, styles: dict[str, dict]) -> dict:
    with ZipFile(docx_path) as zf:
        document_root = _open_xml(zf, "word/document.xml")
        settings_root = _open_xml(zf, "word/settings.xml")
        footnotes_root = _open_xml(zf, "word/footnotes.xml") if "word/footnotes.xml" in zf.namelist() else None

    body = _get_body(document_root)
    paragraph_nodes = body.xpath(".//w:p", namespaces=NS) if body is not None else []

    references = []
    for paragraph_id, node in enumerate(paragraph_nodes, start=1):
        paragraph_text = _get_text(node)
        for ref in node.xpath(".//w:footnoteReference", namespaces=NS):
            raw_id = ref.get(qn("id"))
            if raw_id is None:
                continue
            footnote_id = int(raw_id)
            if footnote_id < 2:
                continue
            run = ref.getparent()
            rpr = run.find(qn("rPr")) if run is not None else None
            rstyle = rpr.find(qn("rStyle")) if rpr is not None else None
            vert_align = rpr.find(qn("vertAlign")) if rpr is not None else None
            references.append(
                {
                    "footnote_id": footnote_id,
                    "paragraph_id": paragraph_id,
                    "paragraph_text": paragraph_text[:120],
                    "style_id": rstyle.get(qn("val")) if rstyle is not None else None,
                    "is_superscript": bool(
                        (vert_align is not None and vert_align.get(qn("val")) == "superscript")
                        or (rstyle is not None and (rstyle.get(qn("val")) or "").lower() == "footnote reference")
                    ),
                }
            )

    settings = {
        "num_restart": None,
        "num_format": None,
        "position": None,
    }
    footnote_pr = settings_root.find("w:footnotePr", namespaces=NS)
    if footnote_pr is not None:
        num_restart = footnote_pr.find("w:numRestart", namespaces=NS)
        num_fmt = footnote_pr.find("w:numFmt", namespaces=NS)
        position = footnote_pr.find("w:pos", namespaces=NS)
        settings["num_restart"] = num_restart.get(qn("val")) if num_restart is not None else None
        settings["num_format"] = num_fmt.get(qn("val")) if num_fmt is not None else None
        settings["position"] = position.get(qn("val")) if position is not None else None

    entries = []
    if footnotes_root is not None:
        for footnote in footnotes_root.findall("w:footnote", namespaces=NS):
            raw_id = footnote.get(qn("id"))
            if raw_id is None:
                continue
            footnote_id = int(raw_id)
            footnote_type = footnote.get(qn("type"))
            if footnote_id < 2 or footnote_type in {"separator", "continuationSeparator"}:
                continue
            paragraphs = []
            for para_idx, node in enumerate(footnote.findall(".//w:p", namespaces=NS), start=1):
                record = _extract_paragraph_record(
                    node,
                    styles=styles,
                    paragraph_id=para_idx,
                    inside_table=bool(node.xpath("ancestor::w:tbl", namespaces=NS)),
                    inside_sdt=bool(node.xpath("ancestor::w:sdt", namespaces=NS)),
                    body_index=None,
                    table_index=None,
                )
                record["footnote_paragraph_index"] = para_idx
                paragraphs.append(record)
            entries.append(
                {
                    "footnote_id": footnote_id,
                    "type": footnote_type or "normal",
                    "paragraph_count": len(paragraphs),
                    "text": "\n".join(
                        (para.get("text") or "").strip()
                        for para in paragraphs
                        if (para.get("text") or "").strip()
                    ),
                    "paragraphs": paragraphs,
                }
            )

    return {
        "settings": settings,
        "reference_count": len(references),
        "references": references,
        "footnote_count": len(entries),
        "entries": entries,
    }
