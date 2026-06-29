from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.redaction import redact_body, redact_headers, redact_url


def test_redact_headers():
    headers = {
        "Authorization": "Bearer abc123secret",
        "X-API-Key": "my-secret-key",
        "Content-Type": "application/json",
        "X-Normal-Header": "hello",
    }

    cfg = InspectorConfig(redact_headers=frozenset({"authorization", "x-api-key"}))

    redacted = redact_headers(headers, cfg)
    assert redacted["Authorization"] == "***REDACTED***"
    assert redacted["X-API-Key"] == "***REDACTED***"
    assert redacted["Content-Type"] == "application/json"
    assert redacted["X-Normal-Header"] == "hello"


def test_redact_body_json():
    import json

    body_dict = {
        "username": "alice",
        "password": "secretpassword123",
        "nested": {
            "token": "token-12345",
            "normal": "value",
        },
        "list": [{"api_key": "key-foo"}, {"other": "ok"}],
    }

    cfg = InspectorConfig(redact_body_keys=frozenset({"password", "token", "api_key"}))

    raw_body = json.dumps(body_dict)
    redacted_str = redact_body(raw_body, "application/json", cfg)
    redacted_dict = json.loads(redacted_str)

    assert redacted_dict["username"] == "alice"
    assert redacted_dict["password"] == "***REDACTED***"
    assert redacted_dict["nested"]["token"] == "***REDACTED***"
    assert redacted_dict["nested"]["normal"] == "value"
    assert redacted_dict["list"][0]["api_key"] == "***REDACTED***"
    assert redacted_dict["list"][1]["other"] == "ok"


def test_redact_url():
    url = "https://example.com/api?search=aquilia&token=secret-token&api_key=some-key"
    redacted = redact_url(url, frozenset({"token", "api_key"}))
    assert "search=aquilia" in redacted
    assert "token=%2A%2A%2AREDACTED%2A%2A%2A" in redacted
    assert "api_key=%2A%2A%2AREDACTED%2A%2A%2A" in redacted
