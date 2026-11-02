import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app


def test_fault_simulation_disabled_by_default():
    settings = Settings(_env_file=None)
    assert settings.fault_simulation_enabled is False
    assert settings.max_delay_seconds == 30


@pytest.mark.parametrize("value", ["ture", "banana", "enabled", ""])
def test_invalid_fault_simulation_value_stops_startup(monkeypatch, value):
    monkeypatch.setenv("DEMO_API_FAULT_SIMULATION_ENABLED", value)
    with pytest.raises(ValidationError, match="fault_simulation_enabled"):
        create_app()


@pytest.mark.parametrize("value, expected", [("true", True), ("false", False), ("1", True), ("0", False)])
def test_valid_fault_simulation_values_are_accepted(monkeypatch, value, expected):
    monkeypatch.setenv("DEMO_API_FAULT_SIMULATION_ENABLED", value)
    assert Settings(_env_file=None).fault_simulation_enabled is expected


def test_enabling_fault_simulation_logs_a_warning(log_lines):
    create_app(Settings(_env_file=None, fault_simulation_enabled=True))
    warnings = [line for line in log_lines() if line["level"] == "WARNING"]
    assert any("Fault simulation ENABLED" in line["message"] for line in warnings)


def test_disabled_fault_simulation_logs_no_warning(log_lines):
    create_app(Settings(_env_file=None))
    assert not any("Fault simulation" in line["message"] for line in log_lines())
