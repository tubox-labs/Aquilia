"""Aquilia MCP server package.

The implementation is local, read-only by default, and backed by the
repository source tree rather than an external retrieval service.
"""

from .config import MCPConfig
from .context.indexer import build_index, load_index, save_index
from .server import AquiliaMCPServer
from .version import __version__

__all__ = [
    "AquiliaMCPServer",
    "MCPConfig",
    "__version__",
    "build_index",
    "load_index",
    "save_index",
]
