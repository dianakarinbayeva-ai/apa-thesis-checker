from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from guide_checker.core.constants import (
    BASE_DIR,
    DEFAULT_DOCX_CANDIDATES,
    DEFAULT_PDF_CANDIDATES,
    IMPLEMENTED_RULE_IDS,
    REGISTRY_PATH,
)
from guide_checker.core.models import CheckContext
from guide_checker.core.registry import ensure_dir, export_selected_rules, load_registry, resolve_existing_path
from guide_checker.extractors import (
    parse_docx_footnotes,
    parse_docx_layout,
    parse_docx_logic,
    parse_docx_tables,
    parse_pdf_pages,
    parse_styles,
)
from guide_checker.reporters import build_report
from guide_checker.rules import RULE_CHECKERS


sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def _save_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_checker(
    *,
    docx: str | None = None,
    pdf: str | None = None,
    output_dir: str | Path | None = None,
    artifact_suffix: str = "",
    analysis_name: str = "analysis.json",
    report_name: str = "report.md",
    rule_ids: list[str] | None = None,
    print_prefix: str = "[checker]",
) -> tuple[CheckContext, list]:
    output_path = Path(output_dir) if output_dir else (BASE_DIR / "guide_checker" / "output")
    ensure_dir(output_path)

    docx_path = resolve_existing_path(BASE_DIR, docx, DEFAULT_DOCX_CANDIDATES, "*.docx", "论文 DOCX")
    pdf_path = resolve_existing_path(BASE_DIR, pdf, DEFAULT_PDF_CANDIDATES, "*.pdf", "排版 PDF")

    registry = load_registry(REGISTRY_PATH)
    active_rule_ids = rule_ids or IMPLEMENTED_RULE_IDS
    selected_rules = export_selected_rules(registry, active_rule_ids, output_path / f"guide_rules{artifact_suffix}.json")

    styles = parse_styles(docx_path)
    paragraphs = parse_docx_logic(docx_path, styles)
    sections = parse_docx_layout(docx_path)
    tables = parse_docx_tables(docx_path, paragraphs)
    footnotes = parse_docx_footnotes(docx_path, styles)
    pdf_pages = parse_pdf_pages(pdf_path)

    context = CheckContext(
        docx_path=docx_path,
        pdf_path=pdf_path,
        registry=registry,
        selected_rules=selected_rules,
        styles=styles,
        paragraphs=paragraphs,
        sections=sections,
        tables=tables,
        footnotes=footnotes,
        pdf_pages=pdf_pages,
    )

    _save_json(output_path / f"styles{artifact_suffix}.json", styles)
    _save_json(output_path / f"docx_logic{artifact_suffix}.json", paragraphs)
    _save_json(output_path / f"docx_layout{artifact_suffix}.json", sections)
    _save_json(output_path / f"docx_tables{artifact_suffix}.json", tables)
    _save_json(output_path / f"docx_footnotes{artifact_suffix}.json", footnotes)
    _save_json(output_path / f"pdf_pages{artifact_suffix}.json", pdf_pages)

    results = []
    artifacts = {}
    for rule in selected_rules:
        checker = RULE_CHECKERS.get(rule["rule_id"])
        if checker is None:
            continue
        result = checker(rule, context)
        results.append(result)
        for name, payload in result.artifacts.items():
            artifacts[name] = payload

    _save_json(output_path / analysis_name, [result.__dict__ for result in results])
    for name, payload in artifacts.items():
        _save_json(output_path / f"{name}{artifact_suffix}.json", payload)

    report = build_report(docx_path, pdf_path, selected_rules, results)
    (output_path / report_name).write_text(report, encoding="utf-8")

    print(f"{print_prefix} report: {(output_path / report_name).resolve()}")
    print(f"{print_prefix} analysis: {(output_path / analysis_name).resolve()}")
    for name in sorted(artifacts):
        print(f"{print_prefix} {name}: {(output_path / f'{name}{artifact_suffix}.json').resolve()}")
    return context, results


def main() -> None:
    parser = argparse.ArgumentParser(description="Guide-driven thesis checker")
    parser.add_argument("--docx", help="Path to thesis DOCX")
    parser.add_argument("--pdf", help="Path to thesis PDF")
    parser.add_argument("--output-dir", help="Directory for outputs")
    parser.add_argument("--artifact-suffix", default="", help="Suffix inserted before .json artifacts")
    parser.add_argument("--analysis-name", default="analysis.json", help="Analysis JSON filename")
    parser.add_argument("--report-name", default="report.md", help="Markdown report filename")
    parser.add_argument("--rule-id", action="append", help="Run only the specified rule id; may be repeated")
    args = parser.parse_args()

    run_checker(
        docx=args.docx,
        pdf=args.pdf,
        output_dir=args.output_dir,
        artifact_suffix=args.artifact_suffix,
        analysis_name=args.analysis_name,
        report_name=args.report_name,
        rule_ids=args.rule_id,
    )


if __name__ == "__main__":
    main()
