# Multi-stage Dockerfile for the auth service.
# Build from the repo root: docker build -f services/auth/Dockerfile .

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

COPY services/auth/pyproject.toml /build/services/auth/
COPY services/auth/app/ /build/services/auth/app/

RUN pip install --upgrade pip wheel && \
    pip wheel --wheel-dir /wheels \
        /build \
        /build/services/auth

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
        shopcloud-auth && \
    rm -rf /wheels

USER 10001:10001

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
