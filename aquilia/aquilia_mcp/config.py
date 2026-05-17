"""Configuration for the local Aquilia MCP server."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aquilia.faults.domains import ConfigInvalidFault


@dataclass(frozen=True)
class MCPConfig:
    """Immutable MCP server configuration."""

    root: Path
    index_path: Path | None = None
    max_results: int = 12
    max_read_bytes: int = 256_000
    max_request_bytes: int = 1_000_000
    read_only: bool = True
    server_name: str = "aquilia-mcp"

    def __post_init__(self) -> None:
        root = self.root.expanduser().resolve()
        if "\x00" in str(root):
            raise ConfigInvalidFault(key="mcp.root", reason="Path contains a null byte")
        if not root.exists():
            raise ConfigInvalidFault(key="mcp.root", reason=f"Path does not exist: {root}")
        if not root.is_dir():
            raise ConfigInvalidFault(key="mcp.root", reason=f"Path is not a directory: {root}")
        object.__setattr__(self, "root", root)

        if self.index_path is None:
            object.__setattr__(self, "index_path", root / ".aquilia" / "mcp" / "index.json")
        else:
            object.__setattr__(self, "index_path", self.index_path.expanduser().resolve())

        if self.max_results <= 0 or self.max_results > 100:
            raise ConfigInvalidFault(key="mcp.max_results", reason="Must be between 1 and 100")
        if self.max_read_bytes < 1024:
            raise ConfigInvalidFault(key="mcp.max_read_bytes", reason="Must be at least 1024 bytes")
        if self.max_request_bytes < 1024:
            raise ConfigInvalidFault(key="mcp.max_request_bytes", reason="Must be at least 1024 bytes")

    @classmethod
    def from_workspace(cls, workspace: str | Path | None = None, index: str | Path | None = None) -> MCPConfig:
        root = Path(workspace) if workspace is not None else Path.cwd()
        index_path = Path(index) if index is not None else None
        return cls(root=root, index_path=index_path)
