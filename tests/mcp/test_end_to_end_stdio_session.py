import json
from io import StringIO

from aquilia.aquilia_mcp.config import MCPConfig
from aquilia.aquilia_mcp.context.indexer import build_index
from aquilia.aquilia_mcp.server import AquiliaMCPServer
from aquilia.aquilia_mcp.transport.stdio import StdioTransport


def test_end_to_end_stdio_initialize_and_tools_call(mcp_repo):
    server = AquiliaMCPServer(MCPConfig(root=mcp_repo), index=build_index(mcp_repo))
    stdout = StringIO()
    transport = StdioTransport(server, stdout=stdout)
    init = transport.handle_line(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}))
    assert init["result"]["serverInfo"]["name"] == "aquilia-mcp"
    call = transport.handle_line(
        json.dumps(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": "find_api", "arguments": {"query": "runtime"}},
            }
        )
    )
    assert call["result"]["structuredContent"]["results"]
