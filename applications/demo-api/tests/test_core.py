from fastapi import FastAPI

from app.main import SERVICE_VERSION, create_app


def test_app_can_be_instantiated_and_responds(client):
    assert isinstance(create_app(), FastAPI)
    assert client.get("/").status_code == 200


def test_root_response_shape(client):
    body = client.get("/").json()
    assert body == {"message": "Demo API operational", "version": SERVICE_VERSION}


def test_liveness_returns_healthy_with_timestamp(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["timestamp"]


def test_readiness_returns_ready(client):
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "connected"}
