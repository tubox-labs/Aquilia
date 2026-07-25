import pytest
from pathlib import Path
from textwrap import dedent

from aquilia.discovery.engine import AutoDiscoveryEngine
from aquilia.manifest import ComponentKind

@pytest.fixture
def workspace_dir(tmp_path):
    modules = tmp_path / "modules"
    modules.mkdir()
    
    # Create module1
    mod1 = modules / "mod1"
    mod1.mkdir()
    
    (mod1 / "__init__.py").write_text("")
    (mod1 / "manifest.py").write_text("from aquilia.manifest import AppManifest\nmanifest = AppManifest(name='mod1')")
    
    # Simple AST-discoverable class
    (mod1 / "simple.py").write_text(dedent("""
        from aquilia.controller import Controller
        class SimpleController(Controller):
            pass
    """))

    # Aliased import
    (mod1 / "aliased.py").write_text(dedent("""
        from aquilia.controller import Controller as MyBase
        class AliasedController(MyBase):
            pass
    """))

    # Transitive inheritance
    (mod1 / "transitive.py").write_text(dedent("""
        from aquilia.controller import Controller
        class BaseControllerCustom(Controller):
            pass
        class TransitiveController(BaseControllerCustom):
            pass
    """))

    # Re-exported classes via __all__
    (mod1 / "reexport_target.py").write_text(dedent("""
        class Service:
            pass
        class ReexportedService(Service):
            pass
    """))
    (mod1 / "reexports.py").write_text(dedent("""
        from modules.mod1.reexport_target import ReexportedService
        __all__ = ["ReexportedService"]
    """))

    # File that raises ImportError
    (mod1 / "bad_import.py").write_text(dedent("""
        import does_not_exist
        class MissingService:
            pass
    """))

    return modules

def test_ast_mode(workspace_dir):
    engine = AutoDiscoveryEngine(workspace_dir)
    res = engine.discover("mod1", strict=False)
    
    names = {c.name for c in res.components}
    
    # AST mode can find simple and transitive because name ends in Controller
    assert "SimpleController" in names
    
def test_strict_mode(workspace_dir):
    engine = AutoDiscoveryEngine(workspace_dir)
    res = engine.discover("mod1", strict=True)
    
    names = {c.name for c in res.components}
    
    assert "SimpleController" in names
    assert "AliasedController" in names
    assert "TransitiveController" in names
    assert "BaseControllerCustom" in names
    assert "ReexportedService" in names
    
    # bad_import should gracefully fail and NOT include MissingService
    assert "MissingService" not in names


def test_ast_mode_misses_aliased_import(workspace_dir):
    """Strict mode finds aliased-base classes that AST mode might miss."""
    engine = AutoDiscoveryEngine(workspace_dir)

    strict_res = engine.discover("mod1", strict=True)
    strict_names = {c.name for c in strict_res.components}

    # AliasedController uses aliased base; strict catches via real MRO
    assert "AliasedController" in strict_names
    # TransitiveController: two hops from Controller; strict resolves the chain
    assert "TransitiveController" in strict_names


def test_strict_mode_no_duplicate_components(workspace_dir):
    """No component returned twice in strict mode."""
    engine = AutoDiscoveryEngine(workspace_dir)
    res = engine.discover("mod1", strict=True)
    names = [c.name for c in res.components]
    # No duplicates
    assert len(names) == len(set(names)), f"Duplicates found: {names}"


def test_strict_mode_import_error_graceful(workspace_dir):
    """Files with bad imports don't crash strict mode."""
    engine = AutoDiscoveryEngine(workspace_dir)
    # Should not raise
    res = engine.discover("mod1", strict=True)
    assert res is not None
    # bad_import.py should have been silently skipped
    assert "MissingService" not in {c.name for c in res.components}


def test_strict_mode_component_has_file_path(workspace_dir):
    """All components in strict mode have valid file_path."""
    engine = AutoDiscoveryEngine(workspace_dir)
    res = engine.discover("mod1", strict=True)
    for comp in res.components:
        assert comp.file_path is not None
        assert comp.file_path != ""


def test_strict_mode_kind_correct(workspace_dir):
    """AliasedController and TransitiveController classified as CONTROLLER."""
    from aquilia.manifest import ComponentKind
    engine = AutoDiscoveryEngine(workspace_dir)
    res = engine.discover("mod1", strict=True)
    by_name = {c.name: c for c in res.components}
    assert by_name["AliasedController"].kind == ComponentKind.CONTROLLER
    assert by_name["TransitiveController"].kind == ComponentKind.CONTROLLER
    assert by_name["SimpleController"].kind == ComponentKind.CONTROLLER
