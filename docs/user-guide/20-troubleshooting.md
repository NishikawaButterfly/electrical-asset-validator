# 20. Troubleshooting

[← Limits](19-limits.md) · [Manual index](README.md) · [Next: A handover, end to end →](21-handover-example.md)

Sorted by what you see. Every message quoted here is one the software actually
produces.

## The upload is refused

### "Choose a CSV or XLSX file."

The browser stopped it before anything was sent, because the filename does not
end in `.csv` or `.xlsx`. Re-save the file in one of the two formats — renaming
it is not enough, and a renamed file will be refused by the server instead.

### "Only .csv and .xlsx files are supported."

The same problem, caught by the server. Usually a `.xls`, `.ods`, or a CSV that
was renamed rather than re-saved.

### "CSV files must use UTF-8 encoding."

The file contains a character that is not valid UTF-8 — almost always an accent,
a degree sign, or a dash from a European or Latin American spreadsheet.

**Fix in Excel:** File → Save As → **CSV UTF-8 (Comma delimited) (\*.csv)**. Not
plain "CSV (Comma delimited)", which writes your system code page.
**In LibreOffice:** tick *Edit filter settings* when saving and set the character
set to **Unicode (UTF-8)**.
**In Google Sheets:** downloaded CSV is already UTF-8.

### "The uploaded file is empty."

Zero bytes. Usually a failed export or a file copied while it was being written.

### "The uploaded file does not contain any data rows."

There is a header row and nothing under it. Check you exported the data and not
just the headings, and that you did not have a filter applied that hid every row.

### "Column names cannot be blank."

One header cell is empty. Three common causes: a merged cell across the header
row; an accidental extra column with no name; or **a file with no header row at
all**, whose first data row is being read as the header — an empty `panel_tag`
cell in that row then looks like a blank column name. Add a proper header row.

### "Duplicate columns after normalization: asset_tag."

Two headers reduce to the same canonical name — `asset_tag` and `Asset Tag`, for
instance. Header matching ignores case, spaces, and hyphens
(chapter [2](02-input-files.md)), so those are the same column. Delete or rename
one.

### "CSV row 3 has 3 fields; the header has 9."

That row has a different number of commas from the header. Usually an unquoted
comma inside a value — `Pump, spare` needs to be `"Pump, spare"` — or a line break
inside a cell. The message names the row.

### "A cell exceeds the maximum supported length of 32,767 characters."

Something very large was pasted into a cell. Find it and remove it.

### "Each file must be no larger than 10 MB." / "The multipart request body is too large for this upload route."

Both are size refusals; see chapter [19](19-limits.md). Saving an XLSX register
as CSV usually solves it outright.

### "Files may contain no more than 50,000 data rows." / "no more than 64 columns."

Split the register, or remove the extra columns. Extra columns cost nothing up to
the cap, so this only bites on very wide exports.

## XLSX-specific refusals

### "The XLSX file is not a valid workbook archive."

The file is named `.xlsx` but is not one — commonly an `.xls` renamed, or a
corrupted download. Open it in Excel and save it again as `.xlsx`.

### "XLSX row 2 contains data beyond the header columns."

There is a value to the right of the last header — a note somebody typed in an
unlabelled column. Delete that content, or give the column a header.

### "The XLSX workbook does not contain a worksheet." / "The first XLSX worksheet extends beyond the supported 250,000 source rows."

The first is an empty workbook. The second is about the sheet's used range, not
your data: stray formatting far down the grid inflates it. Select every row below
your data, delete them, save, and upload again.

## The result looks wrong

### Everything is an error and the score is 0

Look at the top of the finding list. Nine `MISSING_COLUMN` errors mean the file
was never split into columns — the classic cause is a **semicolon-delimited CSV**
from a European Excel. Uploading one produced 16 errors, 2 warnings, and a
score of 0.0 from a single perfectly good row, with an `UNEXPECTED_COLUMN`
finding whose name was the entire header row joined by semicolons.

Fix by saving with comma separators — in Excel, changing the list separator in
your regional settings, or in LibreOffice choosing the field delimiter in the
save dialog.

Four `MISSING_COLUMN` errors rather than nine mean the header row is fine but
some headings do not match. Use the column mapping
(chapter [5](05-column-mapping.md)).

### Every numeric cell reports INVALID_NUMBER

The register is an XLSX whose ratings are **formulas**. They are read as their
formula text, not their calculated value, so `=200*2` fails. Copy the data and
paste-special as values, then upload again (chapter
[3](03-preparing-a-register.md)).

Otherwise check for unit suffixes (`400 V`), comma decimal separators (`18,5`),
and text placeholders (`TBC`).

### Every load reports a missing or invalid panel reference

Two different causes, distinguished by the message:

- `A non-panel asset should reference its supplying panel.` — the `panel_tag`
  cells are empty, or your boards are typed something the software does not
  recognise as a panel, so the boards themselves are being asked for their own
  supply.
- `Referenced asset 'X' is not classified as a panel.` — the board is in the
  file but its `asset_type` does not contain `panel`, `switchboard`, or
  `distribution board`. A register that types its boards `MCC` or `DB` produces
  this on every load. Chapter [3](03-preparing-a-register.md).

### Every load reports an unknown panel

The boards are not in the register at all. Add them as rows, with `power_kw` of
`0` and their own supply cells empty. This is the single highest-value correction
on a load-only register (chapter [11](11-correcting-and-revalidating.md)).

### The score dropped after I fixed something

Usually you added rows, or you cleared a blocking error and revealed the rules
that were hiding behind it. Chapter [11](11-correcting-and-revalidating.md)
lists the three causes.

### A finding I know I fixed is still there

Check you uploaded the corrected file, not the original — the filename is shown
above the score. Each validation is independent; there is no caching of results
between runs.

### I cannot find an asset in the findings list

If the result is truncated — the badge says `10,000 shown` — search only sees what
was returned, and the asset may be beyond the cut
(chapter [19](19-limits.md)).

## The comparison is refused

### "The before file is missing canonical columns: ..."

One of the two files does not have all nine columns under matchable headings.
The comparison form has no mapping panel, so from the browser both files must
already use canonical headers. Rename the headings in your copies, or run the
comparison from the command line with a mapping
(chapter [5](05-column-mapping.md)).

### "The after file contains duplicate asset_tag 'FAN-004'."

A tag appears twice in that file, so revisions cannot be matched. Validate that
file on its own to see every duplicate with its row numbers, fix them, then
compare.

### "The before file has a blank asset_tag on row 3." / "an invalid asset_tag 'mtr 001' on row 3."

The same principle: identity must be sound before anything can be compared.
Validate the file, fix the tag errors, compare again.

### "The comparison exceeds the 10,000-detail output limit."

The two files have almost nothing in common. Check you have not swapped a file
for an unrelated register, then compare matching segments.

### The results read backwards

The before and after files are the wrong way round. Nothing detects this;
re-upload them in the right order.

## History and access

### "No validations yet" but I ran some

The history is scoped to your browser session
(chapter [17](17-authentication.md)). Any of these will empty it: a different
browser or profile, private browsing, cleared cookies, or a different machine.
The runs still exist on the server but can no longer be reached.

On a deployment with a retention window, they may also have been deleted
(chapter [18](18-privacy-and-retention.md)).

### "Validation not found."

The run does not exist, or it belongs to another session or another token. Both
give the same message deliberately. If it was yours, your cookie or token has
changed, or retention removed it.

### "A valid bearer token is required."

Token mode, and the token is missing or wrong. Paste it into the **API token
required** panel and click **Use token**
(chapter [17](17-authentication.md)). The message is the same for a missing token
and a wrong one, so re-check the value with your operator rather than assuming
it is correct.

### "History is unavailable — A valid bearer token is required."

The same cause, shown in the history panel. Enter the token.

## The page itself

### "The validation service could not be reached."

The browser could not talk to the API at all — the backend is not running, or the
address is wrong. On a local development setup, check the backend is up and
answering:

```bash
curl http://localhost:8000/api/v1/health
```

```json
{"status": "ok", "version": "0.2.0", "database": "ok"}
```

### The download button does nothing

The report is generated on demand and can take a moment on a very large result;
the button reads **Preparing…** while it does. If it fails, an error appears
beside it — most often because the run has been removed by retention since you
opened the page.

## When you need to report a problem

Include the version from `/api/v1/health`, the exact message, the row it named,
and — if you can share it — a cut-down file that reproduces it. Because
validation is deterministic, a file that produces a finding will produce it every
time, which makes a small example the fastest possible fix.

---

[← Limits](19-limits.md) · [Manual index](README.md) · [Next: A handover, end to end →](21-handover-example.md)
