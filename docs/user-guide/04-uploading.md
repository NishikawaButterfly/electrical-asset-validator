# 4. Uploading a file

[← Preparing a register](03-preparing-a-register.md) · [Manual index](README.md) · [Next: Mapping non-standard columns →](05-column-mapping.md)

## The workspace

Open the address your operator gave you. The page has one working area, headed
**Start an analysis**, with two tabs:

| Tab | What it takes | What it produces |
|-----|---------------|------------------|
| **Validate file** | One register | A score and a finding list (chapter [6](06-running-a-validation.md)) |
| **Compare revisions** | Two registers, before and after | Added, removed, and changed assets (chapter [12](12-comparing-revisions.md)) |

Below the working area is **Recent validations** — the history of runs from this
browser (chapter [16](16-validation-history.md)). On a deployment that requires a
token, an **API token required** panel appears above everything else; see chapter
[17](17-authentication.md).

## Selecting a file

1. Make sure the **Validate file** tab is selected. It is, when you arrive.
2. Drag your register onto the dashed area marked **Drop your file here**, or
   click **Choose file** and pick it.
3. The dashed area is replaced by the file's name and size. A small **×** next to
   it clears the selection.
4. Click **Run validation**.

Until you pick a file the button is disabled and the line beside it reads
`Select one file to continue`. Once a file is chosen it reads `Ready to
validate`.

**Nothing is sent to the server when you choose a file for the two-tab form** —
except one thing, described below. The note beside the heading says `Files are
sent when you start`, and that is accurate for the validation itself.

## What happens the instant you choose a file

The page immediately sends the file to the server once, to ask what its column
headers are. This is how it knows whether to offer you the mapping panel in
chapter [5](05-column-mapping.md).

This header inspection **stores nothing**. It reads the file, reports the
headers and which canonical field each one matches, and discards it. No
validation is created, nothing appears in your history, and nothing is written to
the database. It is worth knowing about anyway, because on a metered or slow
connection the file does travel twice.

If the inspection fails for any reason, the page says nothing and lets you carry
on; the real refusal, if there is one, comes when you press **Run validation**.

## Files the page refuses without asking the server

The file picker only offers `.csv` and `.xlsx`, and dragging anything else in is
stopped in the browser:

> **Analysis could not be completed**
> Choose a CSV or XLSX file.

This check looks only at the filename ending. A PDF renamed `register.csv` gets
past it and is refused by the server instead.

## Errors from the server

Anything the server refuses appears in the same red banner, with the server's own
words. Selecting a header-only file and pressing **Run validation** gives:

> **Analysis could not be completed**
> The uploaded file does not contain any data rows.

Every such message is listed with its cause in chapters
[19](19-limits.md) and [20](20-troubleshooting.md). A refused upload creates
nothing: no validation, no history entry, no partial result. Fix the file and
select it again.

Dismiss the banner with the **×**, or simply choose another file — selecting a
file clears it.

## While it runs

A progress banner reads **Validating your asset register**, both tabs and the
button are disabled, and the result appears below when the server answers. There
is no cancel button; a validation of a large register runs to completion. In
practice this is quick — a 50,000-row file is well within the limits the software
imposes on itself, and the whole thing happens inside a single request.

When it finishes the page scrolls to the results and announces the score for
screen readers.

## Uploading from the command line

Everything the page does is an HTTP request, and the equivalent is sometimes
easier — for instance when you want to validate the same file after each of five
corrections. `curl` needs a cookie jar, because that is what keeps the runs
yours (chapter [18](18-privacy-and-retention.md)):

```bash
curl --fail-with-body --cookie-jar jar.txt --cookie jar.txt \
  -F "file=@sample-data/invalid-register.csv;type=text/csv" \
  http://localhost:8000/api/v1/validations
```

The response is the whole result — score, counts, and every finding — as JSON,
plus the two report URLs. Without `--cookie-jar` the run is created but you will
never be able to fetch it again, because the next request arrives as a different
session.

On a deployment that requires a token, add `-H "Authorization: Bearer <token>"`
and drop the cookie jar entirely.

---

[← Preparing a register](03-preparing-a-register.md) · [Manual index](README.md) · [Next: Mapping non-standard columns →](05-column-mapping.md)
