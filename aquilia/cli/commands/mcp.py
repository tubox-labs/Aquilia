"""Aquilia MCP CLI command group."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import click


@click.group("mcp")
def mcp_group() -> None:
    """Run and manage the local Aquilia MCP server."""


def _config(workspace: str | None, index: str | None = None, host: str = "127.0.0.1", port: int = 8765, transport: str = "stdio"):
    from aquilia.mcp.config import MCPConfig

    return MCPConfig.from_workspace(workspace or ".", index, host=host, port=port, transport=transport)


def _load_index(config, *, force: bool = False):
    from aquilia.mcp.context.indexer import load_or_build_index

    return load_or_build_index(config.root, config.index_path, force=force)


def _paths(workspace: str | None):
    from aquilia.mcp.config import MCPConfig
    cfg = MCPConfig.from_workspace(workspace or ".")
    mcp_dir = cfg.root / ".aquilia" / "mcp"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    return mcp_dir / "server.pid", mcp_dir / "server.log", cfg


def _find_mcp_processes() -> list[dict[str, Any]]:
    processes = []
    try:
        output = subprocess.check_output(["ps", "-Ao", "pid,pcpu,pmem,comm,args"], text=True)
        for line in output.splitlines()[1:]:
            parts = line.strip().split(None, 4)
            if len(parts) >= 5:
                pid, cpu, mem, comm, args = parts
                if "python" in comm.lower() or "python" in args.lower():
                    if "aquilia.mcp" in args or "aquilia.cli mcp serve" in args or "mcp serve" in args:
                        processes.append({
                            "pid": int(pid),
                            "cpu": cpu,
                            "mem": mem,
                            "command": args
                        })
    except Exception:
        pass
    return processes


@mcp_group.command("serve")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--transport", type=click.Choice(["stdio", "socket"]), default="stdio", help="Transport to use")
@click.option("--host", default="127.0.0.1", help="TCP host to bind socket server")
@click.option("--port", type=int, default=8765, help="TCP port to bind socket server")
@click.option("--index", "index_path", type=click.Path(), default=None, help="Index file path")
@click.option("--daemon", "--background", "daemon", is_flag=True, help="Run in the background as a daemon")
def serve(workspace: str, transport: str, host: str, port: int, index_path: str | None, daemon: bool) -> None:
    """Serve the Aquilia MCP server."""
    pid_path, log_path, config = _paths(workspace)

    from aquilia.mcp.config import MCPConfig
    config = MCPConfig(
        root=config.root,
        index_path=Path(index_path) if index_path else config.index_path,
        host=host,
        port=port,
        transport=transport
    )

    if daemon:
        if transport == "stdio":
            raise click.UsageError(
                "Daemon mode (--daemon) is not supported for STDIO transport. Use '--transport socket' to run in the background."
            )
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                os.kill(pid, 0)
                click.echo(f"Aquilia MCP server is already running in background (PID: {pid}).")
                return
            except (ProcessLookupError, ValueError):
                pass

        args = [sys.executable, "-m", "aquilia.cli", "mcp", "serve"]
        args.extend(["--workspace", str(config.root)])
        args.extend(["--transport", transport])
        args.extend(["--host", host])
        args.extend(["--port", str(port)])
        if index_path:
            args.extend(["--index", index_path])

        log_file = open(log_path, "a")
        proc = subprocess.Popen(
            args,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True
        )
        pid_path.write_text(str(proc.pid))

        click.echo("========================================================")
        click.echo("AQUILIA MCP SERVER STARTED IN BACKGROUND")
        click.echo("========================================================")
        click.echo(f"PID:        {proc.pid}")
        click.echo(f"Workspace:  {config.root}")
        click.echo(f"Transport:  {transport.upper()}")
        if transport == "socket":
            click.echo(f"Address:    {host}:{port}")
        click.echo(f"Log file:   {log_path}")
        click.echo("========================================================")
        return

    from aquilia.mcp.server import AquiliaMCPServer
    index = _load_index(config)
    server = AquiliaMCPServer(config=config, index=index)
    if transport == "stdio":
        server.serve_stdio()
    elif transport == "socket":
        server.serve_socket()


@mcp_group.command("start")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--transport", type=click.Choice(["stdio", "socket"]), default="socket", help="Transport to use")
@click.option("--host", default="127.0.0.1", help="TCP host to bind socket server")
@click.option("--port", type=int, default=8765, help="TCP port to bind socket server")
@click.option("--index", "index_path", type=click.Path(), default=None, help="Index file path")
@click.pass_context
def start(ctx, workspace: str, transport: str, host: str, port: int, index_path: str | None) -> None:
    """Start the Aquilia MCP server in the background."""
    ctx.invoke(serve, workspace=workspace, transport=transport, host=host, port=port, index_path=index_path, daemon=True)


@mcp_group.command("stop")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--force", is_flag=True, help="Force kill the background server")
def stop(workspace: str, force: bool) -> None:
    """Stop the background Aquilia MCP server."""
    pid_path, _, _ = _paths(workspace)
    if not pid_path.exists():
        click.echo("No background MCP server is currently registered.")
        return

    try:
        pid = int(pid_path.read_text().strip())
    except ValueError:
        click.echo("Invalid PID file. Cleaning up.")
        pid_path.unlink(missing_ok=True)
        return

    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        click.echo("Background process is not running. Cleaning up stale PID file.")
        pid_path.unlink(missing_ok=True)
        return

    click.echo(f"Stopping background MCP server (PID: {pid})...")
    sig = signal.SIGKILL if force else signal.SIGTERM
    try:
        os.kill(pid, sig)
        for _ in range(50):
            time.sleep(0.1)
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
        else:
            if not force:
                click.echo("Server did not stop. Attempting force kill...")
                os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass

    pid_path.unlink(missing_ok=True)
    click.echo("Server stopped successfully.")


@mcp_group.command("restart")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--transport", type=click.Choice(["stdio", "socket"]), default="socket", help="Transport to use")
@click.option("--host", default="127.0.0.1", help="TCP host to bind socket server")
@click.option("--port", type=int, default=8765, help="TCP port to bind socket server")
@click.option("--index", "index_path", type=click.Path(), default=None, help="Index file path")
@click.pass_context
def restart(ctx, workspace: str, transport: str, host: str, port: int, index_path: str | None) -> None:
    """Restart the background Aquilia MCP server."""
    ctx.invoke(stop, workspace=workspace)
    ctx.invoke(start, workspace=workspace, transport=transport, host=host, port=port, index_path=index_path)


@mcp_group.command("status")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
def status(workspace: str) -> None:
    """Check the status of the background Aquilia MCP server."""
    pid_path, log_path, config = _paths(workspace)

    pid = None
    is_running = False
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text().strip())
            os.kill(pid, 0)
            is_running = True
        except (ProcessLookupError, ValueError):
            pass

    click.echo("========================================================")
    click.echo("AQUILIA MCP SERVER STATUS")
    click.echo("========================================================")
    click.echo(f"Workspace:    {config.root}")
    if is_running:
        click.echo(f"Status:       Active (Running)")
        click.echo(f"PID:          {pid}")
        processes = _find_mcp_processes()
        mcp_proc = next((p for p in processes if p["pid"] == pid), None)
        if mcp_proc:
            click.echo(f"CPU Usage:    {mcp_proc['cpu']}%")
            click.echo(f"Memory Usage: {mcp_proc['mem']}%")
    else:
        click.echo(f"Status:       Inactive (Stopped)")

    try:
        from aquilia.mcp.context.indexer import load_index
        index = load_index(config.index_path)
        click.echo(f"Indexed:      {len(index.sources)} source files")
        click.echo(f"Fingerprint:  {index.fingerprint}")
    except Exception:
        click.echo("Indexed:      No index built yet.")

    click.echo(f"Log path:     {log_path}")
    click.echo("========================================================")


@mcp_group.command("logs")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--lines", "-n", type=int, default=20, help="Number of log lines to show")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
def logs(workspace: str, lines: int, follow: bool) -> None:
    """Display logs of the background Aquilia MCP server."""
    _, log_path, _ = _paths(workspace)
    if not log_path.exists():
        click.echo("No log file found.")
        return

    if not follow:
        try:
            with open(log_path, "r") as f:
                content = f.readlines()
                for line in content[-lines:]:
                    sys.stdout.write(line)
        except Exception as e:
            click.echo(f"Error reading logs: {e}")
        return

    try:
        with open(log_path, "r") as f:
            f.seek(0, 2)
            click.echo("--- Streaming logs (Press Ctrl+C to stop) ---")
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                sys.stdout.write(line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        click.echo("\n--- Stopped streaming logs ---")


@mcp_group.command("inspect")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--kill-pid", type=int, help="Kill a running MCP server by its PID")
def inspect(workspace: str, kill_pid: int | None) -> None:
    """Inspect all running MCP processes and details."""
    if kill_pid is not None:
        try:
            os.kill(kill_pid, signal.SIGTERM)
            click.echo(f"Sent SIGTERM to process {kill_pid}.")
            pid_path, _, _ = _paths(workspace)
            if pid_path.exists():
                try:
                    stored_pid = int(pid_path.read_text().strip())
                    if stored_pid == kill_pid:
                        pid_path.unlink()
                except ValueError:
                    pass
        except ProcessLookupError:
            click.echo(f"Process {kill_pid} not found.")
        except PermissionError:
            click.echo(f"No permission to kill process {kill_pid}.")
        return

    pid_path, _, config = _paths(workspace)
    bg_pid = None
    if pid_path.exists():
        try:
            bg_pid = int(pid_path.read_text().strip())
        except ValueError:
            pass

    click.echo("========================================================")
    click.echo("RUNNING AQUILIA MCP PROCESSES")
    click.echo("========================================================")

    processes = _find_mcp_processes()
    if not processes:
        click.echo("No running MCP processes detected.")
    else:
        for p in processes:
            role = "Background Daemon" if p["pid"] == bg_pid else "Unknown / Subprocess"
            click.echo(f"PID:      {p['pid']} ({role})")
            click.echo(f"CPU:      {p['cpu']}%")
            click.echo(f"Memory:   {p['mem']}%")
            click.echo(f"Command:  {p['command']}")
            click.echo("--------------------------------------------------------")

    click.echo("\n========================================================")
    click.echo("SERVER SPECIFICATIONS & ACTIVE REGISTRY")
    click.echo("========================================================")
    click.echo(f"Workspace root:   {config.root}")
    click.echo(f"Index storage:    {config.index_path}")

    try:
        from aquilia.mcp.context.indexer import load_index
        index = load_index(config.index_path)
        from aquilia.mcp.server import AquiliaMCPServer
        server = AquiliaMCPServer(config=config, index=index)

        click.echo(f"Schema Version:   {index.metadata.get('schema_version', 1)}")
        click.echo(f"Built At:         {index.built_at}")

        click.echo("\nActive Tools:")
        for tool in server.list_tools()["tools"]:
            click.echo(f"  - {tool['name']}: {tool['description'][:60]}...")

        click.echo("\nActive Prompts:")
        for prompt in server.list_prompts()["prompts"]:
            click.echo(f"  - {prompt['name']}: {prompt['description'][:60]}...")

        click.echo("\nActive Resources:")
        for resource in server.list_resources()["resources"][:5]:
            click.echo(f"  - {resource['uri']} ({resource['mimeType']})")
        if len(server.list_resources()["resources"]) > 5:
            click.echo(f"  ... and {len(server.list_resources()['resources']) - 5} more resources.")
    except Exception as e:
        click.echo(f"Could not load active registry: {e}")
        click.echo("Please run 'aq mcp build-index' to compile the registry first.")

    click.echo("========================================================")


@mcp_group.command("build-index")
@click.option("--force", is_flag=True, help="Rebuild even if an index exists")
@click.option("--workspace", type=click.Path(), default=".", help="Repository/workspace root")
@click.option("--index", "index_path", type=click.Path(), default=None, help="Index file path")
def build_index_cmd(force: bool, workspace: str, index_path: str | None) -> None:
    """Build the persistent local source index."""
    config = _config(workspace, index_path)
    index = _load_index(config, force=force)
    click.echo(
        json.dumps({"path": str(config.index_path), "fingerprint": index.fingerprint, "sources": len(index.sources)})
    )


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
