# 12. Comparing two revisions

[← Correcting and revalidating](11-correcting-and-revalidating.md) · [Manual index](README.md) · [Next: Added, removed, and modified assets →](13-added-removed-modified.md)

## What a comparison answers

"The register was reissued. What actually changed?" It matches the two files row
by row on `asset_tag` and reports four numbers: how many assets are new, how many
are gone, how many changed, and how many are identical.

It is a separate operation from validation. A comparison does not score anything,
does not run any of the rules in chapter [9](09-rule-reference.md), and produces
no findings.

## Running one

1. Select the **Compare revisions** tab.
2. Put the **earlier** register in **Before revision** and the **newer** one in
   **After revision**.
3. Click **Compare revisions**.

The order matters and is not detected. Putting them the wrong way round produces
a valid comparison that reads backwards — every addition becomes a removal.
Comparing `revision-b.csv` against `revision-a.csv` gives the same counts as the
right way round in the sample pair, which is coincidence, not symmetry.

There is no mapping panel on this tab. Both files must already use headers that
match the nine canonical names; chapter [5](05-column-mapping.md) explains the
workaround.

## Reading the result

Comparing `sample-data/revision-a.csv` with `sample-data/revision-b.csv`:

| Panel | Value | Caption on the page |
|-------|-------|--------------------|
| **Added** | 1 | Only in the new revision |
| **Removed** | 1 | Missing from the new revision |
| **Changed** | 4 | Fields differ |
| **Unchanged** | 10 | No detected differences |

Below is a three-tab detail area — **Changed**, **Added**, **Removed** — each
showing its count. **Changed** opens first, listing one card per asset with a
before-and-after table of just the fields that differ:

```
MTR-001   1 field      power_kw   18.5  →  22
MTR-002   1 field      status     standby  →  active
UPS-001   1 field      status     active  →  decommissioned
DB-001    1 field      voltage_v  400  →  415
```

**Added** and **Removed** are plainer — asset tag, the source row in whichever
file it came from, and a badge:

```
Added     MTR-009   row 16
Removed   HTR-003   row 16
```

Chapter [13](13-added-removed-modified.md) explains exactly what each category
means and where it will surprise you.

## What counts as a difference

Only the nine canonical fields are compared, and `asset_tag` itself is excluded —
it is the key, so it cannot differ. Extra columns are ignored entirely: two files
identical except that one has a `notes` column compared as **3 unchanged, 0
changed**.

Values are compared after the same cleaning that validation applies, which means
several ways of writing the same thing do not register as changes. All of these
compared as unchanged:

| Before | After | Reported as |
|--------|-------|-------------|
| `22.0` | `22` | unchanged |
| `400` | `400.0` | unchanged |
| `18.5` | `18.50` | unchanged |
| `Plant Room A` | `  Plant Room A  ` | unchanged |

Case is **not** normalized. `active` → `Active` is reported as a real change to
`status`, which is correct — one of those two is a validation warning — but it does
mean a revision that only changed capitalisation will show up as changed assets.

## What a comparison refuses

Both files must be clean enough to have reliable identity, and the check happens
before anything is compared. Every one of these is an HTTP 400 and produces no
result at all.

| Problem | Message |
|---------|---------|
| A canonical column missing | `The before file is missing canonical columns: asset_tag, panel_tag, voltage_v, power_kw.` |
| A repeated tag | `The after file contains duplicate asset_tag 'FAN-004'.` |
| An empty tag | `The before file has a blank asset_tag on row 3.` |
| A malformed tag | `The before file has an invalid asset_tag 'mtr 001' on row 3.` |

The message always names which of the two files is at fault, so you know which
one to fix.

**This is why you validate before you compare.** Every one of those refusals
corresponds to an error the validation would have shown you first, with the row
number and a suggestion. Trying to compare `revision-a.csv` with
`invalid-register.csv` gets you one line about `FAN-004` and nothing else;
validating `invalid-register.csv` gets you all twelve findings.

Note that a *warning*-only register compares fine. Missing panel references,
location mismatches, and naming inconsistencies do not block a comparison — only
the four identity failures above do.

## Limits

A comparison is rejected when it would produce more than 10,000 details, counting
each added asset, each removed asset, and each individual field change:

```
The comparison exceeds the 10,000-detail output limit. Compare smaller revision segments.
```

Two 5,001-row registers with no tags in common hit this. In practice you only
reach it when comparing two registers that have almost nothing to do with each
other — a genuine revision of a large register changes a small fraction of it.
Chapter [19](19-limits.md) covers the caps.

## Over the API

```bash
curl --fail-with-body --cookie-jar jar.txt --cookie jar.txt \
  -F "before_file=@sample-data/revision-a.csv;type=text/csv" \
  -F "after_file=@sample-data/revision-b.csv;type=text/csv" \
  http://localhost:8000/api/v1/comparisons
```

```json
{
  "id": "0f6c1a29-...",
  "before_filename": "revision-a.csv",
  "after_filename": "revision-b.csv",
  "created_at": "2026-08-14T15:06:02.118Z",
  "summary": {"added": 1, "removed": 1, "changed": 4, "unchanged": 10},
  "added": [{"asset_tag": "MTR-009", "row": 16}],
  "removed": [{"asset_tag": "HTR-003", "row": 16}],
  "changed": [
    {"asset_tag": "DB-001", "changes": [
      {"field": "voltage_v", "before": 400, "after": 415}]},
    {"asset_tag": "MTR-001", "changes": [
      {"field": "power_kw", "before": 18.5, "after": 22}]}
  ]
}
```

Unlike a validation, the API accepts a `mapping` field here — the only way to
compare two registers with non-standard headers (chapter
[5](05-column-mapping.md)). One mapping is applied to both files.

## What a comparison does not give you

- **No export.** There is no PDF or Excel download for a comparison, and no
  print view. To get the result into a handover pack you copy it off the screen,
  or fetch the JSON from the API.
- **No history.** **Recent validations** lists validations only. A comparison
  can be fetched again by its identifier, which the page never shows you — so in
  practice, from the browser, a comparison is gone the moment you navigate away.
  Chapter [16](16-validation-history.md).
- **No validation of the two files.** A comparison tells you what changed, not
  whether either revision is any good. Run both through the validator separately.
- **No list of the unchanged assets.** You get the count, never the tags.

---

[← Correcting and revalidating](11-correcting-and-revalidating.md) · [Manual index](README.md) · [Next: Added, removed, and modified assets →](13-added-removed-modified.md)
