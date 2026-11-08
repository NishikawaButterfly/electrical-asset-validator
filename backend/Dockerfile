# uv turns uv.lock into the hash-pinned list this image installs, in a stage
# of its own, so it never ends up in the image. It is a FROM line rather than
# a COPY --from of the image name because Dependabot updates image tags in
# FROM lines only.
FROM ghcr.io/astral-sh/uv:0.13.7 AS uv

FROM python:3.12-slim AS lock

COPY --from=uv /uv /usr/local/bin/uv

WORKDIR /lock

COPY pyproject.toml uv.lock ./

# --locked fails the build when uv.lock no longer matches pyproject.toml.
RUN uv export --locked --no-default-groups --group image --no-emit-project \
    --output-file requirements.txt

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EAV_DATABASE_URL=sqlite:////data/electrical_asset_validator.db

WORKDIR /app

RUN addgroup --system app && adduser --system --ingroup app app \
    && mkdir -p /data \
    && chown app:app /data

COPY --from=lock /lock/requirements.txt ./
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# The exported set and nothing else: every file is checked against the hash
# the lock records and comes from a wheel. The project then goes in without
# resolving anything, and pip check confirms that the set satisfies every
# requirement, the project's included.
RUN python -m pip install --no-deps --require-hashes --only-binary=:all: \
        --requirement requirements.txt \
    && python -m pip install --no-deps . \
    && python -m pip check

USER app

EXPOSE 8000

CMD ["uvicorn", "electrical_asset_validator.main:app", "--host", "0.0.0.0", "--port", "8000"]
