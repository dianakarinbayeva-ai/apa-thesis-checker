from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Result:
    rule_id: str
    title: str
    priority: str
    status: str
    severity: str
    evidence_types: list[str]
    message: str
    recommendation: str
    coverage: str = "full"
    locations: list[str] = field(default_factory=list)
    artifacts: dict[str, Any] = field(default_factory=dict)


@dataclass
class CheckContext:
    docx_path: Path
    pdf_path: Path
    registry: dict
    selected_rules: list[dict]
    styles: dict[str, dict]
    paragraphs: list[dict]
    sections: list[dict]
    tables: list[dict]
    footnotes: dict[str, Any]
    pdf_pages: list[dict]
