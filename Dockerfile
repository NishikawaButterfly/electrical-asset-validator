FROM node:22-alpine AS frontend

WORKDIR /build

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .

ARG VITE_API_BASE_URL=
ARG VITE_DEMO_NOTICE=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL} \
    VITE_DEMO_NOTICE=${VITE_DEMO_NOTICE}

RUN npm run build

# uv turns backend/uv.lock into the hash-pinned list this image installs, in
# a stage of its own, so it never ends up in the image. It is a FROM line
# rather than a COPY --from of the image name because Dependabot updates image
# tags in FROM lines only.
FROM ghcr.io/astral-sh/uv:0.13.7 AS uv

FROM python:3.12-slim AS lock

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /lock

COPY backend/pyproject.toml backend/uv.lock ./

# --locked fails the build when uv.lock no longer matches pyproject.toml.
RUN uv export --locked --no-default-groups --group image --no-emit-project \
    --output-file requirements.txt

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=lock /lock/requirements.txt ./
COPY backend/pyproject.toml backend/README.md backend/LICENSE ./
COPY backend/src ./src

# The exported set and nothing else: every file is checked against the hash
# the lock records and comes from a wheel. The project then goes in without
# resolving anything, and pip check confirms that the set satisfies every
# requirement, the project's included.
RUN python -m pip install --no-deps --require-hashes --only-binary=:all: \
        --requirement requirements.txt \
    && python -m pip install --no-deps . \
    && python -m pip check

COPY --from=frontend /build/dist ./static

# The single-container image serves the built frontend from the backend and
# keeps its database on ephemeral storage, so a restart wipes demo data.
ENV EAV_STATIC_DIR=/app/static \
    EAV_DATABASE_URL=sqlite:////tmp/electrical_asset_validator.db

USER app

EXPOSE 8000

CMD ["uvicorn", "electrical_asset_validator.main:app", "--host", "0.0.0.0", "--port", "8000"]
