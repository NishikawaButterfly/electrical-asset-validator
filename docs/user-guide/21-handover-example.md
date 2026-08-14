# 21. A handover, end to end

[← Troubleshooting](20-troubleshooting.md) · [Manual index](README.md)

One register, from the email it arrived in to the evidence pack. Every number,
message, and refusal on this page came from running the sequence; you can repeat
it with the files in [`sample-data/`](../../sample-data/).

**The situation.** A fit-out contractor has handed over the electrical asset
register for a fictional Block C. The handover meeting is on Thursday. You have
to say whether the register is fit to accept, and show why.

The file is
[`sample-data/case-study/register-as-received.csv`](../../sample-data/case-study/register-as-received.csv):
22 rows, five distribution panels and the loads behind them, with a header row
nobody asked for.

```csv
Tag,Asset Name,Asset Type,Location,Panel,Circuit Ref,Voltage (V),Power (kW),Status
```

---

## Step 1 — Upload it and map the headers

Open the validator, leave the **Validate file** tab selected, and choose the
file. The mapping panel appears immediately, because four canonical fields could
not be matched:

> Still missing: asset_tag, panel_tag, voltage_v, power_kw.

Set the four dropdowns:

| Source header | Map to |
|---------------|--------|
| `Tag` | `asset_tag` |
| `Panel` | `panel_tag` |
| `Voltage (V)` | `voltage_v` |
| `Power (kW)` | `power_kw` |

The line at the top changes to **Every canonical field is covered.** Click
**Run validation**.

Do not skip this. The same file without the mapping scores **0.0** with 95
findings that say nothing about the data — see chapter
[5](05-column-mapping.md).

## Step 2 — Read the result

| | |
|---|---|
| Quality score | **72.7** — Needs attention |
| Rows checked | 22, `16 valid` |
| Errors | **6** |
| Warnings | **4** |

Ten findings, in the order the page shows them:

```
warning  NAMING_NORMALIZATION       row 8   PDU-B-01   status       Use the canonical lowercase status value.                     → active
error    REQUIRED_FIELD             row 9   UPS-C-01   status       'status' is required.
error    REQUIRED_FIELD             row 14  PMP-C-03   power_kw     'power_kw' is required.
error    VALUE_OUT_OF_RANGE         row 21  LGT-C-202  voltage_v    'voltage_v' must be greater than 0 and no greater than 1,000,000.
error    INVALID_STATUS             row 22  HTR-C-01   status       Status must be one of: active, standby, maintenance, decommissioned.
error    DUPLICATE_ASSET_TAG        row 17  FAN-C-02   asset_tag    Asset tag 'FAN-C-02' occurs more than once.
error    DUPLICATE_ASSET_TAG        row 18  FAN-C-02   asset_tag    Asset tag 'FAN-C-02' occurs more than once.
warning  UNKNOWN_PANEL_REFERENCE    row 15  CHL-C-01   panel_tag    Panel 'PNL-C-ROOF' is not present in this register.
warning  MISSING_PANEL_REFERENCE    row 23  EF-C-01    panel_tag    A non-panel asset should reference its supplying panel.
warning  MISSING_CIRCUIT_REFERENCE  row 23  EF-C-01    circuit_ref  A non-panel asset should reference its supplying circuit.
```

Read as an engineer rather than as a list, this is four separate conversations:

- **Two assets have no data.** `UPS-C-01` has no status; `PMP-C-03` has no rated
  power. Nobody can supply these but the contractor.
- **Two values are wrong and obviously so.** `LGT-C-202` at `-230` volts is a
  stray minus sign. `HTR-C-01` is `in service`, which is `active` in this
  vocabulary.
- **Two different fans share one tag.** Rows 17 and 18 are both `FAN-C-02` — a
  toilet extract fan and a kitchen extract fan. Somebody copied a row.
- **Two boards are missing from the register.** The chiller points at
  `PNL-C-ROOF`, which is not in the file, and the car-park fan has no supply
  information at all. Both are documentation gaps, not site problems.

**Export the Excel report now**, before you correct anything. This is the record
of the register as it was handed over, and it is the attachment your covering
note will refer to (chapter [15](15-xlsx-report.md)).

## Step 3 — Send back what you cannot fix

Four of the ten need the contractor: the missing status, the missing rated power,
and confirmation of which fan is which. Do not invent values to clear findings.
The filtered Issues sheet — severity `error` — is the list to attach to that
email.

Their answers come back: the UPS is `active`, the condenser pump is `11.0` kW,
and the second `FAN-C-02` is a different unit that should be `FAN-C-03`.

## Step 4 — Correct and revalidate

Eight edits, listed in full in chapter
[11](11-correcting-and-revalidating.md), produce
[`register-corrected.csv`](../../sample-data/case-study/register-corrected.csv).
Two of them add rows: the roof panel `PNL-C-ROOF` and the car-park panel
`PNL-C-CP`, each with `power_kw` of `0` and no supply cells of their own.

Upload it, with the same mapping again — mappings are not saved:

| | As received | Corrected |
|---|---|---|
| Quality score | 72.7 | **100** |
| Rows | 22 | **24** |
| Valid rows | 16 | **24** |
| Errors | 6 | **0** |
| Warnings | 4 | **0** |

Zero errors is the acceptance gate (chapter [8](08-errors-and-warnings.md)). A
score of exactly 100 means nothing at all was reported.

## Step 5 — What you cannot do, and why it matters

The obvious next question is "show me exactly what I changed" — a comparison of
the received file against the corrected one. It is refused:

```
The before file contains duplicate asset_tag 'FAN-C-02'.
```

**The register you were handed cannot be compared with anything.** A duplicate
tag means two rows share an identity, so nothing can be matched across revisions.
That is the concrete meaning of "not fit to hand over", and it is worth putting
in the covering note in exactly those terms: not "the file had some errors" but
"the file could not be diffed against any other revision until the duplicate was
resolved."

Record your own changes from the correction list in step 4. The tool cannot
produce that diff for you.

## Step 6 — Compare against the previously issued revision

This is the comparison the handover meeting actually wants: what changed between
the revision operations already holds and the one you are accepting.

Block C has no earlier issued revision, so this step uses the clean pair that
ships for it — `revision-a.csv` as the previously issued revision and
`revision-b.csv` as the new one. The mechanics and the reading are identical.

Select the **Compare revisions** tab, put the earlier file in **Before revision**
and the newer one in **After revision**, and click **Compare revisions**.

| Added | Removed | Changed | Unchanged |
|-------|---------|---------|-----------|
| **1** | **1** | **4** | **10** |

```
Added     MTR-009   row 16
Removed   HTR-003   row 16

MTR-001   power_kw   18.5 → 22
MTR-002   status     standby → active
UPS-001   status     active → decommissioned
DB-001    voltage_v  400 → 415
```

Six questions for the meeting, and only the software can tell you to ask them:

1. `MTR-009` is new. Was a pump installed, or was it always there and missing
   from revision A?
2. `HTR-003` is gone. Was the dock heater removed, or was the row deleted? A
   removal is not a decommissioning (chapter [13](13-added-removed-modified.md)).
3. `MTR-001` went from 18.5 to 22 kW. New pump, or corrected rating? These have
   different consequences for the board.
4. `MTR-002` moved from standby to active — did the duty pair swap?
5. `UPS-001` is now decommissioned. Correctly recorded, and worth confirming it
   is isolated.
6. `DB-001` moved from 400 to 415 V. Almost certainly a data correction, but ask.

**Copy this off the screen before you navigate away.** A comparison has no export
and cannot be reopened from the page (chapter [12](12-comparing-revisions.md)).

## Step 7 — Assemble the evidence

For the corrected register, from its result panel:

- **Download PDF** — a one-page document reading:

  ```
  Electrical Asset Validation Report
  Source: register-corrected.csv    Validation ID: 27178854-c721-4a06-8fa5-f1b4538c29ef

  Quality score  Rows  Valid rows  Errors  Warnings  Information
  100.0          24    24          0       0         0

  Findings
  No issues were found.
  ```

- **Download Excel** — the same numbers on its Summary sheet, with a full UTC
  timestamp, plus the 24 validated rows on its Data sheet.

The pack for Thursday, then:

| Item | Where it comes from |
|------|--------------------|
| The register as received, with its 10 findings | Excel report from step 2 |
| The list of errors returned to the contractor | Issues sheet, filtered to `error` |
| The corrected register's clean certificate | PDF report from step 4 |
| The corrected register as validated | Data sheet of the step 4 Excel report |
| What changed since the last issued revision | Copied from step 6 |
| The date each validation ran | Summary sheet of either Excel report |
| Warnings accepted rather than fixed, with reasons | **You write this.** Nothing in the tool records it |

Two things you must add by hand, because neither export carries them: **the date
on the PDF** (it has none on the page — chapter [14](14-pdf-report.md)) and **the
software version**, from `/api/v1/health`, so the finding list stays meaningful
when the rules change.

## What you can now say

Not "the register looks fine" but:

> The register as received scored 72.7 with six errors, including a duplicate
> asset tag that made it impossible to compare against any previous revision.
> Four errors were referred to the contractor and resolved; two boards missing
> from the register were added. The accepted revision scores 100 over 24 assets
> with no findings. Against the previously issued revision it adds one asset,
> removes one, and changes four; the removal and the two status changes are on
> the agenda.

That is a paragraph somebody can act on, every clause of it traceable to an
attachment.

---

[← Troubleshooting](20-troubleshooting.md) · [Manual index](README.md)
