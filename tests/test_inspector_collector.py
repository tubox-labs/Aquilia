import json

from aquilia.inspector.collector import InspectorCollector
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.redaction import redact_body, redact_headers, redact_url
from aquilia.inspector.trace import RequestTrace


def test_collector_ring_buffer_eviction():
    config = InspectorConfig(max_traces=5)
    collector = InspectorCollector(config)

    traces = []
    for i in range(10):
        t = RequestTrace(
            trace_id=f"trace-{i}",
            method="GET",
            path=f"/path-{i}",
            route_pattern=None,
            started_at=1000.0 + i,
            started_monotonic=2000.0 + i,
        )
        traces.append(t)
        collector.commit(t)

    # Should only keep 5 traces
    recent = collector.list_recent()
    assert len(recent) == 5
    # FIFO order: newest first
    assert recent[0].trace_id == "trace-9"
    assert recent[-1].trace_id == "trace-5"

    # Evicted traces must not be accessible via get()
    assert collector.get("trace-4") is None
    assert collector.get("trace-5") is not None


def test_collector_clear():
    config = InspectorConfig(max_traces=5)
    collector = InspectorCollector(config)
    t = RequestTrace(
        trace_id="t-1",
        method="GET",
        path="/",
        route_pattern=None,
        started_at=100.0,
        started_monotonic=200.0,
    )
    collector.commit(t)
    assert collector.get("t-1") is not None
    collector.clear()
    assert collector.get("t-1") is None
    assert len(collector.list_recent()) == 0


def test_redact_headers():
    config = InspectorConfig()
    headers = {
        "Host": "localhost",
        "Authorization": "Bearer mytoken",
        "Cookie": "session_id=123",
        "x-api-key": "secretkey",
    }
    redacted = redact_headers(headers, config)
    assert redacted["Host"] == "localhost"
    assert redacted["Authorization"] == "***REDACTED***"
    assert redacted["Cookie"] == "***REDACTED***"
    assert redacted["x-api-key"] == "***REDACTED***"


def test_redact_body_json():
    config = InspectorConfig()
    # Nested JSON
    body = {
        "user": {
            "name": "John",
            "password": "my_password",
            "api_key": "secret",
        },
        "items": [
            {"id": 1, "token": "val1"},
            {"id": 2, "cvv": "123"},
        ],
    }
    body_str = json.dumps(body)
    redacted = redact_body(body_str, "application/json", config)
    data = json.loads(redacted)
    assert data["user"]["name"] == "John"
    assert data["user"]["password"] == "***REDACTED***"
    assert data["user"]["api_key"] == "***REDACTED***"
    assert data["items"][0]["token"] == "***REDACTED***"
    assert data["items"][1]["cvv"] == "***REDACTED***"


def test_redact_body_form():
    config = InspectorConfig()
    body_str = "username=john&password=secret&api_key=12345"
    redacted = redact_body(body_str, "application/x-www-form-urlencoded", config)
    assert "username=john" in redacted
    assert "password=%2A%2A%2AREDACTED%2A%2A%2A" in redacted
    assert "api_key=%2A%2A%2AREDACTED%2A%2A%2A" in redacted


def test_redact_url():
    url = "https://example.com/api?token=abc&name=john&signature=xyz"
    redacted = redact_url(url)
    assert "name=john" in redacted
    assert "token=%2A%2A%2AREDACTED%2A%2A%2A" in redacted
    assert "signature=%2A%2A%2AREDACTED%2A%2A%2A" in redacted
