from aquilia.config import ConfigLoader
from aquilia.inspector.config import InspectorConfig, get_inspector_config


def test_config_defaults():
    loader = ConfigLoader()
    loader.config_data = {}

    cfg = get_inspector_config(loader)
    assert isinstance(cfg, InspectorConfig)
    # Default is enabled=None (which means follow debug mode), default size (max_traces) is 200
    assert cfg.enabled is None
    assert cfg.max_traces == 200
    assert cfg.force_enable_in_prod is False


def test_config_explicit():
    loader = ConfigLoader()
    loader.config_data = {
        "inspector": {
            "enabled": True,
            "ring_buffer_size": 42,
            "force_enable_in_prod": True,
            "redact_headers": ["x-api-key"],
            "redact_keys": ["password"],
            "max_body_bytes": 1024,
        }
    }

    cfg = get_inspector_config(loader)
    assert cfg.enabled is True
    assert cfg.max_traces == 42
    assert cfg.force_enable_in_prod is True
    assert "x-api-key" in cfg.redact_headers
    # Note: the key in InspectorConfig is redact_body_keys, which maps to redact_body_keys
    # In explicit config we can also test it filters extra keys
    assert cfg.max_body_bytes == 1024

