FROM python:3.11.18-slim@sha256:db20d8506e2f15b6db39b40b6015ca46bae855dec6dd326d462cfe79ae972893 AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Dependencies go into a pip-free virtualenv so only the app's own packages are shipped;
# the builder's pip is upgraded first so no vulnerable installer touches the downloads
RUN python -m pip install --upgrade "pip>=26.1.2" \
 && python -m venv --without-pip /opt/venv

# requirements.txt is a fully pinned, hashed lock: pip rejects any package or file that doesn't match it
COPY requirements.txt .
RUN pip --python /opt/venv/bin/python install --require-hashes --no-deps -r requirements.txt

FROM python:3.11.18-slim@sha256:db20d8506e2f15b6db39b40b6015ca46bae855dec6dd326d462cfe79ae972893 AS runner

WORKDIR /app

# Fault simulation stays off unless a local/isolated environment overrides it
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    DEMO_API_FAULT_SIMULATION_ENABLED=false

# Packaging tools are not needed at runtime: removing pip and setuptools (which vendors
# wheel and jaraco.context) drops their CVEs and leaves no installer inside the container
RUN python -m pip uninstall -y pip setuptools wheel \
 && rm -rf /usr/local/lib/python3.11/ensurepip /usr/local/bin/pip*

COPY --from=builder /opt/venv /opt/venv

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
