from __future__ import annotations

import json
from types import SimpleNamespace

from aquilia.faults import Fault, FaultDomain, Severity
from aquilia.middleware import ExceptionMiddleware


class _ValidationFault(Fault):
    domain = FaultDomain.custom("test_validation", "Test validation faults")
    severity = Severity.INFO
    code = "TEST_VALIDATION_ERROR"

    def __init__(self):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message="Validation failed",
            metadata={"errors": {"password": ["too short"]}, "_internal": "redact-me"},
            public=True,
            retryable=False,
        )


def _decode_json_response(resp) -> dict:
    raw = resp._content
    if isinstance(raw, (bytes, bytearray)):
        return json.loads(raw.decode("utf-8"))
    if isinstance(raw, str):
        return json.loads(raw)
    return json.loads(str(raw))


async def test_exception_middleware_includes_fault_metadata_for_4xx():
    mw = ExceptionMiddleware(debug=False)

    class DummyReq:
        def __init__(self):
            self.headers = {}
            self.state = {}
            self.scope = {"headers": []}

    req = DummyReq()
    ctx = SimpleNamespace()

    async def _next(_request, _ctx):
        raise _ValidationFault()

    resp = await mw(req, ctx, _next)
    body = _decode_json_response(resp)

    assert resp.status == 400
    assert body["error"]["code"] == "TEST_VALIDATION_ERROR"
    assert body["error"]["metadata"]["errors"]["password"] == ["too short"]
    assert "_internal" not in body["error"]["metadata"]
