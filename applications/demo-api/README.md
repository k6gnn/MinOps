# Demo API

A small FastAPI service that MinOps monitors and deliberately disrupts during tests. It exposes a normal endpoint, liveness and readiness probes, structured JSON request logs, and optional fault-simulation endpoints (HTTP 500, unhandled exception, latency, readiness toggle).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Service message and version |
| GET | `/healthz` | Liveness: always 200 while the process runs |
| GET | `/readyz` | Readiness: 200 when ready, 503 when the simulated dependency is down |
| GET | `/demo/failure/500` | Handled HTTP 500 |
| GET | `/demo/failure/exception` | Unhandled exception, generic HTTP 500 |
| GET | `/demo/failure/timeout?delay=N` | Waits `N` seconds (default 5, max `DEMO_API_MAX_DELAY_SECONDS`) |
| POST | `/demo/toggle-ready?ready=true\|false` | Switches `/readyz` between 200 and 503 |

`/demo/*` routes exist **only** when fault simulation is enabled. Otherwise they return 404 and are hidden from `/docs`.

## Run locally

Commands run from `applications/demo-api` (PowerShell shown; on Linux/macOS activate with `source .venv/bin/activate`):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r ../../requirements-dev.txt

uvicorn app.main:create_app --factory --reload
```

Open http://localhost:8000/docs. To enable the fault-simulation endpoints:

```powershell
$env:DEMO_API_FAULT_SIMULATION_ENABLED = "true"
uvicorn app.main:create_app --factory --reload
```

## Run the tests

```powershell
pytest
```

## Docker

Build from the **repository root** (the build uses the root `requirements.txt`):

```powershell
docker build -t demo-api .

# Fault simulation off (default)
docker run --rm -p 8000:8000 demo-api

# Fault simulation on (local / isolated test environments only)
docker run --rm -p 8000:8000 -e DEMO_API_FAULT_SIMULATION_ENABLED=true demo-api
```

The image runs as a non-root user and has a health check on `/healthz`; `docker ps` shows the container as `healthy` once it is up.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `DEMO_API_FAULT_SIMULATION_ENABLED` | `false` | Registers the `/demo/*` endpoints. Must be a boolean (`true`/`false`/`1`/`0`); any other value stops startup with a validation error. |
| `DEMO_API_MAX_DELAY_SECONDS` | `30` | Upper bound for `delay` in timeout mode. Out-of-range values return 422. |

Never enable fault simulation in shared or production-like environments.

## Logging

Every request produces one JSON log line on stdout with `timestamp`, `level`, `service`, `version`, `request_id`, `method`, `route`, `status_code`, `duration_ms`, and `error_category` for failed requests. The request ID is taken from the `X-Request-ID` header when present (otherwise a UUID is generated) and returned in the `X-Request-ID` response header.
