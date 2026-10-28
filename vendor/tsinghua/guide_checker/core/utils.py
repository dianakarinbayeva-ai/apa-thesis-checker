from __future__ import annotations

import re

from .constants import CM_PER_TWIP, W_NS


ROMAN_PAGE_RE = re.compile(r"^[IVXLCDM]+$")
DECIMAL_PAGE_RE = re.compile(r"^\d+$")


def qn(local: str) -> str:
    return f"{{{W_NS}}}{local}"


def norm(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def twips_to_cm(raw: str | None) -> float | None:
    if raw is None:
        return None
    return round(int(raw) * CM_PER_TWIP, 4)


def half_points_to_pt(raw: str | None) -> float | None:
    if raw is None:
        return None
    return round(int(raw) / 2.0, 3)


def twips_to_pt(raw: str | None) -> float | None:
    if raw is None:
        return None
    return round(int(raw) / 20.0, 3)


def approx(value: float | None, target: float, tol: float = 0.35) -> bool:
    return value is not None and abs(value - target) <= tol


def compare_style(actual: dict, expected: dict) -> list[str]:
    problems = []
    for key, target in expected.items():
        value = actual.get(key)
        if isinstance(target, float):
            if not approx(value, target, 0.4):
                problems.append(f"{key}={value} (应为 {target})")
        elif value != target:
            problems.append(f"{key}={value} (应为 {target})")
    return problems


def get_page_lines(page: dict) -> list[str]:
    return page.get("lines") or [line.strip() for line in page.get("text", "").splitlines() if line.strip()]


def extract_formal_page_label_from_lines(lines: list[str]) -> str | None:
    for line in lines[:6]:
        stripped = line.strip()
        if ROMAN_PAGE_RE.fullmatch(stripped) or DECIMAL_PAGE_RE.fullmatch(stripped):
            return stripped
    return None


def extract_formal_page_label(page: dict) -> str | None:
    return extract_formal_page_label_from_lines(get_page_lines(page))


def is_roman_page_label(label: str | None) -> bool:
    return bool(label) and bool(ROMAN_PAGE_RE.fullmatch(label))


def is_decimal_page_label(label: str | None) -> bool:
    return bool(label) and bool(DECIMAL_PAGE_RE.fullmatch(label))
