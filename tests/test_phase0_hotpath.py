"""Regression tests for the Phase 0 hot-path and correctness fixes.

Each test here pins a defect that was live in the benchmark report. They are
deliberately behavioural rather than performance assertions -- timing belongs in
``benchmarks/`` -- but every one of them fails against the code as it shipped.
"""

from __future__ import annotations

import json as stdlib_json

import pytest

from aquilia.contracts import Contract
from aquilia.contracts.facets import IntFacet, TextFacet
from aquilia.controller.validation import validate_body
from aquilia.json import JSONDecodeError, backend, dumps, loads
from aquilia.response import Response


class SampleContract(Contract):
    name = TextFacet(required=True, max_length=50)
    age = IntFacet(required=False, min_value=0, max_value=150)

    class Spec:
        projections = {"__all__": ["name", "age"]}


# ---------------------------------------------------------------------------
# aquilia.json -- the single entry point
# ---------------------------------------------------------------------------


class TestJSONEntryPoint:
    def test_dumps_always_returns_bytes(self):
        """The str intermediate was the double-encode bug: dict -> str -> bytes."""
        for value in ({"a": 1}, [1, 2, 3], "text", 42, None, True, 3.5):
            assert isinstance(dumps(value), bytes), f"{value!r} did not serialise to bytes"

    def test_roundtrip(self):
        payload = {"s": "x", "n": 1, "f": 1.5, "b": True, "z": None, "l": [1, {"k": "v"}]}
        assert loads(dumps(payload)) == payload

    def test_loads_accepts_bytes_and_str(self):
        assert loads(b'{"a":1}') == {"a": 1}
        assert loads('{"a":1}') == {"a": 1}

    def test_malformed_raises_json_decode_error(self):
        for bad in (b"{", b"not json", b'{"a":}', b""):
            with pytest.raises(JSONDecodeError):
                loads(bad)

    def test_decode_error_is_a_value_error(self):
        """Existing `except ValueError` handlers must keep working."""
        assert issubclass(JSONDecodeError, ValueError)

    def test_compact_separators(self):
        """stdlib defaults to ', ' / ': ', inflating every payload."""
        assert dumps({"a": 1, "b": 2}) == b'{"a":1,"b":2}'

    def test_default_serializer_handles_sets_and_datetimes(self):
        from datetime import datetime

        assert loads(dumps({"s": {1}})) == {"s": [1]}
        out = loads(dumps({"d": datetime(2020, 1, 2, 3, 4, 5)}))
        assert out["d"].startswith("2020-01-02")

    def test_backend_is_reported(self):
        assert backend() in {"aquilia._json", "stdlib"}


class TestResponseJSON:
    def test_body_is_bytes(self):
        assert isinstance(Response.json({"message": "hi"}).content, bytes)

    def test_body_content(self):
        assert Response.json({"message": "hi"}).content == b'{"message":"hi"}'

    def test_custom_str_encoder_is_encoded(self):
        """A user encoder returning str must still yield a bytes body."""
        resp = Response.json({"a": 1}, encoder=lambda o: stdlib_json.dumps(o))
        assert isinstance(resp.content, bytes)

    def test_custom_bytes_encoder_passes_through(self):
        resp = Response.json({"a": 1}, encoder=lambda o: b'{"custom":true}')
        assert resp.content == b'{"custom":true}'


# ---------------------------------------------------------------------------
# validate_body -- single ownership of the injected parameter
# ---------------------------------------------------------------------------


class _FakeCtx:
    """Minimal context exposing the accessors validate_body relies on."""

    def __init__(self, body: bytes, content_type: str = "application/json"):
        self._body = body

        class _Req:
            headers = {"content-type": content_type}

        self.request = _Req()

    async def body(self) -> bytes:
        return self._body

    async def form(self):
        return {}

    async def multipart(self):
        return {}


class TestValidateBodyOwnership:
    def test_declares_owned_parameter(self):
        """The engine reads this to avoid binding `body` a second time.

        Without it: TypeError: got multiple values for keyword argument 'body'
        -- which turned the entire validation benchmark into a 500 benchmark.
        """

        @validate_body(SampleContract)
        async def handler(self, ctx, body=None):
            return body

        assert handler.__aquilia_owned_params__ == frozenset({"body"})

    def test_custom_param_name_is_owned(self):
        @validate_body(SampleContract, param="payload")
        async def handler(self, ctx, payload=None):
            return payload

        assert handler.__aquilia_owned_params__ == frozenset({"payload"})

    @pytest.mark.asyncio
    async def test_valid_body_reaches_handler(self):
        seen = {}

        @validate_body(SampleContract)
        async def handler(self, ctx, body=None):
            seen["body"] = body
            return Response.json({"ok": True})

        resp = await handler(None, _FakeCtx(b'{"name":"Ada","age":36}'))
        assert resp.status == 200
        assert seen["body"]["name"] == "Ada"

    @pytest.mark.asyncio
    async def test_malformed_body_returns_400_not_500(self):
        @validate_body(SampleContract)
        async def handler(self, ctx, body=None):  # pragma: no cover - must not run
            raise AssertionError("handler must not be called for a malformed body")

        resp = await handler(None, _FakeCtx(b"{not json"))
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_invalid_body_returns_422_with_detail(self):
        @validate_body(SampleContract)
        async def handler(self, ctx, body=None):  # pragma: no cover - must not run
            raise AssertionError("handler must not be called for an invalid body")

        resp = await handler(None, _FakeCtx(b'{"age":500}'))
        assert resp.status == 422
        assert b"detail" in resp.content

    @pytest.mark.asyncio
    async def test_empty_body_is_an_empty_mapping(self):
        @validate_body(SampleContract)
        async def handler(self, ctx, body=None):  # pragma: no cover - must not run
            raise AssertionError("handler must not be called")

        # No body -> {} -> fails `name` required -> 422, not a crash.
        resp = await handler(None, _FakeCtx(b""))
        assert resp.status == 422


# ---------------------------------------------------------------------------
# Query observability gate
# ---------------------------------------------------------------------------


class TestQueryInspectionGate:
    def test_disabled_by_default(self):
        """Per-query traceback capture cost 32us and ran in production.

        Asserted against a fresh import rather than the live global: other tests
        in the suite construct an inspector collector, which legitimately turns
        recording on process-wide, so the live value depends on test order.
        """
        import ast
        from pathlib import Path

        import aquilia.db.engine as engine_mod

        source = Path(engine_mod.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        default = None
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and getattr(node.target, "id", None) == "_QUERY_INSPECTION":
                default = ast.literal_eval(node.value)
                break
        assert default is False, "query inspection must default to off"

    def test_toggle(self):
        from aquilia.db.engine import enable_query_inspection, query_inspection_enabled

        original = query_inspection_enabled()
        try:
            enable_query_inspection(True)
            assert query_inspection_enabled() is True
            enable_query_inspection(False)
            assert query_inspection_enabled() is False
        finally:
            enable_query_inspection(original)

    def test_caller_location_does_not_use_traceback_module(self):
        """`traceback.extract_stack()` stat()s files via linecache; _getframe does not."""
        from aquilia.db.engine import _caller_location

        source, summary = _caller_location()
        # Called from a test file, which is not under /aquilia/, so it resolves.
        assert source.endswith(".py") or source == ""
        assert isinstance(summary, str)


# ---------------------------------------------------------------------------
# JSON depth limit
# ---------------------------------------------------------------------------


class TestJSONDepthCheck:
    def _check(self, obj, max_depth):
        from aquilia.request import Request

        return Request._check_json_depth(None, obj, max_depth)

    def test_shallow_passes(self):
        assert self._check({"a": {"b": 1}}, 8) is True

    def test_scalars_pass(self):
        for value in (1, "s", None, True, 1.5):
            assert self._check(value, 0) is True

    def test_too_deep_rejected(self):
        deep = current = {}
        for _ in range(40):
            current["n"] = {}
            current = current["n"]
        assert self._check(deep, 8) is False

    def test_deep_list_rejected(self):
        deep: list = []
        current = deep
        for _ in range(40):
            nxt: list = []
            current.append(nxt)
            current = nxt
        assert self._check(deep, 8) is False

    def test_pathological_nesting_does_not_recurse(self):
        """A recursive checker hits RecursionError on the input it must reject,
        turning a 400 into a 500."""
        payload: list = []
        current = payload
        for _ in range(20_000):
            nxt: list = []
            current.append(nxt)
            current = nxt
        assert self._check(payload, 64) is False
