# 8. Errors versus warnings

[← The quality score](07-quality-score.md) · [Manual index](README.md) · [Next: Rule reference →](09-rule-reference.md)

Every finding carries one of three severities. The distinction is not cosmetic:
it is the difference between "this file cannot be trusted" and "an engineer
should look at this".

| Severity | What it means | What it costs | What you should do |
|----------|---------------|---------------|--------------------|
| **error** | The row cannot be trusted or compared safely. | 8 penalty points; the row stops counting as valid | Correct the source data before handover |
| **warning** | The row is readable, but something about it deserves a look. | 3 penalty points | Decide: correct it, or record why it is right |
| **info** | An observation about the file. | Nothing | Usually nothing |

The severity that comes back from the software is authoritative. There is no
setting that changes a rule's severity, no way to suppress a rule, and no way to
mark a finding as accepted. Judgement about warnings lives in your handover
paperwork, not in the tool.

## Errors

Nine rules can produce an error. They fall into three groups.

**The file's shape is wrong.** `MISSING_COLUMN` — a canonical column is absent.
This one is different from every other finding: it sets the score to zero, marks
every row invalid, and usually means you needed a column mapping
(chapter [5](05-column-mapping.md)) rather than that anything is wrong with the
data.

**Identity is broken.** `DUPLICATE_ASSET_TAG`, `ASSET_TAG_FORMAT` on
`asset_tag`, `ASSET_TAG_LENGTH`, and `REQUIRED_FIELD` on `asset_tag`. These are
the errors that matter most, because `asset_tag` is how revisions are matched. A
register with a duplicate tag cannot be compared at all — the comparison refuses
it outright (chapter [12](12-comparing-revisions.md)).

**A value cannot be what it claims.** `REQUIRED_FIELD` on the other six
mandatory fields, `INVALID_NUMBER`, `VALUE_OUT_OF_RANGE`, and `INVALID_STATUS`.
A blank rated power, a voltage of `-230`, a `power_kw` of `not-a-number`, a
status of `commissioning`.

**Errors are the acceptance gate.** "Zero errors" is a defensible thing to
require before a register is accepted, because every error is either a fact
about the file being unusable or a cell that is provably wrong. The quality score
is not a good gate; chapter [7](07-quality-score.md) explains why.

## Warnings

Nine rules can produce a warning, and they are not all the same kind of thing.
It helps to sort them by how likely they are to mean a genuine defect.

**Usually a real problem.** `UNKNOWN_PANEL_REFERENCE` — a load points at a board
that is not in the register. Either the board is missing from the file or the
reference is stale; both are worth fixing before handover.
`DUPLICATE_CIRCUIT_REFERENCE` — two live assets claim the same way out of the
same board. That is either a data error or a real double-loaded circuit.

**Often a real problem, sometimes correct.** `MISSING_PANEL_REFERENCE` and
`MISSING_CIRCUIT_REFERENCE` — a non-panel asset with no supply information.
Frequently just incomplete data, but genuinely correct for equipment fed from
outside the scope of the register. `PANEL_LOCATION_MISMATCH` — an asset in a
different room from its board. Completely normal for a pump fed from a plant-room
MCC, and a red flag when it says a load in one building is fed from another.
`INVALID_PANEL_REFERENCE` — the referenced row exists but is not classified as a
panel; frequently a naming-convention artefact rather than a fault, since the
software recognises only four words as panel-like (chapter
[3](03-preparing-a-register.md)).

**Usually clerical.** `ASSET_TAG_FORMAT` on `panel_tag`,
`CIRCUIT_REFERENCE_FORMAT`, `NAMING_NORMALIZATION`, and `POSSIBLE_TYPO`. These
are about consistency, and they are the ones to look at when the score is low but
nothing is actually wrong. `POSSIBLE_TYPO` in particular is a guess: it fires
when a value appears once and closely resembles a value that appears repeatedly,
and it will happily flag `Plant Room B` as a possible misspelling of
`Plant Room A` when both rooms exist.

**One warning is about the tool, not your data.** `FINDING_LIMIT_REACHED` says
the result was truncated at 10,000 findings. See chapter [19](19-limits.md).

## Information

Only one rule produces information: `UNEXPECTED_COLUMN`, once per column outside
the nine canonical ones. It costs nothing and does not need action. A register
with a `commissioning_date` and a `notes` column scored **100** with two of these.

Its practical use is as a check on yourself: if you expected a mapping to consume
a column and it appears here instead, the mapping did not take.

## What no severity tells you

No rule at any severity checks anything electrical. The engine does not know
that:

- a `motor` with `power_kw` of `0` is probably a data error;
- `230` in a register whose other lighting circuits are all `400` is suspicious;
- a `ups` should be on an essential board;
- a board with forty loads on twelve circuits is over-subscribed;
- an asset marked `decommissioned` still feeding live loads is a safety issue.

`power_kw` of `0` is explicitly legal — every panel in the sample registers uses
it. `voltage_v` accepts anything above 0 up to 1,000,000, so `1` volt and
`999,999` volts both pass. A register can score 100 and be electrically wrong in
every way that matters. The software checks that the file says something
coherent, and stops there.

---

[← The quality score](07-quality-score.md) · [Manual index](README.md) · [Next: Rule reference →](09-rule-reference.md)
