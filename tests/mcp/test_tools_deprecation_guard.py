from aquilia.aquilia_mcp.context.indexer import build_index
from aquilia.aquilia_mcp.tools.deprecation_guard import deprecation_guard


def test_deprecation_guard_flags_register_methods(mcp_repo):
    result = deprecation_guard(build_index(mcp_repo), {"code": 'Module("x").register_controllers("a:B")'})
    assert result["ok"] is False
    assert result["findings"][0]["pattern"] == "Module.register_controllers"
