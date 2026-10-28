---
name: tsinghua-thesis-format-checker-skill
description: Run the Tsinghua University thesis format review workflow: auto checker, script/SOP review, pure SOP review, subagent PDF checks, and final report synthesis.
---

# Tsinghua Thesis Format Checker Skill

Use this skill when the user wants to run or repeat the Tsinghua University graduate thesis format review workflow.

## Workflow

1. Run `scripts/start_review.py`, `scripts/start_review.ps1`, or `python -X utf8 -m guide_checker.cli.run_full_review`.
2. Inspect the generated outputs in `guide_checker/output/`.
3. For remaining rules, use subagents plus Chrome DevTools PDF visual review.
4. Write conclusions to `guide_checker/output/manual_review_results.json`.
5. Re-run the full review command to refresh `full_review_report.md`.

## Manual Review Split

- PDF visual: `REFSEC-02`, `FIG-03`, `TAB-01`
- Terminology: `G-06`, `WR-04`
- Structure: `WR-05`, `WR-07`
- Bilingual abstract: `ABS-07`

## Constraints

- Use UTF-8 everywhere.
- Do not overwrite unrelated files.
- If a rule fails, record both the DOCX paragraph location and the PDF page in `confirmed_locations`.
- Treat `manual_review_inventory.json` as the source of truth for the current split.

## References

- `references/required-files.md`
- `references/workflow.md`
- `references/rule-map.md`

## Script

- `scripts/start_review.py`
- `scripts/start_review.ps1`
