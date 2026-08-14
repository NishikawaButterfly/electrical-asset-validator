# 3. Preparing a register

[← Supported input files](02-input-files.md) · [Manual index](README.md) · [Next: Uploading a file →](04-uploading.md)

You can upload a register straight out of a contractor's email and read the
findings. This chapter is about the ten minutes of preparation that stop you
reading three hundred findings that all describe the same clerical accident.

## Before you upload

1. **Get it into one sheet.** Only the first worksheet of a workbook is read.
   If the register is on the third tab behind a cover sheet and a legend, move it
   to the front or save that sheet on its own.

2. **Turn formulas into values.** Select the data, copy, and paste-special as
   values. A cell holding `=Design!G14` is read as that text, not as `400`, and
   produces `'voltage_v' must be a finite number.` on every row that has one. This
   is the single most damaging preparation mistake, because it can turn a clean
   register into a wall of errors.

3. **Remove merged cells, subtotal rows, and blank spacer columns.** A merged
   header cell leaves a blank column name, which is refused outright. A note
   typed in an unlabelled column to the right of the data stops an XLSX upload
   with `XLSX row 2 contains data beyond the header columns.`

4. **Check the panels are in the file.** This is the correction that removes the
   most warnings for the least work. If your register lists loads only, every
   load with a `panel_tag` produces `Panel 'PNL-C-ROOF' is not present in this
   register.` Add the boards as rows in their own right, with `power_kw` of `0`
   and their own `panel_tag` and `circuit_ref` left empty.

5. **Agree one spelling for each `asset_type` and `location`,** before you
   distribute the file rather than after. `motor` and `Motor` in the same column
   produce a warning on the minority spelling, and `Plant Roon A` next to
   `Plant Room A` produces a possible-typo warning. Neither blocks anything, but
   both cost score.

6. **Strip units and thousands separators from the numbers.** `voltage_v` wants
   `400`, not `400 V` or `0.4 kV`. `power_kw` wants `18.5`, not `18,5` or
   `18.5 kW`. Use a period as the decimal separator; a comma is not recognised and
   in a CSV will also break the field count.

7. **Save as UTF-8.** In Excel, "CSV UTF-8 (Comma delimited)". The ordinary
   "CSV (Comma delimited)" option writes your system code page, and any accented
   character in it will be refused.

## What the software normalizes for you

You do not need to spend effort on any of these.

| You wrote | How it is read |
|-----------|----------------|
| `  Plant Room A  ` | `Plant Room A` — leading and trailing whitespace is removed everywhere |
| `Asset Tag`, `ASSET-TAG` | `asset_tag` — headers are matched case- and separator-insensitively |
| `22.0` | `22` — a whole number written with a decimal is stored as a whole number |
| `18.50` | `18.5` |
| A UTF-8 byte-order mark | Stripped |
| Blank lines between rows | Skipped, without shifting the row numbers in findings |

That last row matters for the exports: the row number in every finding is the
line number in **your** file, so you can go straight to it.

What is *not* normalized away, and will be reported: repeated spaces inside a
value (`Pump  1`), an upper-case status (`Active`), a lower-case asset tag
(`mtr-007`), and a lower-case circuit reference (`c04`).

## Getting the panel hierarchy right

Several rules exist only to check that loads point at real boards. They all
depend on one thing: the software decides a row is a panel by looking for
`panel`, `switchboard`, `distribution board`, or `distribution_board` anywhere
in its `asset_type`, case-insensitively.

That means:

- `panel`, `Panel`, `distribution_board`, `MV switchboard`, and
  `lighting panel` are all panel assets.
- `board`, `db`, `mcc`, and `switchgear` are **not**. A register that types its
  boards `MCC` will have every load report `Referenced asset 'PNL-MCC-01' is not
  classified as a panel.`

If your naming convention does not contain one of those four words, either add
it to `asset_type` before uploading, or accept a warning on every load. There is
no setting for this.

Panel assets are exempt from needing a `panel_tag` and `circuit_ref` of their
own, which is why a top-level switchboard with both cells empty produces no
findings. Assets with `status` of `decommissioned` are exempt too.

## A worked before-and-after

`sample-data/case-study/register-as-received.csv` is what an unprepared handover
file looks like. Its header row is

```csv
Tag,Asset Name,Asset Type,Location,Panel,Circuit Ref,Voltage (V),Power (kW),Status
```

and four of those nine headers do not match anything. Uploaded as it is, with no
mapping, it scores **0.0**: four `MISSING_COLUMN` errors take the whole file
down, and 22 rows then report 72 errors and 19 warnings between them, because
`asset_tag`, `panel_tag`, `voltage_v`, and `power_kw` all look empty.

Nothing is wrong with the data. Ninety-five findings are an artefact of four
column headings.

You have two ways out, and both are legitimate:

- **Rename the headers in your copy of the file** to the nine canonical names,
  and upload it. Nothing to configure, and the file stays self-describing.
- **Map the headers at upload time** and leave the source file untouched. This
  is the right choice when the register is reissued in the same format every
  month, or when you are not the file's owner. Chapter
  [5](05-column-mapping.md) does exactly this, and the same file then scores
  **72.7** with 10 real findings.

## What to keep out of a register

- **Formulas and macros.** Beyond the reading problem above, a register is
  evidence; it should not compute.
- **Free-text commentary in the canonical columns.** Put site notes in an extra
  column — extra columns are reported once as information and otherwise ignored.
- **Anything you would not want stored.** Uploaded rows are kept in the server's
  database and appear in the Excel export. Chapter
  [18](18-privacy-and-retention.md) is specific about what that means.

---

[← Supported input files](02-input-files.md) · [Manual index](README.md) · [Next: Uploading a file →](04-uploading.md)
