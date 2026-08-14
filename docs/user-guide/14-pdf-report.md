# 14. The PDF report

[← Added, removed, and modified assets](13-added-removed-modified.md) · [Manual index](README.md) · [Next: The Excel report →](15-xlsx-report.md)

## Downloading it

Click **Download PDF**, top right of the validation result. The button reads
**Preparing…** while the server builds it, then your browser downloads it as
`<your file name>-validation-report.pdf` — validating `invalid-register.csv`
gives `invalid-register-validation-report.pdf`.

A report can be produced at any time, including for a run you reopened from
history (chapter [16](16-validation-history.md)). It is generated fresh on each
download from the stored result, so the same run always produces the same
document.

Over the API the file is named after the run instead:

```bash
curl -O -J --cookie jar.txt \
  http://localhost:8000/api/v1/validations/<id>/report.pdf
```

gives `validation-<id>.pdf`.

## What is on page 1

Landscape A4. Top to bottom:

1. **The title** — `Electrical Asset Validation Report`.
2. **One identification line** — `Source: invalid-register.csv    Validation ID:
   0a0b7205-fa0b-44be-b575-9bcb44fb51af`.
3. **The summary table**, six columns across:

   | Quality score | Rows | Valid rows | Errors | Warnings | Information |
   |---|---|---|---|---|---|
   | 58.2 | 17 | 12 | 7 | 5 | 0 |

4. **A heading, `Findings`,** followed by one note:

   > Long values are truncated in this PDF for readability; the XLSX report
   > preserves the accepted source values.

5. **The findings table** — seven columns: Severity, Rule, Row, Asset tag, Field,
   Message, Suggestion. Every finding, in the same order as the screen
   (chapter [10](10-reading-findings.md)), one row each.

For `invalid-register.csv` the whole report is a single page.

## Subsequent pages

When the findings do not fit, the table continues onto further pages and **the
column headings repeat at the top of each one**, so a page pulled out of a bundle
is still readable. The title, summary, and note appear on page 1 only. A
validation with 150 findings produced an eight-page report.

## Truncation of long values

Any cell longer than 500 characters is cut and ends with an ellipsis. In
practice this affects only registers with very long asset names or tags. The note
under the Findings heading says so, and the Excel report
(chapter [15](15-xlsx-report.md)) keeps the full text.

## A clean register

The summary table is the same, and the findings table is replaced by one line:

> No issues were found.

`revision-a.csv` produces a two-paragraph, one-page PDF — which is exactly the
document you want to attach to a handover when the register is clean.

## What is not in it

Read this list before you rely on the PDF as evidence.

- **No date.** The report shows the source filename and the validation
  identifier, and nothing else about when it was produced. The creation date is
  in the file's PDF metadata, where nobody looks and no printout shows it. If the
  date matters — and on a handover it does — write it on the document, or attach
  the Excel report instead, whose Summary sheet carries a full UTC timestamp.
- **No page numbers.** An eight-page findings table has no "page 3 of 8"
  anywhere. Number the pages yourself before circulating a long one.
- **No register data.** The findings name the row and the field; they never show
  the offending value. `'voltage_v' must be greater than 0` does not tell the
  reader it said `-230`. To see the values, use the Excel report's Data sheet.
- **No software version.** Rules change between releases, so a finding list is
  only fully meaningful alongside the version that produced it. The version is
  available from `/api/v1/health`; it is not on the report.
- **No signature, approval, or sign-off block.**
- **Nothing about a comparison.** Comparisons have no export at all
  (chapter [12](12-comparing-revisions.md)).

## When to use the PDF rather than the Excel report

| Use the PDF | Use the Excel report |
|-------------|---------------------|
| Attaching a fixed record to a handover pack or a report | Doing the corrections |
| Circulating a result to people who will read, not edit | Sorting or filtering findings |
| A clean register — the one-page "no issues were found" is a good certificate | Anything over about fifty findings |
| Anywhere the finding list must not be silently editable | When you need the validated data alongside the findings |

For a register with hundreds of findings, the PDF is a long table nobody will
read. Attach the Excel report and quote the summary numbers in the covering note.

---

[← Added, removed, and modified assets](13-added-removed-modified.md) · [Manual index](README.md) · [Next: The Excel report →](15-xlsx-report.md)
