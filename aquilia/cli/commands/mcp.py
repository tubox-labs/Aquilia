"""Aquilia MCP CLI command group."""

from __future__ import annotations

import json
from pathlib import Path

import click


@click.group("mcp")
def mcp_group() -> None:
    """Run and manage the local Aquilia MCP server."""


def _config(workspace: str | None, index: str | None = None):
    from aquilia.mcp.config import MCPConfig

    return MCPConfig.from_workspace(workspace or ".", index)


def _load_index(config, *, force: bool = False):
    from aquilia.mcp.context.indexer import load_or_build_index

    return load_or_build_index(config.root, config.index_path, force=force)


@mcp_group.command("serve")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--stdio", is_flag=True, default=True, help="Serve over stdio")
@click.option("--index", "index_path", type=click.Path(), default=None, help="Index file path")
def serve(workspace: str, stdio: bool, index_path: str | None) -> None:
    """Serve the Aquilia MCP server."""
    from aquilia.mcp.server import AquiliaMCPServer

    config = _config(workspace, index_path)
    index = _load_index(config)
    server = AquiliaMCPServer(config=config, index=index)
    if stdio:
        server.serve_stdio()


@mcp_group.command("build-index")
@click.option("--force", is_flag=True, help="Rebuild even if an index exists")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--index", "index_path", type=click.Path(), default=None, help="Index file path")
def build_index_cmd(force: bool, workspace: str, index_path: str | None) -> None:
    """Build the persistent local source index."""
    config = _config(workspace, index_path)
    index = _load_index(config, force=force)
    click.echo(json.dumps({"path": str(config.index_path), "fingerprint": index.fingerprint, "sources": len(index.sources)}))


@mcp_group.command("doctor")
@click.option("--json", "as_json", is_flag=True, help="Output JSON")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
def doctor(as_json: bool, workspace: str) -> None:
    """Check MCP server health."""
    from aquilia.mcp.server import AquiliaMCPServer

    config = _config(workspace)
    index = _load_index(config)
    server = AquiliaMCPServer(config=config, index=index)
    report = {
        "ok": True,
        "root": str(config.root),
        "index": str(config.index_path),
        "fingerprint": index.fingerprint,
        "sources": len(index.sources),
        "tools": len(server.list_tools()["tools"]),
        "prompts": len(server.list_prompts()["prompts"]),
    }
    if as_json:
        click.echo(json.dumps(report, indent=2, sort_keys=True))
    else:
        click.echo(f"Aquilia MCP ok: {report['tools']} tools, {report['prompts']} prompts, {report['sources']} sources")


@mcp_group.command("install")
@click.option("--agent", type=click.Choice(["claude", "codex", "gemini"]), required=True)
@click.option("--dry-run", is_flag=True, help="Preview config changes without writing")
@click.option("--verify", is_flag=True, help="Verify server tool list after patching")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
def install(agent: str, dry_run: bool, verify: bool, workspace: str) -> None:
    """Install Aquilia MCP into a local agent config."""
    from aquilia.mcp.installers import ClaudeInstaller, CodexInstaller, GeminiInstaller

    root = Path(workspace).resolve()
    installers = {
        "claude": ClaudeInstaller,
        "codex": CodexInstaller,
        "gemini": GeminiInstaller,
    }
    result = installers[agent](root).install(dry_run=dry_run, verify=verify)
    click.echo(json.dumps(result.to_dict(), indent=2, sort_keys=True))


@mcp_group.command("list-tools")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
def list_tools(workspace: str) -> None:
    """List available MCP tools."""
    from aquilia.mcp.server import AquiliaMCPServer

    config = _config(workspace)
    server = AquiliaMCPServer(config=config, index=_load_index(config))
    click.echo(json.dumps(server.list_tools(), indent=2, sort_keys=True))


@mcp_group.command("list-prompts")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
def list_prompts(workspace: str) -> None:
    """List available MCP prompts."""
    from aquilia.mcp.server import AquiliaMCPServer

    config = _config(workspace)
    server = AquiliaMCPServer(config=config, index=_load_index(config))
    click.echo(json.dumps(server.list_prompts(), indent=2, sort_keys=True))


@mcp_group.command("query")
@click.argument("query")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
def query(query: str, workspace: str) -> None:
    """Search the local Aquilia MCP index."""
    from aquilia.mcp.server import AquiliaMCPServer

    config = _config(workspace)
    server = AquiliaMCPServer(config=config, index=_load_index(config))
    result = server.call_tool("find_api", {"query": query, "limit": 8})
    click.echo(json.dumps(result["structuredContent"], indent=2, sort_keys=True))
