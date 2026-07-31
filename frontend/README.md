# Electrical Asset Validator — frontend

React and TypeScript dashboard for validating electrical asset registers and
comparing file revisions. The interface uses only real API responses: empty,
loading, error, and completed states are represented explicitly.

## Run locally

Requires Node.js 22 and the backend on `http://localhost:8000`.

```bash
npm ci
npm run dev
```

Vite serves the app at `http://localhost:5173` and proxies `/api` requests to
the backend. Override the proxy target when needed:

```bash
VITE_API_PROXY_TARGET=http://localhost:8000 npm run dev
```

## Quality checks

```bash
npm run lint
npm run test
npm run build
```

## API integration

- `POST /api/v1/validations` with multipart field `file`
- `GET /api/v1/validations`
- `GET /api/v1/validations/{id}`
- `POST /api/v1/comparisons` with `before_file` and `after_file`
- `GET /api/v1/validations/{id}/report.xlsx`
- `GET /api/v1/validations/{id}/report.pdf`

The browser uses same-origin `/api/v1` by default. `VITE_API_BASE_URL` may be
set at build time when the API is hosted on another origin.

## Container

The production image builds the Vite bundle and serves it with nginx. Nginx
also proxies `/api/` to the Compose service named `backend`.

```bash
docker compose up --build
```

Open `http://localhost:3000`. The frontend image is intended to run in this
Compose network so nginx can resolve the `backend` service.
