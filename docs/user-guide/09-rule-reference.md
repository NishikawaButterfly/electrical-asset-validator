# 9. Rule reference

[← Errors versus warnings](08-errors-and-warnings.md) · [Manual index](README.md) · [Next: Reading and filtering findings →](10-reading-findings.md)

Every rule the engine can report, with the message it actually produces. Each
message below was copied from a run against a file built to trigger that rule;
where a rule produces more than one wording, all of them are here.

A finding always carries the **rule name**, a **severity**, the **row** in your
file (empty for findings about the file as a whole), the **asset tag** on that
row (empty when the tag itself is missing), the **field**, the **message**, and
sometimes a **suggestion** — a corrected value you can paste back.

| # | Rule | Severity | About |
|---|------|----------|-------|
| 1 | [`MISSING_COLUMN`](#1-missing_column) | error | The file |
| 2 | [`UNEXPECTED_COLUMN`](#2-unexpected_column) | info | The file |
| 3 | [`REQUIRED_FIELD`](#3-required_field) | error | A cell |
| 4 | [`DUPLICATE_ASSET_TAG`](#4-duplicate_asset_tag) | error | Identity |
| 5 | [`ASSET_TAG_FORMAT`](#5-asset_tag_format) | error / warning | Identity |
| 6 | [`ASSET_TAG_LENGTH`](#6-asset_tag_length) | error | Identity |
| 7 | [`INVALID_NUMBER`](#7-invalid_number) | error | A rating |
| 8 | [`VALUE_OUT_OF_RANGE`](#8-value_out_of_range) | error | A rating |
| 9 | [`INVALID_STATUS`](#9-invalid_status) | error | Lifecycle |
| 10 | [`NAMING_NORMALIZATION`](#10-naming_normalization) | warning | Consistency |
| 11 | [`POSSIBLE_TYPO`](#11-possible_typo) | warning | Consistency |
| 12 | [`MISSING_PANEL_REFERENCE`](#12-missing_panel_reference) | warning | Supply |
| 13 | [`MISSING_CIRCUIT_REFERENCE`](#13-missing_circuit_reference) | warning | Supply |
| 14 | [`UNKNOWN_PANEL_REFERENCE`](#14-unknown_panel_reference) | warning | Supply |
| 15 | [`INVALID_PANEL_REFERENCE`](#15-invalid_panel_reference) | warning | Supply |
| 16 | [`PANEL_LOCATION_MISMATCH`](#16-panel_location_mismatch) | warning | Supply |
| 17 | [`DUPLICATE_CIRCUIT_REFERENCE`](#17-duplicate_circuit_reference) | warning | Supply |
| 18 | [`CIRCUIT_REFERENCE_FORMAT`](#18-circuit_reference_format) | warning | Supply |
| 19 | [`FINDING_LIMIT_REACHED`](#19-finding_limit_reached) | warning | The result |

---

## 1. `MISSING_COLUMN`

**Severity:** error · **Field:** the missing column · **Row:** none

**Checks** that all nine canonical columns are present after header matching.
One finding per missing column, with the canonical name as the suggestion.

```
Required column 'asset_tag' is missing.
Required column 'panel_tag' is missing.
Required column 'voltage_v' is missing.
Required column 'power_kw' is missing.
```

**Why it matters.** Nothing else in the result can be trusted. A missing
`voltage_v` column does not mean the equipment has no voltage; it means the
software never saw the column, and every row is now reporting a blank one. This
rule forces the score to **0** and marks every row invalid, no matter how good
the data is.

**How to fix.** Almost always the file is fine and the *headers* are not. Check
the header row against chapter [2](02-input-files.md), and use the column mapping
in chapter [5](05-column-mapping.md) rather than editing the file. Seeing all
nine reported at once — as a semicolon-delimited CSV produces — means the file was
not split into columns at all; see chapter [20](20-troubleshooting.md).

---

## 2. `UNEXPECTED_COLUMN`

**Severity:** info · **Field:** the column · **Row:** none

**Checks** for columns outside the nine canonical ones. One finding per column,
using the normalized form of the header.

```
Column 'commissioning_date' is not part of the canonical schema.
Column 'voltage_(v)' is not part of the canonical schema.
```

**Why it matters.** It usually does not. Extra columns are ignored and cost
nothing — a register with two of them scored 100. Its real use is as a check on a
mapping: `voltage_(v)` appearing here means the header `Voltage (V)` was not
mapped and `voltage_v` is missing.

**How to fix.** Nothing, unless the column should have been mapped. Note that
extra columns are dropped from the Excel export's Data sheet
(chapter [15](15-xlsx-report.md)).

---

## 3. `REQUIRED_FIELD`

**Severity:** error · **Field:** the empty one · **Row:** the row

**Checks** that seven fields are non-empty in every row: `asset_tag`,
`asset_name`, `asset_type`, `location`, `voltage_v`, `power_kw`, `status`. A cell
containing only spaces counts as empty. `panel_tag` and `circuit_ref` are not in
this list — they have their own, gentler rules.

```
'asset_tag' is required.
'asset_name' is required.
'asset_type' is required.
'location' is required.
'voltage_v' is required.
'power_kw' is required.
'status' is required.
```

**Why it matters.** A row without a tag cannot be tracked between revisions at
all — it will appear as an addition every time. A missing `power_kw` or
`voltage_v` is a hole in the record that any downstream load schedule or
maintenance system will inherit. A missing `location` makes an asset
unfindable on site.

**How to fix.** Fill the cell. If the value is genuinely unknown, that is worth
knowing before handover — this rule is doing its job. There is no "not
applicable" value; the seven fields are required for every asset, including
panels.

Note that when `asset_tag` is the missing field, the finding has no asset tag to
show, and the findings table shows a dash. Use the row number.

---

## 4. `DUPLICATE_ASSET_TAG`

**Severity:** error · **Field:** `asset_tag` · **Row:** every row involved

**Checks** for the same tag appearing more than once. Comparison is done after
trimming, upper-casing, and turning spaces and underscores into single hyphens —
so `MTR-001`, `mtr 001`, and `MTR_001` are the same tag. **Every** row in the
group is reported, not just the second one.

```
Asset tag 'FAN-004' occurs more than once.
```

The tag in the message is the normalized form.

**Why it matters.** This is the most consequential error in the catalogue.
`asset_tag` is the identity used to match revisions, so a register with a
duplicate cannot be compared at all — the comparison refuses the whole file
(chapter [12](12-comparing-revisions.md)). It also means two different pieces of
equipment share one row of history in anything built on this register.

**How to fix.** Decide which asset keeps the tag and give the other one its own.
In `invalid-register.csv`, rows 15 and 16 are both `FAN-004`, and they are
different fans — an extract fan on circuit C18 and a "Duplicate Extract Fan" on
C19. The corrected case-study register does exactly this: the second `FAN-C-02`
becomes `FAN-C-03`.

Renaming a tag has a consequence in the next comparison: it shows as one removal
and one addition, not a rename. Chapter [13](13-added-removed-modified.md).

---

## 5. `ASSET_TAG_FORMAT`

**Severity:** **error** on `asset_tag`, **warning** on `panel_tag`

**Checks** that a tag starts with an upper-case letter and contains only
upper-case letters, digits, and single hyphens between groups. `MTR-001`,
`PNL-C-L1`, and `A1` pass. `mtr-007`, `MTR 009`, `7MTR-008`, and `MTR--001` do
not.

On `asset_tag`:

```
Asset tags must start with a letter and contain only uppercase letters, numbers, and hyphens.
```

On `panel_tag`, the same rule name with a different message and a lower severity:

```
Panel references must use the canonical asset-tag format.
```

Both offer a suggestion when the value can be cleaned into a legal tag —
`mtr-007` suggests `MTR-007`, `MTR 009` suggests `MTR-009`, `pnl mcc 01` suggests
`PNL-MCC-01`. When it cannot, the suggestion is empty: `7MTR-008` starts with a
digit and there is nothing to propose.

**Why it matters.** Tag matching between revisions is done on the normalized
form, so a tag that only differs in case or spacing will still match — but a tag
that is not in the canonical form at all is rejected outright by the comparison,
which refuses the file with `The before file has an invalid asset_tag 'mtr 001'
on row 3.` A register full of inconsistent tags is also a register where nobody
can search reliably.

**How to fix.** Apply the suggestion. Where there is no suggestion, invent a
conforming tag: tags must begin with a letter, so a purely numeric scheme needs a
prefix.

---

## 6. `ASSET_TAG_LENGTH`

**Severity:** error · **Field:** `asset_tag`

**Checks** that a tag is no longer than 128 characters.

```
Asset tags may contain no more than 128 characters.
```

**Why it matters.** Very long tags are almost always a symptom — a description
pasted into the tag column, or several concatenated fields. It is also the
boundary the comparison enforces, which refuses a file with an over-long tag.

**How to fix.** Shorten the tag, and check whether the tag column has been
loaded with something that belongs in `asset_name`. A tag this long fails the
format rule as well, so expect two errors on the row.

---

## 7. `INVALID_NUMBER`

**Severity:** error · **Fields:** `voltage_v`, `power_kw`

**Checks** that a non-empty rating is a finite number.

```
'voltage_v' must be a finite number.
'power_kw' must be a finite number.
```

**Why it matters.** A rating that is not a number is not a rating. Anything
built on the register — a load schedule, a diversity calculation, a maintenance
plan — will either fail on it or silently treat it as zero.

**How to fix.** Remove whatever is not a number. In practice it is one of four
things:

- Text where a number belongs: `not-a-number`, `TBC`, `see note`, `twenty`.
- A unit suffix: `400 V`, `18.5 kW`. Strip the unit; the column names carry it.
- A comma decimal separator: `18,5`. Use `18.5`.
- **A broken formula in an XLSX file.** A formula is read as the result the
  workbook stored for it, so `=200*2` is `400` and passes. But if the workbook
  stored `#DIV/0!`, `#REF!`, or `#N/A`, that error value is what arrives here.
  Fix the formula in the source workbook and save it again.

A number too large to represent, such as `1e400`, is reported here too rather
than as an out-of-range value.

**What no longer produces this.** A working formula. Earlier versions read every
calculated cell as its own text and reported it here, which turned a register
assembled from another sheet into a wall of errors that said nothing about the
data. A workbook that has never been calculated at all — one
written by a script rather than saved by a spreadsheet program — is refused
before any rule runs, with a single message about the file; chapter
[2](02-input-files.md) shows it.

---

## 8. `VALUE_OUT_OF_RANGE`

**Severity:** error · **Fields:** `voltage_v`, `power_kw`

**Checks** the two ratings against their permitted ranges. The two fields have
deliberately different rules, and the messages say so:

```
'voltage_v' must be greater than 0 and no greater than 1,000,000.
'power_kw' must be at least 0 and no greater than 1,000,000.
```

| Value | `voltage_v` | `power_kw` |
|-------|-------------|-----------|
| Negative | error | error |
| `0` | **error** | **accepted** |
| `1` to `1,000,000` | accepted | accepted |
| Above `1,000,000` | error | error |

**Why it matters.** `power_kw` of zero is legal because that is how panels are
recorded — every panel in the sample registers carries `0`. `voltage_v` of zero
is not, because nothing in an electrical register operates at zero volts; a zero
there means the cell was never filled in properly. Negative values are almost
always a stray minus sign, and `LGT-101` in `invalid-register.csv` (`-2.4` kW)
and `LGT-C-202` in the case-study register (`-230` V) are exactly that.

**How to fix.** Correct the sign or the value. Be aware of what this rule does
**not** catch: `1` volt, `999,999` volts, and a 900 kW toilet extract fan all
pass. The range is a sanity bound, not an engineering check.

---

## 9. `INVALID_STATUS`

**Severity:** error · **Field:** `status`

**Checks** that `status` is one of exactly four values, compared after trimming,
lower-casing, and turning spaces and hyphens into underscores:

`active` · `standby` · `maintenance` · `decommissioned`

```
Status must be one of: active, standby, maintenance, decommissioned.
```

A suggestion is offered when the value is a close misspelling of a legal one:
`activ` suggests `active`, and `Decommisioned` suggests `decommissioned`. It is
not offered when the value is a different word: `commissioning` and `in service`
are both reported with no suggestion, even though `commissioning` is superficially
similar to `decommissioned`.

**Why it matters.** `status` is the only enumerated field in the contract, and
two rules depend on it: assets marked `decommissioned` are exempt from needing
supply information, and only non-decommissioned assets are counted when looking
for two loads on one circuit. An unrecognised status therefore does not just fail
this rule — it puts the row into the "live equipment" side of two other rules.

**How to fix.** Map your own vocabulary onto the four. `in service`,
`energised`, and `operational` are all `active`. `commissioning` needs a
decision: usually `active` if it is energised, `standby` if it is not. There is
no way to add a fifth status.

---

## 10. `NAMING_NORMALIZATION`

**Severity:** warning · **Fields:** `status`, `asset_name`, `asset_type`,
`location`

One rule name covering three different checks, each with its own message.

**Status that is legal but not lower case.** The value is accepted, and the
canonical spelling is suggested:

```
Use the canonical lowercase status value.        suggestion: active
```

`Active`, `ACTIVE`, and `Standby ` all produce this.

**Repeated whitespace inside a value:**

```
Remove repeated whitespace from 'asset_name'.    suggestion: Pump 1
Remove repeated whitespace from 'asset_type'.
Remove repeated whitespace from 'location'.
```

**A minority spelling of a value used elsewhere in the file.** Applies to
`asset_type` and `location`. The software collects every spelling that differs
only in case or spacing, picks the most frequent as preferred, and flags the
others:

```
Use a consistent spelling for 'asset_type'.      suggestion: motor
Use a consistent spelling for 'location'.        suggestion: Plant Room A
```

`Motor` among six rows of `motor` gets the warning; `plant room a` among rows of
`Plant Room A` gets it too.

**Why it matters.** Inconsistent categories fragment every list built from the
register. A maintenance system filtering on `asset_type = motor` silently misses
the rows typed `Motor`. Trailing and repeated spaces are invisible in a
spreadsheet and cause exactly the same problem.

**How to fix.** Apply the suggestion — it is the spelling the rest of your file
already uses. Do it in the source register rather than the export, or it will
come back next revision.

**One quirk to expect.** A value with repeated whitespace usually produces
**two** warnings on the same field: one to remove the whitespace, and one saying
the spelling is inconsistent, both with the same suggestion. `Plant  Room  A` on
one row produced both. It costs six penalty points instead of three, and fixing
the whitespace clears both.

---

## 11. `POSSIBLE_TYPO`

**Severity:** warning · **Fields:** `asset_type`, `location`

**Checks** for a value that appears exactly once and closely resembles a value
that appears repeatedly. Only compares values that start with the same letter.

```
'Plant Roon A' may be a typo or naming variant.      suggestion: Plant Room A
'Plant Room B' may be a typo or naming variant.      suggestion: Plant Room A
```

**Why it matters.** A misspelled location is worse than an inconsistent one,
because nothing will ever match it. A single `Plant Roon A` among forty
`Plant Room A` rows is invisible to the eye and to any filter.

**How to fix.** Check it, and correct it if it is a typo. **Expect false
positives.** The second example above is one: `Plant Room B` is a real, different
room in `invalid-register.csv`, and the rule flags it purely because it looks
like the room next door and appears only once. This warning asks a question; it
does not assert a defect. Where the value is correct, the right response is to
note it in your handover paperwork — there is no way to mark it accepted in the
tool.

---

## 12. `MISSING_PANEL_REFERENCE`

**Severity:** warning · **Field:** `panel_tag`

**Checks** that every asset which is neither a panel nor decommissioned names a
supplying panel.

```
A non-panel asset should reference its supplying panel.
```

**Why it matters.** A load with no recorded supply cannot be traced, isolated,
or included in a board schedule. For an operations team taking over a building,
"what feeds this?" is the first question, and this warning marks every asset that
cannot answer it.

**How to fix.** Fill in `panel_tag` with the tag of the board that supplies it.
Two exemptions are already built in, so you do not need to invent values for
them: rows whose `asset_type` contains `panel`, `switchboard`, or
`distribution board`, and rows whose `status` is `decommissioned`. If your boards
are typed something else — `MCC`, `DB`, `switchgear` — they are not recognised as
panels and will each collect this warning; see chapter
[3](03-preparing-a-register.md).

---

## 13. `MISSING_CIRCUIT_REFERENCE`

**Severity:** warning · **Field:** `circuit_ref`

**Checks** the same set of assets for a circuit reference.

```
A non-panel asset should reference its supplying circuit.
```

**Why it matters.** The panel tells you which board; the circuit tells you which
way out of it. Without it, isolating one load means isolating the board. Together
with the panel reference it is what makes a register usable as a schedule rather
than an inventory.

**How to fix.** Fill in `circuit_ref`. The same two exemptions apply as for the
panel reference, and the two warnings usually appear together on the same row —
`EF-C-01` in the case-study register, a car-park extract fan with no supply
information at all, collects both.

---

## 14. `UNKNOWN_PANEL_REFERENCE`

**Severity:** warning · **Field:** `panel_tag`

**Checks** that the panel a row names exists as a row in the same register.

```
Panel 'PNL-C-ROOF' is not present in this register.
Panel 'PNL-MCC-03' is not present in this register.
```

The tag in the message is the normalized form of what you wrote.

**Why it matters.** This is the rule that finds stale references. Either the
board was renamed and its loads were not updated, or the register is incomplete
and the board is missing from it. In `invalid-register.csv` the pump on row 17
points at `PNL-MCC-03`, which does not exist; in the case-study register a
chiller points at `PNL-C-ROOF`, a roof panel nobody put in the file.

**How to fix.** Either add the board as a row in its own right — with `power_kw`
of `0` and its own supply cells empty — or correct the reference to the board that
really feeds it. Adding the missing boards is usually right, and it is the single
change that clears the most warnings from a load-only register.

Remember there is no cross-file checking: a board in another register is an
unknown panel here (chapter [6](06-running-a-validation.md)).

---

## 15. `INVALID_PANEL_REFERENCE`

**Severity:** warning · **Field:** `panel_tag`

**Checks** that the row a `panel_tag` points at is classified as a panel.

```
Referenced asset 'MTR-001' is not classified as a panel.
```

**Why it matters.** A load fed from another load is either a data error — the
wrong tag was pasted in — or a real sub-feed that the flat register cannot express.
Either way somebody should look.

**How to fix.** First check whether it is a naming-convention artefact rather
than a fault. The software recognises a panel only by the words `panel`,
`switchboard`, `distribution board`, or `distribution_board` in `asset_type`. If
your boards are typed `MCC` or `DB`, every load will produce this warning and the
data is fine — adjust `asset_type`, or accept the warnings knowingly. If the
reference really does point at a motor, correct it.

---

## 16. `PANEL_LOCATION_MISMATCH`

**Severity:** warning · **Field:** `panel_tag`

**Checks** whether an asset's `location` differs from its panel's `location`,
compared case-insensitively after collapsing whitespace. The panel's location is
offered as the suggestion.

```
Asset location differs from panel 'PNL-MCC-01' location.    suggestion: Plant Room A
Asset location differs from panel 'PNL-PWR-03' location.    suggestion: Loading Dock
```

**Why it matters.** It is the cheapest available check on whether the supply
hierarchy is plausible. A load recorded in one building fed from a board in
another is usually a stale reference.

**How to fix.** Usually nothing. **This is the warning most likely to be
correct** — a plant-room MCC feeding pumps all over a building produces one of
these per pump, and every one is right. Treat it as a prompt: look at the pairs it
lists, satisfy yourself the supply is real, and correct only the ones that are
wrong. In `invalid-register.csv`, `MTR-002` sits in `Plant Room B` and is fed from
a board in `Plant Room A` — plausible for a pump, and it also happens to be the
row that triggers `POSSIBLE_TYPO`.

The suggestion is the panel's location, which is only the right correction when
the asset's location is the wrong one.

---

## 17. `DUPLICATE_CIRCUIT_REFERENCE`

**Severity:** warning · **Field:** `circuit_ref`

**Checks** for two or more assets claiming the same panel and circuit
combination. Decommissioned assets are excluded, and only rows that name both a
panel and a circuit are considered. Every row in the group is reported.

```
Circuit 'C01' on panel 'PNL-MCC-01' is assigned to multiple active assets.
```

**Why it matters.** Two live loads on one way is either a data error or a real
shared circuit. If it is real, the board schedule and the protection need to
reflect it; if it is not, one of the two references is stale — and this is the
rule that catches a load moved to a new way without its old entry being updated.

**How to fix.** Look at both rows. Correct the one that is wrong, or — if the
circuit genuinely serves both, as a lighting way often does — record that
decision. The tool has no way to accept it, so the warning will return on every
revision.

Note that the same circuit reference on *different* panels is fine, which is why
`C01` appearing on every board in a register produces nothing.

---

## 18. `CIRCUIT_REFERENCE_FORMAT`

**Severity:** warning · **Field:** `circuit_ref`

**Checks** that a circuit reference is upper-case letters and digits, in groups
separated by single hyphens, slashes, or periods. `C01`, `L1/22`, and `DB-A.14`
pass. `c04` and `C05*1` do not.

```
Circuit references may contain uppercase letters, numbers, hyphens, slashes, and periods.
```

A suggestion appears when the value cleans up into a legal one — `c04` suggests
`C04`. `C05*1` gets none, because the asterisk cannot be removed automatically.

**Why it matters.** Consistency, mostly. Circuit references are compared exactly
when looking for two loads on one way, so `c04` and `C04` on the same board would
not be seen as the same circuit if the format rule did not push everyone to one
spelling.

**How to fix.** Apply the suggestion, or remove the character that is not
allowed. Spaces and underscores inside a reference are turned into hyphens by the
suggestion, so `C 04` becomes `C-04`, not `C04` — check that is what you want
before pasting it back.

---

## 19. `FINDING_LIMIT_REACHED`

**Severity:** warning · **Field:** none · **Row:** none

Not about your data. It appears as the last finding when a validation produced
more than 10,000 findings and the list was cut short.

```
The validation reached the 10,000-finding output limit. Correct the listed findings and run validation again.
```

**Why it matters.** The counts and the score still reflect **every** finding —
a 6,001-row register that produced 12,000 warnings reported all 12,000 in its
warning count and scored 40.0 accordingly — but only the first 9,999 are listed,
followed by this notice. Anything below the cut is invisible until you re-run.

**How to fix.** Correct what is listed and validate again. A result this size
almost always comes from one systematic problem: 12,000 findings in that example
were two warnings on each of 6,000 rows, all fixed by one change. See chapter
[19](19-limits.md).

---

## What no rule checks

Worth stating once more in the place people will look. There is no rule for:
protection coordination, cable sizing, discrimination, earthing, IP rating,
maintenance interval, asset age, duty and standby pairing, load balance across
phases, or compliance with any standard. There is no check that a `motor` has a
non-zero `power_kw`, that voltages within one board agree, or that the register
is complete.

---

[← Errors versus warnings](08-errors-and-warnings.md) · [Manual index](README.md) · [Next: Reading and filtering findings →](10-reading-findings.md)
