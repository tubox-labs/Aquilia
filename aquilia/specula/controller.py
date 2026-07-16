"""
SpeculaController — all observatory routes.

Handlers follow Aquilia's injected-route convention:
``async def handler(self, request, ctx, **path_params)`` — bound methods are
registered as ``CompiledRoute.handler`` by ``aquilia.server`` at startup, with
paths taken from :class:`SpeculaConfig` (never hardcoded).
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from aquilia.response import Response
from aquilia.sse import SSEEvent, SSEResponse

from .config import SpeculaConfig
from .faults import VersionNotFoundFault
from .service import SpeculaService
from .ui.renderer import SpeculaRenderer

_SCHEMA_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,127}$")


class SpeculaController:
    """
    Aquilia Specula API Observatory controller.

    Routes (paths from SpeculaConfig):
        GET  json_path              OpenAPI 3.1.0 spec (JSON)
        GET  yaml_path              OpenAPI 3.1.0 spec (YAML)
        GET  ui_path                Specula Observatory UI
        GET  stream_path            SSE: live spec change events
        GET  versions_path          All versioned specs summary
        GET  versions_path/{ver}    Spec for a specific version
        GET  schemas_path           Component schemas catalogue
        GET  schemas_path/{name}    Single schema by name
        GET  routes_path            Enriched route catalogue
        POST mock_path/{path}       Mock server: example response
        GET  export_path/postman    Postman Collection v2.1
        GET  export_path/insomnia   Insomnia v4 collection
    """

    tags = ["_specula"]

    def __init__(self, service: SpeculaService, config: SpeculaConfig):
        self.service = service
        self.config = config
        self._renderer = SpeculaRenderer(config)

    # ── Spec endpoints ─────────────────────────────────────────────────

    async def spec_json(self, request: Any, ctx: Any) -> Response:
        """Serve the OpenAPI 3.1.0 spec as JSON."""
        version = ctx.query_param("version") or None
        spec_json = await self.service.get_spec_json(version)
        return Response(
            content=spec_json.encode(),
            status=200,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Cache-Control": f"public, max-age={self.config.spec_cache_ttl}",
                "Access-Control-Allow-Origin": "*",
                "X-Specula-Version": "2.0.0",
            },
        )

    async def spec_yaml(self, request: Any, ctx: Any) -> Response:
        """Serve the OpenAPI 3.1.0 spec as YAML."""
        version = ctx.query_param("version") or None
        spec_yaml = await self.service.get_spec_yaml(version)
        return Response(
            content=spec_yaml.encode(),
            status=200,
            headers={
                "Content-Type": "application/yaml; charset=utf-8",
                "Cache-Control": f"public, max-age={self.config.spec_cache_ttl}",
                "Access-Control-Allow-Origin": "*",
            },
        )

    async def observatory_ui(self, request: Any, ctx: Any) -> Response:
        """Serve the Specula Observatory UI (pre-rendered, cached)."""
        return Response.html(self._renderer.render())

    async def spec_stream(self, request: Any, ctx: Any) -> SSEResponse:
        """SSE stream of live spec invalidation events (dev hot-reload)."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=32)
        self.service.subscribe_sse(queue)
        service = self.service

        async def _events():
            try:
                yield SSEEvent(event="connected", data='{"status":"connected","specula":"2.0.0"}')
                while True:
                    try:
                        payload = await asyncio.wait_for(queue.get(), timeout=25.0)
                        yield SSEEvent(event=payload.get("type", "update"), data=json.dumps(payload))
                    except asyncio.TimeoutError:
                        yield SSEEvent(event="ping", data='{"status":"alive"}')
            finally:
                service.unsubscribe_sse(queue)

        return SSEResponse(_events())

    # ── Version endpoints ──────────────────────────────────────────────

    async def versions_index(self, request: Any, ctx: Any) -> Response:
        """Summary of all declared API versions with spec links."""
        versions = self.service.declared_versions()
        all_versions = [*versions, "latest"]
        return Response.json(
            {
                "versions": all_versions,
                "specs": {v: f"{self.config.json_path}?version={v}" for v in all_versions},
            }
        )

    async def version_spec(self, request: Any, ctx: Any, ver: str = "") -> Response:
        """OpenAPI spec filtered to a specific API version."""
        try:
            spec_json = await self.service.get_spec_json(ver)
        except VersionNotFoundFault:
            raise
        except Exception as exc:
            raise VersionNotFoundFault(
                f"API version '{ver}' not found in the version graph",
                detail={"version": ver},
            ) from exc
        return Response(
            content=spec_json.encode(),
            status=200,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )

    # ── Schema explorer ────────────────────────────────────────────────

    async def schemas_index(self, request: Any, ctx: Any) -> Response:
        """Catalogue of all registered component schemas."""
        spec = await self.service.get_spec()
        schemas = spec.get("components", {}).get("schemas", {})
        return Response.json({"count": len(schemas), "schemas": list(schemas.keys())})

    async def schema_detail(self, request: Any, ctx: Any, name: str = "") -> Response:
        """Single component schema by name."""
        if not _SCHEMA_NAME_RE.match(name):
            return Response.json({"error": "Invalid schema name"}, status=400)
        spec = await self.service.get_spec()
        schema = spec.get("components", {}).get("schemas", {}).get(name)
        if schema is None:
            return Response.json({"error": f"Schema '{name}' not found"}, status=404)
        return Response.json(schema)

    # ── Route catalogue ────────────────────────────────────────────────

    async def routes_index(self, request: Any, ctx: Any) -> Response:
        """Enriched route catalogue: module, effects, pipeline, version."""
        from .introspect.routes import enrich_routes

        spec = await self.service.get_spec()
        routes = enrich_routes(spec)
        return Response.json({"count": len(routes), "routes": routes})

    # ── Mock server ────────────────────────────────────────────────────

    async def mock_endpoint(self, request: Any, ctx: Any, path: str = "") -> Response:
        """
        Return a realistic example response for any documented path.
        Body: ``{"method": "GET"}``. Disabled by default.
        """
        if not self.config.mock_server_enabled:
            return Response.json({"error": "Mock server is disabled"}, status=404)

        try:
            body = await ctx.json() or {}
        except Exception:  # noqa: BLE001 — tolerate empty/invalid body
            body = {}
        method = str(body.get("method") or "GET").lower()
        spec = await self.service.get_spec()

        # Path traversal guard
        clean = "/".join(seg for seg in path.split("/") if seg not in ("..", ""))
        norm = f"/{clean}"
        paths = spec.get("paths", {})
        path_item = paths.get(norm) or paths.get(path) or {}
        operation = path_item.get(method, {})
        if not operation:
            return Response.json({"error": f"No operation: {method.upper()} {norm}"}, status=404)

        example = _extract_or_synthesize_example(operation, spec, self.config.mock_max_depth)
        return Response.json(example)

    # ── Export endpoints ───────────────────────────────────────────────

    async def export_postman(self, request: Any, ctx: Any) -> Response:
        """Export the current spec as a Postman Collection v2.1 JSON file."""
        spec = await self.service.get_spec()
        collection = _build_postman_collection(spec, self.config)
        filename = f"{self.config.title.lower().replace(' ', '_')}_postman.json"
        return Response(
            content=json.dumps(collection, indent=2).encode(),
            status=200,
            headers={
                "Content-Type": "application/json",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )

    async def export_insomnia(self, request: Any, ctx: Any) -> Response:
        """Export the current spec as an Insomnia v4 collection."""
        spec = await self.service.get_spec()
        collection = _build_insomnia_collection(spec, self.config)
        filename = f"{self.config.title.lower().replace(' ', '_')}_insomnia.json"
        return Response(
            content=json.dumps(collection, indent=2).encode(),
            status=200,
            headers={
                "Content-Type": "application/json",
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )


# ── Module-level helpers ───────────────────────────────────────────────


def _resolve_ref(spec: dict, ref: str) -> dict:
    """Resolve ``#/components/schemas/Name`` against the spec."""
    if not ref.startswith("#/components/schemas/"):
        return {}
    name = ref.rsplit("/", 1)[-1]
    return spec.get("components", {}).get("schemas", {}).get(name, {})


_STRING_EXAMPLES: dict[str, str] = {
    "email": "user@example.com",
    "uuid": "550e8400-e29b-41d4-a716-446655440000",
    "uri": "https://example.com",
    "url": "https://example.com",
    "date-time": "2025-01-15T10:30:00Z",
    "date": "2025-01-15",
    "time": "10:30:00",
    "duration": "PT1H",
    "ip": "192.0.2.1",
    "binary": "ZXhhbXBsZQ==",
    "decimal": "9.99",
}


def _synthesize(schema: dict, spec: dict, depth: int, field_name: str = "") -> Any:
    """Synthesize a plausible example from a JSON Schema fragment."""
    if depth < 0 or not isinstance(schema, dict):
        return None

    if "$ref" in schema:
        return _synthesize(_resolve_ref(spec, schema["$ref"]), spec, depth - 1, field_name)

    if "example" in schema:
        return schema["example"]
    examples = schema.get("examples")
    if isinstance(examples, dict) and examples:
        first = next(iter(examples.values()))
        return first.get("value", first) if isinstance(first, dict) else first
    if isinstance(examples, list) and examples:
        return examples[0]

    for combinator in ("oneOf", "anyOf"):
        options = schema.get(combinator)
        if options:
            non_null = [o for o in options if o.get("type") != "null"] or options
            return _synthesize(non_null[0], spec, depth - 1, field_name)

    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]

    schema_type = schema.get("type")
    if schema_type == "string":
        fmt = schema.get("format", "")
        if fmt in _STRING_EXAMPLES:
            return _STRING_EXAMPLES[fmt]
        lower = field_name.lower()
        for hint, value in _STRING_EXAMPLES.items():
            if hint in lower:
                return value
        return "example_string"
    if schema_type == "integer":
        return 42
    if schema_type == "number":
        return 3.14
    if schema_type == "boolean":
        return True
    if schema_type == "null":
        return None
    if schema_type == "array":
        item = _synthesize(schema.get("items", {}), spec, depth - 1, field_name)
        return [item] if item is not None else []
    if schema_type == "object" or "properties" in schema:
        return {key: _synthesize(prop, spec, depth - 1, key) for key, prop in schema.get("properties", {}).items()}
    return {}


def _extract_or_synthesize_example(operation: dict, spec: dict, max_depth: int) -> Any:
    """
    Find the first 200/201/202 response example, or synthesize one by
    walking the response schema (recursion capped at ``max_depth``).
    """
    responses = operation.get("responses", {})
    for status in ("200", "201", "202"):
        response = responses.get(status)
        if not response:
            continue
        content = response.get("content", {}).get("application/json", {})
        examples = content.get("examples")
        if isinstance(examples, dict) and examples:
            first = next(iter(examples.values()))
            return first.get("value", first) if isinstance(first, dict) else first
        schema = content.get("schema", {})
        if "example" in schema:
            return schema["example"]
        return _synthesize(schema, spec, max_depth)
    return {"message": "No 2xx response documented for this operation"}


def _build_postman_collection(spec: dict, config: SpeculaConfig) -> dict:
    """Convert an OpenAPI 3.1.0 spec to a Postman Collection v2.1."""
    folders: dict[str, list[dict]] = {}

    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            tag = (operation.get("tags") or ["General"])[0]
            # {param} → {{param}} Postman variables
            postman_path = re.sub(r"\{(\w+)\}", r"{{\1}}", path)
            segments = [s for s in postman_path.split("/") if s]
            item: dict[str, Any] = {
                "name": operation.get("operationId") or f"{method.upper()} {path}",
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": f"{{{{base_url}}}}{postman_path}",
                        "host": ["{{base_url}}"],
                        "path": segments,
                    },
                    "description": operation.get("summary", ""),
                },
            }
            body = operation.get("requestBody", {})
            json_content = body.get("content", {}).get("application/json")
            if json_content is not None:
                example = _synthesize(json_content.get("schema", {}), spec, config.mock_max_depth)
                item["request"]["header"].append({"key": "Content-Type", "value": "application/json"})
                item["request"]["body"] = {
                    "mode": "raw",
                    "raw": json.dumps(example, indent=2, default=str),
                }
            folders.setdefault(tag, []).append(item)

    return {
        "info": {
            "name": config.title,
            "description": config.description,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{access_token}}", "type": "string"}],
        },
        "variable": [
            {"key": "base_url", "value": "http://localhost:8000"},
            {"key": "access_token", "value": ""},
        ],
        "item": [{"name": tag, "item": items} for tag, items in sorted(folders.items())],
    }


def _build_insomnia_collection(spec: dict, config: SpeculaConfig) -> dict:
    """Convert an OpenAPI 3.1.0 spec to the Insomnia v4 export format."""
    resources: list[dict[str, Any]] = [
        {
            "_id": "wrk_specula",
            "_type": "workspace",
            "name": config.title,
            "description": config.description,
            "scope": "collection",
        },
        {
            "_id": "env_specula",
            "_type": "environment",
            "parentId": "wrk_specula",
            "name": "Base Environment",
            "data": {"base_url": "http://localhost:8000"},
        },
    ]

    counter = 0
    for path, path_item in spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.startswith("x-") or not isinstance(operation, dict):
                continue
            counter += 1
            request: dict[str, Any] = {
                "_id": f"req_specula_{counter}",
                "_type": "request",
                "parentId": "wrk_specula",
                "name": operation.get("operationId") or f"{method.upper()} {path}",
                "method": method.upper(),
                "url": "{{ _.base_url }}" + path,
                "description": operation.get("summary", ""),
                "headers": [],
            }
            body = operation.get("requestBody", {})
            json_content = body.get("content", {}).get("application/json")
            if json_content is not None:
                example = _synthesize(json_content.get("schema", {}), spec, config.mock_max_depth)
                request["body"] = {
                    "mimeType": "application/json",
                    "text": json.dumps(example, indent=2, default=str),
                }
                request["headers"].append({"name": "Content-Type", "value": "application/json"})
            resources.append(request)

    return {
        "_type": "export",
        "__export_format": 4,
        "__export_source": "aquilia.specula",
        "resources": resources,
    }
