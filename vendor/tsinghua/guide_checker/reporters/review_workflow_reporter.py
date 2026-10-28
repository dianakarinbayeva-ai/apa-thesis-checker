from __future__ import annotations

from pathlib import Path

from guide_checker.core.manual_review import REVIEW_MODE_LABELS, REVIEW_MODE_PURE_SOP, REVIEW_MODE_SCRIPT_SOP
from guide_checker.core.models import Result


def _mode_items(payload: dict, review_mode: str) -> list[dict]:
    return [item for item in payload.get("rules", []) if item["review_mode"] == review_mode]


def build_manual_checklist(payload: dict, review_mode: str) -> str:
    items = _mode_items(payload, review_mode)
    title = REVIEW_MODE_LABELS[review_mode]
    lines = [
        f"# {title} 规则核查清单",
        "",
        "## 使用方式",
        "",
        "1. 先运行 `guide_checker` 自动审查，确认 `report.md` 已生成。",
        "2. 再根据本清单逐条复核，并把结论写回 `manual_review_results.json`。",
        "3. 复核完成后，重新运行全流程命令，刷新 `full_review_report.md`。",
        "",
        f"## 当前规则数：{len(items)}",
        "",
    ]
    for item in items:
        lines.append(f"### `{item['rule_id']}` {item['title']}")
        lines.append("")
        lines.append(f"- status: `{item['status']}`")
        lines.append(f"- priority: `{item['priority']}`")
        lines.append(f"- source: `{item['source_section']}` / pages `{item['source_pages']}`")
        lines.append(f"- requirement: {item['requirement_summary']}")
        lines.append(f"- classification: {item['classification_reason']}")
        lines.append(f"- prefill: {item['prefill_summary']}")
        if item.get("prefill_locations"):
            lines.append(f"- locations: {'； '.join(item['prefill_locations'])}")
        lines.append("- SOP:")
        for idx, step in enumerate(item.get("sop_steps", []), start=1):
            lines.append(f"  {idx}. {step}")
        if item.get("finding"):
            lines.append(f"- reviewer_finding: {item['finding']}")
        if item.get("decision_reason"):
            lines.append(f"- decision_reason: {item['decision_reason']}")
        lines.append("")
    return "\n".join(lines)


def build_full_review_report(
    *,
    docx_path: Path,
    pdf_path: Path,
    auto_results: list[Result],
    manual_payload: dict,
    auto_report_name: str = "report.md",
) -> str:
    auto_pass = sum(1 for item in auto_results if item.status == "pass")
    auto_fail = sum(1 for item in auto_results if item.status == "fail")
    auto_warn = sum(1 for item in auto_results if item.status == "warning")

    manual_rules = manual_payload.get("rules", [])
    script_items = _mode_items(manual_payload, REVIEW_MODE_SCRIPT_SOP)
    pure_items = _mode_items(manual_payload, REVIEW_MODE_PURE_SOP)

    def status_count(items: list[dict], target: str) -> int:
        return sum(1 for item in items if item.get("status") == target)

    lines = [
        "# Full Review Report",
        "",
        "## Scope",
        "",
        f"- DOCX: `{docx_path.name}`",
        f"- PDF: `{pdf_path.name}`",
        f"- 自动报告: `{auto_report_name}`",
        f"- 自动规则统计: `pass={auto_pass}` `fail={auto_fail}` `warning={auto_warn}`",
        f"- 剩余人工规则: `{len(manual_rules)}`",
        f"- `脚本+SOP`: `{len(script_items)}` 条，`pending={status_count(script_items, 'pending')}` `pass={status_count(script_items, 'pass')}` `fail={status_count(script_items, 'fail')}` `warning={status_count(script_items, 'warning')}`",
        f"- `纯SOP`: `{len(pure_items)}` 条，`pending={status_count(pure_items, 'pending')}` `pass={status_count(pure_items, 'pass')}` `fail={status_count(pure_items, 'fail')}` `warning={status_count(pure_items, 'warning')}`",
        "",
        "## Auto Findings",
        "",
    ]

    auto_failures = [item for item in auto_results if item.status in {"fail", "warning"}]
    if not auto_failures:
        lines.append("- 自动规则当前未发现 fail/warning。")
        lines.append("")
    else:
        for item in auto_failures:
            lines.append(f"### `{item.rule_id}` {item.title}")
            lines.append("")
            lines.append(f"- status: `{item.status}`")
            lines.append(f"- severity: `{item.severity}`")
            lines.append(f"- message: {item.message}")
            if item.locations:
                lines.append(f"- location: {'； '.join(item.locations)}")
            lines.append(f"- recommendation: {item.recommendation}")
            lines.append("")

    def append_manual_section(section_title: str, items: list[dict]) -> None:
        lines.append(f"## {section_title}")
        lines.append("")
        if not items:
            lines.append("- 当前无规则。")
            lines.append("")
            return
        for item in items:
            lines.append(f"### `{item['rule_id']}` {item['title']}")
            lines.append("")
            lines.append(f"- status: `{item['status']}`")
            lines.append(f"- source: `{item['source_section']}` / pages `{item['source_pages']}`")
            lines.append(f"- requirement: {item['requirement_summary']}")
            lines.append(f"- classification: {item['classification_reason']}")
            lines.append(f"- prefill: {item['prefill_summary']}")
            if item.get("prefill_locations"):
                lines.append(f"- candidate_locations: {'； '.join(item['prefill_locations'])}")
            if item.get("finding"):
                lines.append(f"- reviewer_finding: {item['finding']}")
            if item.get("decision_reason"):
                lines.append(f"- decision_reason: {item['decision_reason']}")
            if item.get("follow_up"):
                lines.append(f"- follow_up: {item['follow_up']}")
            if item.get("confirmed_locations"):
                lines.append(f"- confirmed_locations: {'； '.join(item['confirmed_locations'])}")
            lines.append("- SOP:")
            for idx, step in enumerate(item.get("sop_steps", []), start=1):
                lines.append(f"  {idx}. {step}")
            lines.append("")

    append_manual_section("Script+SOP Review", script_items)
    append_manual_section("Pure SOP Review", pure_items)
    return "\n".join(lines)
