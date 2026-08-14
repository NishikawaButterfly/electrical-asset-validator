# 6. Running a validation

[← Mapping non-standard columns](05-column-mapping.md) · [Manual index](README.md) · [Next: The quality score →](07-quality-score.md)

## Running it

1. Select the register on the **Validate file** tab (chapter
   [4](04-uploading.md)).
2. Complete the mapping panel if one appeared (chapter
   [5](05-column-mapping.md)).
3. Click **Run validation**.

The page shows a progress banner, then replaces it with the result and scrolls
to it. Every rule runs on every row; there is no partial or quick mode, and no
way to switch a rule off.

Validation is deterministic. The same file, uploaded again to the same version,
produces the same score and the same findings in the same order. That is what
makes a report worth attaching to a handover.

## Reading the summary

Uploading `sample-data/invalid-register.csv` gives:

| Panel | Shows | For this file |
|-------|-------|---------------|
| Quality score | The score, out of 100, with a word | **58.2** — Needs attention |
| Rows checked | Data rows read, and how many are clean | **17**, `12 valid` |
| Errors | Findings that block (chapter [8](08-errors-and-warnings.md)) | **7** |
| Warnings | Findings that need judgement | **5** |
| Information | Observations that cost nothing | **0** |

Above them is the source filename and the completion time in your local time
zone; to the right, **Download Excel** and **Download PDF** (chapters
[15](15-xlsx-report.md) and [14](14-pdf-report.md)).

### Rows checked

The number of non-empty data rows read from the file. Blank lines in a CSV are
skipped and not counted, but they do not shift the row numbers reported in
findings — those are always the real line in your file.

### Valid rows

**Rows with no error on them.** A row with three errors and a row with one error
each count once against this number; a row with four warnings and no errors is
still valid.

For `invalid-register.csv`, 7 errors fall on 5 distinct rows — rows 12, 15, 16,
17, and 18 — so 17 − 5 = **12 valid rows**.

There is one special case. If the file is missing a canonical column, every row
is untrusted and valid rows becomes **0** regardless of what the rows contain.
The unmapped case-study register in chapter [5](05-column-mapping.md) reports 22
rows and 0 valid.

### The word next to the score

The page picks it from the score alone:

| Score | Word |
|-------|------|
| 90 and above | Excellent |
| 75 to 89.9 | Good |
| 50 to 74.9 | Needs attention |
| Below 50 | Action required |

It is a colour cue, not an assessment. A register with one error in 500 rows
scores well above 90 and reads "Excellent" while still containing a duplicate
tag that will break the next comparison. Read the error count, not the adjective.

## What a clean run looks like

`sample-data/revision-a.csv` gives:

- Quality score **100**, Excellent
- Rows checked **15**, `15 valid`
- Errors **0**, Warnings **0**, Information **0**
- The findings table is replaced by **No issues were reported**

A score of exactly 100 means the engine reported nothing at all: no errors, no
warnings, no information. Any finding of any kind caps the score at 99.9, so 100
is unambiguous.

## What the run created

One **validation** — a stored record holding the score, the counts, every
finding, and a copy of the nine canonical columns of every row. It has an
identifier, it appears at the top of **Recent validations**, and it can be
reopened later (chapter [16](16-validation-history.md)) and exported at any time.

It is scoped to your browser session. Nobody else sees it, including a colleague
looking at the same server. Chapter [18](18-privacy-and-retention.md) explains
the mechanism and its limits.

## The same run over the API

```bash
curl --fail-with-body --cookie-jar jar.txt --cookie jar.txt \
  -F "file=@sample-data/invalid-register.csv;type=text/csv" \
  http://localhost:8000/api/v1/validations
```

The response is HTTP 201 and the complete result:

```json
{
  "id": "0a0b7205-fa0b-44be-b575-9bcb44fb51af",
  "filename": "invalid-register.csv",
  "created_at": "2026-08-14T15:10:31.402816Z",
  "quality_score": 58.2,
  "metrics": {
    "total_rows": 17,
    "valid_rows": 12,
    "issue_count": 12,
    "returned_issue_count": 12,
    "issues_truncated": false,
    "error_count": 7,
    "warning_count": 5,
    "info_count": 0
  },
  "issues": [ ... ],
  "download_urls": {
    "excel": "/api/v1/validations/0a0b7205-.../report.xlsx",
    "pdf": "/api/v1/validations/0a0b7205-.../report.pdf"
  }
}
```

Two of those metrics only differ on very large results:

- `issue_count` — every finding the engine detected.
- `returned_issue_count` — how many are in `issues`. Capped at 10,000.
- `issues_truncated` — `true` when the cap was reached.

Chapter [19](19-limits.md) shows what a truncated result looks like.

Timestamps in the API are UTC, marked with a trailing `Z`. The page converts
them to your local time zone.

## Validating several files

There is no batch mode. One upload validates one register, and each run is
separate: there is no combined score across files and no cross-file checking, so
a load in one file cannot reference a panel in another. A site split across four
registers gets four scores, and the panel references between them will all be
reported as unknown panels.

If your register is split by building or by discipline and the panel hierarchy
crosses those boundaries, concatenate the files into one before uploading — the
50,000-row limit gives plenty of room.

---

[← Mapping non-standard columns](05-column-mapping.md) · [Manual index](README.md) · [Next: The quality score →](07-quality-score.md)
