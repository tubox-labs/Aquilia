"""Regression tests for the CLI / manifest audit fixes (F-MAN-*, N-*).

Each test class maps to one audit finding:

  F-MAN-01/02/03  ``aq run`` / ``doctor`` / ``validate`` resolve component
                  refs by import (not by regex-scraping manifest text), so
                  framework refs (``aquilia.auth.guards:AuthGuard``),
                  cross-module refs, and multi-colon strings
                  (``redis://localhost:6379``) no longer false-error or crash.
  F-MAN-04        ``aq run`` validates the workspace BEFORE any sync writes.
  F-MAN-05        workspace.py rewriter: no-op updates do not rewrite, blank
                  lines outside the modules section survive, messages honest.
  F-MAN-06        manifest sync skips modules that declared auto_discover=False.
  F-MAN-07/N-11   discovery differ never removes by default; prune removes
                  only importlib-verified-dead refs.
  F-MAN-08        AppManifest.to_dict/fingerprint cover every config dimension.
  F-MAN-09        imports/depends_on divergence warns instead of silently
                  keeping two different lists.
  F-MAN-12        manifest names are validated as ASCII identifiers.
  F-MAN-13        AppManifest.database deprecation states the value is DISCARDED.
  N-1             ``aq manifest update`` refuses destructive rewrites when the
                  scan could not import the module.
  N-2             controller detection uses the Controller base class, not
                  get/post/put/delete duck typing.
  N-3             module-builder manifests are rewritten to AppManifest syntax.
  N-4             ``--freeze`` handles the keyword form and reports no-ops
                  honestly.
  N-5             list injection is AST-based, never into commented-out lists.
  N-6             ``aq run`` exits non-zero on validation failure.
  N-7             module-name scraping accepts both quote styles.
  N-8             ``aq add module --depends-on`` ignores commented-out modules.

All scratch workspaces live under pytest's ``tmp_path``; the CLI is always
invoked with its cwd inside the scratch workspace, never inside the repo.
"""

from __future__ import annotations

import ast
import os
import sys
import textwrap
import time
import warnings
from pathlib import Path

import pytest
from click.testing import CliRunner

from aquilia.cli.__main__ import cli
from aquilia.manifest import AppVersioningConfig, FeatureConfig, SessionConfig, TemplateConfig

# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════


def _clean_modules():
    """Drop test workspace modules so fixtures do not leak between tests."""
    for name in [m for m in sys.modules if m.startswith(("modules", "_aq_"))]:
        sys.modules.pop(name, None)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def scratch(tmp_path, monkeypatch):
    """A scratch workspace root; cwd and sys.path point at it."""
    (tmp_path / "modules").mkdir()
    (tmp_path / "modules" / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    _clean_modules()
    yield tmp_path
    _clean_modules()


def _make_module(ws_root: Path, name: str, manifest: str, files: dict[str, str] | None = None) -> Path:
    """Create modules/<name>/ with a manifest and optional extra files."""
    mod = ws_root / "modules" / name
    mod.mkdir(parents=True, exist_ok=True)
    init = mod / "__init__.py"
    if not init.exists():
        init.write_text("", encoding="utf-8")
    (mod / "manifest.py").write_text(textwrap.dedent(manifest), encoding="utf-8")
    for fname, src in (files or {}).items():
        (mod / fname).write_text(textwrap.dedent(src), encoding="utf-8")
    return mod


def _call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _manifest_field(source: str, field: str) -> list[str]:
    """AST-extract the string values of an ``AppManifest(...)`` list kwarg."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and _call_name(node) == "AppManifest":
            for kw in node.keywords:
                if kw.arg == field and isinstance(kw.value, ast.List):
                    return [elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant)]
    raise AssertionError(f"AppManifest field {field!r} not found as a string list")


def _manifest_kwarg(source: str, field: str):
    """AST-extract a constant ``AppManifest(...)`` kwarg (or None)."""
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and _call_name(node) == "AppManifest":
            for kw in node.keywords:
                if kw.arg == field and isinstance(kw.value, ast.Constant):
                    return kw.value.value
    return None


def _pin_mtime(path: Path) -> float:
    """Pin a file's mtime in the past; a rewrite would move it to 'now'."""
    old = time.time() - 3600
    os.utime(path, (old, old))
    return old


CONTROLLERS_PY = """\
from aquilia import Controller


class PetsController(Controller):
    async def get(self, ctx):
        return {"ok": True}
"""

SERVICES_PY = """\
class CleanupService:
    def delete(self, item_id: int) -> None:
        ...
"""

MODELS_PY = """\
class ZooModel:
    def get(self, item_id: int):
        ...
"""


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-01/02/03 — import-based component-ref validation
# ═══════════════════════════════════════════════════════════════════════════


class TestValidatorResolvesRefsByImport:
    """The old text scrape false-errored on framework/cross-module refs and
    crashed on multi-colon strings (F-MAN-01/02/03)."""

    @pytest.fixture
    def ws(self, scratch):
        (scratch / "workspace.py").write_text(
            "from aquilia import Module, Workspace\n"
            "def workspace() -> Workspace:\n"
            "    return Workspace(name='ws').module(Module('auth')).module(Module('billing'))\n",
            encoding="utf-8",
        )
        _make_module(
            scratch,
            "auth",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="auth",
                version="0.1.0",
            )
            """,
            {"services.py": "class TokenService:\n    pass\n"},
        )
        # billing exercises all three audit cases at once: a framework guard
        # ref, a cross-module service ref, and a redis:// URL string.
        _make_module(
            scratch,
            "billing",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="billing",
                version="0.1.0",
                guards=["aquilia.auth.guards:AuthGuard"],
                services=["modules.auth.services:TokenService"],
                middleware=["redis://localhost:6379"],
            )
            """,
        )
        return scratch

    def test_framework_guard_ref_is_not_an_error(self, ws):
        from aquilia.cli.commands.run import _validate_workspace_config

        errors = _validate_workspace_config(ws)
        assert errors == [], errors

    def test_cross_module_ref_resolves(self, ws):
        from aquilia.cli.utils.manifest_scan import resolve_component_ref

        resolved, reason = resolve_component_ref("modules.auth.services:TokenService")
        assert reason is None, reason
        assert resolved.__name__ == "TokenService"

    def test_multi_colon_url_string_does_not_crash(self, ws):
        from aquilia.cli.commands.run import _validate_workspace_config

        # The old scraper split on every colon and crashed on
        # "redis://localhost:6379"; now it is merely an unresolvable
        # (non-modules.*) reference, i.e. a warning at most.
        errors = _validate_workspace_config(ws)
        assert errors == [], errors

    def test_validator_still_catches_genuinely_broken_refs(self, scratch):
        """The import-based resolver must not become a no-op pass."""
        from aquilia.cli.commands.run import _validate_workspace_config

        (scratch / "workspace.py").write_text(
            "from aquilia import Module, Workspace\n"
            "def workspace() -> Workspace:\n"
            "    return Workspace(name='ws').module(Module('users'))\n",
            encoding="utf-8",
        )
        _make_module(
            scratch,
            "users",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="users",
                version="0.1.0",
                controllers=["modules.users.controllers:MissingController"],
            )
            """,
            {"controllers.py": "# intentionally empty\n"},
        )
        errors = _validate_workspace_config(scratch)
        assert any("MissingController" in e for e in errors), errors


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-04 + N-6 — aq run validates first and exits non-zero
# ═══════════════════════════════════════════════════════════════════════════


class TestRunValidatesBeforeMutating:
    @pytest.fixture
    def ws(self, scratch):
        (scratch / "workspace.py").write_text(
            "from aquilia import Module, Workspace\n"
            "def workspace() -> Workspace:\n"
            "    return Workspace(name='broken').module(Module('users'))\n",
            encoding="utf-8",
        )
        manifest = scratch / "modules" / "users" / "manifest.py"
        _make_module(
            scratch,
            "users",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="users",
                version="0.1.0",
                controllers=["modules.users.controllers:MissingController"],
            )
            """,
            # HealthController is discoverable but NOT declared: the old
            # sync-first order rewrote the manifest before failing.
            {"controllers.py": 'from aquilia import Controller\n\n\nclass HealthController(Controller):\n    pass\n'},
        )
        return scratch

    def test_run_exits_nonzero_on_validation_failure(self, runner, ws):
        """N-6: a broken workspace must never exit zero from `aq run`."""
        result = runner.invoke(cli, ["--no-color", "run", "--skip-checks"])
        assert result.exit_code == 1, result.output
        assert "MissingController" in result.output

    def test_run_does_not_mutate_files_before_validation(self, runner, ws):
        """F-MAN-04: the broken launch must leave manifest.py untouched."""
        manifest = ws / "modules" / "users" / "manifest.py"
        workspace_py = ws / "workspace.py"
        before_manifest = manifest.read_text(encoding="utf-8")
        before_workspace = workspace_py.read_text(encoding="utf-8")
        m_time = _pin_mtime(manifest)
        w_time = _pin_mtime(workspace_py)

        result = runner.invoke(cli, ["--no-color", "run", "--skip-checks"])
        assert result.exit_code == 1, result.output

        assert manifest.read_text(encoding="utf-8") == before_manifest
        assert "HealthController" not in manifest.read_text(encoding="utf-8")
        assert manifest.stat().st_mtime == m_time
        assert workspace_py.read_text(encoding="utf-8") == before_workspace
        assert workspace_py.stat().st_mtime == w_time


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-06 — auto_discover=False modules are never synced
# ═══════════════════════════════════════════════════════════════════════════


class TestAutoDiscoverOptOut:
    @pytest.fixture
    def ws(self, scratch):
        _make_module(
            scratch,
            "frozen",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="frozen",
                version="0.1.0",
                auto_discover=False,
                services=[],
            )
            """,
            {"services.py": "class HiddenService:\n    pass\n"},
        )
        _make_module(
            scratch,
            "open",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="open",
                version="0.1.0",
                services=[],
            )
            """,
            {"services.py": "class VisibleService:\n    pass\n"},
        )
        return scratch

    def test_sync_all_leaves_opted_out_manifest_untouched(self, ws):
        from aquilia.discovery.engine import AutoDiscoveryEngine

        manifest = ws / "modules" / "frozen" / "manifest.py"
        before = manifest.read_text(encoding="utf-8")

        reports = AutoDiscoveryEngine(ws / "modules").sync_all()

        assert manifest.read_text(encoding="utf-8") == before
        assert "HiddenService" not in manifest.read_text(encoding="utf-8")
        frozen_report = next(r for r in reports if r.module_name == "frozen")
        assert not frozen_report.has_changes

    def test_opted_in_module_is_still_synced(self, ws):
        """Control: the same fixture with auto-discovery on DOES get synced,
        proving the skip above is caused by the opt-out, not by the fixture."""
        from aquilia.discovery.engine import AutoDiscoveryEngine

        AutoDiscoveryEngine(ws / "modules").sync_all()

        content = (ws / "modules" / "open" / "manifest.py").read_text(encoding="utf-8")
        assert "modules.open.services:VisibleService" in content

    def test_discover_sync_respects_opt_out(self, runner, ws):
        (ws / "workspace.py").write_text(
            "from aquilia import Module, Workspace\n"
            "def workspace() -> Workspace:\n"
            "    return Workspace(name='ws').module(Module('frozen'))\n",
            encoding="utf-8",
        )
        manifest = ws / "modules" / "frozen" / "manifest.py"
        before = manifest.read_text(encoding="utf-8")

        result = runner.invoke(cli, ["--no-color", "discover", "--sync"])

        assert result.exit_code == 0, result.output
        assert manifest.read_text(encoding="utf-8") == before


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-07 / N-11 — the differ never silently removes manifest entries
# ═══════════════════════════════════════════════════════════════════════════


class TestSyncNeverDestroysHandwrittenRefs:
    @pytest.fixture
    def ws(self, scratch):
        _make_module(
            scratch,
            "app",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="app",
                version="0.1.0",
                services=[
                    "modules.app.services:LegacyHelper",
                    "modules.app.services:GoneService",
                ],
            )
            """,
            {
                # LegacyHelper is a real, live class -- it merely does not
                # follow the *Service naming convention, so convention-based
                # discovery never reports it (the hand-written ref case).
                "services.py": "class LegacyHelper:\n    pass\n\n\nclass FreshService:\n    pass\n",
            },
        )
        return scratch

    def test_default_sync_keeps_undeclared_and_stale_refs(self, ws):
        from aquilia.discovery.engine import AutoDiscoveryEngine

        engine = AutoDiscoveryEngine(ws / "modules")
        engine.sync_all()

        content = (ws / "modules" / "app" / "manifest.py").read_text(encoding="utf-8")
        services = _manifest_field(content, "services")
        # FreshService is added; LegacyHelper and GoneService are kept as-is.
        assert "modules.app.services:FreshService" in services
        assert "modules.app.services:LegacyHelper" in services
        assert "modules.app.services:GoneService" in services

    def test_prune_removes_only_truly_dead_refs(self, ws):
        from aquilia.discovery.engine import AutoDiscoveryEngine

        engine = AutoDiscoveryEngine(ws / "modules")
        engine.sync_all()  # add FreshService first
        engine.sync_manifest("app", prune=True)

        content = (ws / "modules" / "app" / "manifest.py").read_text(encoding="utf-8")
        services = _manifest_field(content, "services")
        # GoneService cannot be imported -> removed.
        assert "modules.app.services:GoneService" not in services
        # LegacyHelper still exists on disk -> survives even under --prune.
        assert "modules.app.services:LegacyHelper" in services
        assert "modules.app.services:FreshService" in services


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-08 — fingerprint covers every config dimension
# ═══════════════════════════════════════════════════════════════════════════


class TestManifestFingerprint:
    @pytest.mark.parametrize(
        ("field", "value"),
        [
            ("base_path", "/custom/base"),
            ("sessions", [SessionConfig(name="web")]),
            ("versioning", AppVersioningConfig(strategy="url", versions=["v1"])),
            ("features", [FeatureConfig(name="beta")]),
            ("templates", TemplateConfig(search_paths=["tpl"])),
            ("socket_middleware", ["modules.m.sockets:PingMiddleware"]),
            ("config_schema", {"type": "object"}),
            ("discover_patterns", ["controllers", "custom"]),
        ],
    )
    def test_differing_field_changes_fingerprint(self, field, value):
        from aquilia.manifest import AppManifest

        base = AppManifest(name="m", version="1.0.0")
        variant = AppManifest(name="m", version="1.0.0", **{field: value})
        assert variant.fingerprint() != base.fingerprint(), f"{field} is not covered by the fingerprint"

    def test_identical_manifests_share_fingerprint(self):
        from aquilia.manifest import AppManifest

        assert AppManifest(name="m", version="1.0.0").fingerprint() == AppManifest(name="m", version="1.0.0").fingerprint()

    def test_to_dict_includes_previously_omitted_fields(self):
        from aquilia.manifest import (
            AppManifest,
            AppVersioningConfig,
            FeatureConfig,
            SessionConfig,
            TemplateConfig,
        )

        manifest = AppManifest(
            name="m",
            version="1.0.0",
            base_path="/x",
            sessions=[SessionConfig(name="s")],
            versioning=AppVersioningConfig(strategy="url"),
            features=[FeatureConfig(name="f")],
            templates=TemplateConfig(search_paths=["t"]),
            socket_middleware=["modules.m.sock:XMiddleware"],
            config_schema={"type": "object"},
            discover_patterns=["controllers"],
        )
        data = manifest.to_dict()
        for key in (
            "base_path",
            "sessions",
            "versioning",
            "features",
            "templates",
            "socket_middleware",
            "config_schema",
            "discover_patterns",
        ):
            assert key in data, f"{key} missing from to_dict()"


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-09 — imports/depends_on divergence warning
# ═══════════════════════════════════════════════════════════════════════════


class TestImportsDependsOnDivergence:
    def test_both_set_and_different_warns(self):
        from aquilia.manifest import AppManifest

        with pytest.warns(UserWarning, match="different values"):
            AppManifest(name="m", version="1.0.0", imports=["auth"], depends_on=["billing"])

    def test_depends_on_only_mirrors_to_imports(self):
        from aquilia.manifest import AppManifest

        manifest = AppManifest(name="m", version="1.0.0", depends_on=["auth"])
        assert manifest.imports == ["auth"]

    def test_imports_only_mirrors_to_depends_on(self):
        from aquilia.manifest import AppManifest

        manifest = AppManifest(name="m", version="1.0.0", imports=["billing"])
        assert manifest.depends_on == ["billing"]

    def test_both_set_and_equal_is_silent(self):
        from aquilia.manifest import AppManifest

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            AppManifest(name="m", version="1.0.0", imports=["auth"], depends_on=["auth"])
        assert not [w for w in caught if issubclass(w.category, UserWarning)]


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-12 — manifest name validation
# ═══════════════════════════════════════════════════════════════════════════


class TestManifestNameValidation:
    @pytest.mark.parametrize("bad_name", ["1users", "my-mod", "my mod", "модуль", "a" * 65, ""])
    def test_invalid_names_rejected(self, bad_name):
        from aquilia.faults.domains import ManifestInvalidFault
        from aquilia.manifest import AppManifest

        with pytest.raises(ManifestInvalidFault):
            AppManifest(name=bad_name, version="1.0.0")

    @pytest.mark.parametrize("good_name", ["users", "users_2", "Users2", "a" * 64])
    def test_valid_names_accepted(self, good_name):
        from aquilia.manifest import AppManifest

        assert AppManifest(name=good_name, version="1.0.0").name == good_name


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-13 — AppManifest.database deprecation is explicit about discarding
# ═══════════════════════════════════════════════════════════════════════════


class TestDatabaseDeprecation:
    def test_warning_states_value_is_discarded(self):
        from aquilia.manifest import AppManifest, DatabaseConfig

        with pytest.warns(DeprecationWarning, match="DISCARDED") as caught:
            AppManifest(name="m", version="1.0.0", database=DatabaseConfig(url="sqlite:///x.db"))

        message = " ".join(str(w.message) for w in caught)
        assert "Integration.database()" in message
        assert "workspace.py" in message

    def test_database_value_is_reset_to_none(self):
        from aquilia.manifest import AppManifest, DatabaseConfig

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            manifest = AppManifest(name="m", version="1.0.0", database=DatabaseConfig())
        assert manifest.database is None


# ═══════════════════════════════════════════════════════════════════════════
# F-MAN-05 — workspace.py rewriter honesty
# ═══════════════════════════════════════════════════════════════════════════


class TestWorkspaceRewriterHonesty:
    WORKSPACE = """\
        from aquilia import Module, Workspace


        def workspace() -> Workspace:
            return (
                Workspace(name="app")
                .module(Module("app", version="1.0.0"))
                .integrate(Module("extra", version="0.0.1"))
            )
        """

    def test_noop_update_does_not_rewrite(self, tmp_path, capsys):
        from aquilia.cli.generators.workspace import WorkspaceGenerator

        ws_file = tmp_path / "workspace.py"
        ws_file.write_text(textwrap.dedent(self.WORKSPACE), encoding="utf-8")
        generator = WorkspaceGenerator(name="app", path=tmp_path)
        discovered = {"app": {"version": "1.0.0"}}

        generator.update_workspace_config(ws_file, discovered)
        content = ws_file.read_text(encoding="utf-8")
        pinned = _pin_mtime(ws_file)

        generator.update_workspace_config(ws_file, discovered)

        assert ws_file.read_text(encoding="utf-8") == content
        assert ws_file.stat().st_mtime == pinned
        assert "already in sync" in capsys.readouterr().out

    def test_blank_lines_outside_modules_section_survive(self, tmp_path):
        from aquilia.cli.generators.workspace import WorkspaceGenerator

        # Three-and-more blank line runs around the developer's own comment
        # banner are NOT part of the modules section; the old whole-file
        # \\n{3,} collapse flattened them.
        workspace = textwrap.dedent(
            """\
            from aquilia import Module, Workspace



            # ---- developer notes (keep the air) ----



            def workspace() -> Workspace:
                return (
                    Workspace(name="app")
                    .module(Module("app", version="1.0.0"))
                    .integrate(Module("extra", version="0.0.1"))
                )
            """
        )
        ws_file = tmp_path / "workspace.py"
        ws_file.write_text(workspace, encoding="utf-8")

        generator = WorkspaceGenerator(name="app", path=tmp_path)
        generator.update_workspace_config(ws_file, {"app": {"version": "1.0.0"}})

        content = ws_file.read_text(encoding="utf-8")
        assert "# ---- developer notes (keep the air) ----" in content
        assert "\n\n\n" in content, "blank-line runs outside the modules section were collapsed"
        ast.parse(content)


# ═══════════════════════════════════════════════════════════════════════════
# N-1 — aq manifest update refuses destructive rewrites
# ═══════════════════════════════════════════════════════════════════════════


class TestManifestUpdateDestructiveGuard:
    def test_broken_import_refuses_to_write(self, runner, scratch):
        """A module whose package cannot be imported must not be 'synced' to
        empty lists (the old code swallowed the ImportError and emptied the
        manifest's controllers/services)."""
        _make_module(
            scratch,
            "broken",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="broken",
                version="0.1.0",
                controllers=["modules.broken.controllers:DemoController"],
                services=["modules.broken.services:DemoService"],
            )
            """,
            {
                "__init__.py": "import aquilia_totally_missing_package  # noqa: F401\n",
                "controllers.py": 'from aquilia import Controller\n\n\nclass DemoController(Controller):\n    pass\n',
                "services.py": "class DemoService:\n    pass\n",
            },
        )
        manifest = scratch / "modules" / "broken" / "manifest.py"
        before = manifest.read_text(encoding="utf-8")

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "broken"])

        assert result.exit_code == 1, result.output
        assert "refusing" in result.output
        assert manifest.read_text(encoding="utf-8") == before

    def test_empty_scan_with_declarations_refuses_to_write(self, runner, scratch):
        """Even when the package imports, a scan that found nothing while the
        manifest declares components is a failed scan, not an empty truth."""
        _make_module(
            scratch,
            "hollow",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="hollow",
                version="0.1.0",
                controllers=["modules.hollow.controllers:GhostController"],
            )
            """,
        )
        manifest = scratch / "modules" / "hollow" / "manifest.py"
        before = manifest.read_text(encoding="utf-8")

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "hollow"])

        assert result.exit_code == 1, result.output
        assert "refusing" in result.output
        assert manifest.read_text(encoding="utf-8") == before


# ═══════════════════════════════════════════════════════════════════════════
# N-2 — controller detection via the Controller base class
# ═══════════════════════════════════════════════════════════════════════════


class TestControllerDetection:
    def test_model_with_get_is_not_a_controller(self):
        from aquilia.cli.commands.manifest import _is_controller_class

        class FakeModel:
            def get(self, item_id):
                ...

        assert _is_controller_class(FakeModel) is False

    def test_service_with_delete_is_not_a_controller(self):
        from aquilia.cli.commands.manifest import _is_controller_class

        class FakeService:
            def delete(self, item_id):
                ...

        assert _is_controller_class(FakeService) is False

    def test_real_controller_subclass_is_a_controller(self):
        from aquilia.cli.commands.manifest import _is_controller_class
        from aquilia.controller import Controller

        class RealController(Controller):
            async def get(self, ctx):
                ...

        assert _is_controller_class(RealController) is True

    def test_manifest_update_classifies_correctly(self, runner, scratch):
        """A model with .get and a service with .delete used to land in
        controllers=[...]; only the real Controller subclass may."""
        _make_module(
            scratch,
            "zoo",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="zoo",
                version="0.1.0",
                controllers=[],
                services=[],
            )
            """,
            {
                "controllers.py": CONTROLLERS_PY,
                "services.py": SERVICES_PY,
                "models.py": MODELS_PY,
            },
        )

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "zoo"])
        assert result.exit_code == 0, result.output

        content = (scratch / "modules" / "zoo" / "manifest.py").read_text(encoding="utf-8")
        controllers = _manifest_field(content, "controllers")
        services = _manifest_field(content, "services")

        assert controllers == ["modules.zoo.controllers:PetsController"]
        assert services == ["modules.zoo.services:CleanupService"]
        assert "ZooModel" not in content


# ═══════════════════════════════════════════════════════════════════════════
# N-3 — module-builder manifests get modern AppManifest syntax
# ═══════════════════════════════════════════════════════════════════════════


class TestModernManifestEmission:
    def test_module_builder_manifest_rewritten_to_appmanifest(self, runner, scratch):
        """register_controllers()/register_services() are deprecated no-ops;
        syncing into them wrote dead code. The rewrite must produce a valid
        AppManifest with controllers=/services= entries."""
        _make_module(
            scratch,
            "legacy",
            """\
            from aquilia import Module

            manifest = (
                Module("legacy", version="0.2.0", description="Legacy module")
                .register_controllers("modules.legacy.controllers:LegacyController")
                .depends_on("base")
            )
            """,
            {
                "controllers.py": 'from aquilia import Controller\n\n\nclass LegacyController(Controller):\n    pass\n',
                "services.py": "class LegacyService:\n    pass\n",
            },
        )

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "legacy"])
        assert result.exit_code == 0, result.output

        content = (scratch / "modules" / "legacy" / "manifest.py").read_text(encoding="utf-8")
        # The result must be valid, modern AppManifest syntax (AST-parse).
        assert "register_controllers" not in content
        assert _manifest_field(content, "controllers") == ["modules.legacy.controllers:LegacyController"]
        assert _manifest_field(content, "services") == ["modules.legacy.services:LegacyService"]
        # Identity metadata and dependencies survive the rewrite.
        assert _manifest_kwarg(content, "name") == "legacy"
        assert _manifest_kwarg(content, "version") == "0.2.0"
        assert _manifest_field(content, "imports") == ["base"]


# ═══════════════════════════════════════════════════════════════════════════
# N-4 — --freeze handles the keyword form and reports no-ops honestly
# ═══════════════════════════════════════════════════════════════════════════


class TestFreezeManifest:
    def test_freeze_keyword_form(self, runner, scratch):
        """`auto_discover=True` as an AppManifest kwarg must be frozen too,
        not only the builder form `.auto_discover(True)`."""
        _make_module(
            scratch,
            "kw",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="kw",
                version="0.1.0",
                auto_discover=True,
                controllers=["modules.kw.controllers:KwController"],
            )
            """,
            {"controllers.py": 'from aquilia import Controller\n\n\nclass KwController(Controller):\n    pass\n'},
        )
        manifest = scratch / "modules" / "kw" / "manifest.py"

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "kw", "--freeze"])

        assert result.exit_code == 0, result.output
        content = manifest.read_text(encoding="utf-8")
        assert _manifest_kwarg(content, "auto_discover") is False
        assert "auto_discover=True" not in content
        assert "Updated" in result.output

    def test_freeze_module_builder_form_emits_frozen_appmanifest(self, runner, scratch):
        """Freezing a legacy builder manifest rewrites it to AppManifest
        syntax -- the freeze must be baked into the emitted manifest, not
        lost together with the `.auto_discover(True)` chain element."""
        _make_module(
            scratch,
            "legacy2",
            """\
            from aquilia import Module

            manifest = (
                Module("legacy2", version="0.3.0", description="Legacy")
                .register_controllers("modules.legacy2.controllers:OldController")
                .auto_discover(True)
            )
            """,
            {"controllers.py": 'from aquilia import Controller\n\n\nclass OldController(Controller):\n    pass\n'},
        )
        manifest = scratch / "modules" / "legacy2" / "manifest.py"

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "legacy2", "--freeze"])

        assert result.exit_code == 0, result.output
        content = manifest.read_text(encoding="utf-8")
        assert "register_controllers" not in content
        assert _manifest_kwarg(content, "auto_discover") is False
        assert "Freezing" in result.output

    def test_noop_freeze_does_not_claim_update(self, runner, scratch):
        """Freezing an already-frozen, in-sync manifest must not rewrite the
        file nor print an 'Updated' message."""
        _make_module(
            scratch,
            "cold",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="cold",
                version="0.1.0",
                auto_discover=False,
                controllers=["modules.cold.controllers:ColdController"],
            )
            """,
            {"controllers.py": 'from aquilia import Controller\n\n\nclass ColdController(Controller):\n    pass\n'},
        )
        manifest = scratch / "modules" / "cold" / "manifest.py"
        before = manifest.read_text(encoding="utf-8")
        pinned = _pin_mtime(manifest)

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "cold", "--freeze"])

        assert result.exit_code == 0, result.output
        assert "Updated" not in result.output
        assert manifest.read_text(encoding="utf-8") == before
        assert manifest.stat().st_mtime == pinned


# ═══════════════════════════════════════════════════════════════════════════
# N-5 — list injection never targets commented-out lists
# ═══════════════════════════════════════════════════════════════════════════


class TestCommentAwareInjection:
    def test_injection_targets_the_real_list_not_the_comment(self, runner, scratch):
        _make_module(
            scratch,
            "cmt",
            """\
            from aquilia import AppManifest

            # controllers = [
            #     "modules.cmt.controllers:OldController",
            # ]

            manifest = AppManifest(
                name="cmt",
                version="0.1.0",
                controllers=[],
            )
            """,
            {"controllers.py": 'from aquilia import Controller\n\n\nclass FreshController(Controller):\n    pass\n'},
        )
        manifest = scratch / "modules" / "cmt" / "manifest.py"

        result = runner.invoke(cli, ["--no-color", "manifest", "update", "cmt"])
        assert result.exit_code == 0, result.output

        content = manifest.read_text(encoding="utf-8")
        # The new ref landed in the REAL list...
        assert _manifest_field(content, "controllers") == ["modules.cmt.controllers:FreshController"]
        # ...and the commented-out example above it is untouched.
        assert '#     "modules.cmt.controllers:OldController",' in content
        assert content.count("FreshController") == 1


# ═══════════════════════════════════════════════════════════════════════════
# ManifestWriter append safety (found while building the F-MAN-07 regression)
# ═══════════════════════════════════════════════════════════════════════════


class TestManifestWriterAppendSafety:
    def test_append_to_one_line_list_does_not_splice_strings(self):
        """Appending to a non-empty single-line list used to rely on the last
        entry having a trailing comma -- without one, the two adjacent string
        literals silently concatenated into ONE ref via implicit string
        concatenation, destroying both."""
        from aquilia.discovery.engine import ManifestWriter

        source = 'services = ["modules.app.services:LegacyHelper"]\n'
        out = ManifestWriter()._add_component(source, "services", "modules.app.services:FreshService")

        tree = ast.parse(out)
        assign = tree.body[0]
        elements = [elt.value for elt in assign.value.elts]
        assert elements == ["modules.app.services:LegacyHelper", "modules.app.services:FreshService"]


# ═══════════════════════════════════════════════════════════════════════════
# N-8 — --depends-on ignores commented-out modules
# ═══════════════════════════════════════════════════════════════════════════


class TestDependsOnValidation:
    @pytest.fixture
    def ws(self, scratch):
        (scratch / "workspace.py").write_text(
            "from aquilia import Module, Workspace\n"
            "\n"
            "# Example (do not uncomment):\n"
            "# return Workspace(name='demo').module(Module('ghost'))\n"
            "\n"
            "def workspace() -> Workspace:\n"
            "    return (\n"
            "        Workspace(name='demo')\n"
            "        .module(Module('real'))\n"
            "    )\n",
            encoding="utf-8",
        )
        _make_module(
            scratch,
            "real",
            """\
            from aquilia import AppManifest

            manifest = AppManifest(
                name="real",
                version="0.1.0",
            )
            """,
        )
        return scratch

    def test_commented_out_module_is_not_a_valid_dependency(self, runner, ws):
        result = runner.invoke(cli, ["--no-color", "add", "module", "newmod", "--depends-on", "ghost", "-y", "--no-docker"])

        assert result.exit_code == 1, result.output
        assert "ghost" in result.output
        assert not (ws / "modules" / "newmod").exists()

    def test_registered_module_is_a_valid_dependency(self, runner, ws):
        result = runner.invoke(cli, ["--no-color", "add", "module", "newmod", "--depends-on", "real", "-y", "--no-docker"])

        assert result.exit_code == 0, result.output
        assert (ws / "modules" / "newmod" / "manifest.py").exists()


# ═══════════════════════════════════════════════════════════════════════════
# N-7 — module-name scraping accepts both quote styles
# ═══════════════════════════════════════════════════════════════════════════


class TestModuleNameScraping:
    def test_single_quoted_modules_are_recognized(self):
        from aquilia.cli.utils.manifest_scan import extract_registered_modules

        content = (
            "from aquilia import Module, Workspace\n"
            "def workspace() -> Workspace:\n"
            "    return Workspace(name='w').module(Module('real')).module(Module('other'))\n"
        )
        assert extract_registered_modules(content) == ["real", "other"]

    def test_double_quoted_modules_are_recognized(self):
        from aquilia.cli.utils.manifest_scan import extract_registered_modules

        content = (
            "from aquilia import Module, Workspace\n"
            'def workspace() -> Workspace:\n'
            '    return Workspace(name="w").module(Module("real"))\n'
        )
        assert extract_registered_modules(content) == ["real"]
