from __future__ import annotations

from pathlib import Path

from guide_checker.core.models import Result


def build_report(docx_path: Path, pdf_path: Path, selected_rules: list[dict], results: list[Result]) -> str:
    passed = sum(1 for item in results if item.status == "pass")
    failed = sum(1 for item in results if item.status == "fail")
    warnings = sum(1 for item in results if item.status == "warning")

    lines = [
        "# Guide-Driven Checker Report",
        "",
        "## Scope",
        "",
        f"- DOCX: `{docx_path.name}`",
        f"- PDF: `{pdf_path.name}`",
        f"- 已实现规则数: `{len(selected_rules)}`",
        f"- 结果统计: `pass={passed}` `fail={failed}` `warning={warnings}`",
        "",
        "## Rules",
        "",
    ]
    for rule in selected_rules:
        lines.append(f"- `{rule['rule_id']}` {rule['title']} ({rule['priority']}, {rule['automation']})")

    lines.extend(["", "## Findings", ""])
    for result in results:
        lines.append(f"### `{result.rule_id}` {result.title}")
        lines.append("")
        lines.append(f"- status: `{result.status}`")
        lines.append(f"- severity: `{result.severity}`")
        lines.append(f"- coverage: `{result.coverage}`")
        lines.append(f"- evidence: `{', '.join(result.evidence_types)}`")
        lines.append(f"- message: {result.message}")
        if result.status == "fail" and result.locations:
            lines.append(f"- location: {'； '.join(result.locations)}")
        lines.append(f"- recommendation: {result.recommendation}")
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- 该报告由正式框架生成，`guide_driven_checker_demo/run_demo.py` 仅作为兼容入口。",
            "- 当前结果基于 DOCX/XML 与 PDF 文本双证据链；需要纯视觉确认的项目仍可继续补充 pdf_visual 子流程。",
            "",
        ]
    )
    return "\n".join(lines)
