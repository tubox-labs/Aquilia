"""Run Aquilia MCP over stdio."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import MCPConfig
from .context.indexer import load_or_build_index
from .server import AquiliaMCPServer


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m aquilia.aquilia_mcp")
    parser.add_argument("--workspace", default=".", help="Aquilia repository/workspace root")
    parser.add_argument("--index", default=None, help="Path to persisted MCP index")
    parser.add_argument("--stdio", action="store_true", help="Serve MCP over stdio")
    args = parser.parse_args(argv)
    config = MCPConfig.from_workspace(args.workspace, args.index)
    index = load_or_build_index(config.root, Path(args.index) if args.index else config.index_path)
    server = AquiliaMCPServer(config=config, index=index)
    server.serve_stdio()


if __name__ == "__main__":
    main()
