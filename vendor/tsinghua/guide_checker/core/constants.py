from __future__ import annotations

import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DEMO_DIR = BASE_DIR / "guide_driven_checker_demo"
OUTPUT_DIR = DEMO_DIR / "output"
REGISTRY_PATH = BASE_DIR / "tsinghua_p0_p1_rules.json"

DEFAULT_DOCX_CANDIDATES: list[str] = []
DEFAULT_PDF_CANDIDATES: list[str] = []

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W_NS, "r": R_NS}
CM_PER_TWIP = 2.54 / 1440.0

IMPLEMENTED_RULE_IDS = [
    "STR-01",
    "STR-02",
    "STR-03",
    "STR-04",
    "STR-05",
    "COVER-01",
    "COVER-02",
    "COVER-04",
    "ABS-01",
    "ABS-02",
    "ABS-03",
    "ABS-04",
    "ABS-06",
    "TOC-01",
    "TOC-02",
    "TOC-03",
    "TOC-04",
    "BODY-01",
    "BODY-03",
    "BODY-04",
    "PAGE-01",
    "PAGE-02",
    "PAGE-03",
    "FIG-01",
    "TAB-03",
    "REFSEC-01",
    "BIB-03",
    "BIB-04",
    "BIB-08",
    "ABBR-01",
    "UNIT-01",
    "EQ-01",
    "EQ-02",
    "LIST-01",
    "LIST-02",
    "FOOT-01",
    "FOOT-02",
    "AUTH-01",
    "ABS-05",
    "LOT-01",
    "ACK-01",
    "DEC-01",
    "CV-01",
    "APP-01",
    "APP-02",
    "G-03",
    "WR-08",
    "TAB-02",
]

STYLE_EXPECTATIONS = {
    "heading 1": {
        "font_ascii": "Arial",
        "font_eastAsia": "黑体",
        "size_pt": 16.0,
        "alignment": "center",
        "line_rule": "auto",
        "line_multiple": 1.0,
        "space_before_pt": 24.0,
        "space_after_pt": 18.0,
    },
    "heading 2": {
        "font_ascii": "Arial",
        "font_eastAsia": "黑体",
        "size_pt": 14.0,
        "alignment": "left",
        "line_rule": "exact",
        "line_pt": 20.0,
        "space_before_pt": 24.0,
        "space_after_pt": 6.0,
    },
    "heading 3": {
        "font_ascii": "Arial",
        "font_eastAsia": "黑体",
        "size_pt": 13.0,
        "alignment": "left",
        "line_rule": "exact",
        "line_pt": 20.0,
        "space_before_pt": 12.0,
        "space_after_pt": 6.0,
    },
    "heading 4": {
        "font_ascii": "Arial",
        "font_eastAsia": "黑体",
        "size_pt": 12.0,
        "alignment": "left",
        "line_rule": "exact",
        "line_pt": 20.0,
        "space_before_pt": 12.0,
        "space_after_pt": 6.0,
    },
    "normal": {
        "font_ascii": "Times New Roman",
        "font_eastAsia": "宋体",
        "size_pt": 12.0,
        "alignment": "both",
        "line_rule": "exact",
        "line_pt": 20.0,
        "space_before_pt": 0.0,
        "space_after_pt": 0.0,
        "first_line_indent_pt": 24.0,
    },
    "reference": {
        "font_ascii": "Times New Roman",
        "size_pt": 10.5,
        "line_rule": "exact",
        "line_pt": 16.0,
        "space_before_pt": 3.0,
        "left_indent_pt": 28.35,
        "hanging_pt": 28.35,
    },
}

TRIGGER_WORDS = ["首次", "首创", "领先", "填补空白", "国内外首次", "国际领先"]
VALID_TYPE_CODES = re.compile(
    r"\[(M|C|G|N|J|D|R|S|P|DB|CP|EB|A|CM|DS|Z)(/OL|/MT|/DK|/CD)?\]",
    re.IGNORECASE,
)
