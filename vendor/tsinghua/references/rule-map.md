# Rule Map

## Auto rules

The auto checker is implemented under `guide_checker/rules/` and currently covers 48 rules.

## Manual rules

The remaining 8 rules are handled by the second-stage review workflow.

### Script + SOP

- `REFSEC-02`
- `FIG-03`
- `TAB-01`
- `G-06`
- `WR-04`
- `WR-05`
- `WR-07`

### Pure SOP

- `ABS-07`

## Source of truth

- The generated `guide_checker/output/manual_review_inventory.json` is the authoritative split for the current run.
- If the registry or thesis file changes, re-run `python -X utf8 -m guide_checker.cli.run_full_review` to refresh the inventory.
