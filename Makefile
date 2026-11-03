# Developer shortcuts for the demo API (GNU Make). Run from the repository root.
APP_DIR := applications/demo-api
IMAGE   := demo-api

.PHONY: install test run run-faults docker-build docker-run

install:
	pip install -r requirements-dev.txt

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
