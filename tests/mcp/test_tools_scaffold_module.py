from aquilia.mcp.context.indexer import build_index
from aquilia.mcp.tools.scaffold_module import scaffold_module


def test_scaffold_module_uses_workspace_route_prefix(mcp_repo):
    result = scaffold_module(build_index(mcp_repo), {"name": "orders", "route_prefix": "/orders", "minimal": True})
    assert any(item["path"] == "workspace.py" for item in result["files"])
    assert "Module.register_controllers" in result["anti_patterns"][0]
