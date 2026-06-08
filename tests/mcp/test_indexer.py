from aquilia.mcp.context.indexer import build_index, load_index, load_or_build_index, save_index


def test_index_build_save_load_roundtrip(mcp_repo, tmp_path):
    index = build_index(mcp_repo)
    assert index.sources
    assert index.fingerprint
    path = tmp_path / "index.json"
    save_index(index, path)
    loaded = load_index(path)
    assert loaded.fingerprint == index.fingerprint
    assert loaded.sources[0].path == index.sources[0].path


def test_index_reuses_unchanged_tree(mcp_repo, tmp_path):
    path = tmp_path / "index.json"
    first = load_or_build_index(mcp_repo, path)
    second = load_or_build_index(mcp_repo, path)
    assert second.fingerprint == first.fingerprint
    assert second.metadata["tree_fingerprint"] == first.metadata["tree_fingerprint"]
