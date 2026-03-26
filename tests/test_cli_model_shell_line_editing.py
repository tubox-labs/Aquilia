from __future__ import annotations

import sys
import types

from aquilia.cli.commands import model_cmds


class _FakeReadline:
    def __init__(self) -> None:
        self.bindings: list[str] = []
        self.completer = None

    def parse_and_bind(self, binding: str) -> None:
        self.bindings.append(binding)

    def set_completer(self, completer) -> None:
        self.completer = completer


def test_configure_shell_line_editor_binds_backspace_delete(monkeypatch):
    fake_readline = _FakeReadline()

    class _Completer:
        def __init__(self, namespace):
            self.namespace = namespace

        def complete(self, text, state):
            return None

    fake_rlcompleter = types.SimpleNamespace(Completer=_Completer)

    monkeypatch.setitem(sys.modules, "readline", fake_readline)
    monkeypatch.setitem(sys.modules, "rlcompleter", fake_rlcompleter)

    ok = model_cmds._configure_shell_line_editor({"User": object})

    assert ok is True
    assert fake_readline.completer is not None
    assert "tab: complete" in fake_readline.bindings
    assert '"\\C-?": backward-delete-char' in fake_readline.bindings
    assert '"\\C-h": backward-delete-char' in fake_readline.bindings
    assert '"\\e[3~": delete-char' in fake_readline.bindings


def test_configure_shell_line_editor_survives_partial_binding_failures(monkeypatch):
    class _FlakyReadline(_FakeReadline):
        def parse_and_bind(self, binding: str) -> None:
            if binding == '"\\e[3~": delete-char':
                raise RuntimeError("unsupported key sequence")
            super().parse_and_bind(binding)

    fake_readline = _FlakyReadline()

    class _ExplodingCompleter:
        def __init__(self, namespace):
            raise RuntimeError("completer unavailable")

    fake_rlcompleter = types.SimpleNamespace(Completer=_ExplodingCompleter)

    monkeypatch.setitem(sys.modules, "readline", fake_readline)
    monkeypatch.setitem(sys.modules, "rlcompleter", fake_rlcompleter)

    ok = model_cmds._configure_shell_line_editor({"Model": object})

    assert ok is True
    assert '"\\C-?": backward-delete-char' in fake_readline.bindings
    assert '"\\C-h": backward-delete-char' in fake_readline.bindings


def test_configure_shell_line_editor_returns_false_without_readline(monkeypatch):
    monkeypatch.delitem(sys.modules, "readline", raising=False)

    original_import = __import__

    def _fake_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "readline":
            raise ImportError("no readline")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr("builtins.__import__", _fake_import)

    ok = model_cmds._configure_shell_line_editor({})

    assert ok is False


def test_cmd_shell_invokes_line_editor_before_interact(monkeypatch):
    events: list[str] = []

    class _FakeDB:
        def __init__(self, database_url: str) -> None:
            self.database_url = database_url

        async def connect(self) -> None:
            events.append("db-connect")

        async def disconnect(self) -> None:
            events.append("db-disconnect")

    fake_db_module = types.SimpleNamespace(
        AquiliaDatabase=_FakeDB,
        set_database=lambda db: events.append("set-database"),
    )

    monkeypatch.setitem(sys.modules, "aquilia.db", fake_db_module)
    monkeypatch.setattr(model_cmds, "_discover_models", lambda verbose=False: [])
    monkeypatch.setattr(model_cmds, "_configure_shell_line_editor", lambda namespace: events.append("line-editor"))

    fake_code_module = types.SimpleNamespace(interact=lambda **kwargs: events.append("interact"))
    monkeypatch.setitem(sys.modules, "code", fake_code_module)

    model_cmds.cmd_shell(database_url="sqlite:///test.db", verbose=False)

    assert "line-editor" in events
    assert "interact" in events
    assert events.index("line-editor") < events.index("interact")
    assert "db-connect" in events
    assert "db-disconnect" in events
