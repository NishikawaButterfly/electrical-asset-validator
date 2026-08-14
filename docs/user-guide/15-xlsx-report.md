# 15. The Excel report

[← The PDF report](14-pdf-report.md) · [Manual index](README.md) · [Next: Validation history →](16-validation-history.md)

## Downloading it

Click **Download Excel** on the validation result. The file arrives as
`<your file name>-validation-report.xlsx` — `invalid-register.csv` gives
`invalid-register-validation-report.xlsx`. Over the API it is named after the
run:

```bash
curl -O -J --cookie jar.txt \
  http://localhost:8000/api/v1/validations/<id>/report.xlsx
```

gives `validation-<id>.xlsx`.

This is the working document. Three sheets.

## Sheet 1: Summary

Two columns, `Metric` and `Value`, twelve rows. For the mapped case-study
register:

| Metric | Value |
|--------|-------|
| Validation ID | `b26a65a5-469f-49ce-bfb8-21675a200c34` |
| Source file | `register-as-received.csv` |
| Created at | `2026-08-14T15:05:51.933924Z` |
| Quality score | `72.7` |
| Total rows | `22` |
| Valid rows | `16` |
| Issues | `10` |
| Returned issue details | `10` |
| Issue details truncated | `False` |
| Errors | `6` |
| Warnings | `4` |
| Information | `0` |

Two of these need a word. **Created at** is UTC, in full ISO form with a
trailing `Z` — the only timestamp in either export, which is why this is the
better of the two for evidence (chapter [14](14-pdf-report.md)). **Issues**
against **Returned issue details** differ only when a result was truncated; if
**Issue details truncated** says `True`, the Issues sheet is incomplete and the
counts above it are not (chapter [19](19-limits.md)).

## Sheet 2: Issues

One row per finding, seven columns, in the same order as the screen:

| severity | rule | row | asset_tag | field | message | suggestion |
|----------|------|-----|-----------|-------|---------|------------|
| warning | NAMING_NORMALIZATION | 8 | PDU-B-01 | status | Use the canonical lowercase status value. | active |
| error | REQUIRED_FIELD | 9 | UPS-C-01 | status | 'status' is required. | |
| error | DUPLICATE_ASSET_TAG | 17 | FAN-C-02 | asset_tag | Asset tag 'FAN-C-02' occurs more than once. | |

The header row is frozen and an **auto-filter is already applied to every
column**, so the workbook opens ready to work with. This is where the export
earns its place over the screen:

- **Sort by `row`** to work through your register top to bottom, which the page
  cannot do.
- **Filter `severity` to `error`** to get the acceptance gate on its own.
- **Filter `rule`** to see how many findings come from one cause — the count the
  page never shows you.
- **Filter `asset_tag`** to collect everything wrong with one asset.

Messages are complete here; nothing is truncated the way the PDF truncates.

A clean validation still produces this sheet, with the header row and nothing
under it.

## Sheet 3: Data

The register as the software understood it: the nine canonical columns, one row
per data row, in file order.

| asset_tag | asset_name | asset_type | location | panel_tag | circuit_ref | voltage_v | power_kw | status |
|---|---|---|---|---|---|---|---|---|
| PNL-C-01 | Block C Main Switchboard | panel | Block C Switchroom | | | 400 | 0 | active |
| PDU-B-01 | Server Room PDU B | pdu | Block C Server Room | PNL-C-SVR | C02 | 230 | 8 | Active |

This sheet is what makes the finding list actionable. Put it beside the Issues
sheet and the row numbers line up with your source file, so
`'voltage_v' must be greater than 0` on row 21 can be checked against the `-230`
that caused it.

Three things about it are worth knowing:

- **It shows the data after mapping.** The `asset_tag` column above came from a
  source column headed `Tag`. This is the clearest way to confirm a mapping did
  what you meant.
- **It shows values as accepted, not as typed.** `8.0` in the source arrives as
  `8`; surrounding whitespace is gone. `Active` is still `Active`, because case
  is not normalized — only reported.
- **Extra columns are dropped.** A register with a `commissioning_date` column
  will not have it here. **This sheet is not a corrected copy of your register**;
  it is a record of what was validated. Make your corrections in the original
  file (chapter [11](11-correcting-and-revalidating.md)).

## Formula-looking values

A value that starts with `=`, `+`, `-`, or `@` — the characters a spreadsheet
treats as the start of a formula — is written as literal text and marked so Excel
displays it exactly as it was, rather than trying to evaluate it. A register
containing `=cmd|calc` as an asset name exports that string intact and inert.

You do not have to do anything about this. It is worth knowing because it means
opening a report from an untrusted register is safe, and because it explains why
such a cell shows a small warning marker in Excel.

## Formatting

Every sheet has a dark blue header row in white bold, frozen at row 1, with
auto-filter applied and column widths fitted to the content between 10 and 45
characters. Nothing is colour-coded by severity — filter the `severity` column
instead.

## What is not in it

- **No comparison data.** Comparisons have no export
  (chapter [12](12-comparing-revisions.md)).
- **No pivot tables, charts, or per-rule totals.** Build them yourself from the
  Issues sheet.
- **No software version**, for the same reason as the PDF.
- **No protection or signing.** The workbook is fully editable, so it is a
  working document, not a tamper-evident record. If you need the finding list to
  be fixed, attach the PDF as well.

---

[← The PDF report](14-pdf-report.md) · [Manual index](README.md) · [Next: Validation history →](16-validation-history.md)
