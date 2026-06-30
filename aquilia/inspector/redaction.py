import json
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from .config import InspectorConfig


def redact_headers(headers: dict[str, str], config: InspectorConfig) -> dict[str, str]:
    redacted = {}
    redact_set = {h.lower() for h in config.redact_headers}
    for k, v in headers.items():
        if k.lower() in redact_set:
            redacted[k] = "***REDACTED***"
        else:
            redacted[k] = v
    return redacted


def redact_body_keys_recursive(data: Any, redact_keys: frozenset[str]) -> Any:
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            k_lower = k.lower()
            # case-insensitive substring match
            should_redact = any(rk in k_lower for rk in redact_keys)
            if should_redact:
                new_dict[k] = "***REDACTED***"
            else:
                new_dict[k] = redact_body_keys_recursive(v, redact_keys)
        return new_dict
    elif isinstance(data, (list, tuple)):
        redacted_items = [redact_body_keys_recursive(item, redact_keys) for item in data]
        return tuple(redacted_items) if isinstance(data, tuple) else redacted_items
    return data


def redact_body(body: str | bytes | None, content_type: str | None, config: InspectorConfig) -> str | None:
    if not body:
        return None
    if isinstance(body, bytes):
        try:
            body_str = body.decode("utf-8", errors="replace")
        except Exception:
            return "***BINARY_BODY***"
    else:
        body_str = body

    ct = (content_type or "").lower()
    if "application/json" in ct or ct.endswith("/json"):
        try:
            data = json.loads(body_str)
            redacted_data = redact_body_keys_recursive(data, config.redact_body_keys)
            return json.dumps(redacted_data)
        except Exception:
            pass

    if "application/x-www-form-urlencoded" in ct:
        try:
            pairs = parse_qsl(body_str, keep_blank_values=True)
            redacted_pairs = []
            for k, v in pairs:
                k_lower = k.lower()
                should_redact = any(rk in k_lower for rk in config.redact_body_keys)
                if should_redact:
                    redacted_pairs.append((k, "***REDACTED***"))
                else:
                    redacted_pairs.append((k, v))
            return urlencode(redacted_pairs)
        except Exception:
            pass

    return body_str


def redact_url(url: str, redact_keys: frozenset[str] | None = None) -> str:
    if not url:
        return ""
    if redact_keys is None:
        redact_keys = frozenset({"token", "key", "secret", "signature", "apikey"})
    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url
        query_pairs = parse_qsl(parsed.query, keep_blank_values=True)
        redacted_pairs = []
        for k, v in query_pairs:
            k_lower = k.lower()
            should_redact = any(rk in k_lower for rk in redact_keys)
            if should_redact:
                redacted_pairs.append((k, "***REDACTED***"))
            else:
                redacted_pairs.append((k, v))
        new_query = urlencode(redacted_pairs)
        return urlunparse(parsed._replace(query=new_query))
    except Exception:
        return url
