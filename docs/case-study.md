# Case study: from handover file to clean register

This is a worked example built around the two files in
[`../sample-data/case-study/`](../sample-data/case-study/). Everything in
them is fictional. The building, the equipment, and the numbers were invented
for this walkthrough. The API responses and the committed report are real
output from the backend, and
[`../backend/tests/test_case_study.py`](../backend/tests/test_case_study.py)
re-runs the whole thing in CI, so the numbers on this page cannot silently
drift away from what the rules actually produce.

The commands below assume a backend on `http://localhost:8000`, for example
the one started by `docker compose up --build`.

## The file as it arrived

`register-as-received.csv` plays the part of a register handed over at the
end of a fit-out job in a fictional Block C. It has 22 data rows: five
distribution panels plus the loads behind them. The header row is the first
obstacle:

```csv
Tag,Asset Name,Asset Type,Location,Panel,Circuit Ref,Voltage (V),Power (kW),Status
```

Nobody hands you snake_case. This is the kind of export a contractor's tool
produces, and the data behind it has the usual handover problems: a tag used
twice, cells left empty, a stray sign, a status value the schema has never
heard of, and one fan with no supply information at all.

## Step 1: inspect the headers

Before validating anything I ask the API what it can make of the headers:

```bash
curl --fail-with-body \
  -F "file=@sample-data/case-study/register-as-received.csv;type=text/csv" \
  http://localhost:8000/api/v1/inspections
```

The response matches five headers on its own. `Asset Name`, `Asset Type`,
`Location`, `Circuit Ref`, and `Status` all normalize to canonical fields,
because header matching tolerates case, spaces, and hyphens. Four do not:

```json
{
  "filename": "register-as-received.csv",
  "columns": [
    {"header": "Tag", "canonical_field": null},
    {"header": "Asset Name", "canonical_field": "asset_name"},
    {"header": "Panel", "canonical_field": null},
    {"header": "Voltage (V)", "canonical_field": null},
    {"header": "Power (kW)", "canonical_field": null}
  ],
  "unmatched_canonical_fields": ["asset_tag", "panel_tag", "voltage_v", "power_kw"]
}
```

(Matched columns trimmed for space.) `Tag` and `Panel` are shorter than any
canonical name, and the parentheses in `Voltage (V)` survive normalization,
so the service refuses to guess. In the web UI this is the point where the
upload form offers a mapping dropdown for each unmatched header. On the API
the same mapping is a JSON object in the `mapping` form field.

## Step 2: validate with a mapping

```bash
curl --fail-with-body \
  -F "file=@sample-data/case-study/register-as-received.csv;type=text/csv" \
  -F 'mapping={"Tag": "asset_tag", "Panel": "panel_tag", "Voltage (V)": "voltage_v", "Power (kW)": "power_kw"}' \
  http://localhost:8000/api/v1/validations
```

The summary of the response (id, timestamps, and download links trimmed):

```json
{
  "filename": "register-as-received.csv",
  "quality_score": 72.7,
  "metrics": {
    "total_rows": 22,
    "valid_rows": 16,
    "issue_count": 10,
    "returned_issue_count": 10,
    "issues_truncated": false,
    "error_count": 6,
    "warning_count": 4,
    "info_count": 0
  }
}
```

Six errors and four warnings across 22 rows give a quality score of 72.7.
Sixteen rows carry no error. These are the ten findings, exactly as the API
returned them. Row numbers refer to source file rows, counting the header as
row 1.

| Severity | Rule | Row | Asset tag | Field | Message |
| --- | --- | --- | --- | --- | --- |
| warning | `NAMING_NORMALIZATION` | 8 | PDU-B-01 | status | Use the canonical lowercase status value. |
| error | `REQUIRED_FIELD` | 9 | UPS-C-01 | status | 'status' is required. |
| error | `REQUIRED_FIELD` | 14 | PMP-C-03 | power_kw | 'power_kw' is required. |
| error | `VALUE_OUT_OF_RANGE` | 21 | LGT-C-202 | voltage_v | 'voltage_v' must be greater than 0 and no greater than 1,000,000. |
| error | `INVALID_STATUS` | 22 | HTR-C-01 | status | Status must be one of: active, standby, maintenance, decommissioned. |
| error | `DUPLICATE_ASSET_TAG` | 17 | FAN-C-02 | asset_tag | Asset tag 'FAN-C-02' occurs more than once. |
| error | `DUPLICATE_ASSET_TAG` | 18 | FAN-C-02 | asset_tag | Asset tag 'FAN-C-02' occurs more than once. |
| warning | `UNKNOWN_PANEL_REFERENCE` | 15 | CHL-C-01 | panel_tag | Panel 'PNL-C-ROOF' is not present in this register. |
| warning | `MISSING_PANEL_REFERENCE` | 23 | EF-C-01 | panel_tag | A non-panel asset should reference its supplying panel. |
| warning | `MISSING_CIRCUIT_REFERENCE` | 23 | EF-C-01 | circuit_ref | A non-panel asset should reference its supplying circuit. |

The first finding also carries a suggestion, `active`, because the value
`Active` is valid apart from its capitalization. The rule definitions behind
each identifier are catalogued in [`rules.md`](rules.md).

## Step 3: correct the register

Each finding points at a row and a field, so the corrections are mechanical:

- Row 8: `Active` becomes `active`.
- Row 9: the UPS is running, so its empty status becomes `active`.
- Row 14: the condenser water pump gets its rating, `11.0` kW, same as the
  chilled water pumps beside it.
- Row 15: the chiller referenced `PNL-C-ROOF`, a panel that was genuinely
  missing from the file. I added a `Roof Plant Panel` row rather than
  deleting the reference.
- Rows 17 and 18: two different fans shared the tag `FAN-C-02`. The kitchen
  extract fan is renamed `FAN-C-03`.
- Row 21: the meeting room lighting voltage `-230` loses its stray minus
  sign.
- Row 22: `in service` is not a lifecycle state the schema knows, so the
  water heater becomes `active`.
- Row 23: the car park extract fan had no supply information at all. A
  `Car Park Panel` row was added and the fan now points at it on circuit
  `C01`.

The result is `register-corrected.csv`: 24 rows, because two missing panels
were added. The nonstandard headers were left exactly as they arrived. That
is deliberate. The mapping travels with the request, not with the file, so
there is no need to touch a column the contractor's tool will keep exporting
the same way.

## Step 4: re-validate

Same command, same mapping, corrected file:

```bash
curl --fail-with-body \
  -F "file=@sample-data/case-study/register-corrected.csv;type=text/csv" \
  -F 'mapping={"Tag": "asset_tag", "Panel": "panel_tag", "Voltage (V)": "voltage_v", "Power (kW)": "power_kw"}' \
  http://localhost:8000/api/v1/validations
```

```json
{
  "filename": "register-corrected.csv",
  "quality_score": 100.0,
  "metrics": {
    "total_rows": 24,
    "valid_rows": 24,
    "issue_count": 0,
    "returned_issue_count": 0,
    "issues_truncated": false,
    "error_count": 0,
    "warning_count": 0,
    "info_count": 0
  },
  "issues": []
}
```

Score 100, no findings, every row valid.

## Step 5: try to diff the two revisions

With both files in hand, the obvious next question is what changed between
them. The comparison endpoint accepts the same mapping and applies it to both
uploads:

```bash
curl \
  -F "before_file=@sample-data/case-study/register-as-received.csv;type=text/csv" \
  -F "after_file=@sample-data/case-study/register-corrected.csv;type=text/csv" \
  -F 'mapping={"Tag": "asset_tag", "Panel": "panel_tag", "Voltage (V)": "voltage_v", "Power (kW)": "power_kw"}' \
  http://localhost:8000/api/v1/comparisons
```

The answer is an HTTP 400:

```json
{"detail": "The before file contains duplicate asset_tag 'FAN-C-02'."}
```

This refusal is the point. Comparison identity comes from `asset_tag`, and
the as-received file uses `FAN-C-02` for two different fans, so there is no
reliable way to say what happened to "the" FAN-C-02. The engine will not
guess. A register only becomes a usable comparison baseline once its
identity errors are fixed, which is why the intended order is validate
first, correct, then diff the revisions that follow. The change log for this
particular cleanup is the correction list in step 3. For a clean diff of two
valid revisions, compare `revision-a.csv` with `revision-b.csv` from
[`../sample-data/`](../sample-data/README.md).

## Step 6: export the report

Every validation response includes download links. The XLSX report for the
as-received run is committed at
[`case-study/register-as-received-report.xlsx`](case-study/register-as-received-report.xlsx),
byte for byte as the endpoint returned it:

```bash
curl --fail-with-body -o register-as-received-report.xlsx \
  http://localhost:8000/api/v1/validations/<id>/report.xlsx
```

It has three sheets. `Summary` repeats the metrics above, `Issues` lists the
ten findings with their rows and suggestions, and `Data` holds the parsed
register under canonical headers. A PDF variant is available from the same
response. Validation ids are generated per upload, so your `<id>` and
timestamps will differ; the findings will not.
