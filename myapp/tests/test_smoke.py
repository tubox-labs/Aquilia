"""
Smoke tests for myapp workspace.
"""


def test_workspace_config(app_config):
    """Verify test configuration is loaded."""
    assert app_config["name"] == "myapp"
    assert app_config["mode"] == "test"


def test_aquilia_importable():
    """Verify Aquilia framework is installed."""
    import aquilia
    assert hasattr(aquilia, "__version__")
