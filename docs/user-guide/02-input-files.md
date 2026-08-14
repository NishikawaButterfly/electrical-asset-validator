# 2. Supported input files

[← Introduction](01-introduction.md) · [Manual index](README.md) · [Next: Preparing a register →](03-preparing-a-register.md)

## The two formats

Only `.csv` and `.xlsx` are accepted, judged by the filename extension. Anything
else is refused before it is read:

```
Only .csv and .xlsx files are supported.
```

That includes legacy `.xls`, OpenDocument `.ods`, PDF, and a CSV that somebody
saved as `register.txt`. Re-save it from your spreadsheet program as CSV or
modern Excel and try again.

**The same file produces the same result in either format.** There are no
format-specific rules. Choose CSV when you want something you can diff and
email; choose XLSX when the register lives in a workbook and exporting it would
lose formatting you care about.

## The nine canonical columns

Every register must contain all nine, and only these nine are read:

| Column | Required in every row | What it holds |
|--------|----------------------|---------------|
| `asset_tag` | yes | The stable identifier. `MTR-001`. Unique within the file. |
| `asset_name` | yes | The readable name. `Main Chilled Water Pump`. |
| `asset_type` | yes | Your own category. `motor`, `panel`, `ahu`, `lighting`. Free text. |
| `location` | yes | Where it is. `Plant Room A`. Free text. |
| `panel_tag` | no | The `asset_tag` of the panel that supplies it. |
| `circuit_ref` | no | The way out of that panel. `C01`. |
| `voltage_v` | yes | Volts, as a plain number. |
| `power_kw` | yes | Rated power in kilowatts, as a plain number. |
| `status` | yes | One of `active`, `standby`, `maintenance`, `decommissioned`. |

"Required in every row" means an empty cell produces an error. `panel_tag` and
`circuit_ref` are the exceptions: they may be empty, but leaving them empty on a
non-panel asset produces a warning. See chapter [9](09-rule-reference.md).

A column may be **missing from the file** — that is a different, worse problem.
A missing column makes every row untrusted and forces the quality score to zero.
Chapter [7](07-quality-score.md) explains why.

## What a well-formed register looks like

This is `sample-data/revision-a.csv`, abbreviated. It scores 100 with no
findings.

```csv
asset_tag,asset_name,asset_type,location,panel_tag,circuit_ref,voltage_v,power_kw,status
PNL-MCC-01,Motor Control Centre 1,panel,Plant Room A,,,400,0,active
PNL-LTG-01,Level 1 Lighting Panel,panel,Level 1 North,,,230,0,active
MTR-001,Main Chilled Water Pump,motor,Plant Room A,PNL-MCC-01,C01,400,18.5,active
LGT-101,North Office Lighting,lighting,Level 1 North,PNL-LTG-01,C08,230,2.4,active
```

Four things make it well formed, and each is worth copying:

1. **The panels are in the file.** `PNL-MCC-01` is a row, not just a value in
   somebody else's `panel_tag`. A register that lists loads but not their boards
   produces a warning on every load.
2. **Panels carry `power_kw` of `0`** and no `panel_tag` or `circuit_ref` of
   their own. Zero is a legal power; it is negative power that is rejected.
3. **Every load's `location` matches its panel's `location`.** Where they
   genuinely differ you get a warning, not an error — see
   `PANEL_LOCATION_MISMATCH` in chapter [9](09-rule-reference.md).
4. **`status` is lower case and from the list of four.** `Active` is accepted
   with a warning; `in service` is an error.

## Header matching

You do not have to type the canonical names exactly. Before matching, each
header is trimmed, lower-cased, and has runs of spaces and hyphens turned into
single underscores. All of these match `asset_tag`:

```
asset_tag    Asset Tag    ASSET-TAG    asset tag    "  Asset  Tag  "
```

This file was accepted with no findings at all, because all nine headers
normalize onto canonical names:

```csv
Asset Tag,ASSET-NAME, asset_type ,Location,Panel Tag,Circuit-Ref,Voltage V,POWER KW,Status
```

What does **not** match is anything with extra characters that survive
normalization. `Voltage (V)` becomes `voltage_(v)`, which is not `voltage_v`;
`Tag` stays `tag`, which is not `asset_tag`. Those need the column mapping in
chapter [5](05-column-mapping.md).

Two headers that normalize to the same name are a hard refusal, because the
software cannot know which one you meant:

```
Duplicate columns after normalization: asset_tag.
```

A blank header is refused for the same reason:

```
Column names cannot be blank.
```

## Extra columns are fine

Columns outside the nine are kept out of the way and reported once each as
information. A register with `commissioning_date` and `notes` alongside the nine
canonical columns validated with a score of **100** and these two findings:

```
info  UNEXPECTED_COLUMN  Column 'commissioning_date' is not part of the canonical schema.
info  UNEXPECTED_COLUMN  Column 'notes' is not part of the canonical schema.
```

Information findings never reduce the score. You do not need to strip your extra
columns before uploading, and nothing in the exports will contain them either —
see chapter [15](15-xlsx-report.md).

## CSV specifics

- **UTF-8 only.** A file saved as Windows-1252 or ISO-8859-1 is refused as soon
  as a non-ASCII character appears:

  ```
  CSV files must use UTF-8 encoding.
  ```

  A register containing `Sala Eléctrica` saved from a European Excel will hit
  this. Chapter [20](20-troubleshooting.md) explains how to re-save it.

- **A byte-order mark is fine.** "CSV UTF-8" from Excel writes one, and it is
  stripped silently. That file validated with no findings.

- **Commas, not semicolons.** The delimiter is not detected. A
  semicolon-delimited file is read as a single column, so all nine canonical
  columns are reported missing and the score is zero. This is the most common
  first-upload failure in Europe; chapter [20](20-troubleshooting.md) has the
  fix.

- **Quote fields containing commas** in the ordinary way (`"Pump, spare"`).

- **Blank lines are skipped**, and the row numbers in findings still refer to
  the real line in your file. A register with two blank lines between its data
  rows validated as two rows with no findings.

- **Every row must have exactly as many fields as the header.** A short or long
  row is a hard refusal that names the row:

  ```
  CSV row 3 has 3 fields; the header has 9.
  ```

## XLSX specifics

- **Only the first worksheet is read.** A workbook whose first sheet was the
  register and whose second and third sheets held notes and a legend validated
  as the two rows on sheet one; nothing on the other sheets was read, reported,
  or complained about. If your register is on sheet 3, move it to the front or
  save that sheet as CSV.

- **Formulas are read as their result.** A workbook whose `voltage_v` held
  `=200*2` and whose `power_kw` held `=11*2` validated as `400` and `22`, with a
  score of **100**. A register assembled by formula from a transformer schedule
  or a sum of circuits is read as the numbers an engineer sees on screen.

  The result is the one **your spreadsheet stored** when it last saved the
  file. This software does not calculate anything; it reads what Excel or
  LibreOffice already worked out. That distinction is the whole of the next
  point.

- **A workbook that has never been calculated is refused.** A file written by a
  script — openpyxl, pandas, a reporting tool — contains the formulas but no
  results, because nothing ever evaluated them. There is nothing to read, so
  the upload is refused rather than treated as a register full of empty cells:

  ```
  The XLSX workbook has 5 formulas with no stored result, the first in cell G2. Open it in Excel or LibreOffice and save it so the results are stored, or replace the formulas with their values, then upload it again.
  ```

  Opening the file and saving it is enough — that is what stores the results.
  The message names one cell so you can find the problem in a mixed file, where
  the wording is singular:

  ```
  The XLSX workbook has a formula in cell H4 with no stored result. Open it in Excel or LibreOffice and save it so the results are stored, or replace the formulas with their values, then upload it again.
  ```

  You will not see this from a file a person saved from a spreadsheet program.
  It appears when a register is generated and handed straight over.

- **A formula whose stored result is an error stays an error.** If the workbook
  saved `#DIV/0!` or `#REF!` for a cell, that is what is read, and the ordinary
  rules report it against the row — `'power_kw' must be a finite number.` The
  file is not refused, because the workbook did give an answer. It gave a bad
  one, and that belongs to the row.

- **Text that merely looks like a formula is left alone.** A cell formatted as
  text and containing `=200*2` is not a formula and is read as that string.

- **Date-formatted cells become ISO text.** A real date in `asset_tag` came back
  as `2026-03-01T00:00:00`, which then failed the tag format rule. Keep dates out
  of the nine canonical columns.

- **Data to the right of the header is a refusal**, not a silent truncation:

  ```
  XLSX row 2 contains data beyond the header columns.
  ```

  A stray value in an unlabelled column — a note somebody typed next to row 2 —
  will stop the upload.

- **A file with an `.xlsx` name that is not a workbook** is refused:

  ```
  The XLSX file is not a valid workbook archive.
  ```

## Size and shape limits

| Limit | Value | Message when exceeded |
|-------|-------|----------------------|
| File size | 10 MB by default | `Each file must be no larger than 10 MB.` |
| Data rows | 50,000 | `Files may contain no more than 50,000 data rows.` |
| Columns | 64 | `Files may contain no more than 64 columns.` |
| Characters in one cell | 32,767 | `A cell exceeds the maximum supported length of 32,767 characters.` |

The row limit counts non-empty rows, and 50,000 exactly is accepted — a file
with 50,000 data rows validated normally; 50,001 was refused. The file size
limit is set by whoever runs the installation; the public demo runs with **2 MB**,
not 10. Chapter [19](19-limits.md) lists every cap, including the ones specific
to XLSX archives, and what to do when a register is genuinely too big.

## Empty and headerless files

| The file | What happens |
|----------|--------------|
| Zero bytes | `The uploaded file is empty.` |
| Header row only, no data | `The uploaded file does not contain any data rows.` |
| Data with no header row | The first data row is taken as the header, and that row is then lost. What you get depends on what is in it: `Column names cannot be blank.` if any of its cells is empty, `Duplicate columns after normalization: ...` if two of them are the same, and otherwise nine `MISSING_COLUMN` errors, nine `UNEXPECTED_COLUMN` findings, and a score of **0.0**. |

There is no way to tell the software "this file has no header row". Add one.

---

[← Introduction](01-introduction.md) · [Manual index](README.md) · [Next: Preparing a register →](03-preparing-a-register.md)
