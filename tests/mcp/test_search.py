from aquilia.aquilia_mcp.context.indexer import build_index
from aquilia.aquilia_mcp.context.search import search_index


def test_search_ranks_symbol_and_path_matches(mcp_repo):
    index = build_index(mcp_repo)
    results = search_index(index, "AquiliaRuntime", limit=3)
    assert results
    assert results[0].path.startswith("aquilia/")
