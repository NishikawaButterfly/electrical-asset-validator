# 5. Mapping non-standard columns

[← Uploading a file](04-uploading.md) · [Manual index](README.md) · [Next: Running a validation →](06-running-a-validation.md)

Nobody hands you snake_case. This chapter is about validating a register whose
headers are the ones the contractor's tool wrote, without editing the file.

## When the mapping panel appears

The moment you select a file, the page asks the server what its headers are. If
every canonical field was matched, nothing happens and you go straight to
**Run validation**. If one or more canonical fields could not be matched, a panel
appears under the file, headed **Map unrecognized columns**.

The panel shows only the source headers that matched *nothing*. Headers that
already matched are not listed, because there is nothing to decide about them.

## A worked example

`sample-data/case-study/register-as-received.csv` is a 22-row register from a
fictional Block C fit-out. Its header row:

```csv
Tag,Asset Name,Asset Type,Location,Panel,Circuit Ref,Voltage (V),Power (kW),Status
```

Five of the nine match on their own — `Asset Name`, `Asset Type`, `Location`,
`Circuit Ref`, and `Status`, because matching ignores case and turns spaces into
underscores. Four do not: `Tag` and `Panel` are shorter than the canonical
names, and the parentheses in `Voltage (V)` and `Power (kW)` survive
normalization as `voltage_(v)` and `power_(kw)`.

So the panel appears, and says:

> **Map unrecognized columns**
> Still missing: asset_tag, panel_tag, voltage_v, power_kw.

with one row per unmatched header:

| Source header | Dropdown offers |
|---------------|-----------------|
| `Tag` | Don't map · asset_tag · panel_tag · voltage_v · power_kw |
| `Panel` | Don't map · asset_tag · panel_tag · voltage_v · power_kw |
| `Voltage (V)` | Don't map · asset_tag · panel_tag · voltage_v · power_kw |
| `Power (kW)` | Don't map · asset_tag · panel_tag · voltage_v · power_kw |

Each dropdown offers only the canonical fields that are still missing, plus
**Don't map**. You cannot use the panel to redirect a header that already
matched.

**Step by step:**

1. Set `Tag` to `asset_tag`.
2. Set `Panel` to `panel_tag`.
3. Set `Voltage (V)` to `voltage_v`.
4. Set `Power (kW)` to `power_kw`.

The line at the top of the panel updates as you go, and when the last one is set
it reads:

> Every canonical field is covered.

5. Click **Run validation**.

## What the mapping changes

The same file, same data, same rules:

| | Unmapped | Mapped |
|---|---------|--------|
| Quality score | **0.0** | **72.7** |
| Rows | 22 | 22 |
| Valid rows | 0 | 16 |
| Errors | 72 | 6 |
| Warnings | 19 | 4 |
| Information | 4 | 0 |
| Total findings | 95 | 10 |

Unmapped, the register produces four `MISSING_COLUMN` errors, which force the
score to zero and make every row untrusted, plus a `REQUIRED_FIELD` error on
every row for each of the four fields that now look empty, plus four
`UNEXPECTED_COLUMN` information findings for the headers that matched nothing.
None of those 95 findings describes anything wrong with the data.

Mapped, you get the 10 findings that are actually about the register — a
duplicate tag, a missing status, a missing power, a negative voltage, an unknown
status value, a panel that is not in the file, and a fan with no supply
information. Chapter [11](11-correcting-and-revalidating.md) works through
correcting them.

## Rules the mapping panel enforces for you

The panel will not let you build most invalid mappings, but the server checks
anyway, and its refusals are worth recognising if you ever send a mapping
yourself:

| Mistake | Response |
|---------|----------|
| Two headers mapped to the same field | `Multiple source headers map to the same canonical field: asset_tag.` |
| A target that is not one of the nine | `'asset_reference' is not a canonical field. Canonical fields are: asset_tag, asset_name, asset_type, location, panel_tag, circuit_ref, voltage_v, power_kw, status.` |
| A source header that is not in the file | `Mapped source headers are not present in the file: nope.` |
| A mapping that collides with a header that already matched | `Applying the mapping produces duplicate columns: asset_type.` |
| A mapping that is not valid JSON | `The column mapping must be a valid JSON object of source headers to canonical fields.` |

All five come back as HTTP 422, and the page shows them in the red banner. That
fourth one is the subtle case: mapping `Asset Name` to `asset_type` in a file
that already has an `Asset Type` column would produce two `asset_type` columns,
so it is refused rather than silently preferring one.

Mapped source headers are normalized the same way as file headers, so
`{"Voltage (V)": "voltage_v"}` and `{"voltage (v)": "voltage_v"}` mean the same
thing.

## Mapping over the API

The same mapping is a `mapping` form field holding a JSON object of source
header to canonical field:

```bash
curl --fail-with-body --cookie-jar jar.txt --cookie jar.txt \
  -F "file=@sample-data/case-study/register-as-received.csv;type=text/csv" \
  -F 'mapping={"Tag":"asset_tag","Panel":"panel_tag","Voltage (V)":"voltage_v","Power (kW)":"power_kw"}' \
  http://localhost:8000/api/v1/validations
```

You can also ask what the headers are without validating anything. This is what
the page does when you select a file, and it stores nothing:

```bash
curl -F "file=@sample-data/case-study/register-as-received.csv;type=text/csv" \
  http://localhost:8000/api/v1/inspections
```

```json
{
  "filename": "register-as-received.csv",
  "columns": [
    {"header": "Tag", "canonical_field": null},
    {"header": "Asset Name", "canonical_field": "asset_name"},
    {"header": "Asset Type", "canonical_field": "asset_type"},
    {"header": "Location", "canonical_field": "location"},
    {"header": "Panel", "canonical_field": null},
    {"header": "Circuit Ref", "canonical_field": "circuit_ref"},
    {"header": "Voltage (V)", "canonical_field": null},
    {"header": "Power (kW)", "canonical_field": null},
    {"header": "Status", "canonical_field": "status"}
  ],
  "unmatched_canonical_fields": ["asset_tag", "panel_tag", "voltage_v", "power_kw"]
}
```

## Two limitations worth planning around

**A mapping is not saved.** It applies to one upload. A register that arrives in
the same non-standard format every month has to be mapped again every month —
four dropdowns each time. There is no saved profile, no template, and no way to
export a mapping and reuse it. If that is tedious, rename the headers in your
working copy once and keep the renamed file as your working format.

**The comparison form does not offer mapping at all.** The **Compare revisions**
tab has no mapping panel, and the page never sends a mapping with a comparison —
so from the web page, two revisions with non-standard headers cannot be compared.
Attempting it gives:

```
The before file is missing canonical columns: asset_tag, panel_tag, voltage_v, power_kw.
```

The API does accept a `mapping` field on a comparison, and it works: the same two
files with the mapping above compared cleanly as 24 unchanged assets. So the
options are to rename the headers in your copies, or to run that one comparison
from the command line:

```bash
curl --fail-with-body --cookie-jar jar.txt --cookie jar.txt \
  -F "before_file=@revision-1.csv;type=text/csv" \
  -F "after_file=@revision-2.csv;type=text/csv" \
  -F 'mapping={"Tag":"asset_tag","Panel":"panel_tag","Voltage (V)":"voltage_v","Power (kW)":"power_kw"}' \
  http://localhost:8000/api/v1/comparisons
```

One mapping is applied to **both** files, so the two revisions must use the same
headers as each other. If the format changed between revisions, rename the
headers in your copies instead.

---

[← Uploading a file](04-uploading.md) · [Manual index](README.md) · [Next: Running a validation →](06-running-a-validation.md)
