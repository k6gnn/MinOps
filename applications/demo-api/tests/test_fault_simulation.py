import time

import pytest

from conftest import build_client

DEMO_REQUESTS = [
    ("get", "/demo/failure/500"),
    ("get", "/demo/failure/exception"),
    ("get", "/demo/failure/timeout?delay=0"),
    ("post", "/demo/toggle-ready?ready=false"),
]


# --- Switch off ---

@pytest.mark.parametrize("method, url", DEMO_REQUESTS)
def test_demo_routes_return_404_when_disabled(client, method, url):
    assert getattr(client, method)(url).status_code == 404


def test_demo_routes_absent_from_openapi_when_disabled(client):
    paths = client.get("/openapi.json").json()["paths"]
    assert not any(path.startswith("/demo") for path in paths)


def test_demo_routes_present_in_openapi_when_enabled(demo_client):
    paths = demo_client.get("/openapi.json").json()["paths"]
    assert "/demo/failure/{mode}" in paths
    assert "/demo/toggle-ready" in paths


# --- Controlled failures ---

def test_controlled_failure_returns_500_when_enabled(demo_client):
    response = demo_client.get("/demo/failure/500")
    assert response.status_code == 500
    assert response.json() == {"detail": "Controlled internal server error"}


def test_exception_mode_returns_generic_500_without_stack_trace(demo_client):
    response = demo_client.get("/demo/failure/exception")
    assert response.status_code == 500
    assert response.text == "Internal Server Error"


def test_unknown_mode_returns_400_listing_modes(demo_client):
    response = demo_client.get("/demo/failure/banana")
    assert response.status_code == 400
    assert "timeout" in response.json()["detail"]


@pytest.mark.parametrize("url", [
    "/demo/failure/500",
    "/demo/failure/exception",
    "/demo/failure/banana",
    "/demo/failure/timeout?delay=999",
    "/does-not-exist",
])
def test_errors_do_not_expose_internals(demo_client, url):
    body = demo_client.get(url).text
    for leak in ("Traceback", "RuntimeError", 'File "', "Controlled unhandled application exception"):
        assert leak not in body


# --- Delay scenario ---

def test_delay_introduces_measurable_latency(demo_client):
    start = time.perf_counter()
    response = demo_client.get("/demo/failure/timeout?delay=1")
    elapsed = time.perf_counter() - start

    assert response.status_code == 200
    assert response.json() == {"status": "delayed", "delay_seconds": 1}
    # Lower bound with a little slack; generous upper bound for slow CI machines
    assert 0.9 <= elapsed < 5


def test_default_delay_is_capped_by_max(demo_client):
    # Default is 5s, but this app's max is 2s
    assert demo_client.get("/demo/failure/timeout").json()["delay_seconds"] == 2


@pytest.mark.parametrize("delay", [-1, 3, 9999])
def test_out_of_range_delay_is_rejected_immediately(demo_client, delay):
    start = time.perf_counter()
    response = demo_client.get(f"/demo/failure/timeout?delay={delay}")
    assert response.status_code == 422
    assert time.perf_counter() - start < 1


def test_max_delay_follows_settings():
    client = build_client(fault_simulation_enabled=True, max_delay_seconds=0)
    assert client.get("/demo/failure/timeout?delay=0").status_code == 200
    assert client.get("/demo/failure/timeout?delay=1").status_code == 422


# --- Readiness toggle ---

def test_toggle_readiness_switches_readyz_but_not_healthz(demo_client):
    assert demo_client.post("/demo/toggle-ready?ready=false").status_code == 200
    assert demo_client.get("/readyz").status_code == 503
    assert demo_client.get("/healthz").status_code == 200

    assert demo_client.post("/demo/toggle-ready?ready=true").status_code == 200
    assert demo_client.get("/readyz").status_code == 200
    assert demo_client.get("/healthz").status_code == 200


def test_readiness_state_is_not_shared_between_apps(demo_client):
    demo_client.post("/demo/toggle-ready?ready=false")
    other = build_client(fault_simulation_enabled=True)
    assert other.get("/readyz").status_code == 200
