from aquilia.mcp.config import MCPConfig
from aquilia.mcp.context.indexer import build_index
from aquilia.mcp.protocol import parse_request, success_response
from aquilia.mcp.server import AquiliaMCPServer


def test_parse_request_accepts_jsonrpc_object():
    req = parse_request({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
    assert req.id == 1
    assert req.method == "ping"


def test_success_response_shape():
    assert success_response(1, {"ok": True}) == {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}


def test_initialize_lists_capabilities(mcp_repo):
    server = AquiliaMCPServer(MCPConfig(root=mcp_repo), index=build_index(mcp_repo))
    result = server.initialize({"protocolVersion": "test"})
    assert result["capabilities"]["tools"]
    assert result["serverInfo"]["name"] == "aquilia-mcp"
