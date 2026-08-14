# 16. Validation history

[← The Excel report](15-xlsx-report.md) · [Manual index](README.md) · [Next: Authentication →](17-authentication.md)

## Recent validations

At the bottom of the page, headed **Recent validations**. One entry per
validation, newest first, each showing:

- the source filename;
- when it ran, in your local time zone;
- the quality score in a coloured pill;
- the finding count.

```
many-pages.csv            14 Aug 2026, 17:14    40.8   150 issues
invalid-register.csv      14 Aug 2026, 17:13    58.2    12 issues
register-as-received.csv  14 Aug 2026, 17:13     100     0 issues
```

Before your first run it reads **No validations yet — Completed runs will appear
here.**

## Reopening a run

Click an entry. The full result loads exactly as it was: the same score, the same
counts, the same finding list, and both download buttons. Reopening
`invalid-register.csv` from the list restored all 12 findings, starting with the
same `VALUE_OUT_OF_RANGE` on row 12.

This is how you get a report for a validation you ran earlier and did not export
at the time. Nothing expires within a session, and the reports are generated from
the stored result, so a report downloaded a week later is identical to one
downloaded at the time — as long as the run still exists
(chapter [18](18-privacy-and-retention.md)).

Reopening replaces whatever is currently on screen, including a comparison
result. Reopening the run you are already looking at is harmless.

## What history is scoped to

**Your browser session**, and nothing else. The list contains the runs created
from this browser, and no others. Two people using the same server see two
separate histories; the same person on a laptop and a phone sees two separate
histories. There is no shared or team view.

On a deployment that requires a token, the scope is the **token** instead of the
browser: everyone holding the same token sees the same history, from any browser.
A run created from the command line with a token appeared in the browser's
history as soon as the same token was entered. Chapter
[17](17-authentication.md) covers this.

If history is empty when you expect entries, the usual causes are a different
browser or profile, private browsing, cleared cookies, or a retention window that
has passed. Chapter [20](20-troubleshooting.md) works through them.

## What history does not hold

- **No comparisons.** The list is validations only. A comparison is stored and
  can be fetched by its identifier, but the page never shows you that identifier,
  so from the browser a comparison is unrecoverable once you navigate away. Copy
  anything you need from a comparison before leaving the page.
- **No search or filter.** No box, no date range, no filter by score or
  filename. Validate the same file five times and you get five identical-looking
  entries distinguishable only by their timestamps.
- **No delete.** You cannot remove a run. Uploading the wrong file leaves it in
  the list until the retention window removes it, or forever on a deployment with
  retention switched off.
- **No rename, note, or tag.** The filename is all the identification there is.
  Name your files well.
- **No comparison between two runs.** Nothing shows the score moving from 72.7
  to 100 across two validations of the same register. That is a comparison you do
  by hand.

## Over the API

```bash
curl --cookie jar.txt http://localhost:8000/api/v1/validations
```

Returns the summaries — id, filename, timestamp, score, and metrics — newest
first, but **not** the findings. Fetch a single run by id for those:

```bash
curl --cookie jar.txt http://localhost:8000/api/v1/validations/<id>
```

Paging is by `limit` and `offset`:

```bash
curl --cookie jar.txt "http://localhost:8000/api/v1/validations?limit=10&offset=20"
```

`limit` must be between 1 and 200; anything outside that is rejected with HTTP
422, so `limit=0` and `limit=500` both fail rather than being clamped. The
default is 50 — which means **the web page shows at most your 50 most recent
runs**, with no way to reach older ones from the browser.

An identifier that does not exist, or belongs to another session, answers the
same way:

```json
{"detail": "Validation not found."}
```

That is deliberate: a foreign run is indistinguishable from a missing one, so
nobody can probe for other people's identifiers.

---

[← The Excel report](15-xlsx-report.md) · [Manual index](README.md) · [Next: Authentication →](17-authentication.md)
