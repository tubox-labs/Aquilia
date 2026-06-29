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


def test_cli_mcp_subdirectory_resolution(mcp_repo):
    sub = mcp_repo / "aquilia" / "cli"
    result = CliRunner().invoke(cli, ["mcp", "list-tools", "--workspace", str(sub)])
    assert result.exit_code == 0, result.output
    assert "find_api" in result.output


def test_cli_mcp_daemon_lifecycle(mcp_repo):
    runner = CliRunner()
    
    # Start background daemon on port 28765
    result = runner.invoke(cli, ["mcp", "start", "--workspace", str(mcp_repo), "--port", "28765"])
    assert result.exit_code == 0, result.output
    assert "STARTED IN BACKGROUND" in result.output
    
    # Check status
    result = runner.invoke(cli, ["mcp", "status", "--workspace", str(mcp_repo)])
    assert result.exit_code == 0, result.output
    assert "Active (Running)" in result.output
    
    # Inspect
    result = runner.invoke(cli, ["mcp", "inspect", "--workspace", str(mcp_repo)])
    assert result.exit_code == 0, result.output
    assert "RUNNING AQUILIA MCP PROCESSES" in result.output
    
    # Stop background daemon
    result = runner.invoke(cli, ["mcp", "stop", "--workspace", str(mcp_repo)])
    assert result.exit_code == 0, result.output
    assert "stopped successfully" in result.output

