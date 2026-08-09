"""Exit-code contract tests for CLI commands.

The plan's core rule: *a broken workspace must never exit zero from a health
command.* This parametrized suite is the anti-false-green harness.

Tests run through the real ``aq`` entry point (``CliRunner``) so they cover
argument parsing and the workspace guard, not just command internals. The CLI
resolves the workspace from the current directory, so fixtures ``chdir``.
"""

import json
import sys

import pytest
from click.testing import CliRunner

from aquilia.cli.__main__ import cli


def _clean_modules():
    """Drop test workspace modules so fixtures do not leak between tests."""
    for name in [m for m in sys.modules if m.startswith(("modules", "_aq_"))]:
        sys.modules.pop(name, None)


@pytest.fixture
def ws_empty(tmp_path, monkeypatch):
    """A workspace with no modules -- valid, should pass."""
    (tmp_path / "workspace.py").write_text(
        "from aquilia import Workspace\nworkspace = Workspace(name='empty')\n",
        encoding="utf-8",
    )
    (tmp_path / "modules").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    _clean_modules()
    yield tmp_path
    _clean_modules()


@pytest.fixture
def ws_broken(tmp_path, monkeypatch):
    """A genuinely broken workspace: the manifest names a class that does not exist."""
    (tmp_path / "workspace.py").write_text(
        'from aquilia import Module, Workspace\nworkspace = Workspace(name="broken").module(Module("users"))\n',
        encoding="utf-8",
    )
    mod = tmp_path / "modules" / "users"
    mod.mkdir(parents=True)
    (mod / "__init__.py").write_text("", encoding="utf-8")
    (mod / "manifest.py").write_text(
        "from aquilia import AppManifest\n"
        "manifest = AppManifest(\n"
        "    name='users',\n"
        "    version='0.1.0',\n"
        '    controllers=["modules.users.controllers:MissingController"],\n'
        ")\n",
        encoding="utf-8",
    )
    (mod / "controllers.py").write_text("# intentionally empty\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    _clean_modules()
    yield tmp_path
    _clean_modules()


@pytest.fixture
def runner():
    return CliRunner()


class TestDoctorExitCodes:
    """The false-green fix: doctor previously exited 0 no matter what."""

    def test_doctor_fails_on_broken(self, runner, ws_broken):
        result = runner.invoke(cli, ["--no-color", "doctor"])
        assert result.exit_code == 1, result.output

    def test_doctor_passes_on_valid(self, runner, ws_empty):
        result = runner.invoke(cli, ["--no-color", "doctor"])
        assert result.exit_code == 0, result.output

    def test_doctor_names_the_problem(self, runner, ws_broken):
        """Output must identify the actual defect, not just say 'failed'."""
        result = runner.invoke(cli, ["--no-color", "doctor"])
        assert "MissingController" in result.output


class TestValidateExitCodes:
    """validate is the pre-commit gate."""

    def test_validate_fails_on_broken(self, runner, ws_broken):
        result = runner.invoke(cli, ["--no-color", "validate"])
        assert result.exit_code == 1, result.output

    def test_validate_passes_on_valid(self, runner, ws_empty):
        result = runner.invoke(cli, ["--no-color", "validate"])
        assert result.exit_code == 0, result.output


class TestValidateJson:
    """--json must be parseable and carry the exit code for CI."""

    def test_json_parses_on_broken(self, runner, ws_broken):
        result = runner.invoke(cli, ["--no-color", "validate", "--json"])
        payload = json.loads(result.output)
        assert payload["exit_code"] == 1
        assert payload["summary"]["passed"] is False
        assert result.exit_code == 1

    def test_json_parses_on_valid(self, runner, ws_empty):
        result = runner.invoke(cli, ["--no-color", "validate", "--json"])
        payload = json.loads(result.output)
        assert payload["exit_code"] == 0
        assert payload["summary"]["passed"] is True

    def test_json_findings_carry_codes(self, runner, ws_broken):
        """Tests assert on stable codes, not on message prose."""
        payload = json.loads(runner.invoke(cli, ["--no-color", "validate", "--json"]).output)
        codes = {f["code"] for c in payload["checks"] for f in c["findings"]}
        assert "AQ_REF_MISSING_ATTR" in codes


class TestInspectRoutes:
    """Regression guard for the 1-vs-6 route undercount."""

    def test_reports_zero_routes_for_empty_workspace(self, runner, ws_empty):
        result = runner.invoke(cli, ["--no-color", "inspect", "routes"])
        assert result.exit_code == 0

    def test_surfaces_extraction_failure(self, runner, ws_broken):
        """A controller that cannot be read must be reported, not counted as 1."""
        result = runner.invoke(cli, ["--no-color", "inspect", "routes"])
        assert "MissingController" in result.output
        assert "Total routes: 0" in result.output


class TestNoWorkspaceGuard:
    """Commands requiring a workspace must fail cleanly without one."""

    @pytest.mark.parametrize("cmd", [["validate"], ["doctor"], ["inspect", "routes"]])
    def test_fails_without_workspace(self, runner, tmp_path, monkeypatch, cmd):
        """An all-skipped run must not read as success."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["--no-color", *cmd])
        assert result.exit_code != 0, f"{cmd} exited 0 with no workspace:\n{result.output}"
        assert result.output.strip()

    def test_validate_json_without_workspace(self, runner, tmp_path, monkeypatch):
        """--json must stay parseable on the no-workspace path."""
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, ["--no-color", "validate", "--json"])
        payload = json.loads(result.output)
        assert payload["summary"]["passed"] is False
        assert payload["exit_code"] != 0
