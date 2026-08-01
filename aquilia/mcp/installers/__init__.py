"""Agent installer adapters for Aquilia MCP."""

from aquilia.mcp.installers.claude import ClaudeInstaller
from aquilia.mcp.installers.codex import CodexInstaller
from aquilia.mcp.installers.gemini import GeminiInstaller

__all__ = ["ClaudeInstaller", "CodexInstaller", "GeminiInstaller"]
