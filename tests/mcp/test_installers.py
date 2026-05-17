from aquilia.aquilia_mcp.installers.codex import CodexInstaller


def test_installer_dry_run_is_idempotent(mcp_repo, tmp_path):
    path = tmp_path / "codex.json"
    installer = CodexInstaller(mcp_repo, config_path=path)
    first = installer.install(dry_run=True)
    second = installer.install(dry_run=True)
    assert first.changed is True
    assert second.config == first.config
    assert not path.exists()


def test_installer_verify_returns_tools(mcp_repo, tmp_path):
    installer = CodexInstaller(mcp_repo, config_path=tmp_path / "codex.json")
    result = installer.install(dry_run=True, verify=True)
    assert result.verification["reachable"] is True
    assert result.verification["tool_count"] > 0


def test_installer_uses_canonical_package(mcp_repo, tmp_path):
    installer = CodexInstaller(mcp_repo, config_path=tmp_path / "codex.json")
    result = installer.install(dry_run=True)
    assert "aquilia.aquilia_mcp" in result.config["mcp_servers"]["aquilia"]["args"]
