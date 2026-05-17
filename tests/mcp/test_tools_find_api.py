from aquilia.mcp.context.indexer import build_index
from aquilia.mcp.tools.find_api import find_api


def test_find_api_returns_source_backed_results(mcp_repo):
    result = find_api(build_index(mcp_repo), {"query": "ConfigLoader", "limit": 5})
    assert result["results"]
    assert result["source"]["fingerprint"]
