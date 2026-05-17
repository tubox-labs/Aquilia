from aquilia.aquilia_mcp.config import MCPConfig
from aquilia.aquilia_mcp.context.indexer import build_index
from aquilia.aquilia_mcp.faults import MCPProtocolFault
from aquilia.aquilia_mcp.protocol import fault_to_error, parse_request, success_response
from aquilia.aquilia_mcp.server import AquiliaMCPServer


def test_parse_request_accepts_jsonrpc_object():
    req = parse_request({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})
    assert req.id == 1
    assert req.method == "ping"


def test_success_response_shape():
    assert success_response(1, {"ok": True}) == {"jsonrpc": "2.0", "id": 1, "result": {"ok": True}}


def test_method_not_found_maps_to_jsonrpc_code():
    code, message, data = fault_to_error(MCPProtocolFault("missing", code="MCP_METHOD_NOT_FOUND"))
    assert code == -32601
    assert data["fault_code"] == "MCP_METHOD_NOT_FOUND"


def test_initialize_lists_capabilities(mcp_repo):
    server = AquiliaMCPServer(MCPConfig(root=mcp_repo), index=build_index(mcp_repo))
    result = server.initialize({"protocolVersion": "test"})
    assert result["capabilities"]["tools"]
    assert result["serverInfo"]["name"] == "aquilia-mcp"
