from io import StringIO

from aquilia.mcp.transport.stdio import StdioTransport


class _Server:
    def handle(self, method, params):
        if method == "ping":
            return {}
        raise AssertionError(method)


def test_stdio_transport_handles_ping_line():
    transport = StdioTransport(_Server(), stdout=StringIO())
    response = transport.handle_line('{"jsonrpc":"2.0","id":1,"method":"ping","params":{}}\n')
    assert response["result"] == {}


def test_stdio_transport_handles_malformed_json():
    transport = StdioTransport(_Server(), stdout=StringIO())
    response = transport.handle_line("{bad json\n")
    assert response["error"]["code"] == -32700


def test_stdio_transport_ignores_notifications():
    transport = StdioTransport(_Server(), stdout=StringIO())
    response = transport.handle_line('{"jsonrpc":"2.0","method":"ping","params":{}}\n')
    assert response is None
