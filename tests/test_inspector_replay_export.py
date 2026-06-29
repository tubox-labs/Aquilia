import pytest

from aquilia import GET, POST, Controller, RequestCtx, Response
from aquilia.inspector.config import InspectorConfig
from aquilia.inspector.export import export_trace_json, import_trace_json
from aquilia.inspector.faults import InspectorExportFault, InspectorReplayFault
from aquilia.inspector.replay import run_replay
from aquilia.inspector.trace import RequestTrace
from aquilia.manifest import AppManifest
from aquilia.testing import TestServer


class SimpleReplayController(Controller):
    @GET("/replay-get")
    async def get_test(self, ctx: RequestCtx):
        return Response.json({"status": "get_ok"})

    @POST("/replay-post")
    async def post_test(self, ctx: RequestCtx):
        return Response.json({"status": "post_ok"})


def make_manifest():
    return AppManifest(
        name="test_replay_app",
        version="0.0.1",
        controllers=["tests.test_inspector_replay_export:SimpleReplayController"],
    )


@pytest.mark.asyncio
async def test_replay_idempotent_happy_path():
    manifest = make_manifest()
    async with TestServer(manifests=[manifest]) as server:
        trace = RequestTrace(
            trace_id="t-get",
            method="GET",
            path="/test_replay_app/replay-get",
            route_pattern=None,
            started_at=100.0,
            started_monotonic=200.0,
        )
        config = InspectorConfig()
        # Should execute successfully
        response = await run_replay(trace, config, server.app, {})
        assert response.status_code == 200
        assert response.json()["status"] == "get_ok"


@pytest.mark.asyncio
async def test_replay_non_idempotent_blocks_without_header():
    manifest = make_manifest()
    async with TestServer(manifests=[manifest]) as server:
        trace = RequestTrace(
            trace_id="t-post",
            method="POST",
            path="/test_replay_app/replay-post",
            route_pattern=None,
            started_at=100.0,
            started_monotonic=200.0,
        )
        config = InspectorConfig()

        # Should raise InspectorReplayFault due to MUTATION_BLOCKED
        with pytest.raises(InspectorReplayFault) as exc_info:
            await run_replay(trace, config, server.app, {})
        assert exc_info.value.code == "RESOLUTION_MUTATION_BLOCKED"


@pytest.mark.asyncio
async def test_replay_non_idempotent_allows_with_header():
    manifest = make_manifest()
    async with TestServer(manifests=[manifest]) as server:
        trace = RequestTrace(
            trace_id="t-post-allowed",
            method="POST",
            path="/test_replay_app/replay-post",
            route_pattern=None,
            started_at=100.0,
            started_monotonic=200.0,
        )
        config = InspectorConfig()

        response = await run_replay(trace, config, server.app, {"x-aquilia-allow-replay-mutation": "true"})
        assert response.status_code == 200
        assert response.json()["status"] == "post_ok"


def test_export_import_round_trip():
    trace = RequestTrace(
        trace_id="t-roundtrip",
        method="GET",
        path="/api/test",
        route_pattern="/api/test",
        started_at=12345.67,
        started_monotonic=100.0,
    )
    trace.add_span(lane="database", label="SELECT *", start_offset_ms=5.0, duration_ms=10.0)

    # Export
    json_str = export_trace_json(trace)
    assert "t-roundtrip" in json_str

    # Import
    imported = import_trace_json(json_str)
    assert imported.trace_id == "t-roundtrip"
    assert imported.method == "GET"
    assert imported.path == "/api/test"
    assert len(imported.spans) == 1
    assert imported.spans[0].label == "SELECT *"
    assert imported.spans[0].duration_ms == 10.0


def test_import_missing_trace_id_fails():
    with pytest.raises(InspectorExportFault) as exc_info:
        import_trace_json('{"method": "GET"}')
    assert exc_info.value.code == "IMPORT_INVALID_TRACE"
