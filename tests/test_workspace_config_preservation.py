"""
Workspace-configuration preservation -- F-04/F-05 of the AniWave audit.

F-04 -- ``aq`` commands rewrite ``workspace.py`` to sync module blocks. The
        block-preservation regex required ``.module(Module("name"`` on a
        single line, so a hand-written multi-line block was stripped and
        regenerated with default ``/<name>`` prefixes and no ``depends_on``
        -- silently destroying user configuration. Blocks for modules the
        discovery pass did not report were dropped entirely.
F-05 -- ``aq add module --route-prefix`` was accepted and printed, then
        ignored: the generated module block always carried ``/<name>``.
"""

from __future__ import annotations

import ast
import textwrap

import pytest

from aquilia.cli.generators.workspace import WorkspaceGenerator

WORKSPACE = textwrap.dedent(
    '''\
    from aquilia import Module, Workspace


    def workspace() -> Workspace:
        return (
            Workspace("app", version="1.0.0")
            .module(
                Module(
                    "core",
                    version="1.0.0",
                    description="Core module",
                )
                .route_prefix("/api/core")
                .depends_on("auth")
            )
            .module(
                Module("billing", version="0.1.0")
                .route_prefix("/api/billing")
                # a comment inside the block
                .depends_on("core")
            )
            .module(Module("legacy", version="0.2.0").route_prefix("/old"))
            .integrate(Module("never", version="0.0.1"))
        )
    '''
)


@pytest.fixture
def workspace_file(tmp_path):
    path = tmp_path / "workspace.py"
    path.write_text(WORKSPACE)
    return path


def test_multi_line_module_blocks_are_preserved_verbatim(tmp_path, workspace_file):
    generator = WorkspaceGenerator(name="app", path=tmp_path)
    discovered = {
        "core": {"version": "1.0.0", "description": "Core module"},
        "billing": {"version": "0.1.0"},
    }

    generator.update_workspace_config(workspace_file, discovered)
    content = workspace_file.read_text(encoding="utf-8")

    assert '.route_prefix("/api/core")' in content
    assert '.route_prefix("/api/billing")' in content
    assert '.depends_on("auth")' in content
    assert '.depends_on("core")' in content
    assert "a comment inside the block" in content
    ast.parse(content)


def test_undiscovered_module_blocks_are_not_dropped(tmp_path, workspace_file):
    """A module discovery did not report is still user configuration."""
    generator = WorkspaceGenerator(name="app", path=tmp_path)

    generator.update_workspace_config(workspace_file, {"core": {"version": "1.0.0"}})
    content = workspace_file.read_text(encoding="utf-8")

    assert '"legacy"' in content
    assert '.route_prefix("/old")' in content
    assert '"billing"' in content
    ast.parse(content)


def test_rewrite_is_stable_across_repeated_runs(tmp_path, workspace_file):
    generator = WorkspaceGenerator(name="app", path=tmp_path)
    discovered = {"core": {"version": "1.0.0"}, "billing": {"version": "0.1.0"}}

    generator.update_workspace_config(workspace_file, discovered)
    first = workspace_file.read_text(encoding="utf-8")
    generator.update_workspace_config(workspace_file, discovered)
    second = workspace_file.read_text(encoding="utf-8")

    assert '.route_prefix("/api/billing")' in second
    assert '"legacy"' in second
    assert first == second


def test_unreadable_module_blocks_are_emitted_verbatim(tmp_path):
    """A block whose Module(...) name is not a literal must not be deleted."""
    workspace = textwrap.dedent(
        '''\
        from aquilia import Module, Workspace

        def workspace() -> Workspace:
            return (
                Workspace("app")
                .module(Module(MY_MODULE_VAR))
            )
        '''
    )
    path = tmp_path / "workspace.py"
    path.write_text(workspace)

    generator = WorkspaceGenerator(name="app", path=tmp_path)
    generator.update_workspace_config(path, {})
    content = path.read_text(encoding="utf-8")

    assert "MY_MODULE_VAR" in content
    ast.parse(content)


def test_route_prefix_override_reaches_generated_block(tmp_path):
    """F-05: the explicit --route-prefix value lands in the module block."""
    workspace = textwrap.dedent(
        """\
        from aquilia import Module, Workspace

        def workspace() -> Workspace:
            return Workspace("app")
        """
    )
    path = tmp_path / "workspace.py"
    path.write_text(workspace)

    generator = WorkspaceGenerator(name="app", path=tmp_path)
    generator.update_workspace_config(
        path,
        {"fresh": {"version": "1.0.0"}},
        overrides={"fresh": {"route_prefix": "/api/fresh"}},
    )
    content = path.read_text(encoding="utf-8")

    assert '.route_prefix("/api/fresh")' in content
    ast.parse(content)


def test_new_module_without_override_gets_default_prefix(tmp_path):
    workspace = textwrap.dedent(
        """\
        from aquilia import Module, Workspace

        def workspace() -> Workspace:
            return Workspace("app")
        """
    )
    path = tmp_path / "workspace.py"
    path.write_text(workspace)

    generator = WorkspaceGenerator(name="app", path=tmp_path)
    generator.update_workspace_config(path, {"fresh": {"version": "1.0.0"}})
    content = path.read_text(encoding="utf-8")

    assert '.route_prefix("/fresh")' in content
