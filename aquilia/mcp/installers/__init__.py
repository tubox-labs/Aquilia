"""Agent installer adapters for Aquilia MCP."""

from .claude import ClaudeInstaller
from .codex import CodexInstaller
from .gemini import GeminiInstaller

__all__ = ["ClaudeInstaller", "CodexInstaller", "GeminiInstaller"]
