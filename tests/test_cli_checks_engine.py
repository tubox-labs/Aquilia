"""Tests for the CLI checks engine and core refactor.

Covers the modernization work:
  - check registry + runner isolation
  - severity -> exit code mapping (the false-green fix)
  - JSON output shape for CI
  - workspace loader (replaces 10 spec_from_file_location copies)
  - route introspection (the 1-vs-6 route bug)
  - help categorisation drift (the deploy-gen/deploy mismatch)
"""

import json
import sys

import pytest

from aquilia.cli.checks.base import (
    Check,
    CheckResult,
    Finding,
    all_checks,
    checks_for,
    run_checks,
)
from aquilia.cli.checks.report import render_human, render_json, result_exit_code, summarise
from aquilia.cli.core.context import AqContext
from aquilia.cli.core.exits import ExitCode, exit_code_for, max_severity, severity_rank
from aquilia.cli.core.workspace import load_workspace
from aquilia.cli.introspect.routes import collect_routes, count_routes
from aquilia.faults.core import Severity

CONTROLLER_SRC = """
from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response


class UsersController(Controller):
    prefix = "/"

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        return Response.json([])

    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        return Response.json({})

    @GET("/<id:int>")
    async def get_user(self, ctx: RequestCtx, id: int):
        return Response.json({})

    @PUT("/<id:int>")
    async def update_user(self, ctx: RequestCtx, id: int):
        return Response.json({})

    @DELETE("/<id:int>")
    async def delete_user(self, ctx: RequestCtx, id: int):
        return Response.json({})
"""


def _make_workspace(tmp_path, *, controllers=("modules.users.controllers:UsersController",)):
    """Build a minimal but real workspace on disk."""
    (tmp_path / "workspace.py").write_text(
        "from aquilia import Module, Workspace\n"
        'workspace = Workspace(name="demo").module(Module("users", version="0.1.0"))\n',
        encoding="utf-8",
    )
    mod = tmp_path / "modules" / "users"
    mod.mkdir(parents=True)
    (mod / "__init__.py").write_text("", encoding="utf-8")
    (mod / "controllers.py").write_text(CONTROLLER_SRC, encoding="utf-8")
    refs = ", ".join(f'"{c}"' for c in controllers)
    (mod / "manifest.py").write_text(
        "from aquilia import AppManifest\n"
        f'manifest = AppManifest(name="users", version="0.1.0", controllers=[{refs}])\n',
        encoding="utf-8",
    )
    return tmp_path


@pytest.fixture
def importable(tmp_path):
    """Workspace on disk and importable, cleaned up afterwards."""
    _make_workspace(tmp_path)
    sys.path.insert(0, str(tmp_path))
    try:
        yield tmp_path
    finally:
        if str(tmp_path) in sys.path:
            sys.path.remove(str(tmp_path))
        for name in [m for m in sys.modules if m.startswith(("modules.", "_aq_"))]:
            sys.modules.pop(name, None)


class TestSeverityExitMapping:
    """Severity -> exit code. The fix for doctor reporting 0 on a broken workspace."""

    def test_no_findings_is_ok(self):
        assert exit_code_for([]) == ExitCode.OK

    def test_warnings_do_not_fail(self):
        """Warnings stay visible but must not break a build."""
        assert exit_code_for([Severity.INFO, Severity.WARN]) == ExitCode.OK

    def test_error_fails(self):
        assert exit_code_for([Severity.WARN, Severity.ERROR]) == ExitCode.FAILED

    def test_fatal_fails(self):
        assert exit_code_for([Severity.FATAL]) == ExitCode.FAILED

    def test_rank_is_ordered(self):
        """Severity is a str-Enum, so ranking must be explicit."""
        assert severity_rank(Severity.INFO) < severity_rank(Severity.WARN)
        assert severity_rank(Severity.WARN) < severity_rank(Severity.ERROR)
        assert severity_rank(Severity.ERROR) < severity_rank(Severity.FATAL)

    def test_max_severity_picks_worst(self):
        assert max_severity([Severity.INFO, Severity.ERROR, Severity.WARN]) == Severity.ERROR

    def test_max_severity_empty_is_none(self):
        assert max_severity([]) is None


class TestCheckRunner:
    """Runner isolates failures so one broken probe cannot hide the rest."""

    def _ctx(self, path):
        return AqContext(cwd=path)

    def test_findings_are_collected(self, tmp_path):
        check = Check(
            name="t.find",
            summary="",
            run=lambda ctx: [Finding("T_CODE", "boom", Severity.ERROR)],
            requires_workspace=False,
        )
        results = run_checks(self._ctx(tmp_path), [check])
        assert len(results) == 1
        assert results[0].findings[0].code == "T_CODE"
        assert not results[0].ok

    def test_raising_check_is_isolated(self, tmp_path):
        """A check that raises is reported, not propagated."""

        def boom(ctx):
            raise RuntimeError("kaboom")

        good = Check(name="t.good", summary="", run=lambda ctx: [], requires_workspace=False)
        bad = Check(name="t.bad", summary="", run=boom, requires_workspace=False)

        results = run_checks(self._ctx(tmp_path), [bad, good])
        assert results[0].error is not None
        assert "kaboom" in results[0].error
        assert results[1].ok  # the good check still ran

    def test_workspace_required_checks_skip_without_workspace(self, tmp_path):
        check = Check(name="t.ws", summary="", run=lambda ctx: [], requires_workspace=True)
        results = run_checks(self._ctx(tmp_path), [check])
        assert results[0].skipped
        assert "no workspace" in results[0].skip_reason

    def test_clean_check_passes(self, tmp_path):
        check = Check(name="t.ok", summary="", run=lambda ctx: [], requires_workspace=False)
        assert run_checks(self._ctx(tmp_path), [check])[0].ok


class TestRegistry:
    """Built-in checks are discoverable and filterable."""

    def test_builtin_checks_registered(self):
        names = {c.name for c in all_checks()}
        for expected in ("env.python", "workspace.present", "routes.parsable", "db.reachable"):
            assert expected in names

    def test_filter_by_tag(self):
        quick = checks_for(tags=["quick"])
        assert quick
        assert all("quick" in c.tags for c in quick)

    def test_filter_by_subsystem(self):
        routes = checks_for(subsystems=["routes"])
        assert routes
        assert all(c.subsystem == "routes" for c in routes)

    def test_subsystem_coverage_expanded(self):
        """Phase 4: subsystems previously absent from the CLI now have checks."""
        subsystems = {c.subsystem for c in all_checks()}
        for expected in ("tasks", "templates", "db", "routes", "di"):
            assert expected in subsystems


class TestReporting:
    """Human and JSON renderers read the same findings."""

    def _results(self):
        check = Check(name="t.r", summary="s", run=lambda ctx: [], requires_workspace=False)
        return [
            CheckResult(
                check=check,
                findings=[
                    Finding("E1", "an error", Severity.ERROR, remedy="fix it", location="a.py"),
                    Finding("W1", "a warning", Severity.WARN),
                ],
            )
        ]

    def test_summarise_counts_by_severity(self):
        s = summarise(self._results())
        assert s["total_findings"] == 2
        assert s["findings"]["error"] == 1
        assert s["findings"]["warn"] == 1
        assert s["passed"] is False

    def test_json_is_parseable_and_shaped(self):
        payload = json.loads(render_json(self._results()))
        assert payload["summary"]["total_findings"] == 2
        assert payload["exit_code"] == int(ExitCode.FAILED)
        assert payload["checks"][0]["findings"][0]["code"] == "E1"

    def test_human_output_shows_warnings_by_default(self):
        """Warnings were previously hidden unless -v, which produced false greens."""
        text = render_human(self._results(), verbose=False)
        assert "W1" in text
        assert "a warning" in text

    def test_human_output_includes_remedy(self):
        assert "fix it" in render_human(self._results(), verbose=False)

    def test_exit_code_from_results(self):
        assert result_exit_code(self._results()) == ExitCode.FAILED


class TestWorkspaceLoader:
    """One loader replaces ten spec_from_file_location copies."""

    def test_missing_workspace_does_not_raise(self, tmp_path):
        ws = load_workspace(tmp_path)
        assert ws.exists is False
        assert ws.module_names == []

    def test_imports_workspace_object(self, importable):
        ws = load_workspace(importable)
        assert ws.exists
        assert ws.module_names == ["users"]
        assert ws.used_fallback is False  # real import, not the regex path

    def test_regex_fallback_when_no_workspace_object(self, tmp_path):
        """A workspace.py without a `workspace` variable still yields modules."""
        (tmp_path / "workspace.py").write_text(
            'from aquilia import Module\nnot_the_expected_name = [Module("users")]\n',
            encoding="utf-8",
        )
        ws = load_workspace(tmp_path)
        assert ws.module_names == ["users"]
        assert ws.used_fallback is True

    def test_commented_modules_ignored(self, tmp_path):
        """The regex fallback must not pick up commented-out Module() lines."""
        (tmp_path / "workspace.py").write_text('# .module(Module("ghost"))\nfoo = 1\n', encoding="utf-8")
        assert load_workspace(tmp_path).module_names == []

    def test_manifest_is_loaded_and_cached(self, importable):
        ws = load_workspace(importable)
        assert ws.manifest("users") is ws.manifest("users")
        assert ws.manifest("users").name == "users"


class TestRouteIntrospection:
    """The headline bug: a 5-route controller reported as 1 route."""

    def test_all_routes_are_found(self, importable):
        ws = load_workspace(importable)
        entries = collect_routes(ws)
        assert len(entries) == 1
        assert entries[0].ok
        assert len(entries[0].routes) == 5

    def test_count_routes_counts_routes_not_controllers(self, importable):
        """Regression: count was previously the controller count."""
        assert count_routes(load_workspace(importable)) == 5

    def test_http_methods_are_correct(self, importable):
        entries = collect_routes(load_workspace(importable))
        assert {r.http_method for r in entries[0].routes} == {"GET", "POST", "PUT", "DELETE"}

    def test_bad_reference_reports_error(self, tmp_path):
        _make_workspace(tmp_path, controllers=("modules.users.controllers:GhostController",))
        sys.path.insert(0, str(tmp_path))
        try:
            entries = collect_routes(load_workspace(tmp_path))
            assert entries[0].error is not None
            assert entries[0].routes == []
        finally:
            sys.path.remove(str(tmp_path))
            for name in [m for m in sys.modules if m.startswith(("modules.", "_aq_"))]:
                sys.modules.pop(name, None)


class TestRuntimeParity:
    """Reported paths must equal the paths the server actually serves."""

    def test_module_route_prefix_is_applied(self, tmp_path):
        """Regression: the module's .route_prefix() was ignored, so a module
        mounted at /users displayed its routes at /."""
        (tmp_path / "workspace.py").write_text(
            "from aquilia import Module, Workspace\n"
            'workspace = Workspace(name="demo").module(\n'
            '    Module("users", version="0.1.0").route_prefix("/api/users")\n'
            ")\n",
            encoding="utf-8",
        )
        mod = tmp_path / "modules" / "users"
        mod.mkdir(parents=True)
        (mod / "__init__.py").write_text("", encoding="utf-8")
        (mod / "controllers.py").write_text(CONTROLLER_SRC, encoding="utf-8")
        (mod / "manifest.py").write_text(
            "from aquilia import AppManifest\n"
            'manifest = AppManifest(name="users", version="0.1.0",\n'
            '    controllers=["modules.users.controllers:UsersController"])\n',
            encoding="utf-8",
        )
        sys.path.insert(0, str(tmp_path))
        try:
            entries = collect_routes(load_workspace(tmp_path))
            paths = {r.full_path for r in entries[0].routes}
            assert all(p.startswith("/api/users") for p in paths), paths
        finally:
            sys.path.remove(str(tmp_path))
            for name in [m for m in sys.modules if m.startswith(("modules.", "_aq_"))]:
                sys.modules.pop(name, None)

    def test_starter_controller_is_included(self, tmp_path):
        """Regression: a declared .starter() served GET / but was never
        reported, so the route total was short by one."""
        _make_workspace(tmp_path)
        (tmp_path / "workspace.py").write_text(
            "from aquilia import Module, Workspace\n"
            'workspace = Workspace(name="demo").module(\n'
            '    Module("users", version="0.1.0")\n'
            ').starter("starter")\n',
            encoding="utf-8",
        )
        (tmp_path / "starter.py").write_text(
            "from aquilia import Controller, GET, Response\n\n"
            "class StarterController(Controller):\n"
            '    prefix = "/"\n\n'
            '    @GET("/")\n'
            "    async def welcome(self, ctx):\n"
            "        return Response.json({})\n",
            encoding="utf-8",
        )
        sys.path.insert(0, str(tmp_path))
        try:
            ws = load_workspace(tmp_path)
            assert ws.starter_module == "starter"
            assert count_routes(ws) == 6
            starter = [e for e in collect_routes(ws) if e.module == "(starter)"]
            assert len(starter) == 1
            assert [r.full_path for r in starter[0].routes] == ["/"]
        finally:
            sys.path.remove(str(tmp_path))
            for name in [m for m in sys.modules if m.startswith(("modules.", "_aq_"))]:
                sys.modules.pop(name, None)

    def test_starter_ignored_when_file_absent(self, importable):
        """A .starter() declaration with no file on disk must not be reported."""
        assert load_workspace(importable).starter_module is None


class TestBrokenWorkspaceFailsChecks:
    """End-to-end: a broken manifest must not report healthy."""

    def test_dangling_reference_produces_error(self, tmp_path):
        _make_workspace(tmp_path, controllers=("modules.users.controllers:GhostController",))
        sys.path.insert(0, str(tmp_path))
        try:
            results = run_checks(AqContext(cwd=tmp_path), all_checks())
            assert result_exit_code(results) == ExitCode.FAILED
            codes = {f.code for r in results for f in r.findings}
            assert "AQ_REF_MISSING_ATTR" in codes
        finally:
            sys.path.remove(str(tmp_path))
            for name in [m for m in sys.modules if m.startswith(("modules.", "_aq_"))]:
                sys.modules.pop(name, None)

    def test_healthy_workspace_passes(self, importable):
        results = run_checks(AqContext(cwd=importable), all_checks())
        assert result_exit_code(results) == ExitCode.OK


class TestHelpCategorisation:
    """Guards the deploy-gen/deploy drift that hid 7 commands under 'Other'."""

    def test_every_registered_command_has_a_category(self):
        import click

        from aquilia.cli.__main__ import cli
        from aquilia.cli.core.registry import uncategorised

        names = cli.list_commands(click.Context(cli))
        assert uncategorised(names) == []
