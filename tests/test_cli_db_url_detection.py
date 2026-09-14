"""CLI database-URL auto-detection (user-reported from the AniWave build).

``aq db status`` connected with ``postgresql://:5432/`` -- a URL
reconstructed from a *commented-out* ``PostgresConfig`` block -- and then
failed with "password authentication failed for user '<os-login>'" against
an unrelated local Postgres. The real configuration
(``DatabaseIntegration(url=Env("DATABASE_URL", default=...))``) was never
read: the static scan neither stripped comments nor knew that shape.
"""

from __future__ import annotations

import textwrap

import pytest

from aquilia.cli.__main__ import _detect_workspace_db_url, _strip_source_comments

WORKSPACE = textwrap.dedent(
    '''\
    from aquilia import Env, Workspace
    from aquilia.integrations import DatabaseIntegration


    def workspace() -> Workspace:
        return (
            Workspace("app")
            # config = PostgresConfig(
            #     engine="postgresql",
            #     host="",
            # )
            .integrate(
                DatabaseIntegration(
                    url=Env("DATABASE_URL", default="postgres://aniwave:aniwave@localhost:5433/aniwave"),
                    pool_size=5,
                )
            )
        )
    '''
)


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("AQ_DATABASE_URL", raising=False)


def test_commented_out_config_is_ignored(tmp_path, monkeypatch):
    (tmp_path / "workspace.py").write_text(WORKSPACE)
    monkeypatch.chdir(tmp_path)

    url = _detect_workspace_db_url()

    assert url == "postgres://aniwave:aniwave@localhost:5433/aniwave"


def test_environment_override_wins(tmp_path, monkeypatch):
    (tmp_path / "workspace.py").write_text(WORKSPACE)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AQ_DATABASE_URL", "postgresql://env:env@localhost:9999/envdb")

    assert _detect_workspace_db_url() == "postgresql://env:env@localhost:9999/envdb"


def test_database_integration_literal_url(tmp_path, monkeypatch):
    (tmp_path / "workspace.py").write_text(
        WORKSPACE.replace(
            'url=Env("DATABASE_URL", default="postgres://aniwave:aniwave@localhost:5433/aniwave")',
            'url="sqlite:///literal.db"',
        )
    )
    monkeypatch.chdir(tmp_path)

    assert _detect_workspace_db_url() == "sqlite:///literal.db"


def test_default_without_workspace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    assert _detect_workspace_db_url() == "sqlite:///db.sqlite3"


def test_strip_source_comments_preserves_strings():
    text = 'url = "postgres://h/db#notacomment"  # real comment\nplain = 1\n'
    stripped = _strip_source_comments(text)

    assert "# real comment" not in stripped
    assert '"postgres://h/db#notacomment"' in stripped
    assert "plain = 1" in stripped
