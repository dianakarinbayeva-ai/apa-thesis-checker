from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from guide_checker.cli.run_checker import run_checker
from guide_checker.core.manual_review import build_manual_review_payload, merge_manual_review_payload
from guide_checker.core.registry import ensure_dir
from guide_checker.reporters.review_workflow_reporter import build_full_review_report, build_manual_checklist


sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


def _save_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run full thesis review workflow")
    parser.add_argument("--docx", help="Path to thesis DOCX")
    parser.add_argument("--pdf", help="Path to thesis PDF")
    parser.add_argument("--output-dir", help="Directory for outputs")
    args = parser.parse_args()

    output_dir = Path(args.output_dir) if args.output_dir else Path("guide_checker/output")
    ensure_dir(output_dir)

    context, auto_results = run_checker(
        docx=args.docx,
        pdf=args.pdf,
        output_dir=output_dir,
        analysis_name="analysis.json",
        report_name="report.md",
        print_prefix="[full-review:auto]",
    )

    template_payload = build_manual_review_payload(context, context.registry, auto_results)
    template_path = output_dir / "manual_review_results.template.json"
    results_path = output_dir / "manual_review_results.json"

    existing_payload = None
    if results_path.exists():
        existing_payload = json.loads(results_path.read_text(encoding="utf-8"))

    merged_payload = merge_manual_review_payload(template_payload, existing_payload)
    inventory_payload = {
        "meta": merged_payload["meta"],
        "rules": [
            {
                "rule_id": item["rule_id"],
                "title": item["title"],
                "priority": item["priority"],
                "automation": item["automation"],
                "review_mode": item["review_mode"],
                "review_mode_label": item["review_mode_label"],
                "source_section": item["source_section"],
                "source_pages": item["source_pages"],
                "requirement_summary": item["requirement_summary"],
                "classification_reason": item["classification_reason"],
                "sop_refs": item["sop_refs"],
            }
            for item in merged_payload["rules"]
        ],
    }

    _save_json(template_path, template_payload)
    _save_json(output_dir / "manual_review_inventory.json", inventory_payload)
    _save_json(results_path, merged_payload)

    script_md = build_manual_checklist(merged_payload, "script_plus_sop")
    pure_md = build_manual_checklist(merged_payload, "pure_sop")
    (output_dir / "script_sop_checklist.md").write_text(script_md, encoding="utf-8")
    (output_dir / "pure_sop_checklist.md").write_text(pure_md, encoding="utf-8")

    full_report = build_full_review_report(
        docx_path=context.docx_path,
        pdf_path=context.pdf_path,
        auto_results=auto_results,
        manual_payload=merged_payload,
        auto_report_name="report.md",
    )
    full_report_path = output_dir / "full_review_report.md"
    full_report_path.write_text(full_report, encoding="utf-8")

    print(f"[full-review] manual inventory: {output_dir.resolve() / 'manual_review_inventory.json'}")
    print(f"[full-review] manual template: {template_path.resolve()}")
    print(f"[full-review] manual results: {results_path.resolve()}")
    print(f"[full-review] script+sop checklist: {(output_dir / 'script_sop_checklist.md').resolve()}")
    print(f"[full-review] pure sop checklist: {(output_dir / 'pure_sop_checklist.md').resolve()}")
    print(f"[full-review] full report: {full_report_path.resolve()}")


if __name__ == "__main__":
    main()
