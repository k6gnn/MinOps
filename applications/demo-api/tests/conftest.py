import io
import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings, get_settings
from app.main import JSONFormatter, create_app


def build_client(**settings_overrides) -> TestClient:
    """Fresh app per test; ignores any .env file so results don't depend on the machine."""
    settings = Settings(_env_file=None, **settings_overrides)
    return TestClient(create_app(settings), raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Keep the developer's shell variables and cached settings out of the tests."""
    monkeypatch.delenv("DEMO_API_FAULT_SIMULATION_ENABLED", raising=False)
    monkeypatch.delenv("DEMO_API_MAX_DELAY_SECONDS", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    """App with default settings (fault simulation disabled)."""
    return build_client()


@pytest.fixture
def demo_client() -> TestClient:
    """App with fault simulation enabled and a small delay limit to keep tests fast."""
    return build_client(fault_simulation_enabled=True, max_delay_seconds=2)


@pytest.fixture
def log_lines():
    """Captures demo_api log output and returns it as parsed JSON objects."""
    stream = io.StringIO()
    capture = logging.StreamHandler(stream)
    capture.setFormatter(JSONFormatter())
    logger = logging.getLogger("demo_api")
    logger.addHandler(capture)
    yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()]
    logger.removeHandler(capture)
