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

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app

COPY backend/pyproject.toml backend/README.md ./
COPY backend/src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install .

COPY --from=frontend /build/dist ./static

# The single-container image serves the built frontend from the backend and
# keeps its database on ephemeral storage, so a restart wipes demo data.
ENV EAV_STATIC_DIR=/app/static \
    EAV_DATABASE_URL=sqlite:////tmp/electrical_asset_validator.db

USER app

EXPOSE 8000

CMD ["uvicorn", "electrical_asset_validator.main:app", "--host", "0.0.0.0", "--port", "8000"]
