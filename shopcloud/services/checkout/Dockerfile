# Checkout Dockerfile.
# Same image is also used for the alembic migration Job - that's why we
# bundle migrations/ and alembic.ini.

FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY libs/ /build/libs/
COPY pyproject.toml /build/

COPY services/checkout/pyproject.toml /build/services/checkout/
COPY services/checkout/app/ /build/services/checkout/app/

RUN pip install --upgrade pip wheel && \
    pip wheel --wheel-dir /wheels \
        /build \
        /build/services/checkout

FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --no-create-home --shell /sbin/nologin app

WORKDIR /app

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels \
        shopcloud-libs \
        shopcloud-checkout && \
    # psycopg installed alongside asyncpg for alembic (sync driver)
    pip install --quiet "psycopg[binary]>=3.1" && \
    rm -rf /wheels

# Bundle migrations + alembic config so the migration Job can run them.
# These are tiny so the bloat is negligible (and only one image needs it).
COPY alembic.ini /app/alembic.ini
COPY migrations/ /app/migrations/
# Alembic seed migration reads catalog JSON from this path (same layout as dev checkout).
COPY services/catalog/data /app/services/catalog/data

USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
