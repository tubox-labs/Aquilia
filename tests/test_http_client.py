"""
Tests for Aquilia HTTP client module.

Comprehensive tests covering configuration, request building,
response handling, cookies, retry, streaming, and fault handling.
"""

import time

import pytest

from aquilia.http import (
    HTTP_CLIENT_DOMAIN,
    APIKeyAuth,
    BasicAuth,
    BearerAuth,
    ChunkedDecoder,
    ChunkedEncoder,
    ConnectionFault,
    ConstantBackoff,
    Cookie,
    CookieJar,
    ExponentialBackoff,
    HeaderInterceptor,
    HTTPClientConfig,
    HTTPClientFault,
    HTTPClientRequest,
    HTTPMethod,
    InterceptorChain,
    LoggingInterceptor,
    MockTransport,
    MultipartFormData,
    NoRetry,
    PoolConfig,
    RequestBuilder,
    RetryConfig,
    RetryExhaustedFault,
    RetryState,
    StreamingBody,
    TimeoutConfig,
    TimeoutFault,
    TLSConfig,
    TLSFault,
    create_response,
    stream_bytes,
)

# ============================================================================
# Configuration Tests
# ============================================================================


class TestTimeoutConfig:
    """Tests for TimeoutConfig."""

    def test_default_values(self):
        config = TimeoutConfig()
        assert config.total == 30.0
        assert config.connect == 10.0
        assert config.read is None
        assert config.write is None

    def test_fast_factory(self):
        config = TimeoutConfig.fast()
        assert config.total == 5.0
        assert config.connect == 2.0

    def test_slow_factory(self):
        config = TimeoutConfig.slow()
        assert config.total == 300.0
        assert config.connect == 30.0

    def test_no_timeout_factory(self):
        config = TimeoutConfig.no_timeout()
        assert config.total is None
        assert config.connect is None

    def test_negative_timeout_raises(self):
        with pytest.raises(ValueError):
            TimeoutConfig(total=-1.0)


class TestPoolConfig:
    """Tests for PoolConfig."""

    def test_default_values(self):
        config = PoolConfig()
        assert config.max_connections == 100
        assert config.max_connections_per_host == 10


class TestRetryConfig:
    """Tests for RetryConfig."""

    def test_default_values(self):
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.backoff_base == 1.0

    def test_no_retry_factory(self):
        config = RetryConfig.no_retry()
        assert config.max_attempts == 0

    def test_aggressive_factory(self):
        config = RetryConfig.aggressive()
        assert config.max_attempts == 5


class TestHTTPClientConfig:
    """Tests for HTTPClientConfig."""

    def test_default_values(self):
        config = HTTPClientConfig()
        assert config.base_url is None
        assert config.follow_redirects is True
        assert config.max_redirects == 10

    def test_with_base_url(self):
        config = HTTPClientConfig()
        new_config = config.with_base_url("https://api.example.com")
        assert new_config.base_url == "https://api.example.com"
        assert config.base_url is None  # Original unchanged

    def test_with_timeout(self):
        config = HTTPClientConfig()
        new_config = config.with_timeout(total=60.0, connect=15.0)
        assert new_config.timeout.total == 60.0
        assert new_config.timeout.connect == 15.0

    def test_to_dict_and_from_dict(self):
        config = HTTPClientConfig(
            base_url="https://api.example.com",
            follow_redirects=False,
        )
        d = config.to_dict()
        restored = HTTPClientConfig.from_dict(d)
        assert restored.base_url == config.base_url
        assert restored.follow_redirects == config.follow_redirects


class TestTLSConfig:
    """Tests for TLSConfig."""

    def test_default_values(self):
        config = TLSConfig()
        assert config.verify is True


# ============================================================================
# Request Tests
# ============================================================================


class TestHTTPClientRequest:
    """Tests for HTTPClientRequest."""

    def test_basic_request(self):
        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="https://api.example.com/users",
        )
        assert request.method == HTTPMethod.GET
        assert request.url == "https://api.example.com/users"
        assert request.body is None

    def test_request_properties(self):
        request = HTTPClientRequest(
            method=HTTPMethod.POST,
            url="https://api.example.com:8080/users?page=1",
            headers={"Content-Type": "application/json"},
        )
        assert request.host == "api.example.com:8080"
        assert request.path == "/users"
        assert request.scheme == "https"
        assert request.query_string == "page=1"
        assert request.content_type == "application/json"

    def test_request_copy(self):
        request = HTTPClientRequest(
            method=HTTPMethod.GET,
            url="https://example.com",
            headers={"X-Custom": "value"},
        )
        request2 = request.copy(headers={"Authorization": "Bearer token"})
        assert "Authorization" in request2.headers
        assert "X-Custom" not in request2.headers
        assert "X-Custom" in request.headers  # Original unchanged

    def test_has_body(self):
        request_no_body = HTTPClientRequest(method=HTTPMethod.GET, url="http://example.com")
        request_with_body = HTTPClientRequest(method=HTTPMethod.POST, url="http://example.com", body=b"data")
        assert request_no_body.has_body() is False
        assert request_with_body.has_body() is True


class TestRequestBuilder:
    """Tests for RequestBuilder."""

    def test_basic_build(self):
        builder = RequestBuilder(HTTPMethod.GET, "https://example.com")
        request = builder.build()
        assert request.method == HTTPMethod.GET
        assert request.url == "https://example.com"

    def test_fluent_api_with_headers_and_params(self):
        request = (
            RequestBuilder(HTTPMethod.POST, "https://api.example.com/users")
            .header("Authorization", "Bearer token")
            .param("page", "1")
            .json({"name": "John"})
            .build()
        )
        assert request.method == HTTPMethod.POST
        assert "Authorization" in request.headers
        assert "page=1" in request.url
        assert request.body is not None

    def test_builder_with_base_url(self):
        request = RequestBuilder(
            HTTPMethod.GET,
            "/users",
            base_url="https://api.example.com",
        ).build()
        assert request.url == "https://api.example.com/users"


# ============================================================================
# Response Tests
# ============================================================================


class TestHTTPClientResponse:
    """Tests for HTTPClientResponse."""

    @pytest.mark.asyncio
    async def test_basic_response(self):
        response = create_response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=b'{"status": "ok"}',
        )
        assert response.status_code == 200
        assert response.is_success is True
        assert response.ok is True

    @pytest.mark.asyncio
    async def test_json_parsing(self):
        response = create_response(
            status_code=200,
            headers={"Content-Type": "application/json"},
            body=b'{"name": "John", "age": 30}',
        )
        data = await response.json()
        assert data["name"] == "John"
        assert data["age"] == 30

    @pytest.mark.asyncio
    async def test_text_parsing(self):
        response = create_response(
            status_code=200,
            headers={"Content-Type": "text/plain"},
            body=b"Hello, World!",
        )
        text = await response.text()
        assert text == "Hello, World!"

    @pytest.mark.asyncio
    async def test_error_response(self):
        response = create_response(status_code=404, body=b"Not Found")
        assert response.is_error is True
        assert response.is_client_error is True
        assert response.is_server_error is False

    @pytest.mark.asyncio
    async def test_redirect_response(self):
        response = create_response(
            status_code=302,
            headers={"Location": "https://example.com/new"},
        )
        assert response.is_redirect is True
        assert response.location == "https://example.com/new"

    def test_status_properties(self):
        ok_response = create_response(status_code=200)
        assert ok_response.is_success is True
        assert ok_response.is_informational is False

        info_response = create_response(status_code=100)
        assert info_response.is_informational is True

        client_error = create_response(status_code=400)
        assert client_error.is_client_error is True

        server_error = create_response(status_code=500)
        assert server_error.is_server_error is True


# ============================================================================
# Cookie Tests
# ============================================================================


class TestCookie:
    """Tests for Cookie."""

    def test_basic_cookie(self):
        cookie = Cookie(name="session", value="abc123", domain="example.com")
        assert cookie.name == "session"
        assert cookie.value == "abc123"

    def test_cookie_expired(self):
        cookie = Cookie(
            name="expired",
            value="value",
            domain="example.com",
            expires=time.time() - 3600,
        )
        assert cookie.is_expired is True

    def test_cookie_not_expired(self):
        cookie = Cookie(
            name="valid",
            value="value",
            domain="example.com",
            expires=time.time() + 3600,
        )
        assert cookie.is_expired is False

    def test_cookie_matches_domain_exact(self):
        cookie = Cookie(name="test", value="value", domain="example.com")
        assert cookie.matches_domain("example.com") is True
        assert cookie.matches_domain("other.com") is False

    def test_cookie_matches_domain_subdomain(self):
        cookie = Cookie(name="test", value="value", domain=".example.com")
        assert cookie.matches_domain("example.com") is True
        assert cookie.matches_domain("www.example.com") is True
        assert cookie.matches_domain("api.example.com") is True
        assert cookie.matches_domain("other.com") is False

    def test_cookie_matches_path(self):
        cookie = Cookie(name="test", value="value", domain="example.com", path="/api")
        assert cookie.matches_path("/api") is True
        assert cookie.matches_path("/api/users") is True
        assert cookie.matches_path("/other") is False

    def test_to_set_cookie(self):
        cookie = Cookie(
            name="session",
            value="abc123",
            domain="example.com",
            path="/",
            secure=True,
            http_only=True,
        )
        header = cookie.to_set_cookie()
        assert "session=abc123" in header
        assert "Secure" in header
        assert "HttpOnly" in header

    def test_from_set_cookie(self):
        header = "session=abc123; Domain=example.com; Path=/; Secure; HttpOnly"
        cookie = Cookie.from_set_cookie(header)
        assert cookie.name == "session"
        assert cookie.value == "abc123"


class TestCookieJar:
    """Tests for CookieJar."""

    def test_set_and_get_cookies(self):
        jar = CookieJar()
        jar.set(Cookie(name="session", value="abc123", domain="example.com"))
        jar.set(Cookie(name="user", value="john", domain="example.com"))

        cookies = jar.get_for_url("https://example.com/")
        assert len(cookies) == 2

    def test_domain_filtering(self):
        jar = CookieJar()
        jar.set(Cookie(name="session", value="abc", domain="example.com"))
        jar.set(Cookie(name="other", value="xyz", domain="other.com"))

        cookies = jar.get_for_url("https://example.com/")
        assert len(cookies) == 1
        assert cookies[0].name == "session"

    def test_path_filtering(self):
        jar = CookieJar()
        jar.set(Cookie(name="api", value="key", domain="example.com", path="/api"))
        jar.set(Cookie(name="web", value="val", domain="example.com", path="/web"))

        api_cookies = jar.get_for_url("https://example.com/api/users")
        assert len(api_cookies) == 1
        assert api_cookies[0].name == "api"

    def test_expired_cookie_not_returned(self):
        jar = CookieJar()
        jar.set(
            Cookie(
                name="expired",
                value="val",
                domain="example.com",
                expires=time.time() - 3600,
            )
        )
        jar.set(Cookie(name="valid", value="val", domain="example.com"))

        cookies = jar.get_for_url("https://example.com/")
        assert len(cookies) == 1
        assert cookies[0].name == "valid"

    def test_get_header(self):
        jar = CookieJar()
        jar.set(Cookie(name="a", value="1", domain="example.com"))
        jar.set(Cookie(name="b", value="2", domain="example.com"))

        header = jar.get_header("https://example.com/")
        assert header is not None
        assert "a=1" in header
        assert "b=2" in header

    def test_clear(self):
        jar = CookieJar()
        jar.set(Cookie(name="session", value="abc", domain="example.com"))
        jar.clear()
        assert len(jar.all()) == 0


# ============================================================================
# Retry Tests
# ============================================================================


class TestRetryState:
    """Tests for RetryState."""

    def test_initial_state(self):
        state = RetryState()
        assert state.attempt == 0
        assert state.last_error is None


class TestExponentialBackoff:
    """Tests for ExponentialBackoff."""

    def test_delay_calculation(self):
        config = RetryConfig(backoff_base=1.0, backoff_multiplier=2.0, backoff_max=60.0)
        strategy = ExponentialBackoff(config)

        state = RetryState(attempt=1)
        delay = strategy.get_delay(state)
        assert delay >= 1.0  # Base delay with possible jitter

    def test_should_retry_on_connection_error(self):
        config = RetryConfig(max_attempts=3)
        strategy = ExponentialBackoff(config)
        state = RetryState(attempt=1)
        request = HTTPClientRequest(method=HTTPMethod.GET, url="http://example.com")

        error = ConnectionFault("Failed")
        should = strategy.should_retry(state, request, None, error)
        assert should is True

    def test_should_not_retry_after_max_attempts(self):
        config = RetryConfig(max_attempts=3)
        strategy = ExponentialBackoff(config)
        state = RetryState(attempt=3)  # Already at max
        request = HTTPClientRequest(method=HTTPMethod.GET, url="http://example.com")

        error = ConnectionFault("Failed")
        should = strategy.should_retry(state, request, None, error)
        assert should is False


class TestConstantBackoff:
    """Tests for ConstantBackoff."""

    def test_constant_delay(self):
        strategy = ConstantBackoff(delay=5.0)

        state = RetryState(attempt=1)
        delay = strategy.get_delay(state)
        assert delay == 5.0

        state2 = RetryState(attempt=5)
        delay2 = strategy.get_delay(state2)
        assert delay2 == 5.0


class TestNoRetry:
    """Tests for NoRetry."""

    def test_no_retry(self):
        strategy = NoRetry()
        state = RetryState()
        request = HTTPClientRequest(method=HTTPMethod.GET, url="http://example.com")

        should = strategy.should_retry(state, request, None, ConnectionFault("Failed"))
        assert should is False


# ============================================================================
# Interceptor Tests
# ============================================================================


class TestInterceptorChain:
    """Tests for InterceptorChain."""

    @pytest.mark.asyncio
    async def test_empty_chain_with_handler(self):
        chain = InterceptorChain([])
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")
        response = create_response(status_code=200)

        async def handler(req):
            return response

        chain.set_handler(handler)
        result = await chain.execute(request)
        assert result.status_code == 200

    @pytest.mark.asyncio
    async def test_header_interceptor(self):
        interceptor = HeaderInterceptor({"X-Custom": "value"})
        chain = InterceptorChain([interceptor])
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")
        response = create_response(status_code=200)

        captured_request = None

        async def handler(req):
            nonlocal captured_request
            captured_request = req
            return response

        chain.set_handler(handler)
        await chain.execute(request)
        assert captured_request.headers.get("X-Custom") == "value"


class TestLoggingInterceptor:
    """Tests for LoggingInterceptor."""

    @pytest.mark.asyncio
    async def test_logging_interceptor(self):
        interceptor = LoggingInterceptor()
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")
        response = create_response(status_code=200)

        async def handler(req):
            return response

        result = await interceptor.intercept(request, handler)
        assert result.status_code == 200


# ============================================================================
# Streaming Tests
# ============================================================================


class TestStreamingBody:
    """Tests for StreamingBody."""

    @pytest.mark.asyncio
    async def test_streaming_iteration(self):
        async def gen():
            yield b"chunk1"
            yield b"chunk2"
            yield b"chunk3"

        body = StreamingBody(gen())
        chunks = []
        async for chunk in body:
            chunks.append(chunk)

        assert len(chunks) == 3
        assert chunks[0] == b"chunk1"


class TestChunkedEncoder:
    """Tests for ChunkedEncoder."""

    @pytest.mark.asyncio
    async def test_chunked_encoding(self):
        async def gen():
            yield b"Hello"
            yield b"World"

        encoder = ChunkedEncoder(gen())
        chunks = []
        async for chunk in encoder:
            chunks.append(chunk)

        assert any(b"5\r\n" in chunk for chunk in chunks)  # Length prefix
        assert chunks[-1] == b"0\r\n\r\n"  # Terminator


class TestChunkedDecoder:
    """Tests for ChunkedDecoder."""

    @pytest.mark.asyncio
    async def test_chunked_decoding(self):
        async def gen():
            yield b"5\r\nHello\r\n"
            yield b"5\r\nWorld\r\n"
            yield b"0\r\n\r\n"

        decoder = ChunkedDecoder(gen())
        chunks = []
        async for chunk in decoder:
            chunks.append(chunk)

        assert b"Hello" in chunks
        assert b"World" in chunks


class TestStreamHelpers:
    """Tests for stream helper functions."""

    @pytest.mark.asyncio
    async def test_stream_bytes(self):
        data = b"Hello, World!"
        body = stream_bytes(data, chunk_size=5)
        chunks = []
        async for chunk in body:
            chunks.append(chunk)

        assert b"".join(chunks) == data


# ============================================================================
# Multipart Tests
# ============================================================================


class TestMultipartFormData:
    """Tests for MultipartFormData."""

    def test_field_creation(self):
        form = MultipartFormData()
        form.field("name", "John")
        form.field("age", "30")

        assert len(form._fields) == 2
        assert form._fields[0].name == "name"
        assert form._fields[0].value == "John"

    def test_file_creation(self):
        form = MultipartFormData()
        form.file("document", "test.txt", b"file content")

        assert len(form._files) == 1
        assert form._files[0].name == "document"
        assert form._files[0].filename == "test.txt"

    def test_content_type(self):
        form = MultipartFormData()
        content_type = form.content_type

        assert "multipart/form-data" in content_type
        assert "boundary=" in content_type

    @pytest.mark.asyncio
    async def test_encode(self):
        form = MultipartFormData()
        form.field("name", "John")

        body = await form.encode()
        assert b"name" in body
        assert b"John" in body


# ============================================================================
# Authentication Tests
# ============================================================================


class TestBasicAuth:
    """Tests for BasicAuth."""

    @pytest.mark.asyncio
    async def test_basic_auth_header(self):
        auth = BasicAuth("username", "password")
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")

        captured_request = None

        async def handler(req):
            nonlocal captured_request
            captured_request = req
            return create_response(status_code=200)

        await auth.intercept(request, handler)
        assert "Basic" in captured_request.headers.get("Authorization", "")


class TestBearerAuth:
    """Tests for BearerAuth."""

    @pytest.mark.asyncio
    async def test_bearer_auth_header(self):
        auth = BearerAuth("my-token")
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")

        captured_request = None

        async def handler(req):
            nonlocal captured_request
            captured_request = req
            return create_response(status_code=200)

        await auth.intercept(request, handler)
        assert "Bearer my-token" in captured_request.headers.get("Authorization", "")


class TestAPIKeyAuth:
    """Tests for APIKeyAuth."""

    @pytest.mark.asyncio
    async def test_api_key_in_header(self):
        auth = APIKeyAuth("my-api-key", header_name="X-API-Key")
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")

        captured_request = None

        async def handler(req):
            nonlocal captured_request
            captured_request = req
            return create_response(status_code=200)

        await auth.intercept(request, handler)
        assert captured_request.headers.get("X-API-Key") == "my-api-key"


# ============================================================================
# Transport Tests
# ============================================================================


class TestMockTransport:
    """Tests for MockTransport."""

    @pytest.mark.asyncio
    async def test_mock_default_response(self):
        transport = MockTransport()
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")
        response = await transport.send(request)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mock_add_response(self):
        transport = MockTransport()
        transport.add_response(
            "GET",
            "https://example.com/users",
            create_response(status_code=200, body=b'{"users": []}'),
        )

        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com/users")
        response = await transport.send(request)

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_mock_records_requests(self):
        transport = MockTransport()
        request = HTTPClientRequest(method=HTTPMethod.GET, url="https://example.com")
        await transport.send(request)

        assert len(transport.requests) == 1
        assert transport.requests[0].url == "https://example.com"


# ============================================================================
# Fault Tests
# ============================================================================


class TestHTTPClientFaults:
    """Tests for HTTP client faults."""

    def test_http_client_fault(self):
        fault = HTTPClientFault("http_client_error", "Something went wrong")
        assert fault.message == "Something went wrong"
        assert fault.domain == HTTP_CLIENT_DOMAIN
        assert fault.code == "http_client_error"

    def test_connection_fault(self):
        fault = ConnectionFault("Connection refused", host="example.com", port=443)
        assert fault.code == "HTTP_CONNECTION_FAILED"
        assert fault.metadata.get("host") == "example.com"
        assert fault.metadata.get("port") == 443

    def test_timeout_fault(self):
        fault = TimeoutFault("HTTP_TIMEOUT", "Request timed out", timeout=30.0)
        assert fault.code == "HTTP_TIMEOUT"
        assert fault.metadata.get("timeout") == 30.0

    def test_tls_fault(self):
        fault = TLSFault("Certificate verification failed")
        assert fault.code == "HTTP_TLS_ERROR"

    def test_fault_retryable(self):
        connection_fault = ConnectionFault("Failed")
        assert connection_fault.retryable is True

    def test_retry_exhausted_fault(self):
        original_error = ConnectionFault("Connection failed")
        fault = RetryExhaustedFault(attempts=3, last_error=original_error)

        assert fault.code == "HTTP_RETRY_EXHAUSTED"
        assert fault.metadata.get("attempts") == 3
        assert fault.retryable is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
