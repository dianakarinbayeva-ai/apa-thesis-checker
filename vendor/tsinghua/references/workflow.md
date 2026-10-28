# Workflow

## Canonical sequence

1. Run the full workflow once to generate the auto report and the manual-review template.
2. Read `script_sop_checklist.md` and `pure_sop_checklist.md`.
3. Use subagents for the remaining manual rules.
4. Fill `manual_review_results.json` without deleting prefilled evidence.
5. Run the full workflow again to regenerate `full_review_report.md`.

## Subagent Split

- `REFSEC-02`, `FIG-03`, `TAB-01`: PDF visual inspection.
- `G-06`, `WR-04`: terminology and abstract-form checks.
- `WR-05`, `WR-07`: introduction and conclusion structure checks.
- `ABS-07`: bilingual abstract semantic correspondence.

## Manual result fields

When updating a rule, keep these fields consistent:

- `status`
- `reviewer`
- `checked_at`
- `finding`
- `decision_reason`
- `follow_up`
- `confirmed_locations`

## Location formatting

Prefer human-readable locations:

- `DOCX 段落号 / PDF 页码 / 段首 5-10 字符`
- For visual issues, include the exact PDF page and the figure/table/reference number.

## Failure handling

- If a rule fails, do not leave the location vague.
- If a rule is only a soft issue, use `warning` instead of forcing `fail`.
- If the result is already present, preserve it unless a later review genuinely changes the judgment.
