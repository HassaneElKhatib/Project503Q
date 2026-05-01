# Multi-stage Dockerfile.
# Stage 1 builds wheels, stage 2 is the slim runtime as a non-root user.
# This pattern keeps the runtime image small and avoids shipping build tools.

# ----- builder -----
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build deps for any wheels that need compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy shared libs first (they change less often -> better layer caching)
COPY libs/ /build/libs/
COPY pyproject.toml /build/

# Copy this service's own pyproject + source
COPY services/_template/pyproject.toml /build/services/_template/
COPY services/_template/app/ /build/services/_template/app/

# Build a wheelhouse so we don't need build tools in runtime
RUN pip install --upgrade pip wheel && \
    pip wheel --wheel-dir /wheels \
        /build \
        /build/services/_template

# ----- runtime -----
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Create non-root user (UID 10001 by convention so K8s securityContext matches)
RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --no-create-home --shell /sbin/nologin app

WORKDIR /app

# Install only runtime deps from the wheelhouse
COPY --from=builder /wheels /wheels
RUN pip install --no-index --find-links=/wheels \
        shopcloud-libs \
        shopcloud-template && \
    rm -rf /wheels

# Drop privileges
USER 10001:10001

EXPOSE 8000

# Liveness via curl is intentionally NOT in the image - K8s does HTTP probes itself
ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
