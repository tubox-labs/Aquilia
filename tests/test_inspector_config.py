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


def test_admin_integration_request_inspector():
    from aquilia.integrations import AdminModules
    from aquilia.integrations._legacy import Integration

    # 1. Modern AdminModules constructor + to_dict
    m1 = AdminModules(request_inspector=True)
    assert m1.request_inspector is True
    assert m1.to_dict()["inspector"] is True

    # 2. Modern AdminModules fluent methods
    m2 = AdminModules().enable_request_inspector()
    assert m2.request_inspector is True
    assert m2.to_dict()["inspector"] is True

    m3 = AdminModules(inspector=True).disable_request_inspector()
    assert m3.request_inspector is False
    assert m3.to_dict()["inspector"] is False

    # 3. Legacy AdminModules fluent methods
    lm1 = Integration.AdminModules().enable_request_inspector()
    assert lm1.request_inspector is True
    assert lm1.to_dict()["inspector"] is True

    lm2 = Integration.AdminModules(enable_request_inspector=True)
    assert lm2.request_inspector is True
    assert lm2.to_dict()["inspector"] is True

    # 4. Legacy Integration.admin flat parameters
    res1 = Integration.admin(enable_request_inspector=True)
    assert res1["modules"]["inspector"] is True

    res2 = Integration.admin(enable_inspector=True)
    assert res2["modules"]["inspector"] is True
