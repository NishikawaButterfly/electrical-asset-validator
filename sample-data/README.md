# Sample data

These fictional CSV files demonstrate both revision comparison and validation.
They contain no customer, site, or production data.

The application also accepts XLSX input. CSV fixtures are used here because
they are easy to inspect, diff, and reuse in command-line examples.

## Files

- `revision-a.csv` is a clean 15-asset baseline, including the referenced
  parent panels.
- `revision-b.csv` is a comparison-ready candidate with legitimate additions,
  removals, and field changes.
- `invalid-register.csv` contains deliberate data-quality failures for the
  validation workflow.

## Expected comparison highlights

When revision B is compared with revision A:

- `MTR-001` changes `power_kw` from `18.5` to `22.0`.
- `MTR-002` changes from `standby` to `active`.
- `DB-001` changes `voltage_v` from `400` to `415`.
- `UPS-001` changes to `decommissioned`.
- `HTR-003` is removed.
- `MTR-009` is added.

## Expected validation highlights

`invalid-register.csv` intentionally includes:

- a negative power value for `LGT-101`;
- a missing `panel_tag` for `FAN-004`;
- a duplicate `asset_tag` (`FAN-004`);
- an invalid asset-tag format (`MTR 009`);
- a non-numeric `power_kw`;
- an unsupported status (`commissioning`);
- a missing required `asset_tag`.

It also demonstrates non-blocking review findings:

- `MTR-002` is located differently from its referenced panel;
- `MTR 009` references a panel that is not present;
- the unidentified spare motor is located differently from its panel;
- the similar `Plant Room A` and `Plant Room B` labels trigger a possible-typo
  review.

With the baseline rules, revisions A and B score 100 with no findings.
`invalid-register.csv` produces seven errors and five warnings; those counts
are useful smoke-check expectations for future rule-engine changes.

Use the files as a quick product tour:

1. Compare `revision-a.csv` with `revision-b.csv` and review the field-level
   changes.
2. Validate `invalid-register.csv` and inspect its blocking errors and review
   warnings.
3. Correct or remove invalid rows, then run validation again.

The exact rule identifiers and severity definitions are documented in
[`../docs/rules.md`](../docs/rules.md).
