FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EAV_DATABASE_URL=sqlite:////data/electrical_asset_validator.db

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /data \
    && chown app:app /data

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --upgrade pip \
    && python -m pip install .

USER app

EXPOSE 8000

CMD ["uvicorn", "electrical_asset_validator.main:app", "--host", "0.0.0.0", "--port", "8000"]
