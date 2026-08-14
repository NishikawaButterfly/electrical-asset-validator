# 18. Privacy and retention

[← Authentication](17-authentication.md) · [Manual index](README.md) · [Next: Limits →](19-limits.md)

An asset register describes real infrastructure: what equipment a building has,
where it is, what feeds it, and what is currently out of service. Treat it as
you would a single-line diagram. This chapter says exactly what happens to it.

## What is stored when you validate

A validation stores, on the server, for as long as the deployment keeps it:

- The **filename** you uploaded.
- The **nine canonical columns of every row**, as accepted — your register's
  data, in the database.
- Every **finding**, with its message, row, asset tag, field, and suggestion.
- The score, the counts, and the timestamp.
- The **source column headers** of your file.

A comparison stores both filenames, the counts, and the added, removed, and
changed details, including the before and after values of every changed field.

**Your data is stored, not just your results.** The Data sheet of the Excel
report (chapter [15](15-xlsx-report.md)) is that stored copy, which makes it easy
to check. Columns outside the canonical nine are not stored.

What is *not* stored: the original file itself, anything outside the nine
columns, and — in token mode — the token, which is stored only as an irreversible
hash.

**One operation stores nothing at all.** The header inspection the page runs the
moment you select a file (chapter [4](04-uploading.md)) reads the file, reports
its headers, and discards it.

## Who can see it

**Other users of the same server: no.** Runs are scoped, and the isolation was
tested from both sides:

- A second browser session listing validations got `[]`.
- The same session fetching another session's run by its exact identifier got
  HTTP 404 `Validation not found.` — the same answer as an identifier that does
  not exist, so nobody can probe for other people's runs.
- The report URLs are scoped the same way. A foreign report answers 404.
- In token mode, one token fetching another token's run gets the same 404.

**The people who run the server: yes, completely.** Uploaded rows are stored
unencrypted. Anyone with database access, a backup, or a copy of the server's
disk can read every register anybody has validated. Scoping keeps users apart
from each other; it does not keep anything from the operator. If that matters,
the question to ask before uploading is who administers this instance, not what
the software does.

**Anyone who obtains your session cookie or your token: yes.** Both are bearer
credentials. Chapter [17](17-authentication.md).

## Retention

A deployment can be configured to delete stored runs after a set number of
minutes. The default is to keep them **indefinitely** — a local installation with
no configuration keeps every run until somebody clears the database.

Where retention is switched on, this is what happens, measured on an instance
with a one-minute window:

| Time after the run was created | History | Fetching it by id |
|---|---|---|
| 20 seconds | 1 entry | HTTP 200 |
| 45 seconds | 1 entry | HTTP 200 |
| 70 seconds | 0 entries | HTTP 404 `Validation not found.` |

Two details are worth understanding:

**Deletion is real.** The run and all of its findings are removed from the
database, not hidden. A report URL that worked before the window passed returns
404 afterwards, and there is no undo and no export of expired data.

**Deletion happens lazily, on the next request.** There is no background
scheduler. Checking the database directly 70 seconds after the run was created —
with the window long past but before any request arrived — showed the run still
there. The very next API call swept it, and a second check showed the table
empty. In practice deployments receive regular health checks, so expiry is
prompt; but "the window has passed" and "the data is gone" are not the same
instant.

## The public demo

<https://electrical-asset-validator.fly.dev/> is a public instance. Its own
banner says what it is:

> Public demo. Uploads stay private to your browser session and are deleted
> after 30 minutes. Never upload a real asset register; use the sample files.

Take that literally. Specifically:

- **It is open.** No token. Anyone on the internet can use it.
- **It runs with a 30-minute retention window**, and its uploads are capped at
  **2 MB**, not the 10 MB of a default installation.
- **It is administered by somebody you do not know**, and your register is
  stored unencrypted on their machine for the duration. Session scoping protects
  you from other visitors, not from the operator.
- **It restarts.** Anything in it may vanish before the 30 minutes are up.
- **At the time of writing it reports version `0.1.0`** from
  `/api/v1/health`, while this manual documents 0.2.0. Behaviour on the demo may
  differ from what is written here. Check the version yourself if it matters.

Use it to see what the software does, with the fictional files in
[`sample-data/`](../../sample-data/). For a real register, use an installation
your organisation controls.

## Practical advice

1. **Validate real registers on an instance you or your organisation runs.**
   Everything in this manual works identically there.
2. **Assume the server operator can read what you upload.** Ask who that is.
3. **Export what you need to keep.** Where retention is enabled, the report is
   the durable artefact; the run is not.
4. **Do not put commentary in the register.** A `notes` column is not stored —
   only the nine canonical columns are — but the nine are, so keep anything
   sensitive out of `asset_name` and `location`.
5. **Clear a token from a shared machine** when you finish
   (chapter [17](17-authentication.md)).
6. **Remember the file travels twice**: once for header inspection when you
   select it, once when you validate.

## What the software does not do

- No telemetry, analytics, or third-party upload services are added by this
  project.
- No email, no notifications, no external calls with your data.
- No encryption of stored register data. Tokens are hashed; registers are not.
- No audit trail. Nothing records who uploaded what.

---

[← Authentication](17-authentication.md) · [Manual index](README.md) · [Next: Limits →](19-limits.md)
