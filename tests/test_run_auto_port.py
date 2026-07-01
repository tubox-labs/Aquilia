import socket
from unittest.mock import patch

from aquilia.cli.commands.run import _find_available_port


def test_find_available_port_returns_directly_when_free():
    # Find an available port dynamically
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_sock.bind(("127.0.0.1", 0))
    port = temp_sock.getsockname()[1]
    temp_sock.close()

    with patch("click.secho") as mock_secho:
        resolved_port = _find_available_port("127.0.0.1", port)
        assert resolved_port == port
        mock_secho.assert_not_called()


def test_find_available_port_switches_when_occupied():
    # Find two adjacent available ports dynamically
    temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_sock.bind(("127.0.0.1", 0))
    port = temp_sock.getsockname()[1]
    temp_sock.close()

    # Occupy the port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", port))
    sock.listen(1)

    try:
        with patch("click.secho") as mock_secho:
            resolved_port = _find_available_port("127.0.0.1", port)
            assert resolved_port == port + 1
            mock_secho.assert_called_once()
            assert f"Port {port} is occupied. Switching to port {port + 1}" in mock_secho.call_args[0][0]
    finally:
        sock.close()
