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

# uv turns backend/uv.lock into the hash-pinned lists this image is built
# from, in a stage of its own, so it never ends up in the image. It is a FROM
# line rather than a COPY --from of the image name because Dependabot updates
# images in FROM lines only. The digest holds the stage to the image the tag
# named when it was set: a tag can be moved to another image, a digest cannot.
FROM ghcr.io/astral-sh/uv:0.13.7@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 AS uv

FROM python:3.12-slim AS lock

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /lock

COPY backend/pyproject.toml backend/uv.lock ./

# Two lists: what the image installs, the runtime dependencies and pip, and
# what the project is built with. --locked fails the build when uv.lock no
# longer matches pyproject.toml.
RUN uv export --locked --no-default-groups --group image --no-emit-project \
        --output-file requirements.txt \
    && uv export --locked --only-group build --output-file build-requirements.txt

# The project's wheel, built with the locked build requirements and nothing
# else: without build isolation pip fetches nothing for the build, and
# --check-build-dependencies fails it when what is installed does not meet
# [build-system].requires.
FROM python:3.12-slim AS wheel

WORKDIR /build

COPY --from=lock /lock/build-requirements.txt ./

RUN python -m pip install --no-deps --require-hashes --only-binary=:all: \
        --requirement build-requirements.txt

COPY backend/pyproject.toml backend/README.md backend/LICENSE ./
COPY backend/src ./src

RUN python -m pip wheel --no-deps --no-build-isolation --check-build-dependencies \
        --no-index --wheel-dir /wheels .

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY --from=lock /lock/requirements.txt ./

# The exported set and nothing else: every file is checked against the hash
# the lock records and comes from a wheel.
RUN python -m pip install --no-deps --require-hashes --only-binary=:all: \
        --requirement requirements.txt

COPY --from=wheel /wheels ./wheels

# Then the project's wheel, from that directory alone and without anything it
# would bring with it. pip check confirms that the set meets every
# requirement, the project's included.
RUN python -m pip install --no-deps --no-index wheels/electrical_asset_validator-*.whl \
    && python -m pip check

COPY --from=frontend /build/dist ./static

# The single-container image serves the built frontend from the backend and
# keeps its database on ephemeral storage, so a restart wipes demo data.
ENV EAV_STATIC_DIR=/app/static \
    EAV_DATABASE_URL=sqlite:////tmp/electrical_asset_validator.db

USER app

EXPOSE 8000

CMD ["uvicorn", "electrical_asset_validator.main:app", "--host", "0.0.0.0", "--port", "8000"]
