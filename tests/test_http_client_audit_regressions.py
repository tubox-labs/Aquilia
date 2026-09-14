"""
HTTP client regressions from the AniWave migration audit (2026-09-14).

F-07 -- ``NativeTransport._read_response_head`` collapsed duplicate header
        lines into a dict (last one wins), so a response setting several
        cookies (a session plus a CSRF token) lost all but the last, and
        ``HTTPClientResponse.get_headers`` could never return more than one
        value.
F-08 -- ``NativeTransport.send`` returned the connection to the pool while
        the response body was still unread; a later request could be served
        leftover bytes, and closing the client closed the connection under
        an in-flight reader (SSL errors / truncated bodies when reading
        ``await res.text()`` after the client context exited).

Both are verified against a real asyncio HTTP server on a loopback socket,
not against mocks: the failure modes live in byte-level parsing and socket
ownership, which mocks cannot reproduce.
"""

from __future__ import annotations

import asyncio

import pytest

from aquilia.http import AsyncHTTPClient
from aquilia.http.response import create_response

BODY = b'{"ok": true}'


@pytest.fixture
async def server():
    """A keep-alive HTTP server that answers every request identically."""

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        head = (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Type: application/json\r\n"
            b"Content-Length: " + str(len(BODY)).encode() + b"\r\n"
            b"Set-Cookie: xsrf=abc123; Path=/; Expires=Wed, 21 Oct 2026 07:28:00 GMT; HttpOnly\r\n"
            b"Set-Cookie: session=xyz789; Path=/; Expires=Wed, 21 Oct 2026 07:28:00 GMT; HttpOnly\r\n"
            b"X-Multi: one\r\n"
            b"X-Multi: two\r\n"
            b"Connection: keep-alive\r\n"
            b"\r\n"
        )
        try:
            while True:
                first = await reader.readline()
                if not first:
                    break
                while True:
                    line = await reader.readline()
                    if line in (b"\r\n", b"\n", b""):
                        break
                writer.write(head + BODY)
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    srv = await asyncio.start_server(handle, "127.0.0.1", 0)
    port = srv.sockets[0].getsockname()[1]
    yield f"http://127.0.0.1:{port}"
    srv.close()
    await srv.wait_closed()


# ── F-07: multi-value headers ───────────────────────────────────────────────


async def test_duplicate_set_cookie_headers_are_preserved(server):
    async with AsyncHTTPClient() as client:
        response = await client.get(server + "/")

        values = response.get_headers("Set-Cookie")

    assert len(values) == 2
    assert any(v.startswith("xsrf=abc123") for v in values)
    assert any(v.startswith("session=xyz789") for v in values)
    # Expires dates contain commas; the raw values must be unmangled.
    assert all("Expires=Wed, 21 Oct 2026" in v for v in values)


async def test_cookies_property_sees_every_cookie(server):
    async with AsyncHTTPClient() as client:
        response = await client.get(server + "/")

    assert response.cookies == {"xsrf": "abc123", "session": "xyz789"}


async def test_combinable_duplicate_headers_list_all_values(server):
    async with AsyncHTTPClient() as client:
        response = await client.get(server + "/")

    assert sorted(response.get_headers("X-Multi")) == ["one", "two"]
    # The first value wins for the single-value accessor.
    assert response.get_header("X-Multi") == "one"


async def test_case_insensitive_header_access(server):
    async with AsyncHTTPClient() as client:
        response = await client.get(server + "/")

    assert response.get_header("content-type") == "application/json"
    assert response.get_header("CONTENT-LENGTH") == str(len(BODY))


async def test_create_response_keeps_raw_lines_from_dict():
    response = create_response(200, {"Set-Cookie": "a=1", "X": "y"})

    assert response.get_headers("set-cookie") == ["a=1"]
    assert response.get_header("X") == "y"


# ── F-08: body / connection lifecycle ───────────────────────────────────────


async def test_body_readable_after_client_close(server):
    """The audit's exact scenario: read after the client context exits."""
    holder: dict[str, object] = {}
    async with AsyncHTTPClient() as client:
        holder["response"] = await client.get(server + "/after")

    response = holder["response"]
    assert await response.text() == '{"ok": true}'


async def test_connection_is_reused_across_requests(server):
    async with AsyncHTTPClient() as client:
        first = await client.get(server + "/one")
        assert await first.read() == BODY

        second = await client.get(server + "/two")
        assert await second.read() == BODY


async def test_unread_response_does_not_poison_the_pool(server):
    async with AsyncHTTPClient() as client:
        unread = await client.get(server + "/unread")  # body deliberately not read

        clean = await client.get(server + "/clean")
        assert await clean.read() == BODY

        await unread.close()


async def test_concurrent_requests_on_one_client(server):
    async with AsyncHTTPClient() as client:
        responses = await asyncio.gather(*[client.get(server + f"/n{i}") for i in range(8)])
        texts = await asyncio.gather(*[response.text() for response in responses])

    assert all(text == '{"ok": true}' for text in texts)


async def test_response_close_without_read_releases_connection(server):
    """Closing an unconsumed response must not leak the connection."""
    async with AsyncHTTPClient() as client:
        response = await client.get(server + "/closed")
        await response.close()

        # The pool must still be able to serve the next request.
        next_response = await client.get(server + "/next")
        assert await next_response.read() == BODY
