FROM python:3.11.18-slim AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11.18-slim AS runner

WORKDIR /app

# Fault simulation stays off unless a local/isolated environment overrides it
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEMO_API_FAULT_SIMULATION_ENABLED=false

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Code stays root-owned so the non-root runtime user can read but not modify it
COPY applications/demo-api/app ./app

RUN adduser --disabled-password --gecos "" --no-create-home appuser
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz')" || exit 1

# One worker per container: readiness state is per process, and scaling is done with replicas.
# The access log is off because the app already writes one structured JSON line per request.
# Graceful shutdown finishes below Kubernetes' default 30s termination grace period.
CMD ["uvicorn", "app.main:create_app", "--factory", \
     "--host", "0.0.0.0", "--port", "8000", \
     "--no-access-log", "--no-server-header", \
     "--timeout-graceful-shutdown", "20"]
