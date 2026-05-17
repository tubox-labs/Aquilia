"""Codex installer."""

from __future__ import annotations

from pathlib import Path

from .common import JSONConfigInstaller


class CodexInstaller(JSONConfigInstaller):
    agent = "codex"

    def __init__(self, root: Path, config_path: Path | None = None) -> None:
        super().__init__(config_path or (Path.home() / ".codex" / "config.json"), root)

    def patch(self, data: dict) -> dict:
        patched = dict(data)
        servers = dict(patched.get("mcpServers") or patched.get("mcp_servers") or {})
        servers["aquilia"] = self.server_command()
        patched["mcp_servers"] = servers
        return patched
