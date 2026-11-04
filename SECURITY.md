# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems. Report them privately through GitHub instead: **Security → Report a vulnerability** on this repository, or go directly to <https://github.com/k6gnn/MinOps/security/advisories/new>.

Include what you found, how to reproduce it, and what an attacker could do with it. You will get a reply as soon as possible, and the report stays private until a fix is available.

## Supported versions

Only the `main` branch is supported. There are no releases yet.

## Scope

MinOps is a learning project, not a production service. Two things are intentional and are not vulnerabilities:

- The demo API's fault-simulation endpoints (`/demo/*`) deliberately degrade the service. They are disabled by default (`DEMO_API_FAULT_SIMULATION_ENABLED=false`) and must only be enabled in local or isolated test environments. A report that they can be abused **while disabled**, or that they are enabled by default somewhere, is in scope.
- The project documentation describes planned components that do not exist yet.

In scope are, for example: the demo API itself, the container image, the dependency locks, and the CI workflow.

## How the project protects itself

- Every dependency, including transitive ones, is pinned with SHA-256 hashes and installed with `--require-hashes`.
- The container image is pinned by digest, runs as a non-root user, and contains no package installer.
- CI fails on any fixable HIGH or CRITICAL vulnerability, secret or misconfiguration that Trivy finds in the image.
- Dependabot keeps packages, the base image and GitHub Actions current, and GitHub secret scanning and CodeQL run on the repository.
