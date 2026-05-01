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

COPY services/api-gateway/pyproject.toml /build/services/api-gateway/
COPY services/api-gateway/gateway/ /build/services/api-gateway/gateway/

RUN pip install --upgrade pip wheel && \
    pip wheel --wheel-dir /wheels \
        /build \
        /build/services/api-gateway

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN useradd --uid 10001 --create-home --shell /bin/false app
WORKDIR /app
RUN mkdir -p /data && chown -R 10001:10001 /data /app

COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels \
        shopcloud-libs \
        shopcloud-api-gateway && \
    rm -rf /wheels

COPY services/api-gateway/gateway ./gateway

USER 10001
EXPOSE 8080
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8080"]
