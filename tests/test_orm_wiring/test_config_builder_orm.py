from aquilia.config import ConfigLoader
from aquilia.workspace import Module, Workspace


def test_config_builder_database_scan_dirs():
    """Workspace database config stays in workspace config; manifest DB is deprecated."""

    workspace = (
        Workspace("test_db_workspace")
        .database(url="sqlite:///:memory:", scan_dirs=["custom_models"])
        .module(Module("test_app"))
    )

    config_dict = workspace.to_dict()
    loader = ConfigLoader()
    loader._merge_dict(loader.config_data, config_dict)
    loader._build_apps_namespace()

    manifest_data = loader.config_data["modules"][0]

    from aquilia.aquilary.loader import ManifestLoader

    manifest_loader = ManifestLoader()

    # Simulate loading from dict like in AquiliaServer
    manifest_cls = manifest_loader._dict_to_manifest(manifest_data, "config")
    manifest = manifest_loader.load_manifests([manifest_cls])[0]

    assert hasattr(manifest, "database")
    assert manifest.database is None
    assert "database" in loader.config_data
    assert "custom_models" in loader.config_data["database"].get("scan_dirs", [])


def test_get_database_config_defaults():
    loader = ConfigLoader()
    config = loader.get_database_config()
    assert config["enabled"] is False
    assert config["url"] is None
    assert config["auto_connect"] is True
    assert config["auto_create"] is True
    assert config["auto_migrate"] is False
    assert config["migrations_dir"] == "migrations"
    assert config["pool_size"] == 5
    assert config["echo"] is False
    assert config["model_paths"] == []
    assert config["scan_dirs"] == ["models"]


def test_get_database_config_with_overrides():
    loader = ConfigLoader()
    loader.config_data["database"] = {
        "enabled": True,
        "url": "postgresql://localhost/mydb",
        "pool_size": 10,
    }
    config = loader.get_database_config()
    assert config["enabled"] is True
    assert config["url"] == "postgresql://localhost/mydb"
    assert config["pool_size"] == 10
    assert config["auto_connect"] is True  # preserved default


def test_get_database_config_from_integrations():
    loader = ConfigLoader()
    loader.config_data["integrations"] = {
        "database": {
            "enabled": True,
            "url": "sqlite:///custom.db",
        }
    }
    config = loader.get_database_config()
    assert config["enabled"] is True
    assert config["url"] == "sqlite:///custom.db"
