"""Auto-port resolution for `aq run` / `aq serve`.

Port recovery moved from the CLI into ``aquilia.devplatform.portmanager``.
``run._resolve_port`` is now a thin wrapper over ``PortManager`` — these tests
cover the CLI-facing behaviour; deeper cases live in
``tests/devplatform/test_port_manager.py``.
"""

import socket
from unittest.mock import patch

from aquilia.cli.commands.run import _resolve_port


def test_resolve_port_returns_directly_when_free():
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_sock.bind(("127.0.0.1", 0))
    port = temp_sock.getsockname()[1]
    temp_sock.close()

    with patch("click.secho") as mock_secho:
        resolved_port = _resolve_port("127.0.0.1", port)
        assert resolved_port == port
        mock_secho.assert_not_called()


def test_resolve_port_switches_when_live_listener():
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_sock.bind(("127.0.0.1", 0))
    port = temp_sock.getsockname()[1]
    temp_sock.close()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", port))
    sock.listen(1)
    try:
        with patch("click.secho") as mock_secho:
            resolved_port = _resolve_port("127.0.0.1", port)
            assert resolved_port != port
            mock_secho.assert_called_once()
            assert "actively in use" in mock_secho.call_args[0][0]
    finally:
        sock.close()
