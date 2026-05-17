"""Gemini CLI installer."""

from __future__ import annotations

from pathlib import Path

from .common import JSONConfigInstaller


class GeminiInstaller(JSONConfigInstaller):
    agent = "gemini"

    def __init__(self, root: Path, config_path: Path | None = None) -> None:
        super().__init__(config_path or (Path.home() / ".gemini" / "settings.json"), root)
