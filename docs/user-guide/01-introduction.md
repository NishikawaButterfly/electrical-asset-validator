# 1. Introduction

[Manual index](README.md) · [Next: Supported input files →](02-input-files.md)

## The problem this solves

An asset register arrives at the end of a job. It is a spreadsheet, it has a few
hundred rows, and somebody has to sign that it is fit to hand to the operations
team. The faults that matter are not visible by reading: a tag that appears twice
three hundred rows apart, a rated power left blank in one cell, a load whose
supply panel was renamed in a later revision and never updated, a status column
where four people used four different spellings.

Finding those by eye takes a day and misses things. This software finds them in
one pass and writes down what it found, so the finding list becomes an artefact
you can attach to the handover rather than a conversation you half remember.

## What one run gives you

1. **A quality score** out of 100 — a single number to put in a status report.
   Chapter [7](07-quality-score.md) explains what it does and does not mean.
2. **A finding list** — one line per problem, each with the source row, the
   field, a severity, and where possible a suggested corrected value.
3. **Two exports** — a PDF for the meeting, an Excel workbook for the person
   doing the corrections.

A second mode compares two revisions of the same register and reports which
assets were added, which were removed, and which changed field by field.

## Vocabulary

The manual uses these words consistently. So does the software.

| Term | Meaning here |
|------|--------------|
| **Register** | The whole file. One upload, one register. |
| **Asset** | One row. One piece of equipment. |
| **Asset tag** | The identifier in the `asset_tag` column, such as `MTR-001`. This is the software's idea of identity: it is how duplicates are detected and how revisions are matched. |
| **Canonical field** | One of the nine columns the software understands. Listed in chapter [2](02-input-files.md). |
| **Finding** (or **issue**) | One reported problem. Has a rule, a severity, a row, a field, and a message. |
| **Rule** | The named check that produced a finding, such as `DUPLICATE_ASSET_TAG`. Chapter [9](09-rule-reference.md) documents every one. |
| **Severity** | `error`, `warning`, or `info`. Chapter [8](08-errors-and-warnings.md). |
| **Validation** | One run over one file. Gets an identifier, is stored, and can be reopened and exported. |
| **Comparison** | One run over two files. Gets an identifier and is stored, but cannot be exported. |
| **Panel asset** | A row whose `asset_type` contains `panel`, `switchboard`, or `distribution board`. Several rules treat these differently — see chapter [9](09-rule-reference.md). |

## What it does not do

Being clear about this early saves an argument later.

- **It is not an engineering check.** No protection coordination, no cable
  sizing, no discrimination study, no code compliance. A register can score 100
  and describe an installation that would fail an inspection.
- **It has no opinion about your equipment.** `asset_type` is free text. The
  software does not know that a `motor` should have a `power_kw` above zero or
  that a `ups` belongs on an essential board.
- **It does not edit your file.** Every correction is made by you, in your own
  spreadsheet, and then uploaded again. There is no in-place editing, no "apply
  all suggestions", and no way to download a corrected register. See chapter
  [11](11-correcting-and-revalidating.md).
- **It does not remember users.** There are no accounts, no names against a
  run, and no approval workflow. Chapter [17](17-authentication.md) explains what
  access control does exist.
- **It does not detect renames.** If an asset tag changes between revisions, the
  comparison reports one removal and one addition. Chapter
  [13](13-added-removed-modified.md) shows exactly what that looks like.

## The shape of a session

A typical first use, start to finish:

1. Export the register from wherever it lives, as CSV or XLSX
   (chapter [3](03-preparing-a-register.md)).
2. Open the web page and select the file (chapter [4](04-uploading.md)).
3. If the headers are not the canonical names, map them
   (chapter [5](05-column-mapping.md)).
4. Run the validation and read the score and counts
   (chapter [6](06-running-a-validation.md)).
5. Work through the findings, filtering to errors first
   (chapter [10](10-reading-findings.md)).
6. Correct the source file and upload it again
   (chapter [11](11-correcting-and-revalidating.md)).
7. Compare it with the previously issued revision
   (chapter [12](12-comparing-revisions.md)).
8. Export the PDF and the Excel workbook
   (chapters [14](14-pdf-report.md) and [15](15-xlsx-report.md)).

Chapter [21](21-handover-example.md) runs that sequence on a real file with real
output at every step.

---

[Manual index](README.md) · [Next: Supported input files →](02-input-files.md)
