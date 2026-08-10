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
| `EAV_DEMO_RETENTION_MINUTES` | `0` | Delete stored runs older than this many minutes; `0` keeps them |
| `EAV_API_TOKENS` | empty | Comma-separated shared bearer tokens; empty leaves the API open with session-cookie scoping |
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
- `GET /api/v1/config`
- `POST /api/v1/validations` with multipart field `file`
- `GET /api/v1/validations`
- `GET /api/v1/validations/{id}`
- `GET /api/v1/validations/{id}/report.xlsx`
- `GET /api/v1/validations/{id}/report.pdf`
- `POST /api/v1/comparisons` with multipart fields `before_file` and
  `after_file`
- `GET /api/v1/comparisons/{id}`

## Optional token authentication

`EAV_API_TOKENS` accepts one or more comma-separated tokens
(`alpha-token,beta-token`); empty entries are rejected at startup with a
clear error. When any tokens are configured:

- Every data route (validations, comparisons, reports, inspections)
  requires `Authorization: Bearer <token>` and answers 401 with a
  `WWW-Authenticate: Bearer` challenge otherwise. `GET /health` and
  `GET /config` stay open: orchestrator health checks and the frontend's
  auth discovery must work before credentials exist, and neither route
  exposes stored data.
- The token replaces the session cookie as the scope key for stored runs.
  Runs created with one token answer 404 to every other token, exactly as
  session scoping treats a foreign session. The cookie is neither read nor
  set in this mode, so API clients need no cookie jar.
- Runs store a SHA-256 of the token (`token:<hex>` in the existing
  `session_token` column), never the raw token, so a database dump cannot
  leak working credentials. Consequence: rotating a token orphans the runs
  created with it.
- Token comparison uses `secrets.compare_digest` against every configured
  token so response timing does not leak partial matches.
- `GET /config` reports `{"auth_required": true}` so the web UI knows to
  ask for a token.

Tokens are shared secrets, not user accounts: there is no per-user
identity, role model, or audit trail, and everyone holding a token shares
one pool of runs. Transport security is the deployer's job - terminate TLS
in front of the API before sending real tokens over a network. With
`EAV_API_TOKENS` unset, behavior is exactly the pre-token, session-scoped
behavior described below.

## Session scoping

With `EAV_API_TOKENS` unset (the default), stored runs are keyed to an
opaque `eav_session` cookie (httponly, random, minted on first use).
Listings return only the calling session's
runs, and fetching another session's run or report returns 404. This is
isolation between browser sessions, not authentication: anyone who has
the cookie value has the session. API clients that want to read a run
back later must keep a cookie jar, for example
`curl --cookie-jar cookies.txt` on the create and
`curl --cookie cookies.txt` on the fetch. Upgrading an existing
deployment needs the `session_token` column added to `validation_runs`
and `comparison_runs`, or a recreated database; there is no migration
tooling in this repository.

When `EAV_DEMO_RETENTION_MINUTES` is set above zero, runs older than the
window are deleted together with their findings and diffs. The sweep is
lazy: it happens at the start of the next API request rather than on a
scheduler, so an idle instance deletes expired data as soon as anything
(including a health check) touches the API again.
