from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class InspectorConfig:
    enabled: bool | None = None  # None = "follow debug mode" (see server._is_inspector_enabled)
    force_enable_in_prod: bool = False  # second, explicit opt-in required outside dev — see §5.2
    max_traces: int = 200
    max_body_bytes: int = 65_536
    capture_request_body: bool = True
    capture_response_body: bool = True
    capture_client_addr: bool = False  # off by default — IP is PII in many jurisdictions
    redact_headers: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "authorization",
                "cookie",
                "set-cookie",
                "x-api-key",
                "x-auth-token",
                "proxy-authorization",
            }
        )
    )
    redact_body_keys: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {
                "password",
                "passwd",
                "secret",
                "token",
                "api_key",
                "apikey",
                "authorization",
                "credit_card",
                "card_number",
                "cvv",
                "signature",
            }
        )
    )
    slow_request_threshold_ms: float = 500.0
    mount_path: str = "/__aquilia__/inspector"
    standalone_ui_enabled: bool = True
    admin_page_enabled: bool = True  # whether the admin panel surfaces it (independent of standalone mount)
    replay_enabled: bool = True
    live_stream_enabled: bool = True
    toolbar_enabled: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "InspectorConfig":
        data = dict(data)
        if "ring_buffer_size" in data:
            data["max_traces"] = data.pop("ring_buffer_size")

        kw = {}
        import inspect

        sig = inspect.signature(cls)
        valid_keys = sig.parameters.keys()

        for k, v in data.items():
            if k in valid_keys:
                if k in ("redact_headers", "redact_body_keys"):
                    kw[k] = frozenset(v)
                else:
                    kw[k] = v
        return cls(**kw)

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "force_enable_in_prod": self.force_enable_in_prod,
            "max_traces": self.max_traces,
            "max_body_bytes": self.max_body_bytes,
            "capture_request_body": self.capture_request_body,
            "capture_response_body": self.capture_response_body,
            "capture_client_addr": self.capture_client_addr,
            "redact_headers": list(self.redact_headers),
            "redact_body_keys": list(self.redact_body_keys),
            "slow_request_threshold_ms": self.slow_request_threshold_ms,
            "mount_path": self.mount_path,
            "standalone_ui_enabled": self.standalone_ui_enabled,
            "admin_page_enabled": self.admin_page_enabled,
            "replay_enabled": self.replay_enabled,
            "live_stream_enabled": self.live_stream_enabled,
            "toolbar_enabled": self.toolbar_enabled,
        }


def get_inspector_config(config_loader: Any) -> InspectorConfig:
    """Helper to load and parse InspectorConfig from ConfigLoader."""
    raw = config_loader.get_inspector_config()
    return InspectorConfig.from_dict(raw)
