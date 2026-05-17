from click.testing import CliRunner

from aquilia.cli.__main__ import cli


def test_cli_mcp_list_tools_runs(mcp_repo):
    result = CliRunner().invoke(cli, ["mcp", "list-tools", "--workspace", str(mcp_repo)])
    assert result.exit_code == 0, result.output
    assert "find_api" in result.output


def test_cli_mcp_query_runs(mcp_repo):
    result = CliRunner().invoke(cli, ["mcp", "query", "runtime", "--workspace", str(mcp_repo)])
    assert result.exit_code == 0, result.output
    assert "results" in result.output
