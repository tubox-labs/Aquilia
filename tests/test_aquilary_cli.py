"""
Tests for the Click-based aquilary CLI integration.
"""

from click.testing import CliRunner
from aquilia.cli.__main__ import cli


def test_aquilary_cli_help():
    """Verify that 'aq aquilary --help' command works and displays help text."""
    runner = CliRunner()
    result = runner.invoke(cli, ["aquilary", "--help"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Manifest-driven App Registry management commands." in result.output
    assert "freeze" in result.output
    assert "graph" in result.output
    assert "inspect" in result.output
    assert "run" in result.output
    assert "validate" in result.output


def test_aquilary_subcommand_helps():
    """Verify that help is available for each of the aquilary subcommands."""
    runner = CliRunner()
    subcommands = ["validate", "inspect", "freeze", "graph", "run"]
    for cmd in subcommands:
        result = runner.invoke(cli, ["aquilary", cmd, "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "Options" in result.output
