# Guide Checker

This package implements the rule-based checker used by the Tsinghua thesis format skill.

## Main Components

- `core/`: constants, registry loading, models, and manual-review helpers
- `extractors/`: DOCX and PDF parsers
- `rules/`: implemented automated rules
- `reporters/`: markdown report generation
- `cli/`: command-line entry points

## CLI

Run the automated checker:

```bash
python -X utf8 -m guide_checker.cli.run_checker --docx /path/to/thesis.docx --pdf /path/to/thesis.pdf
```

Run the full workflow:

```bash
python -X utf8 -m guide_checker.cli.run_full_review --docx /path/to/thesis.docx --pdf /path/to/thesis.pdf
```

## Outputs

The full workflow writes the following files into `guide_checker/output/`:

- `report.md`
- `analysis.json`
- `manual_review_inventory.json`
- `manual_review_results.template.json`
- `manual_review_results.json`
- `script_sop_checklist.md`
- `pure_sop_checklist.md`
- `full_review_report.md`

## Rule Coverage

- 48 rules are implemented in code
- 8 rules remain in the second-stage review workflow
