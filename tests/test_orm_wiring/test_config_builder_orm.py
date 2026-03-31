from aquilia.config_builders import Module, Workspace
from aquilia.config import ConfigLoader


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
