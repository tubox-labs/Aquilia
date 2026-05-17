from aquilia.aquilia_mcp.context.indexer import build_index
from aquilia.aquilia_mcp.prompts.catalog import build_prompt_registry


def test_prompt_catalog_contains_required_prompt(mcp_repo):
    registry = build_prompt_registry(build_index(mcp_repo))
    prompts = registry.list_prompts()
    names = {prompt["name"] for prompt in prompts}
    assert "aquilia.build_workspace" in names
    rendered = registry.get_prompt("aquilia.add_module", {"goal": "orders"})
    assert "Anti-Pattern Guards" in rendered["messages"][0]["content"]["text"]
