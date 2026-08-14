# Validation rules

The validator treats each CSV row or XLSX data row as one electrical asset.
Validation is deterministic: the same file and rule version produce the same
findings.
Findings identify the source row, field, severity, rule, and a human-readable
message so users can correct the source register.

This baseline rule catalogue detects data-quality problems. It is not a
substitute for an electrical design review, protective-device study, site
inspection, or compliance assessment against local regulations.

## Severity model

| Severity | Meaning | Effect |
| --- | --- | --- |
| `error` | The row cannot be trusted or compared safely. | Blocks a clean validation result. |
| `warning` | The row is parseable but deserves engineering review. | Does not block processing. |
| `info` | A useful observation about the file or comparison. | Informational only. |

The quality score applies weighted penalties for errors and warnings relative
to the number of data rows. Informational findings do not reduce the score. A
missing canonical column is a structural error: all rows become untrusted and
the score is set to zero.

## File acceptance

Empty, unreadable, or structurally ambiguous files—including files with
duplicate headers—are rejected with an HTTP `400` response. They do not create
a persisted validation result because the service cannot establish a reliable
row and column model.

The service accepts at most 50,000 non-empty rows, 64 columns, and 32,767
characters per cell. XLSX input is additionally limited to 2,000 archive
entries, 100 MiB expanded size, a bounded compression ratio, and a used range
that does not extend beyond source row 250,000. These are product-safety
limits, not spreadsheet-format maxima.

An XLSX formula cell contributes the result the authoring application stored
for it; the service evaluates nothing. A workbook that stores no result for a
formula—one written programmatically and never opened by a spreadsheet
application—cannot be given a reliable cell model and is rejected with an HTTP
`400` naming the count and the first such cell. A stored error value such as
`#DIV/0!` is a result, and reaches the rules as an invalid number on its row.

Files that can be parsed produce findings with stable `rule` values. The
severity returned by the API is authoritative.

| Rule | Severity | Condition |
| --- | --- | --- |
| `MISSING_COLUMN` | error | One or more required contract columns are absent after header normalization. |
| `UNEXPECTED_COLUMN` | info | The file contains a column outside the canonical contract. |
| `DUPLICATE_ASSET_TAG` | error | The same trimmed, case-insensitive `asset_tag` occurs more than once. |
| `FINDING_LIMIT_REACHED` | warning | The bounded result reached 10,000 returned details; metrics still count every detected finding, and listed corrections should be applied before revalidation. |

## Field-level rules

Whitespace surrounding text is ignored during validation. Empty strings count
as missing values.

| Rule | Field or scope | Severity | Condition |
| --- | --- | --- | --- |
| `REQUIRED_FIELD` | core fields | error | A required asset tag, name, type, location, voltage, power, or status is missing. |
| `ASSET_TAG_LENGTH` | `asset_tag` | error | The asset tag exceeds 128 characters and cannot be used as a stable comparison identity. |
| `ASSET_TAG_FORMAT` | `asset_tag`, `panel_tag` | error for an asset tag; warning for a panel reference | The value does not start with an uppercase letter or contain valid uppercase letter/digit groups separated by single hyphens. |
| `NAMING_NORMALIZATION` | identifiers | warning | An identifier is usable but does not follow the recommended normalized naming convention. |
| `POSSIBLE_TYPO` | text identifiers | warning | A value is suspiciously similar to another identifier and may be a typo. |
| `INVALID_NUMBER` | `voltage_v`, `power_kw` | error | The value is not a finite decimal number. |
| `VALUE_OUT_OF_RANGE` | `voltage_v`, `power_kw` | error | Voltage is not greater than 0 and at most 1,000,000, or power is not between 0 and 1,000,000 inclusive. |
| `INVALID_STATUS` | `status` | error | The value is not one of the supported lifecycle states. |
| `MISSING_PANEL_REFERENCE` | `panel_tag` | warning | A non-panel asset has no upstream panel reference. |
| `MISSING_CIRCUIT_REFERENCE` | `circuit_ref` | warning | A non-panel asset has no circuit or feeder reference. |
| `UNKNOWN_PANEL_REFERENCE` | `panel_tag` | warning | The referenced panel tag does not exist in the same register. |
| `INVALID_PANEL_REFERENCE` | `panel_tag` | warning | The referenced row exists but is not a valid panel-like parent. |
| `PANEL_LOCATION_MISMATCH` | `panel_tag`, `location` | warning | A parent/child location relationship is inconsistent and should be reviewed. |
| `DUPLICATE_CIRCUIT_REFERENCE` | `panel_tag`, `circuit_ref` | warning | More than one asset claims the same panel and circuit combination. |
| `CIRCUIT_REFERENCE_FORMAT` | `circuit_ref` | warning | The circuit reference does not follow the accepted format. |

The accepted statuses are:

- `active`
- `standby`
- `maintenance`
- `decommissioned`

`asset_type` is required but intentionally remains an organization-defined
string in the MVP. Panel-like assets are exempt from parent `panel_tag` and
`circuit_ref` values. A controlled taxonomy can be added without changing the
tabular contract.

## Comparison rules

`asset_tag` is the stable identity used to match rows across revisions:

- a tag present only in the candidate revision is **added**;
- a tag present only in the baseline revision is **removed**;
- a matched tag with one or more changed fields is **modified**;
- a matched tag with identical normalized values is **unchanged**.

Invalid or duplicate tags cannot be matched reliably and must be corrected
before a comparison is considered clean. Changing an asset tag is represented
as one removal and one addition, not a rename.

A comparison is rejected when it would return or persist more than 10,000
combined added, removed, or field-level change details. Segment larger
revisions or use a future asynchronous workflow.

## Input authoring guidance

- Use UTF-8 for CSV input; XLSX is also accepted.
- Include all nine contract columns in the input table.
- Use canonical snake-case headers. Matching tolerates case, surrounding
  whitespace, spaces, and hyphens, but canonical names keep exports portable.
- Preserve `asset_tag` across revisions.
- Use a period as the decimal separator and do not include unit suffixes.
- Express voltage in volts and rated power in kilowatts.
- In CSV files, quote text containing commas according to RFC 4180.
- XLSX formulas are supported, provided the workbook has been saved by a
  spreadsheet application so that its results are stored. Issued revisions are
  better held as values.
- Do not place macros or sensitive free-form notes in the register.

See [`../sample-data/README.md`](../sample-data/README.md) for a reproducible
example containing both valid records and intentional failures.
