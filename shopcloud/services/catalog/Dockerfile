# Multi-stage Dockerfile for the catalog service.
# Run from the repo root: docker build -f services/catalog/Dockerfile .

# ----- builder -----
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

COPY services/catalog/pyproject.toml /build/services/catalog/
COPY services/catalog/app/ /build/services/catalog/app/

RUN pip install --upgrade pip wheel && \
    pip wheel --wheel-dir /wheels \
        /build \
        /build/services/catalog

# ----- runtime -----
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
        shopcloud-catalog && \
    rm -rf /wheels

# Bake the seed JSON into the image so the container is self-contained on Day 1.
# Day 2: replace with SqlProductRepository and remove this COPY.
COPY services/catalog/data/ /app/data/
ENV PRODUCTS_JSON_PATH=/app/data/products.json

USER 10001:10001

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
