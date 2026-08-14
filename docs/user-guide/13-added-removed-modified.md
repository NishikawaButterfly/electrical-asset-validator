# 13. Added, removed, and modified assets

[← Comparing two revisions](12-comparing-revisions.md) · [Manual index](README.md) · [Next: The PDF report →](14-pdf-report.md)

The four categories look obvious. Three of them behave in ways worth knowing
before you present a comparison to anybody.

## The definitions

Every asset tag in either file lands in exactly one category:

| Category | Definition |
|----------|------------|
| **Added** | The tag is in the after file and not in the before file |
| **Removed** | The tag is in the before file and not in the after file |
| **Changed** | The tag is in both, and at least one of the eight comparable fields differs |
| **Unchanged** | The tag is in both, and all eight fields are identical |

The eight comparable fields are the nine canonical columns minus `asset_tag`
itself. Anything else in your file — extra columns, formatting, row order — is
invisible to the comparison. Moving a row from line 5 to line 40 changes nothing.

## Added

An addition means only that a tag is new to this file. It does **not** mean new
equipment was installed. In practice, an addition is one of:

- Genuinely new plant.
- Existing plant that was missing from the earlier register — a documentation
  fix, not a site change.
- An asset whose tag was changed (see below).
- The same asset, still present, whose tag was mistyped in one revision.

The detail view gives you the tag and the row it sits on in the after file:

```
Added   MTR-009   row 16
```

That is all. There is no name, no type, no location, no rating — so a comparison
alone cannot tell you what `MTR-009` is. You need the register open next to it.

## Removed

The mirror image, and the one that deserves attention on a handover. A removal
means a tag that used to be in the register is not any more, and the interesting
question is always *why*:

- The equipment was actually removed, and the register is right.
- The equipment is still installed and somebody deleted the row.
- The tag was changed, so the asset is present under a new name and appears as an
  addition elsewhere in the same comparison.

**A removal is not a decommissioning.** Marking an asset `decommissioned` keeps
it in the register and shows as a *change* to `status` — as `UPS-001` does in the
sample pair. Deleting the row shows as a removal. The two are different
statements, and the second loses the history.

```
Removed   HTR-003   row 16
```

The row number is the line in the **before** file, which is where you go to see
what it was.

## Changed

One card per asset, listing only the fields that differ, with the old value and
the new. From the sample pair:

| Asset | Field | Before | After | What it probably means |
|-------|-------|--------|-------|------------------------|
| `MTR-001` | `power_kw` | `18.5` | `22` | The pump was replaced, or the rating was corrected |
| `MTR-002` | `status` | `standby` | `active` | The duty/standby pair was swapped |
| `UPS-001` | `status` | `active` | `decommissioned` | Taken out of service, kept in the record |
| `DB-001` | `voltage_v` | `400` | `415` | Almost certainly a data correction, not a change to the installation |

The software says what changed. It has no opinion on which of these matters, and
they are shown in one flat list. A `status` change from `active` to
`decommissioned` and a corrected spelling in `asset_name` are presented
identically.

Empty cells are shown as **Empty** rather than left blank, so filling in a
missing `panel_tag` reads `Empty → PNL-MCC-01`.

Values that only differ in how the number was written do not appear at all.
`22.0` becoming `22`, or `400` becoming `400.0`, is not a change
(chapter [12](12-comparing-revisions.md)). Case is not normalized, so `active`
becoming `Active` **is** reported as a change.

## Renamed tags: one removal plus one addition

This is the behaviour to understand before you rely on a comparison.

**There is no rename detection.** The comparison matches on `asset_tag` and
nothing else. If a tag changes, the asset leaves one category and enters another,
and nothing connects the two halves.

Taking the sample pair and renaming `MTR-001` to `PMP-001` in the after file
only, the result changes like this:

| | Original pair | With `MTR-001` renamed |
|---|---------------|------------------------|
| Added | 1 | **2** — `MTR-009`, `PMP-001` |
| Removed | 1 | **2** — `HTR-003`, `MTR-001` |
| Changed | 4 | **3** |
| Unchanged | 10 | 10 |

Three things happened at once, and all three are misleading if you read the
summary without the detail:

1. The renamed asset appears twice, as a removal and an addition, with nothing
   marking them as the same equipment.
2. The **changed** count went *down*, from 4 to 3. `MTR-001`'s rated power
   change from `18.5` to `22` disappeared — the asset is no longer in both files
   under one tag, so the field-level comparison never happened. **A rename hides
   every other change to that asset.**
3. Nothing in the output hints that a rename is what occurred. `PMP-001` and
   `MTR-001` sit in different tabs.

Two practical consequences:

- **Treat `asset_tag` as immutable.** Once a register is issued, a tag is an
  identity, not a description. Renaming `MTR-001` to `PMP-001` because it is a
  pump costs you the audit trail for that asset permanently.
- **When you must rename** — resolving a duplicate, for instance, as chapter
  [11](11-correcting-and-revalidating.md) does — record it separately. The
  comparison cannot carry that information, so a note in the handover pack is the
  only place it can live.

Read added and removed together, sorted by tag, whenever the counts are equal and
non-zero. A pair of similar tags on the two lists is usually a rename.

## Unchanged

A count and nothing else. There is no list of unchanged tags anywhere in the page
or the API. The number is still useful as a sanity check: added + removed +
changed + unchanged should account for every asset you expect, and a total well
below your asset count means one of the two files is short.

For the sample pair, 1 + 1 + 4 + 10 = 16 tags across two 15-row registers — the
14 shared tags, plus one on each side.

---

[← Comparing two revisions](12-comparing-revisions.md) · [Manual index](README.md) · [Next: The PDF report →](14-pdf-report.md)
