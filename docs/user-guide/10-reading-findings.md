# 10. Reading and filtering findings

[← Rule reference](09-rule-reference.md) · [Manual index](README.md) · [Next: Correcting and revalidating →](11-correcting-and-revalidating.md)

## The findings table

Below the score panels, headed **Validation issues**, with a badge on the right
showing the total. Six columns:

| Column | What is in it |
|--------|---------------|
| **Severity** | `Error`, `Warning`, or `Information`, colour-coded |
| **Rule** | The rule name, with the field it applies to underneath |
| **Row** | The line number in your file, or a dash for findings about the file as a whole |
| **Asset** | The asset tag from that row, or a dash when the tag itself is missing |
| **Message** | The full message from chapter [9](09-rule-reference.md) |
| **Suggestion** | A corrected value you can paste back, or a dash |

Fifteen rows per page, with **Page 1 of N** and arrows at the bottom, and a line
reading `Showing 1–15 of 150`.

## The order findings come in

**Findings are not sorted by row.** They come in rule-family order, and within a
family in row order:

1. File-level findings — missing and unexpected columns.
2. Per-row rules — required fields, tag format and length, ratings, status,
   whitespace.
3. Duplicate tags.
4. Supply references — missing, unknown, invalid, location mismatch, circuit
   format.
5. Duplicate circuits.
6. Naming consistency and possible typos.
7. The truncation notice, if there is one.

For `invalid-register.csv` that produces this order, and row 12 comes before rows
17 and 18, which come before row 15:

```
error    VALUE_OUT_OF_RANGE       12   LGT-101   power_kw
error    ASSET_TAG_FORMAT         17   MTR 009   asset_tag    suggestion: MTR-009
error    INVALID_NUMBER           17   MTR 009   power_kw
error    INVALID_STATUS           17   MTR 009   status
error    REQUIRED_FIELD           18   —         asset_tag
error    DUPLICATE_ASSET_TAG      15   FAN-004   asset_tag
error    DUPLICATE_ASSET_TAG      16   FAN-004   asset_tag
warning  PANEL_LOCATION_MISMATCH  10   MTR-002   panel_tag    suggestion: Plant Room A
warning  MISSING_PANEL_REFERENCE  15   FAN-004   panel_tag
warning  UNKNOWN_PANEL_REFERENCE  17   MTR 009   panel_tag
warning  PANEL_LOCATION_MISMATCH  18   —         panel_tag    suggestion: Loading Dock
warning  POSSIBLE_TYPO            10   MTR-002   location
```

If you want to work file-in-hand, top to bottom, sort by row in the Excel export
instead (chapter [15](15-xlsx-report.md)) — the table on the page cannot be
sorted.

## Filtering by severity

The dropdown on the right of the toolbar offers **All severities**, **Errors**,
**Warnings**, and **Information**. Selecting **Errors** on the register above
leaves seven rows and the footer reads `Showing 1–7 of 7`.

**Filter to errors first.** They are the acceptance gate
(chapter [8](08-errors-and-warnings.md)), they are usually far fewer than the
warnings, and fixing them often removes warnings as a side effect — correcting an
asset tag can clear a duplicate, a format error, and an unknown panel reference
in one edit.

## Searching

The search box matches text anywhere in a finding — severity, rule, row number,
asset tag, field, message, or suggestion — case-insensitively.

Useful things to type:

| Search | Finds |
|--------|-------|
| `FAN-004` | Everything about one asset. Three findings in the example register. |
| `DUPLICATE` | Both duplicate rules at once. |
| `panel_tag` | Every supply-reference problem. |
| `17` | Everything on row 17 — but also any finding whose message happens to contain `17`. |

Searching for an asset tag is the most useful of these, because it collects
everything wrong with one row into one view before you go and edit it.

When nothing matches, the table is replaced by **No issues match these filters**.
When the validation genuinely had no findings, it reads **No issues were
reported** instead — a different message, so you can tell the two apart.

Filter and search combine, and changing either returns you to page 1.

## Both act only on what was returned

On a truncated result — more than 10,000 findings — the search box and the filter
only see the findings that were sent to your browser. Searching for an asset that
falls beyond the cut returns nothing, which does not mean the asset is clean. The
banner above the table says so:

> Showing a bounded set of 12,000 detected issues. Correct the listed findings and run validation again.

and the badge changes from `12 total` to `10,000 shown`. Chapter
[19](19-limits.md) covers this in full.

## Working through a list efficiently

1. Filter to **Errors** and read them all first. Note the rows.
2. Search each affected asset tag in turn, so you see everything about one row
   before you edit it. A tag that is malformed *and* duplicated *and* points at a
   missing panel is one edit, not three.
3. Switch to **Warnings** and triage rather than fix: `UNKNOWN_PANEL_REFERENCE`
   and `DUPLICATE_CIRCUIT_REFERENCE` are usually real;
   `PANEL_LOCATION_MISMATCH` and `POSSIBLE_TYPO` are usually not. Chapter
   [8](08-errors-and-warnings.md) sorts them.
4. Use the **Suggestion** column. Where it is filled in, it is a value the
   software believes is correct and you can paste directly into the cell.
5. Export the Excel workbook to do the actual editing
   (chapter [15](15-xlsx-report.md)) — its Issues sheet has the same six columns
   plus filters, and can be sorted by row.

## What the table does not do

- **No sorting.** Column headings are not clickable.
- **No grouping by rule or by row**, and no count per rule anywhere in the page.
  With 150 findings across three rules you cannot see that shape without
  exporting.
- **No link from a finding to the row's data.** The table shows the tag and the
  row number, never the offending value. To see what is actually in
  `voltage_v` on row 21 you need your own file, or the Data sheet of the Excel
  export.
- **No copying a finding**, other than selecting text with the mouse.
- **No way to hide, accept, or annotate a finding.** Every warning you have
  consciously accepted will be there again next revision, at full weight in the
  score.

---

[← Rule reference](09-rule-reference.md) · [Manual index](README.md) · [Next: Correcting and revalidating →](11-correcting-and-revalidating.md)
