from __future__ import annotations

from pathlib import Path

import fitz

from guide_checker.core.utils import extract_formal_page_label_from_lines, norm


def parse_pdf_pages(pdf_path: Path) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages: list[dict] = []
    try:
        for page_idx in range(doc.page_count):
            page = doc.load_page(page_idx)
            text = page.get_text("text")
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            pages.append(
                {
                    "page_no": page_idx + 1,
                    "width_pt": round(page.rect.width, 3),
                    "height_pt": round(page.rect.height, 3),
                    "text": text,
                    "lines": lines,
                    "first_line": lines[0] if lines else "",
                    "last_line": lines[-1] if lines else "",
                    "top_text_norm": norm("".join(lines[:12])),
                    "page_label": extract_formal_page_label_from_lines(lines),
                }
            )
    finally:
        doc.close()
    return pages
