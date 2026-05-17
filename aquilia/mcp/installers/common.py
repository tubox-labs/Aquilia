"""Shared installer logic for local agent MCP configuration."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..config import MCPConfig
from ..server import AquiliaMCPServer


@dataclass(frozen=True)
class InstallResult:
    agent: str
    path: str
    changed: bool
    dry_run: bool
    backup_path: str | None = None
    verification: dict[str, Any] | None = None
    config: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent": self.agent,
            "path": self.path,
            "changed": self.changed,
            "dry_run": self.dry_run,
            "backup_path": self.backup_path,
            "verification": self.verification,
            "config": self.config,
        }


class JSONConfigInstaller:
    agent = "agent"

    def __init__(self, config_path: Path, root: Path) -> None:
        self.config_path = config_path.expanduser()
        self.root = root.expanduser().resolve()

    def server_command(self) -> dict[str, Any]:
        return {
            "command": "python",
            "args": ["-m", "aquilia.mcp", "--stdio", "--workspace", str(self.root)],
        }

    def load(self) -> dict[str, Any]:
        if not self.config_path.exists():
            return {}
        return json.loads(self.config_path.read_text(encoding="utf-8"))

    def patch(self, data: dict[str, Any]) -> dict[str, Any]:
        patched = dict(data)
        servers = dict(patched.get("mcpServers") or patched.get("mcp_servers") or {})
        servers["aquilia"] = self.server_command()
        patched["mcpServers"] = servers
        return patched

    def install(self, *, dry_run: bool = False, verify: bool = False) -> InstallResult:
        before = self.load()
        after = self.patch(before)
        changed = before != after
        backup_path = None
        if changed and not dry_run:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            if self.config_path.exists():
                stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                backup = self.config_path.with_suffix(self.config_path.suffix + f".bak.{stamp}")
                shutil.copy2(self.config_path, backup)
                backup_path = str(backup)
            self.config_path.write_text(json.dumps(after, indent=2, sort_keys=True), encoding="utf-8")
        verification = self.verify() if verify else None
        return InstallResult(
            agent=self.agent,
            path=str(self.config_path),
            changed=changed,
            dry_run=dry_run,
            backup_path=backup_path,
            verification=verification,
            config=after if dry_run else None,
        )

    def verify(self) -> dict[str, Any]:
        server = AquiliaMCPServer(MCPConfig(root=self.root))
        tools = server.list_tools()["tools"]
        return {"reachable": bool(tools), "tool_count": len(tools)}
