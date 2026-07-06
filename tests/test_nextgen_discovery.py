import pytest
from pathlib import Path
import json
import time

from aquilia.manifest import ComponentKind
from aquilia.discovery.engine import (
    AutoDiscoveryEngine,
    DiscoveryCache,
    ASTClassifier,
    register_component_rule,
    _compute_file_hash,
)


def test_discovery_caching(tmp_path):
    """Test that file discovery caches scan results and detects changes correctly."""
    pytest.importorskip("surp")

    cache_file = tmp_path / "cache.surp"
    cache = DiscoveryCache(cache_file)

    test_file = tmp_path / "service.py"
    test_file.write_text(
        "class UsersService:\n    pass\n", encoding="utf-8"
    )

    mtime = test_file.stat().st_mtime
    file_hash = _compute_file_hash(test_file)
    components = [
        {
            "name": "UsersService",
            "kind": "service",
            "file_path": str(test_file),
            "line": 1,
            "import_path": "modules.users.service:UsersService",
            "bases": [],
            "decorators": [],
        }
    ]

    # Save to cache
    cache.set(str(test_file), mtime, file_hash, components)
    cache.save()

    # Read back cache
    new_cache = DiscoveryCache(cache_file)
    cached = new_cache.get(str(test_file))
    assert cached is not None
    assert cached["mtime"] == mtime
    assert cached["hash"] == file_hash
    assert cached["components"][0]["name"] == "UsersService"

    # Modify file to invalidate cache
    time.sleep(0.01)  # Ensure mtime updates
    test_file.write_text(
        "class UsersService:\n    # modified\n    pass\n", encoding="utf-8"
    )
    new_hash = _compute_file_hash(test_file)
    assert new_hash != file_hash


def test_extensible_component_rules(tmp_path):
    """Test registering a custom component rule dynamically."""
    # Register custom kind and match rule
    register_component_rule(
        ComponentKind.VALIDATOR,
        decorators={"custom_validator"},
        name_suffixes={"Validator"},
    )

    classifier = ASTClassifier()
    test_file = tmp_path / "validator.py"
    test_file.write_text(
        "@custom_validator\nclass DataValidator:\n    pass\n", encoding="utf-8"
    )

    components = classifier.classify_file(test_file)
    assert len(components) == 1
    assert components[0].name == "DataValidator"
    assert components[0].kind == ComponentKind.VALIDATOR


def test_workspace_deep_validation(tmp_path):
    """Test cycle detection, duplicate routes, and duplicate class name validation."""
    # Setup mock workspace structure
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()

    # Module A depends on Module B, Module B depends on Module A (Cycle)
    (modules_dir / "mod_a").mkdir()
    (modules_dir / "mod_b").mkdir()

    manifest_a = modules_dir / "mod_a" / "manifest.py"
    manifest_a.write_text(
        "from aquilia.manifest import AppManifest\n"
        "AppManifest(\n"
        "    name='mod_a',\n"
        "    version='1.0.0',\n"
        "    imports=['mod_b'],\n"
        "    route_prefix='/prefix',\n"
        ")\n",
        encoding="utf-8",
    )

    manifest_b = modules_dir / "mod_b" / "manifest.py"
    manifest_b.write_text(
        "from aquilia.manifest import AppManifest\n"
        "AppManifest(\n"
        "    name='mod_b',\n"
        "    version='1.0.0',\n"
        "    imports=['mod_a'],\n"
        "    route_prefix='/prefix',\n"
        ")\n",
        encoding="utf-8",
    )

    # Component file inside module a
    (modules_dir / "mod_a" / "controller.py").write_text(
        "class DuplicateController:\n    pass\n", encoding="utf-8"
    )
    # Component file inside module b (Duplicate class name check)
    (modules_dir / "mod_b" / "controller.py").write_text(
        "class DuplicateController:\n    pass\n", encoding="utf-8"
    )

    engine = AutoDiscoveryEngine(modules_dir)
    workspace_py = tmp_path / "workspace.py"
    workspace_py.write_text("# workspace.py content\n", encoding="utf-8")

    validation = engine.validate_workspace(workspace_py)

    # Assert validation catches:
    # 1. Circular dependency
    assert any("Circular dependency" in err for err in validation["errors"])
    # 2. Duplicate route prefix
    assert any("Duplicate route prefix" in err for err in validation["errors"])
    # 3. Duplicate class name warning
    assert any("Duplicate component class name 'DuplicateController'" in warn for warn in validation["warnings"])
