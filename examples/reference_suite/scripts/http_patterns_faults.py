from __future__ import annotations

import logging

from aquilia.faults.engine import FaultEngine
from aquilia.faults.core import Escalate
from aquilia.http import AsyncHTTPClient, MockTransport
from aquilia.patterns import PatternMatcher, compile_pattern


async def run() -> dict:
    transport = MockTransport()
    transport.add_json_response("GET", "https://api.example.test/users/42", {"id": 42, "name": "Ada"})
    async with AsyncHTTPClient(transport=transport) as client:
        response = await client.get("https://api.example.test/users/42")
        user = await response.json()

    matcher = PatternMatcher()
    matcher.add_pattern(compile_pattern("/users/<id:int>"))
    matched = await matcher.match("/users/42")

    faults_seen = []
    fault_logger = logging.getLogger("examples.reference_suite.faults")
    fault_logger.disabled = True
    engine = FaultEngine(logger=fault_logger, debug=True)
    engine.on_fault(lambda ctx: faults_seen.append(ctx.fault.code))
    result = await engine.process(ValueError("boom"), app="reference", route="/users/<id:int>", request_id="req-1")

    return {
        "http_user": user,
        "http_requests": len(transport.requests),
        "pattern_params": matched.params if matched else {},
        "fault_seen": faults_seen[0],
        "fault_escalated": isinstance(result, Escalate),
    }
