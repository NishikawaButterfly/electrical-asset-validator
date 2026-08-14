# 19. Limits

[← Privacy and retention](18-privacy-and-retention.md) · [Manual index](README.md) · [Next: Troubleshooting →](20-troubleshooting.md)

Every cap the software imposes, the message you get when you cross it, and what
to do. All of these were reached deliberately and the messages copied from the
responses.

## File size

| Cap | Default | Message |
|-----|---------|---------|
| One uploaded file | 10 MB | `Each file must be no larger than 10 MB.` |
| The whole request | file cap + 1 MB | `The multipart request body is too large for this upload route.` |

The first is the one you will see: a 10.4 MB register was refused with it. The
second comes from a guard further out and appears with a much larger file — an
11.5 MB upload triggered it instead. Both are HTTP 413 and both mean the same
thing to you.

The file cap is set per deployment. The public demo runs with **2 MB**. Ask your
operator what yours is; nothing in the page displays it.

**If your register is too big:** it is almost certainly XLSX. The same data as
CSV is a fraction of the size — a 50,000-row register saved as CSV is under
2.5 MB. Otherwise split it by building or by board and validate the parts,
accepting that panel references crossing the split will report as unknown
(chapter [6](06-running-a-validation.md)).

## Rows, columns, and cells

| Cap | Value | Message |
|-----|-------|---------|
| Data rows | 50,000 | `Files may contain no more than 50,000 data rows.` |
| Columns | 64 | `Files may contain no more than 64 columns.` |
| Characters in one cell | 32,767 | `A cell exceeds the maximum supported length of 32,767 characters.` |

The row cap counts non-empty rows and is inclusive: a file with exactly 50,000
data rows validated normally; 50,001 was refused. The column cap counts every
column, canonical or not, so a register with the nine plus 56 extras is refused
at 65.

The cell limit is the maximum a spreadsheet cell can hold anyway, so hitting it
means something has gone wrong — usually a whole table pasted into one cell.

## Findings per validation

A validation returns at most **10,000 finding details**. The counts and the score
still reflect everything that was found.

A 6,001-row register with two warnings on every row produced:

| | |
|---|---|
| Warnings counted | **12,000** |
| Finding details returned | **10,000** |
| Truncated | **yes** |
| Quality score | **40.0** — computed from all 12,000 |

On the page, the badge changes from a total to `10,000 shown`, and a note
appears above the table:

> Showing a bounded set of 12,000 detected issues. Correct the listed findings
> and run validation again.

The last returned finding is the notice itself:

```
warning  FINDING_LIMIT_REACHED
The validation reached the 10,000-finding output limit. Correct the listed
findings and run validation again.
```

**What this means for you.** The score is trustworthy; the list is not complete.
The search box and severity filter only see what was returned
(chapter [10](10-reading-findings.md)), so an asset beyond the cut cannot be
found by searching, and its absence proves nothing.

A result this size always comes from a systematic cause, not 10,000 separate
mistakes. In the example above, one change — adding the panel and circuit columns'
content — clears all 12,000. Fix the systematic cause, re-run, and the list will
fit.

In the Excel report, **Issues** and **Returned issue details** on the Summary
sheet differ whenever this has happened, and **Issue details truncated** says
`True` (chapter [15](15-xlsx-report.md)).

## Comparison details

A comparison is refused when it would produce more than **10,000 details** —
counting each added asset, each removed asset, and each individual changed field:

```
The comparison exceeds the 10,000-detail output limit. Compare smaller revision segments.
```

Two 5,001-row registers with no tags in common reach it. Unlike the validation
cap, this one produces **no result at all** rather than a truncated one.

You will only meet it comparing two registers that are not really revisions of
each other. If you do, compare matching segments — one building, one voltage
level — rather than the whole estate.

## History

| Cap | Value |
|-----|-------|
| Entries returned per request | 50 by default, 200 maximum |

`limit` below 1 or above 200 is rejected with HTTP 422 rather than clamped. The
web page never asks for more than the default, so **it shows at most your 50 most
recent validations** and older ones are reachable only through the API with an
`offset` (chapter [16](16-validation-history.md)).

## XLSX archive limits

These protect the server from deliberately malicious workbooks. A register
produced by ordinary spreadsheet software will not approach them.

| Cap | Value |
|-----|-------|
| Files inside the workbook archive | 2,000 |
| Expanded size of the workbook | 100 MB |
| Compression ratio (above 5 MB expanded) | 200:1 |
| Rows scanned on the first worksheet | 250,000 |

That last one is about the worksheet's *used range*, not your data. A workbook
whose first sheet has stray formatting far down the grid can exceed it while
holding fifty rows of register — delete the empty rows below your data and save
again.

## Time

There is no timeout you can configure and no background processing: a validation
runs inside the request that started it, and everything above is sized so that
completes promptly. There is also no way to cancel a running validation.

## What has no limit

- **The number of validations you may run.** No quota, no rate limit in the
  application.
- **How long a run is kept**, unless the deployment sets a retention window
  (chapter [18](18-privacy-and-retention.md)).
- **How many times a report may be downloaded.**
- **The number of distinct asset types or locations** in a register.

---

[← Privacy and retention](18-privacy-and-retention.md) · [Manual index](README.md) · [Next: Troubleshooting →](20-troubleshooting.md)
