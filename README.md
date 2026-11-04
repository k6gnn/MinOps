# MinOps

A learning-oriented, cloud-native infrastructure operations platform: monitor containerized workloads, detect anomalies, diagnose incidents, and apply only remediations that pass deterministic safety checks.

The full design, architecture and roadmap are in [MinOps_Technical_Project_Documentation.md](MinOps_Technical_Project_Documentation.md). Most of it is planned, not built yet.

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Repository and architecture foundation | Done |
| 1 | Demo application | Done |
| 2 | Containerization | Done |
| 3+ | Kubernetes, observability, ML, incidents, AI diagnosis, remediation | Planned |

## Repository layout

| Path | Contents |
|---|---|
| `applications/demo-api/` | FastAPI workload that MinOps monitors and deliberately disrupts ([README](applications/demo-api/README.md)) |
| `Dockerfile` | Container image for the demo API (build from the repository root) |
| `requirements.in` / `requirements-dev.in` / `requirements-build.in` | Top-level runtime, development and image-build (pip) dependencies (edit these) |
| `requirements.txt` / `requirements-dev.txt` / `requirements-build.txt` | Generated, fully pinned and hashed locks (never edit by hand; see [Dependencies](#dependencies)) |
| `infrastructure/`, `monitoring/`, `ml/`, `services/`, `docs/` | Reserved for later phases |

## Quick start

```powershell
cd applications/demo-api
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r ../../requirements-dev.txt
pytest
uvicorn app.main:create_app --factory --reload
```

With GNU Make available (Linux/macOS/CI), the same tasks are `make install`, `make test`, `make run`, `make run-faults`, `make docker-build` and `make docker-run`.

## Dependencies

Every dependency, including transitive ones, is pinned with SHA-256 hashes, and the image installs with `pip install --require-hashes`. To change dependencies, edit a `.in` file and regenerate its lock:

- `make lock` regenerates `requirements.txt` and `requirements-build.txt` (the pip version used in the image's builder stage) inside the Dockerfile's Python image. The runtime lock must be generated on Linux/Python 3.11 because some packages (for example `uvloop`) are platform-specific.
- `make lock-dev` regenerates `requirements-dev.txt` for your local platform with `pip-compile` from `pip-tools`.
- Dependabot (`.github/dependabot.yml`) opens weekly PRs for new package versions and new base image digests, so pins stay current through review instead of floating.

## Safety

The demo API's fault-simulation endpoints (`/demo/*`) are disabled by default and must only be enabled in local or isolated test environments. Never commit `.env` files or secrets.
