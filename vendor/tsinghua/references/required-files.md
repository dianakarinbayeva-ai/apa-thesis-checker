# Required Files

This skill wraps the existing thesis-review project instead of duplicating its logic.

## Inputs

- Thesis DOCX file
- Typeset thesis PDF file
- Tsinghua University thesis writing guide PDF

## Core Scripts

- `guide_checker/cli/run_checker.py`
- `guide_checker/cli/run_full_review.py`
- `guide_checker/core/manual_review.py`
- `guide_checker/reporters/review_workflow_reporter.py`
- `guide_checker/rules/*.py`
- `tsinghua_p0_p1_rules.json`

## Generated Artifacts

- `guide_checker/output/report.md`
- `guide_checker/output/analysis.json`
- `guide_checker/output/manual_review_inventory.json`
- `guide_checker/output/manual_review_results.template.json`
- `guide_checker/output/manual_review_results.json`
- `guide_checker/output/script_sop_checklist.md`
- `guide_checker/output/pure_sop_checklist.md`
- `guide_checker/output/full_review_report.md`

## Editable Result File

- `guide_checker/output/manual_review_results.json`

## Visual Review Assets

- `guide_checker/output/pdf_review_images/*.png`
- `guide_checker/output/review_images/*.png`
