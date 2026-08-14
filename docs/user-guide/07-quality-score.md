# 7. The quality score

[← Running a validation](06-running-a-validation.md) · [Manual index](README.md) · [Next: Errors versus warnings →](08-errors-and-warnings.md)

The score is the one number that leaves the tool and ends up in a status report,
so it is worth understanding exactly.

## How it is computed

1. Each error costs **8 penalty points**. Each warning costs **3**. Information
   findings cost nothing.
2. Those are measured against a budget of **10 points per data row**, with a
   floor of 10 for very small files.
3. The score is `100 − (penalty ÷ budget) × 100`, rounded to one decimal, and
   never below 0.
4. If the file is missing a canonical column, the score is **0**, whatever else
   is in it.
5. If there is at least one error or warning, the score is capped at **99.9**.

Worked on the sample registers:

| Register | Rows | Errors | Warnings | Penalty | Budget | Score |
|----------|------|--------|----------|---------|--------|-------|
| `revision-a.csv` | 15 | 0 | 0 | 0 | 150 | **100** |
| `invalid-register.csv` | 17 | 7 | 5 | 71 | 170 | **58.2** |
| `register-as-received.csv` (mapped) | 22 | 6 | 4 | 60 | 220 | **72.7** |
| `register-as-received.csv` (unmapped) | 22 | 72 | 19 | — | — | **0.0** — missing columns |

Every one of those numbers came from a run.

## What follows from the arithmetic

**The score is a density, not a count.** Six errors in 22 rows scores 72.7; six
errors in 220 rows would score 97.3. That is the intended behaviour — it lets you
compare a 50-row register with a 5,000-row one — but it means a good score does
not mean a clean file. **Always read the error count as well as the score.**

**Small files swing violently.** The 10-point floor means a one-row file with one
error scores **20.0**, and a one-row file with two warnings scores **40.0**.
Below about ten rows the score says more about the file's size than its quality.

**100 means nothing was reported at all.** Because any error or warning caps the
score at 99.9, you never have to wonder whether a 100 is a rounded 99.96. A
701-row register with a single `Active` where `active` was expected scored
**99.9**, not 100. If you need a bright line for handover, "score is exactly 100"
is a meaningful one; "score above 95" is not.

**Zero has two different meanings.** A register that is structurally broken — a
canonical column missing — is set to 0 directly. A register whose findings simply
outrun the budget also lands on 0: five rows in which every field was wrong
produced 20 errors and 10 warnings against a 50-point budget and floored at
**0.0**. The counts underneath tell you which situation you are in, and the
`MISSING_COLUMN` findings at the top of the list are unmistakable.

**Errors and warnings are not distinguishable from the score.** Eight warnings
cost the same 24 points as three errors. A register with many style warnings can
score lower than one with a couple of duplicate tags, even though the second is
the one that will break your comparison. This is the strongest reason not to
manage a handover by score alone.

## What the score is not

- **It is not a measure of the installation.** It measures the file. A perfectly
  maintained register describing a badly designed switchboard scores 100.
- **It is not an engineering judgement.** No rule behind it knows anything about
  electrical engineering; see chapter [8](08-errors-and-warnings.md).
- **It is not comparable across versions of the software.** Rules get added.
  A file that scored 58.2 on version 0.2.0 may score differently on a later
  release. If you are tracking a score over months, record the version alongside
  it — the API's `/api/v1/health` reports it.
- **It is not a completeness check.** Nothing knows how many assets *should* be
  in the register. A file containing three of your four hundred assets, all
  correctly filled in, scores 100.
- **It is not weighted by importance.** A duplicate tag on a main switchboard and
  a duplicate tag on a toilet extract fan cost eight points each.

## Using it well

A defensible way to use the number, given all of the above:

- Treat **errors = 0** as the acceptance gate, not a score threshold. Chapter
  [8](08-errors-and-warnings.md) explains why that line is the meaningful one.
- Use the score to track **progress between revisions** of the same register,
  where the row count is roughly stable and the number therefore means something
  comparable.
- Quote it with its parts: "72.7, with 6 errors and 4 warnings over 22 rows" is a
  statement somebody can act on. "72.7" on its own is not.

---

[← Running a validation](06-running-a-validation.md) · [Manual index](README.md) · [Next: Errors versus warnings →](08-errors-and-warnings.md)
