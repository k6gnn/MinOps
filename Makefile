# Developer shortcuts for the demo API (GNU Make). Run from the repository root.
APP_DIR := applications/demo-api
IMAGE   := demo-api
CLUSTER := minops

PYTHON_IMAGE := python:3.11.18-alpine3.24@sha256:09d17d5e4c16d0a7a1eea690bcb7c6ab8616b211f8421e429e97c1bef5bd0ed2
PIP_COMPILE  := pip-compile --quiet --generate-hashes --allow-unsafe --strip-extras

.PHONY: install lock test run run-faults docker-build docker-run cluster-image

install:
	pip install --require-hashes -r requirements-dev.txt

# Regenerate every lock inside the same Linux/Python image the Dockerfile uses, so runtime,
# build and dev locks agree with each other, with CI and with WSL2 development
lock:
	docker run --rm -v "$(CURDIR)":/src -w /src $(PYTHON_IMAGE) \
	  sh -c "pip install -q --root-user-action=ignore pip-tools \
	    && $(PIP_COMPILE) requirements.in -o requirements.txt \
	    && $(PIP_COMPILE) requirements-build.in -o requirements-build.txt \
	    && $(PIP_COMPILE) requirements-dev.in -o requirements-dev.txt"

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

# k3d nodes can't see the local Docker image store, so copy the freshly built image into the cluster
cluster-image: docker-build
	k3d image import $(IMAGE) -c $(CLUSTER)
