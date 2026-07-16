
from aquilia.cli.commands.run import _discover_and_update_manifests


def test_run_discover_and_update_manifests(tmp_path):
    """Test that _discover_and_update_manifests auto-syncs newly created models on aq run."""
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()
    brief_dir = modules_dir / "brief"
    brief_dir.mkdir()

    manifest_file = brief_dir / "manifest.py"
    manifest_file.write_text(
        'from aquilia import AppManifest\n'
        'manifest = AppManifest(\n'
        '    name="brief",\n'
        '    version="0.1.0",\n'
        '    models=[],\n'
        ')\n',
        encoding="utf-8",
    )

    # Create a new model file with a model class Users
    model_file = brief_dir / "models.py"
    model_file.write_text(
        'from aquilia.models import Model\n'
        'class Users(Model):\n'
        '    pass\n',
        encoding="utf-8",
    )

    # Execute discovery
    _discover_and_update_manifests(tmp_path, verbose=True)

    # Assert that the manifest file was updated to include the new model reference
    updated_manifest = manifest_file.read_text(encoding="utf-8")
    assert "modules.brief.models:Users" in updated_manifest
