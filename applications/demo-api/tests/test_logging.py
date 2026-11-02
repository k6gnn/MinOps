import uuid

from app.main import SERVICE_NAME, SERVICE_VERSION

REQUIRED_FIELDS = {"timestamp", "level", "service", "version", "message",
                   "request_id", "method", "route", "status_code", "duration_ms"}


def request_logs(lines):
    return [line for line in lines if "request_id" in line]


def test_request_log_has_expected_fields(client, log_lines):
    client.get("/healthz")
    [entry] = request_logs(log_lines())

    assert REQUIRED_FIELDS <= entry.keys()
    assert entry["service"] == SERVICE_NAME
    assert entry["version"] == SERVICE_VERSION
    assert entry["method"] == "GET"
    assert entry["route"] == "/healthz"
    assert entry["status_code"] == 200
    assert entry["duration_ms"] >= 0
    assert "error_category" not in entry


def test_route_is_logged_as_template_not_raw_path(demo_client, log_lines):
    demo_client.get("/demo/failure/timeout?delay=0")
    [entry] = request_logs(log_lines())
    assert entry["route"] == "/demo/failure/{mode}"


def test_request_id_is_generated_when_missing(client, log_lines):
    response = client.get("/")
    [entry] = request_logs(log_lines())

    request_id = response.headers["X-Request-ID"]
    assert uuid.UUID(request_id)
    assert entry["request_id"] == request_id


def test_request_id_from_client_is_reused(client, log_lines):
    response = client.get("/", headers={"X-Request-ID": "trace-abc.123"})
    [entry] = request_logs(log_lines())

    assert response.headers["X-Request-ID"] == "trace-abc.123"
    assert entry["request_id"] == "trace-abc.123"


def test_unsafe_request_id_is_replaced(client):
    response = client.get("/", headers={"X-Request-ID": "x" * 500})
    assert uuid.UUID(response.headers["X-Request-ID"])


def test_handled_error_logs_error_category(demo_client, log_lines):
    demo_client.get("/demo/failure/500")
    [entry] = request_logs(log_lines())
    assert entry["status_code"] == 500
    assert entry["error_category"] == "server_error"


def test_unhandled_exception_is_logged_with_status_500(demo_client, log_lines):
    demo_client.get("/demo/failure/exception")
    [entry] = request_logs(log_lines())

    assert entry["level"] == "ERROR"
    assert entry["status_code"] == 500
    assert entry["error_category"] == "unhandled_exception"
    assert entry["exception_type"] == "RuntimeError"
    assert uuid.UUID(entry["request_id"])


def test_sensitive_headers_are_not_logged(client, log_lines):
    client.get("/", headers={"Authorization": "Bearer secret-token", "Cookie": "session=secret-cookie"})
    raw = str(log_lines())
    assert "secret-token" not in raw
    assert "secret-cookie" not in raw
