import ast
from pathlib import Path

from aquilia.aquilary.core import AppContext
from aquilia.discovery.engine import (
    ASTClassifier,
    AutoDiscoveryEngine,
    ManifestDiffer,
    ManifestWriter,
)
from aquilia.manifest import AppManifest, ComponentKind


def test_ast_classifier_heuristics():
    """Verify that ASTClassifier correctly classifies classes based on base classes, decorators, and naming conventions."""
    classifier = ASTClassifier()

    # Check Controller classification
    content = """
class UsersController:
    pass

class MySuperController(BaseController):
    pass

class ItemsController(Controller):
    pass
"""
    # Create temp file
    tree = ast.parse(content)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]

    assert classifier._classify_class(classes[0]) == ComponentKind.CONTROLLER
    assert classifier._classify_class(classes[1]) == ComponentKind.CONTROLLER
    assert classifier._classify_class(classes[2]) == ComponentKind.CONTROLLER

    # Check Service classification
    content = """
class UsersService:
    pass

@service()
class SomeCustomService:
    pass

@injectable
class LegacyProvider:
    pass
"""
    tree = ast.parse(content)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]

    assert classifier._classify_class(classes[0]) == ComponentKind.SERVICE
    assert classifier._classify_class(classes[1]) == ComponentKind.SERVICE
    assert classifier._classify_class(classes[2]) == ComponentKind.SERVICE

    # Check Socket Controller classification
    content = """
@Socket("/chat")
class ChatRoom:
    pass

class ChatSocketController:
    pass
"""
    tree = ast.parse(content)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]

    assert classifier._classify_class(classes[0]) == ComponentKind.SOCKET_CONTROLLER
    assert classifier._classify_class(classes[1]) == ComponentKind.SOCKET_CONTROLLER

    # Check Middleware classification
    content = """
class LogMiddleware:
    pass

class CustomAuthMiddleware(BaseMiddleware):
    pass
"""
    tree = ast.parse(content)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)]

    assert classifier._classify_class(classes[0]) == ComponentKind.MIDDLEWARE
    assert classifier._classify_class(classes[1]) == ComponentKind.MIDDLEWARE


def test_import_path_namespace_preservation(tmp_path):
    """Verify that _compute_import_path preserves the correct modules package prefix."""
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()

    user_module = modules_dir / "users"
    user_module.mkdir()

    controller_file = user_module / "controllers.py"
    controller_file.write_text("class UsersController:\n    pass")

    engine = AutoDiscoveryEngine(modules_dir)
    import_path = engine._compute_import_path(controller_file, user_module, "users", "UsersController")

    # Expected namespaced format: parent_folder.module.file:Class
    expected = f"{modules_dir.name}.users.controllers:UsersController"
    assert import_path == expected


def test_manifest_differ_declared_namespaces():
    """Verify that ManifestDiffer only considers a component declared if it has a fully namespaced prefix."""
    differ = ManifestDiffer(root_package="modules")

    # Component to test
    from aquilia.discovery.engine import ClassifiedComponent

    comp = ClassifiedComponent(
        name="UsersController",
        kind=ComponentKind.CONTROLLER,
        file_path=Path("modules/users/controllers.py"),
        line=1,
        import_path="modules.users.controllers:UsersController",
    )

    # Test cases: incorrect or incomplete namespaces should trigger a sync
    assert differ._is_declared(comp, ["modules.users.controllers:UsersController"]) is True
    assert differ._is_declared(comp, ["users.controllers:UsersController"]) is False
    assert differ._is_declared(comp, ["UsersController"]) is False


def test_manifest_writer_inplace_replacement():
    """Verify that ManifestWriter replaces incorrectly/partially namespaced references in-place."""
    writer = ManifestWriter()

    # Test replacement of class name only
    source = """
AppManifest(
    name="users",
    version="1.0.0",
    controllers=[
        "UsersController",
    ]
)
"""
    expected = """
AppManifest(
    name="users",
    version="1.0.0",
    controllers=[
        "modules.users.controllers:UsersController",
    ]
)
"""
    result = writer._add_component(source, "controllers", "modules.users.controllers:UsersController")
    assert result.strip() == expected.strip()

    # Test replacement of partially namespaced ref
    source = """
AppManifest(
    name="users",
    version="1.0.0",
    controllers=[
        "users.controllers:UsersController",
    ]
)
"""
    result = writer._add_component(source, "controllers", "modules.users.controllers:UsersController")
    assert result.strip() == expected.strip()


def test_runtime_middleware_autodiscovery(tmp_path):
    """Verify perform_autodiscovery dynamically registers middlewares under modules package."""
    # Scaffold temporary modules structure
    modules_dir = tmp_path / "modules"
    modules_dir.mkdir()

    auth_module = modules_dir / "auth"
    auth_module.mkdir()

    (auth_module / "__init__.py").write_text("")
    (auth_module / "manifest.py").write_text("""
from aquilia.manifest import AppManifest
manifest = AppManifest(
    name="auth",
    version="1.0.0",
    middleware=[],
)
""")
    (auth_module / "middleware.py").write_text("""
from aquilia.middleware import Middleware
class AuthMiddleware(Middleware):
    async def __call__(self, scope, receive, send):
        pass
""")

    # Load app context and run autodiscovery
    manifest = AppManifest(name="auth", version="1.0.0", middleware=[])

    import sys

    sys.path.insert(0, str(tmp_path))
    try:
        ctx = AppContext(
            name="auth",
            version="1.0.0",
            manifest=manifest,
            config_namespace={},
            route_prefix="/auth",
            controllers=[],
            services=[],
            models=[],
            middlewares=[],
        )

        from aquilia.aquilary.core import AquilaryRegistry, RegistryMode

        registry_meta = AquilaryRegistry(
            app_contexts=[ctx],
            fingerprint="fake",
            mode=RegistryMode.DEV,
            dependency_graph={},
            route_index={},
            validation_report={},
            config=None,
        )

        # Instantiate Registry
        from aquilia.aquilary.core import RuntimeRegistry

        registry = RuntimeRegistry(registry_meta, None)

        # Override workspace root resolver
        registry._workspace_root = lambda: tmp_path

        registry.perform_autodiscovery()

        # Assert middleware got discovered and registered
        assert len(ctx.middlewares) == 1
        assert ctx.middlewares[0].class_path == "modules.auth.middleware:AuthMiddleware"
    finally:
        sys.path.pop(0)
