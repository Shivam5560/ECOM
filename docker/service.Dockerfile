FROM python:3.12-slim AS python-base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

FROM python-base AS runtime-base

COPY docker/requirements-base.txt /tmp/requirements-base.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements-base.txt && \
    rm /tmp/requirements-base.txt

# Install curl (needed by consul-register.sh to call Consul HTTP API)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

FROM python-base AS tooling-base
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install uv

FROM tooling-base AS wheel-builder

COPY core-common ./core-common
COPY msg-common ./msg-common
COPY auth-service ./auth-service
COPY user-service ./user-service
COPY product-service ./product-service
COPY order-service ./order-service
COPY payment-service ./payment-service
COPY invoice-service ./invoice-service
COPY notification-service ./notification-service
COPY workflow-service ./workflow-service

RUN --mount=type=cache,target=/root/.cache/uv \
    uv build --wheel --out-dir /wheels core-common && \
    uv build --wheel --out-dir /wheels msg-common && \
    uv build --wheel --out-dir /wheels auth-service && \
    uv build --wheel --out-dir /wheels user-service && \
    uv build --wheel --out-dir /wheels product-service && \
    uv build --wheel --out-dir /wheels order-service && \
    uv build --wheel --out-dir /wheels payment-service && \
    uv build --wheel --out-dir /wheels invoice-service && \
    uv build --wheel --out-dir /wheels notification-service && \
    uv build --wheel --out-dir /wheels workflow-service

FROM runtime-base AS runtime

ENV MODULE=""

COPY --from=wheel-builder /wheels/*.whl /wheels/
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl && \
    rm -rf /wheels

# Copy Consul registration entrypoint script
COPY docker/consul-register.sh /usr/local/bin/consul-register.sh
RUN chmod +x /usr/local/bin/consul-register.sh

WORKDIR /app

# consul-register.sh runs first → registers with Consul → then execs uvicorn
ENTRYPOINT ["/usr/local/bin/consul-register.sh"]
CMD ["sh", "-c", "python -m uvicorn ${MODULE} --factory --host 0.0.0.0 --port 8000"]
