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

Development happens on Linux (on Windows, inside WSL2) with the Python version in `.python-version`, so the locks, the image and CI all use the same platform and interpreter. Clone the repository inside the WSL2 filesystem (for example `~/src/MinOps`), not under `/mnt/c`.

```bash
pyenv install --skip-existing   # reads .python-version
python -m venv .venv
source .venv/bin/activate
make install
make test
make run
```

The other tasks are `make run-faults`, `make docker-build`, `make docker-run` and `make lock`.

## Dependencies

Every dependency, including transitive ones, is pinned with SHA-256 hashes and installed with `pip install --require-hashes`. To change dependencies, edit a `.in` file and run `make lock`, which regenerates `requirements.txt`, `requirements-build.txt` (the pip version used in the image's builder stage) and `requirements-dev.txt` inside the Dockerfile's Python image.

The image is based on `python:<version>-alpine`, pinned by tag and digest. Alpine has far fewer OS-level vulnerabilities than the Debian slim images, and every dependency ships a prebuilt musl wheel (the build uses `--only-binary=:all:`, so it never compiles from source).

Dependabot (`.github/dependabot.yml`) opens weekly PRs for new package versions, base image patch releases and GitHub Actions, so pins stay current through review instead of floating. Python minor upgrades are excluded on purpose: change the Dockerfile, the Makefile's `PYTHON_IMAGE` and `.python-version` together, then run `make lock`.

## CI

`.github/workflows/ci.yml` runs on every PR and on pushes to `main`. It checks that the Python pins agree, runs the tests from the locked dev dependencies, builds the image, smoke-tests `/healthz`, and fails on any fixable HIGH or CRITICAL vulnerability, secret or misconfiguration found by Trivy.

## Safety

The demo API's fault-simulation endpoints (`/demo/*`) are disabled by default and must only be enabled in local or isolated test environments. Never commit `.env` files or secrets.
