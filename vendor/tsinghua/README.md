# Tsinghua University Thesis Format Checker Skill

[简体中文](./README.zh-CN.md)

A reusable Codex skill and Python workflow for reviewing **Tsinghua University graduate thesis formatting**.

This repository packages a rule-based checker plus a second-stage review workflow. It is designed for cases where pure text extraction is not enough: some rules can be judged automatically from DOCX/PDF structure, while others still require **visual PDF inspection** and **human or subagent judgment**.

## What This Project Does

The workflow is split into three layers:

1. **Automated script checking**
   Extracts evidence from DOCX and PDF, runs implemented rules, and generates machine-readable and Markdown reports.
2. **Script + SOP review**
   Uses prefilled evidence from scripts, then asks the reviewer or subagents to confirm layout-sensitive rules by reading the rendered PDF.
3. **Pure SOP review**
   Handles rules that cannot be judged reliably by scripts alone, such as bilingual abstract correspondence.

In practice, this makes the project useful for:

- pre-defense format review
- advisor or student self-check
- structured thesis QA before final PDF submission
- building review reply materials with traceable locations

## Key Features

- Checks **DOCX text**, **DOCX XML metadata**, **PDF text**, and **PDF visual layout** as parallel evidence sources.
- Implements **48 automated rules** in code.
- Organizes the remaining **8 rules** into a second-stage manual workflow.
- Generates location-aware findings with:
  - DOCX paragraph ids
  - PDF page numbers
  - leading text snippets for easier manual positioning
- Supports **Codex subagents** for parallel SOP review.
- Produces a consolidated final report after manual review results are written back.

## Repository Layout

- `SKILL.md`
  Codex skill entry point.
- `agents/openai.yaml`
  Skill metadata for UI integration.
- `scripts/`
  Wrapper scripts for running the workflow.
- `references/`
  Workflow notes, required files, and rule mapping.
- `guide_checker/`
  Core checker implementation.
- `tsinghua_p0_p1_rules.json`
  Active rule registry used by the checker.

## Requirements

- Python 3.10+
- `lxml`
- `PyMuPDF`

Install dependencies:

```bash
pip install -e .
```

## Quick Start

Run the full workflow directly:

```bash
python -X utf8 -m guide_checker.cli.run_full_review \
  --docx /path/to/thesis.docx \
  --pdf /path/to/thesis.pdf
```

Or use the wrapper script:

```bash
python scripts/start_review.py \
  --docx /path/to/thesis.docx \
  --pdf /path/to/thesis.pdf
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_review.ps1 `
  -Docx "D:\path\to\thesis.docx" `
  -Pdf "D:\path\to\thesis.pdf"
```

If only one DOCX and one PDF are present in the repository root, the checker can also auto-detect them. If multiple candidates exist, pass paths explicitly.

## Outputs

The full workflow writes artifacts under `guide_checker/output/`.

Core outputs:

- `report.md`
- `analysis.json`
- `manual_review_inventory.json`
- `manual_review_results.template.json`
- `manual_review_results.json`
- `script_sop_checklist.md`
- `pure_sop_checklist.md`
- `full_review_report.md`

These files serve different purposes:

- `report.md`
  Automated findings only.
- `manual_review_inventory.json`
  The authoritative split of second-stage rules for the current run.
- `manual_review_results.json`
  The editable file where manual review conclusions are stored.
- `full_review_report.md`
  The merged final report after automatic and manual review.

## Review Workflow

Recommended sequence:

1. Run `run_full_review`.
2. Read `script_sop_checklist.md` and `pure_sop_checklist.md`.
3. Review the remaining rules with subagents and PDF visual inspection.
4. Write conclusions into `manual_review_results.json`.
5. Run `run_full_review` again to refresh `full_review_report.md`.

Current second-stage split:

- **PDF visual review**
  `REFSEC-02`, `FIG-03`, `TAB-01`
- **Terminology and abstract-form review**
  `G-06`, `WR-04`
- **Structure and writing review**
  `WR-05`, `WR-07`
- **Bilingual abstract correspondence**
  `ABS-07`

## Codex Skill Usage

Invoke the skill in Codex with:

```text
Use $tsinghua-thesis-format-checker-skill to run the thesis review workflow and refresh the report.
```

The intended Codex pattern is:

- run automatic analysis first
- generate second-stage review checklists
- spawn subagents for PDF visual and SOP checks
- write results back into `manual_review_results.json`
- regenerate the merged review report

## What Is Automated vs. What Is Not

This repository is intentionally not a "one-shot full automation" tool.

Automated rules work well for:

- document structure
- headings and styles
- page numbering patterns
- bibliography structure cues
- units, equations, footnotes, and table text style

Manual or subagent-assisted review is still needed for:

- figure placement quality
- whether a table is truly acceptable as a three-line table
- whether a reference visibly breaks across pages
- whether new abbreviations are explained well enough
- whether the Chinese and English abstracts are semantically aligned

That hybrid design is deliberate: for thesis review, false certainty is worse than explicitly requiring manual confirmation.

## Privacy and Data Handling

This repository is meant to be open-sourced **without** bundling real thesis files.

Do **not** commit:

- real thesis DOCX files
- final thesis PDFs
- generated review outputs
- screenshots
- personal information
- committee names, student CVs, or unpublished academic results

The included `.gitignore` blocks common local artifacts, but privacy review is still your responsibility before each push.

## Scope and Limitations

- The rule registry is tailored to **Tsinghua University graduate thesis formatting**.
- Some rules assume the conventions of the corresponding writing guide and may not generalize to other schools.
- PDF visual review is still required for layout-sensitive rules.
- This repository does not include sample thesis files because privacy-safe public samples were intentionally excluded.

## Package Entry Points

After installation, these CLI entry points are available:

- `tsinghua-thesis-check`
- `tsinghua-thesis-full-review`

Examples:

```bash
tsinghua-thesis-check --docx /path/to/thesis.docx --pdf /path/to/thesis.pdf
tsinghua-thesis-full-review --docx /path/to/thesis.docx --pdf /path/to/thesis.pdf
```

## License

Released under the MIT License. See [LICENSE](LICENSE).
