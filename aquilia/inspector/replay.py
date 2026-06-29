from typing import Any

from aquilia.testing import TestClient

from .config import InspectorConfig
from .faults import InspectorReplayFault
from .trace import RequestTrace


async def run_replay(trace: RequestTrace, config: InspectorConfig, app: Any, headers: dict[str, str]) -> Any:
    if not config.replay_enabled:
        raise InspectorReplayFault(
            code="RESOLUTION_REPLAY_DISABLED",
            message="Replay is disabled in configuration.",
            public=True,
        )

    # Mutation safeguard
    if trace.method not in ("GET", "HEAD", "OPTIONS"):
        allow_mutation = False
        for k, v in headers.items():
            if k.lower() == "x-aquilia-allow-replay-mutation" and v.lower() == "true":
                allow_mutation = True
                break
        if not allow_mutation:
            raise InspectorReplayFault(
                code="RESOLUTION_MUTATION_BLOCKED",
                message="Non-idempotent replay requires 'X-Aquilia-Allow-Replay-Mutation: true' header.",
                public=True,
            )

    # Build headers
    req_headers = {}
    for k, v in trace.request_headers.items():
        req_headers[k] = v
    for k, v in headers.items():
        req_headers[k] = v

    client = TestClient(app, raise_server_exceptions=False)

    body = trace.request_body_preview.encode("utf-8") if trace.request_body_preview else None

    path = trace.path
    if trace.query_params:
        from urllib.parse import urlencode

        flat_q = []
        for k, vals in trace.query_params.items():
            for v in vals:
                flat_q.append((k, v))
        if flat_q:
            path = f"{path}?{urlencode(flat_q)}"

    response = await client._request(
        method=trace.method,
        path=path,
        headers=req_headers,
        body=body,
    )
    return response
