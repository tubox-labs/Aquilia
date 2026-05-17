from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aquilia.middleware_ext.rate_limit import RateLimitRule, api_key_extractor, ip_key_extractor
from aquilia.middleware_ext.security import CSPPolicy


@dataclass(slots=True)
class FakeRequest:
    path: str
    method: str = "GET"
    headers: dict[str, str] | None = None
    client: tuple[str, int] | None = ("127.0.0.1", 50000)
    state: dict[str, Any] | None = None

    def header(self, name: str, default: str | None = None) -> str | None:
        headers = self.headers or {}
        return headers.get(name.lower(), default)


class SecurityPolicyService:
    def __init__(self) -> None:
        self.public_rule = RateLimitRule(limit=120, window=60, scope="/public", methods=["GET"])
        self.write_rule = RateLimitRule(limit=20, window=60, scope="/api", methods=["POST"], key_func=api_key_extractor)
        self.csp = CSPPolicy().default_src("'self'").script_src("'self'").frame_ancestors("'none'")

    def classify_request(self, path: str, method: str = "GET", headers: dict[str, str] | None = None) -> dict[str, Any]:
        request = FakeRequest(
            path=path,
            method=method,
            headers={k.lower(): v for k, v in (headers or {}).items()},
            state={"client_ip": "127.0.0.1"},
        )
        matching = [rule for rule in (self.public_rule, self.write_rule) if rule.matches(request)]
        key = matching[0].key_func(request) if matching else ip_key_extractor(request)
        return {
            "matched_rules": len(matching),
            "rate_limit_key": key,
            "csp": self.csp.build(),
        }
