import pytest
from pathlib import Path
from click.testing import CliRunner
from aquilia.cli.__main__ import cli


def test_admin_setup_config_rewrite(tmp_path):
    # Create mock workspace.py with a multiline parenthesized import block
    workspace_py = tmp_path / "workspace.py"
    workspace_py.write_text('''"""
Mock workspace
"""
from aquilia import Workspace, Module
from aquilia.integrations import (
    MiddlewareChain,
    DiIntegration,
    RegistryIntegration,
    StaticFilesIntegration,
)

workspace = (
    Workspace(
        name="test_workspace",
        version="1.0.0",
    )
    .starter("starter")
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RegistryIntegration())
    .integrate(StaticFilesIntegration())
)
''', encoding="utf-8")

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        Path("workspace.py").write_text(workspace_py.read_text(encoding="utf-8"), encoding="utf-8")

        result = runner.invoke(cli, ["admin", "setup", "-y"])
        assert result.exit_code == 0

        updated = Path("workspace.py").read_text(encoding="utf-8")

        # Verify imports are not broken inside the parenthesized import block
        assert "from aquilia.integrations import (\n    MiddlewareChain," in updated
        assert "from datetime import timedelta" in updated
        assert "from aquilia.sessions import SessionPolicy" in updated
        assert "from aquilia.integrations import AdminIntegration" in updated

        # Verify DatabaseIntegration is injected (since it was missing)
        assert "DatabaseIntegration" in updated

        # Verify AdminIntegration is injected and has correct indentation (4 spaces)
        assert "    .integrate(AdminIntegration(" in updated
