# Electrical Asset Validator — User Manual

**Documents version 0.2.0.**

This manual explains what you can do with Electrical Asset Validator and how to
perform each operation correctly. It assumes you have never seen the source code
and never need to.

The repository [README](../../README.md) answers a different question — what the
software is and how it is built. If you want to run the test suite, read the
architecture, or deploy the service, read that instead.

## Who this is for

The electrical engineer or document controller who receives an asset register
and has to certify it before handover. You are expected to know what a
distribution board, a circuit reference, and a rated power are. You are not
expected to know what JSON, HTTP, or a validation rule engine are: everything in
this manual can be done from the web page, and where an operation is only
available another way, the chapter says so plainly.

## What the software does

You give it an asset register — a spreadsheet with one row per piece of
electrical equipment — and it tells you what is wrong with it: tags used twice,
required cells left empty, ratings that cannot be real, loads pointing at panels
that do not exist in the file. It scores the register, lists every finding with
the row and field it came from, and exports that list as a PDF or an Excel
workbook you can attach to a handover pack. It also compares two revisions of
the same register and tells you which assets were added, removed, and changed.

It checks **data quality, not electrical engineering**. It does not know whether
a 22 kW motor is correctly protected, whether a cable is sized for its load, or
whether the design complies with any standard. It knows that `power_kw` must be
a number and that `FAN-004` must not appear twice. Chapter
[8](08-errors-and-warnings.md) is explicit about where that line falls.

## How to read this manual

Chapters 1 to 6 are the shortest path from a file on your desk to a result on
screen; read them in order the first time. Chapters 7 to 16 are reference — one
operation each, readable on their own. Chapter
[21](21-handover-example.md) is the one to read if you only read one: it takes a
single register from first upload to the evidence a handover meeting asks for.

| # | Chapter | What it covers |
|---|---------|----------------|
| 1 | [Introduction](01-introduction.md) | What the software is for, and the vocabulary the rest of the manual uses |
| 2 | [Supported input files](02-input-files.md) | CSV and XLSX, encodings, size limits, and what a well-formed register looks like |
| 3 | [Preparing a register](03-preparing-a-register.md) | What to do to the file before you upload it |
| 4 | [Uploading a file](04-uploading.md) | Selecting a file and what happens the moment you do |
| 5 | [Mapping non-standard columns](05-column-mapping.md) | Using a register whose headers are not the canonical names |
| 6 | [Running a validation](06-running-a-validation.md) | Starting the run and reading the result summary |
| 7 | [The quality score](07-quality-score.md) | How the number is computed, and what it is not |
| 8 | [Errors versus warnings](08-errors-and-warnings.md) | Which findings block a handover and which ask for judgement |
| 9 | [Rule reference](09-rule-reference.md) | Every rule the engine can report, with its exact message and how to fix it |
| 10 | [Reading and filtering findings](10-reading-findings.md) | The findings table, its search box, severity filter, and paging |
| 11 | [Correcting and revalidating](11-correcting-and-revalidating.md) | Turning a finding list into an edited file and a clean re-run |
| 12 | [Comparing two revisions](12-comparing-revisions.md) | Running a comparison and what it refuses to compare |
| 13 | [Added, removed, and modified assets](13-added-removed-modified.md) | Exactly what each category means, including renamed tags |
| 14 | [The PDF report](14-pdf-report.md) | What is on each page and when to use it |
| 15 | [The Excel report](15-xlsx-report.md) | What is on each sheet and when to use it |
| 16 | [Validation history](16-validation-history.md) | Reopening a past run, and what history does not keep |
| 17 | [Authentication](17-authentication.md) | Open deployments and token deployments |
| 18 | [Privacy and retention](18-privacy-and-retention.md) | What is stored, for how long, who can read it — and the public demo |
| 19 | [Limits](19-limits.md) | Every cap, with the message you get when you cross it |
| 20 | [Troubleshooting](20-troubleshooting.md) | When something does not behave as this manual says |
| 21 | [A handover, end to end](21-handover-example.md) | One register from first upload to exported evidence |

## About the examples

Every message, number, score, and refusal quoted in this manual was produced by
running version 0.2.0 and copying what came back. Nothing is transcribed from the
rule tables or inferred from the code. Where the engine's behaviour surprised the
author, the manual says so rather than tidying it up.

The examples use the fictional registers that ship with the software, in
[`sample-data/`](../../sample-data/):

| File | What it is |
|------|------------|
| `revision-a.csv` | A clean 15-asset register. Scores 100 with no findings. |
| `revision-b.csv` | The next revision of the same register. The comparison pair. |
| `invalid-register.csv` | A 17-row register with deliberate faults. Scores 58.2. |
| `case-study/register-as-received.csv` | A 22-row register with non-standard headers and the usual handover problems. |
| `case-study/register-corrected.csv` | The same register after the corrections in chapter [11](11-correcting-and-revalidating.md). Scores 100. |

None of it is real plant data, and none of it is an engineering design basis.

Two things will differ on your system. Every validation and comparison gets a
fresh identifier when it is created, so the ids in these examples will not match
yours — read them as placeholders. Timestamps are shown in UTC by the API and in
your own time zone by the web page.

## Where the software runs

Three places, and they behave the same:

- **A local or company installation** at whatever address your operator gives
  you, commonly `http://localhost:3000`.
- **The public demo** at <https://electrical-asset-validator.fly.dev/>. Read
  chapter [18](18-privacy-and-retention.md) before you put anything in it.
- **The API**, for the operations the page does not offer. Every chapter that
  needs it shows the exact request.
