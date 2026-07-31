# Electrical Asset Validator API

FastAPI backend for validating CSV/XLSX asset registers, comparing revisions,
storing validation history, and exporting Excel/PDF reports.

## Local development

Python 3.12 or newer is required.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
python -m pytest
uvicorn electrical_asset_validator.main:app --reload
```

The API is available at `http://localhost:8000/api/v1`. Interactive API
documentation is available at `/docs`.

## Configuration

Settings use the `EAV_` prefix:

| Variable | Default | Purpose |
| --- | --- | --- |
| `EAV_DATABASE_URL` | `sqlite:///./electrical_asset_validator.db` | SQLAlchemy database URL |
| `EAV_MAX_UPLOAD_MB` | `10` | Maximum size of each uploaded file |
| `EAV_DOCS_ENABLED` | `true` | Enable OpenAPI browser pages |
| `EAV_CORS_ORIGINS` | localhost origins | JSON array of allowed web origins |

For PostgreSQL, use a URL such as
`postgresql+psycopg://validator:validator@db:5432/validator`. Tables are created
idempotently when the application starts. Secrets belong in environment
variables; they are never stored in validation records.

## Canonical columns

`asset_tag`, `asset_name`, `asset_type`, `location`, `panel_tag`,
`circuit_ref`, `voltage_v`, `power_kw`, and `status`.

CSV files must be UTF-8 compatible. XLSX workbooks use the first worksheet.
Header spelling is normalized for casing, spaces, and hyphens, but canonical
snake_case headers are recommended.

The parser accepts at most 50,000 non-empty rows, 64 columns, and 32,767
characters per cell. XLSX inputs also have archive-entry, expanded-size,
compression-ratio, and source-row-extent limits; the used range may not extend
beyond row 250,000. Blank CSV lines are ignored while subsequent findings
retain their original source row numbers. Validation output is capped at
10,000 finding details; summary metrics, invalid-row counts, and the quality
score still account for all detected findings. Comparisons that would exceed
10,000 detailed changes are rejected with a clear error.

Upload request bodies are counted before multipart parsing. The configured
per-file limit therefore also bounds temporary spooling, including chunked
requests and unrecognized multipart fields.

## Main routes

- `GET /api/v1/health`
- `POST /api/v1/validations` with multipart field `file`
- `GET /api/v1/validations`
- `GET /api/v1/validations/{id}`
- `GET /api/v1/validations/{id}/report.xlsx`
- `GET /api/v1/validations/{id}/report.pdf`
- `POST /api/v1/comparisons` with multipart fields `before_file` and
  `after_file`
- `GET /api/v1/comparisons/{id}`
