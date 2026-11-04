# Developer shortcuts for the demo API (GNU Make). Run from the repository root.
APP_DIR := applications/demo-api
IMAGE   := demo-api

PYTHON_IMAGE := python:3.11.18-slim@sha256:db20d8506e2f15b6db39b40b6015ca46bae855dec6dd326d462cfe79ae972893
PIP_COMPILE  := pip-compile --quiet --generate-hashes --allow-unsafe --strip-extras

.PHONY: install lock lock-dev test run run-faults docker-build docker-run

install:
	pip install --require-hashes -r requirements-dev.txt

# Regenerate the runtime and build-tool locks inside the same Linux/Python image the Dockerfile uses
lock:
	docker run --rm -v "$(CURDIR)":/src -w /src $(PYTHON_IMAGE) \
	  sh -c "pip install -q --root-user-action=ignore pip-tools \
	    && $(PIP_COMPILE) requirements.in -o requirements.txt \
	    && $(PIP_COMPILE) requirements-build.in -o requirements-build.txt"

# Regenerate the dev lock for the local platform (needs pip-tools installed locally)
lock-dev:
	$(PIP_COMPILE) requirements-dev.in -o requirements-dev.txt

test:
	cd $(APP_DIR) && python -m pytest

run:
	cd $(APP_DIR) && uvicorn app.main:create_app --factory --reload

# Local only: exposes the /demo/* fault-simulation endpoints
run-faults: export DEMO_API_FAULT_SIMULATION_ENABLED := true
run-faults: run

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -p 8000:8000 $(IMAGE)
