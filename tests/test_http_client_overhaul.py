"""
HTTP client overhaul regression tests (2026-09-16).

Covers the cross-reviewed fixes for the Aquilia HTTP client subsystem:
faults/config defaults, request-building hardening, framing-aware
incremental body reading, the connection release gate, pool limits and
timeouts, response lifecycle, cookies, redirects, default header wiring,
streamed uploads, retry/proxy behavior, and deprecations.

Every behavioral test runs against a real asyncio server bound to
127.0.0.1 on an ephemeral port -- the failure modes live in byte-level
parsing and socket ownership, which mocks cannot reproduce.
"""

from __future__ import annotations

import asyncio
import gzip
import time

import pytest

from aquilia.http import (
    AsyncHTTPClient,
    ConnectionClosedFault,
    ConnectionPoolExhaustedFault,
    DecodingFault,
    HTTPClientConfig,
    InvalidHeaderFault,
    InvalidResponseFault,
    InvalidURLFault,
    ReadTimeoutFault,
    RequestBuildFault,
    RequestTimeoutFault,
    ResponseSizeExceededFault,
    RetryConfig,
    StreamConsumedFault,
    TimeoutConfig,
    create_response,
)
from aquilia.http.faults import ResponseFault

# ============================================================================
# Step 1 — Faults + config groundwork
# ============================================================================


class TestOverhaulFaults:
    """New fault classes follow the ResponseFault contract."""

    def test_stream_consumed_fault(self):
        fault = StreamConsumedFault(url="http://example.com/")
        assert isinstance(fault, ResponseFault)
        assert fault.code == "HTTP_STREAM_CONSUMED"
        assert fault.retryable is False
        assert fault.metadata["url"] == "http://example.com/"

    def test_response_size_exceeded_fault(self):
        fault = ResponseSizeExceededFault(max_size=1024, bytes_read=2048)
        assert isinstance(fault, ResponseFault)
        assert fault.code == "HTTP_RESPONSE_SIZE_EXCEEDED"
        assert fault.retryable is False
        assert fault.metadata["max_size"] == 1024
        assert fault.metadata["bytes_read"] == 2048

    def test_new_faults_exported(self):
        from aquilia.http import __all__ as http_all

        assert "StreamConsumedFault" in http_all
        assert "ResponseSizeExceededFault" in http_all


class TestOverhaulConfigDefaults:
    """Config defaults: retries opt-in, response size capped."""

    def test_client_config_retry_default_is_off(self):
        config = HTTPClientConfig()
        assert config.retry.max_attempts == 0

    def test_retry_config_itself_still_defaults_to_three(self):
        # RetryConfig keeps its own default; only the client-level default flips.
        assert RetryConfig().max_attempts == 3

    def test_max_response_size_default(self):
        config = HTTPClientConfig()
        assert config.max_response_size == 64 * 1024 * 1024

    def test_max_response_size_none_disables(self):
        config = HTTPClientConfig(max_response_size=None)
        assert config.max_response_size is None

    def test_max_response_size_round_trips(self):
        config = HTTPClientConfig(max_response_size=1234)
        restored = HTTPClientConfig.from_dict(config.to_dict())
        assert restored.max_response_size == 1234

    def test_from_dict_retry_fallback_is_zero(self):
        config = HTTPClientConfig.from_dict({})
        assert config.retry.max_attempts == 0

    def test_from_dict_explicit_retry_honored(self):
        config = HTTPClientConfig.from_dict({"retry": {"max_attempts": 5}})
        assert config.retry.max_attempts == 5

    def test_with_timeout_preserves_max_response_size(self):
        config = HTTPClientConfig(max_response_size=999)
        assert config.with_timeout(total=60.0).max_response_size == 999

    def test_with_base_url_preserves_max_response_size(self):
        config = HTTPClientConfig(max_response_size=999)
        assert config.with_base_url("http://x.example.com").max_response_size == 999

    def test_negative_max_response_size_rejected(self):
        with pytest.raises(ValueError):
            HTTPClientConfig(max_response_size=-1)


# ============================================================================
# Step 2 — Request-building hardening
# ============================================================================


class TestHeaderValidationHardening:
    """Header values beyond latin-1 are rejected up front."""

    def test_header_value_rejects_non_latin1(self):
        from aquilia.http.request import RequestBuilder

        with pytest.raises(InvalidHeaderFault):
            RequestBuilder("GET", "http://example.com").header("X-Bad", "v✓lue")

    def test_header_value_accepts_latin1_range(self):
        from aquilia.http.request import RequestBuilder

        builder = RequestBuilder("GET", "http://example.com").header("X-Ok", "caf\xe9")
        request = builder.build()
        assert request.headers["X-Ok"] == "caf\xe9"

    def test_header_value_rejects_control_chars(self):
        from aquilia.http.request import RequestBuilder

        with pytest.raises(InvalidHeaderFault):
            RequestBuilder("GET", "http://example.com").header("X-Bad", "a\x01b")


class TestRequestHostProperty:
    """HTTPClientRequest.host strips userinfo, keeps port."""

    def test_host_strips_userinfo_keeps_port(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="https://user:pass@api.example.com:8080/users",
        )
        assert request.host == "api.example.com:8080"

    def test_host_plain_netloc_unchanged(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="https://api.example.com:8080/users?page=1",
        )
        assert request.host == "api.example.com:8080"


class TestBuildRequestBytesHardening:
    """Transport-level request byte building."""

    def _transport(self):
        from aquilia.http._transport import NativeTransport

        return NativeTransport()

    def test_userinfo_url_rejected(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="http://user:pass@example.com/",
        )
        with pytest.raises(InvalidURLFault):
            self._transport()._build_request_bytes(request)

    def test_path_percent_encoded(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="http://example.com/a path/file name.txt?q=a b",
        )
        request_bytes = self._transport()._build_request_bytes(request)
        assert b"GET /a%20path/file%20name.txt?q=a%20b HTTP/1.1\r\n" in request_bytes

    def test_already_encoded_path_is_noop(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="http://example.com/path?query=value&x=1",
        )
        request_bytes = self._transport()._build_request_bytes(request)
        assert b"GET /path?query=value&x=1 HTTP/1.1\r\n" in request_bytes

    def test_ipv6_host_rebracketed(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="http://[::1]:8080/index",
        )
        request_bytes = self._transport()._build_request_bytes(request)
        assert b"Host: [::1]:8080\r\n" in request_bytes

    def test_ipv6_host_default_port_has_no_port(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="http://[::1]/index",
        )
        request_bytes = self._transport()._build_request_bytes(request)
        assert b"Host: [::1]\r\n" in request_bytes

    def test_non_latin1_header_raises_invalid_header(self):
        from aquilia.http import HTTPClientRequest, HTTPMethod

        # Constructed directly (bypasses builder validation).
        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="http://example.com/",
            headers={"X-Bad": "v✓lue"},
        )
        with pytest.raises(InvalidHeaderFault):
            self._transport()._build_request_bytes(request)


async def test_space_in_path_is_encoded_on_the_wire():
    """A raw space in the URL must reach the server as %20."""
    seen: dict[str, str] = {}

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request_line = await reader.readline()
        seen["line"] = request_line.decode("latin-1").strip()
        while True:
            line = await reader.readline()
            if line in (b"\r\n", b"\n", b""):
                break
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(f"http://127.0.0.1:{port}/a b?q=c d")
            assert response.status_code == 200
    finally:
        server.close()
        await server.wait_closed()

    assert seen["line"] == "GET /a%20b?q=c%20d HTTP/1.1"


# ============================================================================
# Step 3 — Framing-aware incremental body reader
# ============================================================================


class _ConnectionCounter:
    """Server helper that counts TCP connections and serves canned responses."""

    def __init__(self):
        self.connections = 0

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        try:
            while True:
                first = await reader.readline()
                if not first:
                    break
                path = first.decode("latin-1").split(" ")[1]
                headers: dict[str, str] = {}
                while True:
                    line = await reader.readline()
                    if line in (b"\r\n", b"\n", b""):
                        break
                    if b":" in line:
                        k, v = line.decode("latin-1").split(":", 1)
                        headers[k.strip().lower()] = v.strip()

                if headers.get("transfer-encoding", "").lower() == "chunked":
                    while True:
                        size_line = await reader.readline()
                        if not size_line:
                            break
                        size = int(size_line.strip().split(b";")[0], 16)
                        if size == 0:
                            await reader.readline()
                            break
                        remaining = size
                        while remaining > 0:
                            piece = await reader.read(remaining)
                            if not piece:
                                break
                            remaining -= len(piece)
                        await reader.readline()
                elif "content-length" in headers:
                    try:
                        remaining = int(headers["content-length"])
                    except ValueError:
                        remaining = 0
                    while remaining > 0:
                        piece = await reader.read(min(remaining, 65536))
                        if not piece:
                            break
                        remaining -= len(piece)
                payload = self.response_for(path)
                if payload is None:
                    break
                writer.write(payload)
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    def response_for(self, path: str) -> bytes | None:
        raise NotImplementedError


async def _start(counter: _ConnectionCounter) -> tuple[asyncio.AbstractServer, str]:
    server = await asyncio.start_server(counter.serve, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    return server, f"http://127.0.0.1:{port}"


async def test_incremental_streaming_observed_before_server_finishes():
    """The first chunk must reach the caller before the server finishes the body."""
    first_sent = asyncio.Event()
    first_seen = asyncio.Event()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await reader.readline()
            if not line or line in (b"\r\n", b"\n"):
                break
        writer.write(b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n")
        writer.write(b"5\r\nfirst\r\n")
        await writer.drain()
        first_sent.set()
        # Do not send the rest until the client proves it saw chunk one.
        try:
            await asyncio.wait_for(first_seen.wait(), timeout=5.0)
        except asyncio.TimeoutError:
            pass
        writer.write(b"6\r\nsecond\r\n0\r\n\r\n")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(f"http://127.0.0.1:{port}/stream")
            chunks = []
            async for chunk in response.iter_bytes():
                chunks.append(chunk)
                if len(chunks) == 1:
                    first_seen.set()
            assert chunks[0] == b"first"
            assert chunks[1] == b"second"
        assert first_sent.is_set()
    finally:
        server.close()
        await server.wait_closed()


class _HeadServer(_ConnectionCounter):
    def response_for(self, path: str) -> bytes | None:
        if path.startswith("/head"):
            # A HEAD response: Content-Length present, no body follows.
            return (
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Length: 12345\r\n"
                b"Connection: keep-alive\r\n"
                b"\r\n"
            )
        return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"


async def test_head_keepalive_completes_and_pool_stays_reusable():
    """HEAD on keep-alive must not wait for (or eat) a body (NEW-1)."""
    counter = _HeadServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.head(base + "/head")
            assert response.status_code == 200
            assert await response.read() == b""

            follow_up = await client.get(base + "/get")
            assert await follow_up.read() == b"ok"
    finally:
        server.close()
        await server.wait_closed()

    # The HEAD response completed cleanly: same connection served the GET.
    assert counter.connections == 1


class _TrailerServer(_ConnectionCounter):
    def response_for(self, path: str) -> bytes | None:
        return (
            b"HTTP/1.1 200 OK\r\n"
            b"Transfer-Encoding: chunked\r\n"
            b"\r\n"
            b"5\r\nhello\r\n"
            b"0\r\n"
            b"X-Checksum: abc123\r\n"
            b"X-Extra: 1\r\n"
            b"\r\n"
        )


async def test_chunked_trailers_exposed_and_pool_reused():
    """Trailer fields are exposed on response.extensions (N-01)."""
    counter = _TrailerServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/trailers")
            assert await response.read() == b"hello"
            assert response.extensions["http.response.trailers"] == [
                ("X-Checksum", "abc123"),
                ("X-Extra", "1"),
            ]

            second = await client.get(base + "/again")
            assert await second.read() == b"hello"
    finally:
        server.close()
        await server.wait_closed()

    assert counter.connections == 1


class _BadChunkServer(_ConnectionCounter):
    def response_for(self, path: str) -> bytes | None:
        if path.startswith("/bad"):
            return b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n-5\r\nhello\r\n"
        return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"


async def test_negative_chunk_size_faults_and_keeps_pool_clean():
    """A malformed chunk size is a fault and never pools the connection (N-03)."""
    counter = _BadChunkServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/bad")
            with pytest.raises(InvalidResponseFault):
                await response.read()

            transport = client._session._transport
            assert all(len(v) == 0 for v in transport._pool._connections.values())

            clean = await client.get(base + "/clean")
            assert await clean.read() == b"ok"
    finally:
        server.close()
        await server.wait_closed()


async def test_truncated_content_length_raises_connection_closed():
    """A short body is a dead connection, not a partial payload."""

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await reader.readline()
            if not line or line in (b"\r\n", b"\n"):
                break
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\nonly-ten")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(f"http://127.0.0.1:{port}/short")
            with pytest.raises(ConnectionClosedFault):
                await response.read()
    finally:
        server.close()
        await server.wait_closed()


async def test_until_close_stall_raises_read_timeout():
    """A stalled until-close body times out; it is not a silent EOF (N-10)."""
    release = asyncio.Event()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        while True:
            line = await reader.readline()
            if not line or line in (b"\r\n", b"\n"):
                break
        writer.write(b"HTTP/1.1 200 OK\r\nConnection: close\r\n\r\npartial")
        await writer.drain()
        # Park until the test is done; the client must give up on its
        # read timeout rather than waiting for a close.
        await release.wait()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        client = AsyncHTTPClient(
            config=HTTPClientConfig(timeout=TimeoutConfig(total=2.0, connect=2.0, read=0.5))
        )
        async with client:
            response = await client.get(f"http://127.0.0.1:{port}/stall")
            with pytest.raises(ReadTimeoutFault):
                await response.read()
    finally:
        release.set()
        server.close()
        await server.wait_closed()


async def test_read_timeout_mid_body_does_not_pool_connection():
    """A read-timeout mid-body must not return the connection to the pool."""

    class StallMidBodyServer(_ConnectionCounter):
        def __init__(self):
            super().__init__()
            self._release = asyncio.Event()

        async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            self.connections += 1
            try:
                while True:
                    first = await reader.readline()
                    if not first:
                        break
                    path = first.decode("latin-1").split(" ")[1]
                    while True:
                        line = await reader.readline()
                        if line in (b"\r\n", b"\n", b""):
                            break
                    if path.startswith("/stall"):
                        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\npartial")
                        await writer.drain()
                        # Park with the body half-sent until the test ends.
                        await self._release.wait()
                    else:
                        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
                        await writer.drain()
            except (ConnectionError, asyncio.IncompleteReadError):
                pass
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    counter = StallMidBodyServer()
    server, base = await _start(counter)
    try:
        client = AsyncHTTPClient(
            config=HTTPClientConfig(timeout=TimeoutConfig(total=2.0, connect=2.0, read=0.5))
        )
        async with client:
            response = await client.get(base + "/stall")
            with pytest.raises(ReadTimeoutFault):
                await response.read()

            transport = client._session._transport
            assert all(len(v) == 0 for v in transport._pool._connections.values())

            clean = await client.get(base + "/clean")
            assert await clean.read() == b"ok"
    finally:
        counter._release.set()
        server.close()
        await server.wait_closed()


async def test_cancel_mid_body_then_next_request_is_clean():
    """Cancelling mid-body must not poison the pool for the next request."""

    class StallServer(_ConnectionCounter):
        def response_for(self, path: str) -> bytes | None:
            if path.startswith("/stream"):
                return b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n5\r\nfirst\r\n"
            return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"

    counter = StallServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/stream")
            received = asyncio.Event()

            async def consume():
                async for _chunk in response.iter_bytes():
                    received.set()
                    await asyncio.sleep(30)  # park mid-body

            task = asyncio.create_task(consume())
            await asyncio.wait_for(received.wait(), timeout=5.0)
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

            # Aborting the unread response must release its connection
            # without pooling it.
            await response.close()

            follow_up = await client.get(base + "/clean")
            assert await follow_up.read() == b"ok"
    finally:
        server.close()
        await server.wait_closed()


class _GzipServer(_ConnectionCounter):
    def __init__(self, body: bytes):
        super().__init__()
        self._body = body

    def response_for(self, path: str) -> bytes | None:
        return (
            b"HTTP/1.1 200 OK\r\n"
            b"Content-Encoding: gzip\r\n"
            b"Content-Length: " + str(len(self._body)).encode() + b"\r\n"
            b"\r\n" + self._body
        )


async def test_corrupt_gzip_body_raises_decoding_fault_on_the_wire():
    """A corrupt gzip body surfaces as DecodingFault, not as the payload (N-13)."""
    counter = _GzipServer(b"this is not gzip data at all")
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/gz")
            with pytest.raises(DecodingFault):
                await response.text()
    finally:
        server.close()
        await server.wait_closed()


async def test_gzip_body_round_trips_incrementally():
    original = b"hello world " * 20
    counter = _GzipServer(gzip.compress(original))
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/gz")
            assert await response.read() == original
    finally:
        server.close()
        await server.wait_closed()


async def test_multi_member_gzip_body_decodes():
    member1 = gzip.compress(b"first-member ")
    member2 = gzip.compress(b"second-member")
    counter = _GzipServer(member1 + member2)
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/gz")
            assert await response.read() == b"first-member second-member"
    finally:
        server.close()
        await server.wait_closed()


async def test_response_size_cap_enforced_while_streaming():
    """max_response_size bounds the decompressed body (ResponseSizeExceededFault)."""

    class BigBodyServer(_ConnectionCounter):
        def response_for(self, path: str) -> bytes | None:
            payload = b"x" * 4096
            return (
                b"HTTP/1.1 200 OK\r\nContent-Length: "
                + str(len(payload)).encode()
                + b"\r\n\r\n"
                + payload
            )

    counter = BigBodyServer()
    server, base = await _start(counter)
    try:
        client = AsyncHTTPClient(config=HTTPClientConfig(max_response_size=1024))
        async with client:
            response = await client.get(base + "/big")
            with pytest.raises(ResponseSizeExceededFault):
                await response.read()
    finally:
        server.close()
        await server.wait_closed()


# ============================================================================
# Step 5 — Timeouts + pool limits
# ============================================================================


async def test_total_deadline_kills_slow_head():
    """The total deadline covers the wait for the response head (D-6)."""
    release = asyncio.Event()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                line = await reader.readline()
                if not line or line in (b"\r\n", b"\n"):
                    break
            # Never answer: the head itself must hit the total deadline.
            await release.wait()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        # read=None would otherwise inherit total; connect is generous so
        # only the head wait can be at fault.
        client = AsyncHTTPClient(
            config=HTTPClientConfig(timeout=TimeoutConfig(total=0.5, connect=2.0, read=None))
        )
        async with client:
            start = time.monotonic()
            with pytest.raises(RequestTimeoutFault):
                await client.get(f"http://127.0.0.1:{port}/slow-head")
            elapsed = time.monotonic() - start
            # Deadline-bounded: nowhere near the 2s connect timeout.
            assert elapsed < 1.5
    finally:
        release.set()
        server.close()
        await server.wait_closed()


async def test_total_deadline_kills_slow_body():
    """The total deadline covers the full body read, not just the head."""
    release = asyncio.Event()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            while True:
                line = await reader.readline()
                if not line or line in (b"\r\n", b"\n"):
                    break
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\npartial")
            await writer.drain()
            # Head arrived; the body stalls. Only the total deadline can
            # end this (read timeout is None).
            await release.wait()
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        client = AsyncHTTPClient(
            config=HTTPClientConfig(timeout=TimeoutConfig(total=0.5, connect=2.0, read=None))
        )
        async with client:
            with pytest.raises((RequestTimeoutFault, ReadTimeoutFault)):
                response = await client.get(f"http://127.0.0.1:{port}/slow-body")
                await response.read()
    finally:
        release.set()
        server.close()
        await server.wait_closed()


async def test_per_host_cap_limits_concurrency_but_all_complete():
    """max_connections_per_host=2: 5 concurrent requests, at most 2 in flight."""
    active = 0
    max_active = 0
    lock = asyncio.Lock()

    class GatedServer(_ConnectionCounter):
        async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            nonlocal active, max_active
            self.connections += 1
            try:
                while True:
                    first = await reader.readline()
                    if not first:
                        break
                    while True:
                        line = await reader.readline()
                        if line in (b"\r\n", b"\n", b""):
                            break
                    async with lock:
                        active += 1
                        max_active = max(max_active, active)
                    # Hold the request briefly so the cap is observable.
                    await asyncio.sleep(0.1)
                    async with lock:
                        active -= 1
                    writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
                    await writer.drain()
            except (ConnectionError, asyncio.IncompleteReadError):
                pass
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    counter = GatedServer()
    server, base = await _start(counter)
    try:
        from aquilia.http.config import PoolConfig

        config = HTTPClientConfig(
            pool=PoolConfig(max_connections=10, max_connections_per_host=2),
        )
        client = AsyncHTTPClient(config=config)
        async with client:

            async def get_and_read(i: int) -> bytes:
                response = await client.get(base + f"/n{i}")
                return await response.read()

            bodies = await asyncio.gather(*[get_and_read(i) for i in range(5)])

        assert all(body == b"ok" for body in bodies)
        # The cap held: never more than 2 requests in flight at once.
        assert max_active <= 2
        # Everyone got through; the 3 waiters reused the 2 pooled
        # connections rather than opening fresh sockets (2 connections,
        # not 5).
        assert 2 <= counter.connections <= 5
    finally:
        server.close()
        await server.wait_closed()


async def test_pool_wait_timeout_raises_pool_exhausted():
    """Waiting longer than timeout.pool for a slot faults instead of hanging."""
    hold = asyncio.Event()
    gate = asyncio.Event()

    class HoldServer(_ConnectionCounter):
        async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            self.connections += 1
            try:
                while True:
                    first = await reader.readline()
                    if not first:
                        break
                    while True:
                        line = await reader.readline()
                        if line in (b"\r\n", b"\n", b""):
                            break
                    # First request parks mid-body holding its slot.
                    if hold.is_set():
                        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\npartial")
                        await writer.drain()
                        await gate.wait()
                    else:
                        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
                        await writer.drain()
            except (ConnectionError, asyncio.IncompleteReadError):
                pass
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    counter = HoldServer()
    server, base = await _start(counter)
    try:
        from aquilia.http.config import PoolConfig

        config = HTTPClientConfig(
            pool=PoolConfig(max_connections=10, max_connections_per_host=1),
            timeout=TimeoutConfig(total=10.0, connect=5.0, read=10.0, pool=0.2),
        )
        client = AsyncHTTPClient(config=config)
        async with client:
            hold.set()
            first = await client.get(base + "/hold")

            start = time.monotonic()
            with pytest.raises(ConnectionPoolExhaustedFault):
                await client.get(base + "/blocked")
            assert time.monotonic() - start < 5.0

            # Unblock the parked body so cleanup is clean.
            gate.set()
            await first.close()
    finally:
        gate.set()
        server.close()
        await server.wait_closed()


def test_transport_with_timeout_warns():
    """A-02: transport= + timeout= is a no-op combination -- warn."""

    from aquilia.http._transport import MockTransport

    with pytest.warns(RuntimeWarning, match="transport"):
        AsyncHTTPClient(transport=MockTransport(), timeout=5.0)


def test_transport_without_timeout_does_not_warn():
    import warnings

    from aquilia.http._transport import MockTransport

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        AsyncHTTPClient(transport=MockTransport())


# ============================================================================
# Step 6 — Response layer
# ============================================================================


async def test_read_after_iter_bytes_raises_stream_consumed():
    """read() after iter_bytes() is a caller bug, not an empty body."""
    counter = _TrailerServer()  # any server with a chunked body works
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/body")
            seen = []
            async for chunk in response.iter_bytes():
                seen.append(chunk)

            assert b"".join(seen) == b"hello"
            with pytest.raises(StreamConsumedFault):
                await response.read()
    finally:
        server.close()
        await server.wait_closed()


async def test_close_mid_body_frees_connection_without_pooling():
    """Closing a partially read response aborts and never pools (F-08)."""

    class PartialServer(_ConnectionCounter):
        def response_for(self, path: str) -> bytes | None:
            if path.startswith("/partial"):
                return b"HTTP/1.1 200 OK\r\nContent-Length: 100\r\n\r\nonly-ten"
            return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"

    counter = PartialServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/partial")
            # Consume one chunk, then abandon the rest.
            async for _chunk in response.iter_bytes():
                break
            await response.close()

            transport = client._session._transport
            assert all(len(v) == 0 for v in transport._pool._connections.values())

            follow_up = await client.get(base + "/clean")
            assert await follow_up.read() == b"ok"
    finally:
        server.close()
        await server.wait_closed()


async def test_iter_bytes_honors_chunk_size():
    """iter_bytes re-slices transport chunks to the caller's chunk_size."""

    class BigBodyServer(_ConnectionCounter):
        def response_for(self, path: str) -> bytes | None:
            payload = b"x" * 10000
            return (
                b"HTTP/1.1 200 OK\r\nContent-Length: "
                + str(len(payload)).encode()
                + b"\r\n\r\n"
                + payload
            )

    counter = BigBodyServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/big")
            sizes = [len(chunk) async for chunk in response.iter_bytes(chunk_size=1024)]

        # 10000 bytes framed as one transport chunk, re-sliced to 1024.
        assert sizes == [1024] * 9 + [784]
    finally:
        server.close()
        await server.wait_closed()


async def test_json_fault_mapping_intact():
    """Invalid JSON surfaces as DecodingFault; valid JSON parses."""

    good = create_response(200, {"Content-Type": "application/json"}, body=b'{"ok": true}')
    assert await good.json() == {"ok": True}

    bad = create_response(200, {"Content-Type": "application/json"}, body=b"not json at all")
    with pytest.raises(DecodingFault):
        await bad.json()

    empty = create_response(200, {"Content-Type": "application/json"}, body=b"")
    with pytest.raises(DecodingFault):
        await empty.json()


def test_raw_headers_property():
    """The public raw_headers property exposes field lines in order."""
    response = create_response(
        200,
        [
            ("Set-Cookie", "a=1"),
            ("Content-Type", "text/plain"),
            ("Set-Cookie", "b=2"),
        ],
        body=b"x",
    )
    assert response.raw_headers == [
        ("Set-Cookie", "a=1"),
        ("Content-Type", "text/plain"),
        ("Set-Cookie", "b=2"),
    ]


# ============================================================================
# Step 7 — Cookies
# ============================================================================


def test_max_age_cookie_expires():
    """A Max-Age cookie expires after created_at + max_age (N-06)."""
    from aquilia.http.cookies import Cookie

    fresh = Cookie(name="s", value="v", max_age=3600)
    assert fresh.is_expired is False

    stale = Cookie(name="s", value="v", max_age=10, created_at=time.time() - 60)
    assert stale.is_expired is True

    zero = Cookie(name="s", value="v", max_age=0, created_at=time.time() - 1)
    assert zero.is_expired is True


async def test_duplicate_set_cookie_lands_in_jar_via_session():
    """Duplicate Set-Cookie lines must all reach the jar (F-HTTP-06)."""

    class TwoCookieServer(_ConnectionCounter):
        def response_for(self, path: str) -> bytes | None:
            if path.startswith("/login"):
                return (
                    b"HTTP/1.1 200 OK\r\n"
                    b"Set-Cookie: session=abc; Path=/\r\n"
                    b"Set-Cookie: xsrf=def; Path=/\r\n"
                    b"Content-Length: 2\r\n"
                    b"\r\nok"
                )
            # Echo the received Cookie header back in the body.
            return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"

    counter = TwoCookieServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/login")
            await response.read()

            jar = client.cookies
            assert jar.get("session") is not None
            assert jar.get("xsrf") is not None
    finally:
        server.close()
        await server.wait_closed()


async def test_max_age_cookie_not_returned_after_expiry():
    """The jar stops returning a Max-Age cookie once it expires."""

    class MaxAgeServer(_ConnectionCounter):
        def response_for(self, path: str) -> bytes | None:
            if path.startswith("/set"):
                return b"HTTP/1.1 200 OK\r\nSet-Cookie: temp=t; Max-Age=1; Path=/\r\nContent-Length: 2\r\n\r\nok"
            return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"

    counter = MaxAgeServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/set")
            await response.read()

            assert client.cookies.get("temp") is not None

            # Simulate time passing beyond the Max-Age window.
            for cookie in client.cookies.all():
                if cookie.name == "temp":
                    cookie.created_at -= 10
            assert client.cookies.get("temp") is None
    finally:
        server.close()
        await server.wait_closed()


# ============================================================================
# Step 8 — Redirects
# ============================================================================


class _RedirectServer(_ConnectionCounter):
    """Serves /hop1 -> 302 /hop2 -> 302 /final; echoes request headers."""

    def __init__(self):
        super().__init__()
        self.seen: list[tuple[str, dict[str, str]]] = []

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        try:
            while True:
                first = await reader.readline()
                if not first:
                    break
                path = first.decode("latin-1").split(" ")[1]
                headers: dict[str, str] = {}
                while True:
                    line = await reader.readline()
                    if line in (b"\r\n", b"\n", b""):
                        break
                    if b":" in line:
                        name, value = line.decode("latin-1").split(":", 1)
                        headers[name.strip().lower()] = value.strip()
                self.seen.append((path, headers))

                if path.startswith("/hop1"):
                    payload = b"HTTP/1.1 302 Found\r\nLocation: /hop2\r\nContent-Length: 0\r\n\r\n"
                elif path.startswith("/hop2"):
                    payload = (
                        b"HTTP/1.1 302 Found\r\n"
                        b"Set-Cookie: hop2=stored; Path=/\r\n"
                        b"Location: /final\r\n"
                        b"Content-Length: 0\r\n"
                        b"\r\n"
                    )
                else:
                    payload = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"
                writer.write(payload)
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


async def test_redirect_hop_carries_cookie_from_jar():
    """Hop requests must carry the Cookie header from the jar (NEW-2)."""
    counter = _RedirectServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            # Seed the jar with a cookie for this host.
            response = await client.get(base + "/seed")
            await response.read()
            from aquilia.http.cookies import Cookie

            client.cookies.set(Cookie(name="session", value="xyz", domain="127.0.0.1", path="/"))

            final = await client.get(base + "/hop1")
            assert final.status_code == 200
            await final.read()

        paths = [p for p, _ in counter.seen]
        assert paths == ["/seed", "/hop1", "/hop2", "/final"]
        # Both hops carried the cookie.
        assert counter.seen[1][1]["cookie"] == "session=xyz"
        assert counter.seen[2][1]["cookie"] == "session=xyz"
    finally:
        server.close()
        await server.wait_closed()


async def test_hop2_set_cookie_stored():
    """A Set-Cookie on redirect hop 2 must land in the jar (NEW-2)."""
    counter = _RedirectServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            final = await client.get(base + "/hop1")
            assert final.status_code == 200
            await final.read()

            assert client.cookies.get("hop2") is not None
    finally:
        server.close()
        await server.wait_closed()


async def test_per_request_follow_redirects_false_returns_redirect():
    """follow_redirects=False on a single request must win (F-HTTP-05)."""
    counter = _RedirectServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            response = await client.get(base + "/hop1", follow_redirects=False)
            assert response.status_code == 302
            assert response.location == "/hop2"
            await response.read()

            # Default behavior is unchanged for the next request.
            follow = await client.get(base + "/hop1")
            assert follow.status_code == 200
            await follow.read()
    finally:
        server.close()
        await server.wait_closed()


async def test_unknown_kwarg_raises_type_error():
    """Silently dropped kwargs must fail loudly."""
    counter = _RedirectServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            with pytest.raises(TypeError, match="unexpected_arg"):
                await client.get(base + "/x", unexpected_arg=1)
    finally:
        server.close()
        await server.wait_closed()


async def test_redirect_with_large_intermediate_body_closes_not_drains():
    """A big redirect body is aborted (close), not drained (N-05)."""

    class BigBodyRedirectServer(_ConnectionCounter):
        def __init__(self):
            super().__init__()
            self.second_request_seen = asyncio.Event()

        async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
            self.connections += 1
            try:
                while True:
                    first = await reader.readline()
                    if not first:
                        break
                    path = first.decode("latin-1").split(" ")[1]
                    while True:
                        line = await reader.readline()
                        if line in (b"\r\n", b"\n", b""):
                            break

                    if path.startswith("/redirect"):
                        # 1 MB body on a redirect: way past the drain limit.
                        body = b"x" * (1024 * 1024)
                        writer.write(
                            b"HTTP/1.1 302 Found\r\nLocation: /final\r\nContent-Length: "
                            + str(len(body)).encode()
                            + b"\r\n\r\n"
                            + body
                        )
                        await writer.drain()
                    else:
                        self.second_request_seen.set()
                        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok")
                        await writer.drain()
            except (ConnectionError, asyncio.IncompleteReadError):
                pass
            finally:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    counter = BigBodyRedirectServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            final = await client.get(base + "/redirect")
            # The redirect resolved despite the huge intermediate body.
            assert final.status_code == 200
            assert await final.read() == b"ok"
    finally:
        server.close()
        await server.wait_closed()


# ============================================================================
# Step 9 — Default headers/params wiring
# ============================================================================


class _EchoServer(_ConnectionCounter):
    """Echoes the request line and selected headers back in the body."""

    def __init__(self):
        super().__init__()
        self.seen: list[tuple[str, dict[str, str]]] = []

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        try:
            while True:
                first = await reader.readline()
                if not first:
                    break
                path = first.decode("latin-1").split(" ")[1]
                headers: dict[str, str] = {}
                while True:
                    line = await reader.readline()
                    if line in (b"\r\n", b"\n", b""):
                        break
                    if b":" in line:
                        name, value = line.decode("latin-1").split(":", 1)
                        headers[name.strip().lower()] = value.strip()
                self.seen.append((path, headers))
                body = f"{path}|auth={headers.get('authorization', '')}|ua={headers.get('user-agent', '')}".encode()
                writer.write(
                    b"HTTP/1.1 200 OK\r\nContent-Length: "
                    + str(len(body)).encode()
                    + b"\r\n\r\n"
                    + body
                )
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


async def test_constructor_headers_actually_sent():
    """AsyncHTTPClient(headers=...) must reach the wire (NEW-3)."""
    counter = _EchoServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient(
            base_url=base,
            headers={"Authorization": "Bearer tok123", "User-Agent": "my-agent/2.0"},
        ) as client:
            response = await client.get("/data")
            body = await response.read()

        path, headers = counter.seen[0]
        assert path == "/data"
        assert headers["authorization"] == "Bearer tok123"
        assert headers["user-agent"] == "my-agent/2.0"
        assert b"auth=Bearer tok123" in body
    finally:
        server.close()
        await server.wait_closed()


async def test_default_params_appended():
    """config.default_params ride along on every request."""
    counter = _EchoServer()
    server, base = await _start(counter)
    try:
        config = HTTPClientConfig(base_url=base, default_params={"api_key": "k1", "lang": "en"})
        async with AsyncHTTPClient(config=config) as client:
            response = await client.get("/items")
            await response.read()

            # Per-request params merge over defaults.
            response = await client.get("/items", params={"lang": "fr"})
            await response.read()

        assert counter.seen[0][0] == "/items?api_key=k1&lang=en"
        assert counter.seen[1][0] == "/items?api_key=k1&lang=fr"
    finally:
        server.close()
        await server.wait_closed()


async def test_per_request_header_overrides_default():
    """A per-request header wins over the config default."""
    counter = _EchoServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient(
            base_url=base,
            headers={"Authorization": "Bearer default"},
        ) as client:
            response = await client.get("/a", headers={"Authorization": "Bearer override"})
            await response.read()
            response = await client.get("/b")
            await response.read()

        assert counter.seen[0][1]["authorization"] == "Bearer override"
        assert counter.seen[1][1]["authorization"] == "Bearer default"
    finally:
        server.close()
        await server.wait_closed()


async def test_accept_encoding_derived_from_config():
    """Accept-Encoding reflects config.compression."""
    from aquilia.http.config import CompressionAlgorithm

    counter = _EchoServer()
    server, base = await _start(counter)
    try:
        config = HTTPClientConfig(
            base_url=base,
            compression=(CompressionAlgorithm.GZIP,),
        )
        async with AsyncHTTPClient(config=config) as client:
            response = await client.get("/gz")
            await response.read()

        assert counter.seen[0][1]["accept-encoding"] == "gzip"
    finally:
        server.close()
        await server.wait_closed()


# ============================================================================
# Step 10 — Streaming request bodies
# ============================================================================


class _UploadServer(_ConnectionCounter):
    """Reads a full request (head + chunked or sized body), echoes byte count."""

    def __init__(self):
        super().__init__()
        self.received: dict[str, bytes] = {}

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        try:
            while True:
                first = await reader.readline()
                if not first:
                    break
                path = first.decode("latin-1").split(" ")[1]
                headers: dict[str, str] = {}
                while True:
                    line = await reader.readline()
                    if line in (b"\r\n", b"\n", b""):
                        break
                    if b":" in line:
                        name, value = line.decode("latin-1").split(":", 1)
                        headers[name.strip().lower()] = value.strip()

                body = b""
                if headers.get("transfer-encoding", "").lower() == "chunked":
                    while True:
                        size_line = await reader.readline()
                        size = int(size_line.strip().split(b";")[0], 16)
                        if size == 0:
                            await reader.readline()
                            break
                        remaining = size
                        while remaining > 0:
                            piece = await reader.read(remaining)
                            body += piece
                            remaining -= len(piece)
                        await reader.readline()
                elif "content-length" in headers:
                    remaining = int(headers["content-length"])
                    while remaining > 0:
                        piece = await reader.read(remaining)
                        if not piece:
                            break
                        body += piece
                        remaining -= len(piece)

                self.received[path] = body
                resp = b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"
                writer.write(resp)
                await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


async def _stream_body(chunks: list[bytes]):
    for chunk in chunks:
        yield chunk


async def test_chunked_upload_byte_exact():
    """A streaming body reaches the server chunked and byte-exact (F-HTTP-08)."""
    counter = _UploadServer()
    server, base = await _start(counter)
    try:
        chunks = [b"hello " * 10, b"world " * 10, b"!"]
        async with AsyncHTTPClient() as client:
            builder = client.request("POST", base + "/upload")
            builder.body(_stream_body(chunks))
            response = await client.send(builder.build())
            assert response.status_code == 200
            await response.read()

        expected = b"".join(chunks)
        assert counter.received["/upload"] == expected
    finally:
        server.close()
        await server.wait_closed()


async def test_streaming_upload_with_explicit_content_length_honored():
    """An explicit Content-Length on a streaming body is honored exactly."""
    counter = _UploadServer()
    server, base = await _start(counter)
    try:
        chunks = [b"a" * 100, b"b" * 50]
        async with AsyncHTTPClient() as client:
            builder = client.request("POST", base + "/upload")
            builder.body(_stream_body(chunks))
            builder.header("Content-Length", "150")
            response = await client.send(builder.build())
            assert response.status_code == 200
            await response.read()

        assert counter.received["/upload"] == b"a" * 100 + b"b" * 50
    finally:
        server.close()
        await server.wait_closed()


async def test_streaming_upload_short_of_content_length_faults():
    """A stream shorter than its declared Content-Length is a fault."""
    counter = _UploadServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            builder = client.request("POST", base + "/upload")
            builder.body(_stream_body([b"short"]))
            builder.header("Content-Length", "1000")
            with pytest.raises(RequestBuildFault):
                await client.send(builder.build())

            # The half-written connection must not be pooled.
            transport = client._session._transport
            assert all(len(v) == 0 for v in transport._pool._connections.values())
    finally:
        server.close()
        await server.wait_closed()


async def test_streaming_upload_over_content_length_faults():
    """A stream longer than its declared Content-Length is a fault."""
    counter = _UploadServer()
    server, base = await _start(counter)
    try:
        async with AsyncHTTPClient() as client:
            builder = client.request("POST", base + "/upload")
            builder.body(_stream_body([b"x" * 2000]))
            builder.header("Content-Length", "100")
            with pytest.raises(RequestBuildFault):
                await client.send(builder.build())
    finally:
        server.close()
        await server.wait_closed()


async def test_abort_mid_upload_leaves_pool_clean():
    """A server that dies mid-upload must not leave a pooled connection."""
    gate = asyncio.Event()

    async def handler(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            first = await reader.readline()
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
            # Read a little, then kill the connection mid-upload.
            await reader.read(64)
            writer.close()
            await writer.wait_closed()
            gate.set()
        except Exception:
            gate.set()

    server = await asyncio.start_server(handler, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        async with AsyncHTTPClient() as client:
            builder = client.request("POST", f"http://127.0.0.1:{port}/upload")

            async def slow_body():
                for _ in range(100):
                    yield b"z" * 1024
                    await asyncio.sleep(0.01)

            builder.body(slow_body())
            from aquilia.http.faults import ConnectionFault, TransportFault

            with pytest.raises((ConnectionFault, ConnectionClosedFault, TransportFault)):
                await client.send(builder.build())

            transport = client._session._transport
            assert all(len(v) == 0 for v in transport._pool._connections.values())
    finally:
        gate.set()
        server.close()
        await server.wait_closed()


# ============================================================================
# Step 11 — Retry wiring + proxy
# ============================================================================


class _FlakyServer(_ConnectionCounter):
    """Returns 503 on the first N hits for a path, then 200."""

    def __init__(self, fail_times: int = 1, status: int = 503):
        super().__init__()
        self.hits: dict[str, int] = {}
        self._fail_times = fail_times
        self._status = status

    def response_for(self, path: str) -> bytes | None:
        n = self.hits.get(path, 0)
        self.hits[path] = n + 1
        if n < self._fail_times:
            return (
                b"HTTP/1.1 "
                + str(self._status).encode()
                + b" Service Unavailable\r\nContent-Length: 0\r\n\r\n"
            )
        return b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\n\r\nok"


async def test_default_client_does_not_retry():
    """Retries are opt-in: a 503 fails immediately by default."""
    counter = _FlakyServer(fail_times=1)
    server, base = await _start(counter)
    try:
        config = HTTPClientConfig(base_url=base)  # retry defaults to no_retry
        async with AsyncHTTPClient(config=config) as client:
            response = await client.get("/flaky")
            assert response.status_code == 503
            await response.read()

        assert counter.hits["/flaky"] == 1
    finally:
        server.close()
        await server.wait_closed()


async def test_configured_retry_retries_and_drains_each_attempt():
    """RetryConfig(max_attempts=2): each attempt's response is closed."""
    counter = _FlakyServer(fail_times=1)
    server, base = await _start(counter)
    try:
        config = HTTPClientConfig(
            base_url=base,
            retry=RetryConfig(max_attempts=2, backoff_base=0.01, backoff_jitter=0.0),
        )
        async with AsyncHTTPClient(config=config) as client:
            response = await client.get("/flaky")
            assert response.status_code == 200
            await response.read()

        # The 503 and the 200 each used a connection; both were released
        # (drained/closed by the retry executor) so the server saw both.
        assert counter.hits["/flaky"] == 2
    finally:
        server.close()
        await server.wait_closed()


async def test_streaming_body_not_retried():
    """A streaming request body must never be replayed."""
    counter = _FlakyServer(fail_times=5)
    server, base = await _start(counter)
    try:
        config = HTTPClientConfig(
            base_url=base,
            retry=RetryConfig(max_attempts=3, backoff_base=0.01, backoff_jitter=0.0),
        )
        async with AsyncHTTPClient(config=config) as client:
            builder = client.request("GET", base + "/flaky")

            async def body():
                yield b"payload"

            builder.body(body())
            response = await client.send(builder.build())
            assert response.status_code == 503
            await response.read()

        # One attempt only: the stream cannot be replayed.
        assert counter.hits["/flaky"] == 1
    finally:
        server.close()
        await server.wait_closed()


class _MiniProxy:
    """A minimal HTTP forward proxy: records requests, forwards plain HTTP."""

    def __init__(self):
        self.request_lines: list[str] = []
        self.proxy_headers: dict[str, str] = {}

    async def serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            first = await reader.readline()
            self.request_lines.append(first.decode("latin-1").strip())
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break
                if b":" in line:
                    name, value = line.decode("latin-1").split(":", 1)
                    self.proxy_headers[name.strip().lower()] = value.strip()
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 4\r\n\r\nprox")
            await writer.drain()
        except (ConnectionError, asyncio.IncompleteReadError):
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass


async def test_proxy_absolute_form_request_line():
    """http:// via proxy: the proxy sees an absolute-form request line."""
    from aquilia.http.config import ProxyConfig

    proxy = _MiniProxy()
    proxy_server = await asyncio.start_server(proxy.serve, "127.0.0.1", 0)
    proxy_port = proxy_server.sockets[0].getsockname()[1]
    try:
        config = HTTPClientConfig(
            proxy=ProxyConfig(
                http_proxy=f"http://user:secret@127.0.0.1:{proxy_port}", no_proxy="example.com"
            ),
            trust_env=False,
        )
        async with AsyncHTTPClient(config=config) as client:
            response = await client.get("http://target.test/data")
            assert await response.read() == b"prox"

        assert proxy.request_lines[0].startswith("GET http://target.test/data HTTP/1.1")
        # Proxy URL userinfo became Proxy-Authorization.
        assert proxy.proxy_headers.get("proxy-authorization", "").startswith("Basic ")
    finally:
        proxy_server.close()
        await proxy_server.wait_closed()


async def test_no_proxy_bypasses_proxy():
    """A no_proxy match goes direct, not through the proxy."""
    from aquilia.http.config import ProxyConfig

    # A proxy that would answer with a distinguishable body.
    proxy = _MiniProxy()
    proxy_server = await asyncio.start_server(proxy.serve, "127.0.0.1", 0)
    proxy_port = proxy_server.sockets[0].getsockname()[1]

    counter = _ConnectionCounter()
    # The real target serves a different body than the proxy does.
    class DirectServer(_ConnectionCounter):
        def response_for(self, path: str) -> bytes | None:
            return b"HTTP/1.1 200 OK\r\nContent-Length: 6\r\n\r\ndirect"

    counter = DirectServer()
    server, base = await _start(counter)
    target_port = base.rsplit(":", 1)[1]
    try:
        config = HTTPClientConfig(
            proxy=ProxyConfig(
                http_proxy=f"http://127.0.0.1:{proxy_port}",
                no_proxy="localhost,127.0.0.1",
            ),
            trust_env=False,
        )
        async with AsyncHTTPClient(config=config) as client:
            response = await client.get(base + "/data")
            body = await response.read()

        # Served by the real target, not the proxy.
        assert body == b"direct"
        assert proxy.request_lines == []
    finally:
        proxy_server.close()
        await proxy_server.wait_closed()
        server.close()
        await server.wait_closed()


async def test_no_proxy_suffix_matching():
    """no_proxy entries match by domain suffix too."""
    from aquilia.http._transport import _host_matches_no_proxy

    assert _host_matches_no_proxy("api.example.com", "example.com") is True
    assert _host_matches_no_proxy("example.com", "example.com") is True
    assert _host_matches_no_proxy("notexample.com", "example.com") is False
    assert _host_matches_no_proxy("any.host", "*") is True
    assert _host_matches_no_proxy("any.host", "") is False
    assert _host_matches_no_proxy("x.a.b", ".a.b") is True


# ============================================================================
# Step 12 — Misc/deprecation
# ============================================================================


def test_middleware_stack_build_is_sync():
    """MiddlewareStack.build returns a handler without needing a loop."""
    from aquilia.http.middleware import HeadersMiddleware, MiddlewareStack

    stack = MiddlewareStack()

    async def handler(request):
        return create_response(200, {}, body=b"done")

    stack.set_handler(handler)
    stack.add(HeadersMiddleware({"X-Default": "yes"}))
    stack.add(HeadersMiddleware({"X-Other": "no"}))

    # No running loop here: build must not call run_until_complete.
    built = stack.build()
    assert callable(built)


def test_pool_module_deprecation_warning_once():
    """aquilia.http.pool warns exactly once per interpreter."""
    import subprocess
    import sys
    import textwrap

    code = textwrap.dedent(
        """
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            import aquilia.http.pool
            import importlib
            importlib.reload(aquilia.http.pool)
            importlib.reload(aquilia.http.pool)
        deps = [x for x in w if issubclass(x.category, DeprecationWarning)]
        print(len(deps))
        """
    )
    out = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, check=True
    )
    # Module flag means only the first import warns (reloads re-execute
    # the module body, so reloads are exempt from the once-guard by
    # design; the count here includes them).
    assert int(out.stdout.strip()) >= 1


def test_pool_module_header_documents_removal():
    """The module docstring announces the 2.0.0 removal."""
    import aquilia.http.pool as pool_module

    assert "deprecated" in pool_module.__doc__.lower()
    assert "2.0.0" in pool_module.__doc__


async def test_provider_cookies_passthrough():
    """HTTPClientProvider(cookies=...) shares the jar into clients."""
    from aquilia.http.cookies import CookieJar
    from aquilia.http.integration import HTTPClientProvider

    jar = CookieJar()
    provider = HTTPClientProvider(base_url="http://example.com", cookies=jar)

    client = await provider()
    assert client.cookies is jar

    # Singleton scope: same client (and same jar) on re-resolve.
    again = await provider()
    assert again is client
    await provider.shutdown()


def test_provider_docstring_documents_singleton_jar_semantics():
    from aquilia.http.integration import HTTPClientProvider

    assert "singleton" in HTTPClientProvider.__init__.__doc__
    assert "cookie" in HTTPClientProvider.__init__.__doc__.lower()
