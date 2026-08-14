# 11. Correcting a register and revalidating

[← Reading and filtering findings](10-reading-findings.md) · [Manual index](README.md) · [Next: Comparing two revisions →](12-comparing-revisions.md)

## The loop

The software never edits your file. The cycle is always:

1. Validate.
2. Read the findings.
3. Edit **your** register, in your own spreadsheet.
4. Validate the edited file.
5. Repeat until the errors are gone.

There is no in-place editing, no "apply all suggestions", and no way to download
a corrected register. The Excel export contains your data on a Data sheet
(chapter [15](15-xlsx-report.md)), but that sheet is a record of what was
validated, not a working copy to correct and re-upload — it drops any extra
columns your register had.

## A worked correction

`sample-data/case-study/register-as-received.csv`, mapped as in chapter
[5](05-column-mapping.md), scores **72.7** with six errors and four warnings.
Here is every finding and the edit that clears it. The result is
`sample-data/case-study/register-corrected.csv`, which is committed next to it so
you can diff the two.

| Row | Severity | Rule | Asset | The edit |
|-----|----------|------|-------|----------|
| 8 | warning | `NAMING_NORMALIZATION` | `PDU-B-01` | `Active` → `active` |
| 9 | error | `REQUIRED_FIELD` | `UPS-C-01` | Empty status → `active` |
| 14 | error | `REQUIRED_FIELD` | `PMP-C-03` | Empty `power_kw` → `11.0` |
| 15 | warning | `UNKNOWN_PANEL_REFERENCE` | `CHL-C-01` | Add `PNL-C-ROOF` as a row |
| 17, 18 | error | `DUPLICATE_ASSET_TAG` | `FAN-C-02` | Second fan becomes `FAN-C-03` |
| 21 | error | `VALUE_OUT_OF_RANGE` | `LGT-C-202` | `-230` → `230` |
| 22 | error | `INVALID_STATUS` | `HTR-C-01` | `in service` → `active` |
| 23 | warning | `MISSING_PANEL_REFERENCE` | `EF-C-01` | Add `PNL-C-CP` as a row, reference it |
| 23 | warning | `MISSING_CIRCUIT_REFERENCE` | `EF-C-01` | `circuit_ref` → `C01` |

Ten findings, eight edits, two of which are new rows. Revalidated with the same
mapping:

| | As received | Corrected |
|---|------------|-----------|
| Quality score | 72.7 | **100** |
| Rows | 22 | **24** |
| Valid rows | 16 | **24** |
| Errors | 6 | **0** |
| Warnings | 4 | **0** |
| Findings | 10 | **0** |

## What the corrections teach

**Adding the missing boards clears more than it looks like.** Two new rows —
`PNL-C-ROOF` and `PNL-C-CP`, each with `power_kw` of `0` and no supply cells of
their own — cleared the unknown-panel warning on the chiller and gave the car-park
fan something to reference. On a load-only register this is the highest-value
correction available.

**Some errors need a decision, not a fix.** `UPS-C-01` had no status. The
software cannot know whether it is `active` or `standby`; somebody has to ask.
Likewise `PMP-C-03` had no rated power, and `11.0` came from the pump's twin, not
from the tool. **Do not invent values to clear findings.** An error that reveals
missing information is the software working correctly.

**Renaming a tag has a downstream cost.** `FAN-C-02` appearing twice was
resolved by renaming the second to `FAN-C-03`. That is the right correction, and
it means the next comparison against the previous revision will report
`FAN-C-03` added and nothing removed — because the old duplicate never had a
distinct identity. Chapter [13](13-added-removed-modified.md).

**Use the suggestions.** Four of the eight edits above are exactly what the
suggestion column offered: `active` for `Active`, and so on. Where a suggestion
exists, it is a value the engine believes is correct.

## Revalidating

Select the corrected file and run it again. There is nothing to link the two
runs — the second validation is a new record with a new identifier, and both stay
in your history (chapter [16](16-validation-history.md)). Nothing in the tool
compares one validation with another or shows you a trend; if you want to record
progress, note the score and counts each time.

Two things make revalidation cheaper if you do it often:

- **Keep the mapping selections in mind.** They are not saved, so a
  non-standard register has to be mapped again on every re-run
  (chapter [5](05-column-mapping.md)).
- **Use the command line for a tight loop.** One line per attempt, and the score
  comes straight back:

  ```bash
  curl -s --cookie-jar jar.txt --cookie jar.txt \
    -F "file=@register.csv;type=text/csv" \
    http://localhost:8000/api/v1/validations
  ```

## When the count goes up after a correction

Not a bug, usually one of three things:

- **You added rows.** Two new panels are two more rows to check. Both of the
  boards added above were clean, but a board added with an empty `location` would
  bring its own error.
- **You cleared a blocking error and revealed the rules behind it.** A row whose
  `asset_tag` was missing produces one `REQUIRED_FIELD` error and is invisible to
  the tag-format, duplicate, and supply-reference rules. Give it a tag and those
  rules can finally see it.
- **You changed a spelling to a minority one.** `NAMING_NORMALIZATION` flags
  whichever spelling is less common. Correcting one row of five toward a spelling
  used by two rows can move the warning rather than remove it.

## Stopping

The defensible stopping point is **zero errors**, with each remaining warning
either fixed or written down with the reason it was accepted. The tool has no way
to record that acceptance — no annotation, no sign-off, no suppression — so the
reasons belong in your handover paperwork, and the PDF report
(chapter [14](14-pdf-report.md)) is the attachment they refer to.

Chasing 100 is worth it only when the remaining warnings are genuinely clerical.
A register with eight `PANEL_LOCATION_MISMATCH` warnings that are all correct
will never reach 100, and should not be edited until it does.

---

[← Reading and filtering findings](10-reading-findings.md) · [Manual index](README.md) · [Next: Comparing two revisions →](12-comparing-revisions.md)
