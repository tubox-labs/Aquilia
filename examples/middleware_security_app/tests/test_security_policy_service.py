from examples.middleware_security_app.modules.security.services import SecurityPolicyService


def test_security_policy_matches_public_route_and_builds_csp():
    service = SecurityPolicyService()
    result = service.classify_request("/public/catalog", "GET")

    assert result["matched_rules"] == 1
    assert result["rate_limit_key"] == "ip:127.0.0.1"
    assert "frame-ancestors 'none'" in result["csp"]


def test_security_policy_uses_api_key_for_write_route():
    service = SecurityPolicyService()
    result = service.classify_request("/api/orders", "POST", {"x-api-key": "key-123"})

    assert result["matched_rules"] == 1
    assert result["rate_limit_key"] == "apikey:key-123"
