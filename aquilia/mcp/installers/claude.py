"""Claude Desktop installer."""

from __future__ import annotations

import sys
from pathlib import Path

from .common import JSONConfigInstaller


def default_claude_config_path() -> Path:
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if sys.platform == "win32":
        return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    return home / ".config" / "Claude" / "claude_desktop_config.json"


class ClaudeInstaller(JSONConfigInstaller):
    agent = "claude"

    def __init__(self, root: Path, config_path: Path | None = None) -> None:
        super().__init__(config_path or default_claude_config_path(), root)
