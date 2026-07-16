"""
SpeculaBuilder — the OpenAPI 3.1.0 specification engine for Aquilia.
"""

from __future__ import annotations

import inspect
import logging
import re
from dataclasses import dataclass, field
from typing import Any, get_args, get_origin

from aquilia.controller.compiler import CompiledRoute
from aquilia.controller.router import ControllerRouter
from aquilia.patterns.openapi import generate_openapi_params, generate_openapi_path

from ..config import SpeculaConfig
from .fault import aquilia_error_schema, aquilia_validation_error_schema
from .standard import STANDARD_SCHEMAS
from .types import python_type_to_schema

logger = logging.getLogger("aquilia.specula.builder")

_BODY_METHODS = {"POST", "PUT", "PATCH"}

_STATUS_DESCRIPTIONS: dict[int, str] = {
    200: "Successful response",
    201: "Resource created",
    202: "Accepted for processing",
    204: "No content",
    301: "Moved permanently",
    302: "Found (redirect)",
    400: "Bad request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not found",
    409: "Conflict",
    422: "Unprocessable entity",
    429: "Too many requests",
    500: "Internal server error",
}

_ERROR_REF = {"$ref": "#/components/schemas/AquiliaError"}
_VALIDATION_REF = {"$ref": "#/components/schemas/AquiliaValidationError"}


@dataclass
class ParsedDocstring:
    """Parsed handler docstring with structured sections."""

    summary: str = ""
    description: str = ""
    params: dict[str, str] = field(default_factory=dict)
    returns: str = ""
    raises: list[dict[str, str]] = field(default_factory=list)
    body_description: str | None = None


def _parse_docstring(docstring: str) -> ParsedDocstring:
    """Parse a Google-style docstring into structured sections."""
    result = ParsedDocstring()
    if not docstring:
        return result

    lines = docstring.split("\n")
    for line in lines:
        stripped = line.strip()
        if stripped:
            result.summary = stripped
            break

    in_description = False
    description_lines: list[str] = []
    current_section: str | None = None
    current_key: str | None = None

    for line in lines:
        stripped = line.strip()
        if not in_description and current_section is None and stripped == result.summary:
            continue

        lower = stripped.lower()
        if lower.startswith(("args:", "params:", "parameters:")):
            current_section = "params"
            continue
        if lower.startswith(("returns:", "return:")):
            current_section = "returns"
            result.returns = stripped.split(":", 1)[1].strip()
            continue
        if lower.startswith(("raises:", "raise:")):
            current_section = "raises"
            continue
        if lower.startswith(("body:", "request body:")):
            current_section = "body"
            result.body_description = stripped.split(":", 1)[1].strip()
            continue

        if current_section == "params":
            match = re.match(r"^\s*(\w+)\s*(?:\([^)]*\))?\s*:\s*(.*)", stripped)
            if match:
                result.params[match.group(1)] = match.group(2).strip()
                current_key = match.group(1)
            elif current_key and stripped:
                result.params[current_key] += " " + stripped
        elif current_section == "raises":
            match = re.match(r"^\s*(\w+)\s*(?:\((\d+)\))?\s*:\s*(.*)", stripped)
            if match:
                result.raises.append(
                    {
                        "exception": match.group(1),
                        "status": match.group(2) or "",
                        "description": match.group(3).strip(),
                    }
                )
        elif current_section is None:
            if not stripped:
                if result.summary:
                    in_description = True
            elif in_description:
                description_lines.append(stripped)

    result.description = "\n".join(description_lines).strip()
    return result


def _is_contract(obj: Any) -> bool:
    """True if obj is an Aquilia Contract class."""
    try:
        from aquilia.contracts import Contract

        return isinstance(obj, type) and issubclass(obj, Contract)
    except Exception:  # noqa: BLE001 — contracts subsystem optional at runtime
        return False


def _is_model(obj: Any) -> bool:
    """True if obj is an Aquilia ORM Model class."""
    return isinstance(obj, type) and isinstance(getattr(obj, "_fields", None), dict)


def _node_name(node: Any) -> str:
    """Class name for a pipeline node (class ref, instance, or function)."""
    if isinstance(node, type):
        return node.__name__
    if inspect.isfunction(node) or inspect.ismethod(node):
        return node.__name__
    return type(node).__name__


class SpeculaBuilder:
    """
    Production-grade OpenAPI 3.1.0 specification engine for Aquilia.

    - Full 3.1.0 compliance: ``oneOf`` for optionals, webhooks, no ``nullable``.
    - Multi-strategy schema resolution: Contract → Facet schema, ORM Model →
      field schema, Python type → JSON Schema.
    - Vendor extensions: ``x-specula-effects``, ``x-specula-pipeline``,
      ``x-specula-module``, ``x-specula-version``.
    - Fault-aware error responses from docstring ``Raises:`` sections.
    - WebSocket route annotation (``x-specula-websocket: true``).
    - Tag groups (``x-tagGroups``) for ReDoc compat + the Specula UI.
    """

    def __init__(self, config: SpeculaConfig):
        self.config = config
        self._schemas: dict[str, dict] = {}
        self._path_items: dict[str, dict] = {}
        self._security_schemes: dict[str, dict] = {}
        self._tags: list[dict] = []
        self._tag_names: set[str] = set()

    # ── Public API ─────────────────────────────────────────────────────

    def build(self, router: ControllerRouter, routes: list[CompiledRoute] | None = None) -> dict[str, Any]:
        """
        Build the complete OpenAPI 3.1.0 spec dict.

        Idempotent — resets all accumulators before generation.

        Args:
            router: The compiled controller router.
            routes: Optional pre-filtered route list (used by the
                versioned builder); defaults to all routes.
        """
        self._schemas = {}
        self._path_items = {}
        self._security_schemes = {}
        self._tags = []
        self._tag_names = set()

        if routes is None:
            routes = router.get_routes_full()

        # Phase 1: security schemes across all routes
        if self.config.detect_security:
            self._detect_all_security_schemes(routes)

        # Phase 2: standard Aquilia schemas
        self._schemas["AquiliaError"] = aquilia_error_schema()
        self._schemas["AquiliaValidationError"] = aquilia_validation_error_schema()
        for name, schema in STANDARD_SCHEMAS.items():
            self._schemas.setdefault(name, schema)

        # Phase 3: routes → path items
        for route in routes:
            try:
                self._process_route(route)
            except Exception as exc:  # noqa: BLE001 — one bad route must not kill the spec
                logger.warning("Specula: skipping route %s %s: %s", route.http_method, route.full_path, exc)

        # Phase 4: response_model / response_contract schemas
        for route in routes:
            self._register_response_schema(route)

        # Phase 5: extra security schemes from config
        self._security_schemes.update(self.config.extra_security_schemes)

        return self._assemble_spec()

    # ── Route processing ───────────────────────────────────────────────

    def _specula_paths(self) -> set[str]:
        cfg = self.config
        return {
            cfg.ui_path,
            cfg.json_path,
            cfg.yaml_path,
            cfg.stream_path,
            cfg.versions_path,
            cfg.schemas_path,
            cfg.routes_path,
            cfg.export_path,
            cfg.mock_path,
        }

    def _process_route(self, route: CompiledRoute) -> None:
        """Convert one CompiledRoute into a path item operation."""
        if not self.config.include_internal and route.full_path.startswith("/_"):
            return
        if route.full_path in self._specula_paths():
            return
        # Sub-paths of Specula endpoints (versions/{v}, export/postman, ...)
        for base in (
            self.config.versions_path,
            self.config.schemas_path,
            self.config.export_path,
            self.config.mock_path,
        ):
            if route.full_path.startswith(base + "/"):
                return

        tags = list(getattr(route.route_metadata, "tags", []) or [])
        ctrl_tags = list(getattr(route.controller_metadata, "tags", []) or []) if route.controller_metadata else []
        if "_docs" in tags + ctrl_tags or "_specula" in tags + ctrl_tags:
            return

        path = generate_openapi_path(route.compiled_pattern)
        method = route.http_method.lower()

        if route.http_method == "WS":
            self._process_websocket_route(route, path)
            return

        handler = getattr(route.controller_class, route.route_metadata.handler_name, None)
        docstring = inspect.getdoc(handler) if handler else ""
        doc = _parse_docstring(docstring or "")

        self._path_items.setdefault(path, {})[method] = self._build_operation(route, handler, doc)

    def _build_operation(self, route: CompiledRoute, handler: Any, doc: ParsedDocstring) -> dict[str, Any]:
        """Build a complete OpenAPI operation object for one route."""
        route_meta = route.route_metadata
        ctrl_name = route.controller_class.__name__.replace("Controller", "")
        op_id = f"{ctrl_name}_{route_meta.handler_name}"

        summary = route_meta.summary or doc.summary or route_meta.handler_name.replace("_", " ").title()
        description = route_meta.description or doc.description or ""

        operation: dict[str, Any] = {"operationId": op_id, "summary": summary}
        if description:
            operation["description"] = description

        tags = self._resolve_tags(route)
        if tags:
            operation["tags"] = tags
            self._register_tags(route, tags)

        parameters = self._build_parameters(route, doc)
        if parameters:
            operation["parameters"] = parameters

        if self.config.infer_request_body and route.http_method in _BODY_METHODS:
            body = self._build_request_body(route, handler, doc)
            if body:
                operation["requestBody"] = body

        operation["responses"] = self._build_responses(route, handler, doc)

        if self.config.detect_security:
            security = self._build_operation_security(route)
            if security:
                operation["security"] = security
                # Auto-document auth failures
                operation["responses"].setdefault(
                    "401",
                    {"description": _STATUS_DESCRIPTIONS[401], "content": {"application/json": {"schema": _ERROR_REF}}},
                )

        if route_meta.deprecated:
            operation["deprecated"] = True

        if self.config.include_extensions:
            operation.update(self._build_extensions(route))

        return operation

    # ── Parameters ─────────────────────────────────────────────────────

    def _build_parameters(self, route: CompiledRoute, doc: ParsedDocstring) -> list[dict[str, Any]]:
        """Path/query/header params from pattern, metadata, docstring, and DRF-style extras."""
        parameters = [dict(p) for p in generate_openapi_params(route.compiled_pattern)]
        seen = {p.get("name") for p in parameters}

        # ParameterMetadata (query / header)
        for pm in getattr(route.route_metadata, "parameters", []) or []:
            if pm.source not in ("query", "header") or pm.name in seen:
                continue
            param: dict[str, Any] = {
                "name": pm.name,
                "in": pm.source,
                "required": pm.required,
                "schema": python_type_to_schema(pm.type),
            }
            if pm.has_default:
                param["schema"]["default"] = pm.default
                param["required"] = False
            parameters.append(param)
            seen.add(pm.name)

        raw = getattr(route.route_metadata, "_raw_metadata", {}) or {}

        # Pagination params
        pagination = raw.get("pagination_class")
        if pagination is not None:
            pag_name = _node_name(pagination).lower()
            if "cursor" in pag_name:
                pag_params = [
                    ("cursor", "string", "Opaque pagination cursor"),
                    ("page_size", "integer", "Items per page"),
                ]
            elif "limitoffset" in pag_name or "offset" in pag_name:
                pag_params = [("limit", "integer", "Maximum items to return"), ("offset", "integer", "Items to skip")]
            else:
                pag_params = [("page", "integer", "Page number"), ("page_size", "integer", "Items per page")]
            for name, typ, desc in pag_params:
                if name not in seen:
                    parameters.append(
                        {"name": name, "in": "query", "required": False, "schema": {"type": typ}, "description": desc}
                    )
                    seen.add(name)

        # FilterSet fields
        for fname in raw.get("filterset_fields") or []:
            if fname not in seen:
                parameters.append(
                    {
                        "name": fname,
                        "in": "query",
                        "required": False,
                        "schema": {"type": "string"},
                        "description": f"Filter by {fname}",
                    }
                )
                seen.add(fname)

        # search_fields → ?search=
        if raw.get("search_fields") and "search" not in seen:
            parameters.append(
                {
                    "name": "search",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                    "description": f"Search across: {', '.join(raw['search_fields'])}",
                }
            )
            seen.add("search")

        # ordering_fields → ?ordering=
        if raw.get("ordering_fields") and "ordering" not in seen:
            fields_list = raw["ordering_fields"]
            parameters.append(
                {
                    "name": "ordering",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "string"},
                    "description": f"Order by: {', '.join(fields_list)} (prefix with - for descending)",
                }
            )
            seen.add("ordering")

        # Docstring descriptions enrich everything
        for param in parameters:
            name = param.get("name", "")
            if name in doc.params and "description" not in param:
                param["description"] = doc.params[name]

        return parameters

    # ── Request body ───────────────────────────────────────────────────

    def _build_request_body(self, route: CompiledRoute, handler: Any, doc: ParsedDocstring) -> dict[str, Any] | None:
        """Multi-strategy request body inference."""
        raw = getattr(route.route_metadata, "_raw_metadata", {}) or {}

        # 1. request_contract=
        request_contract = raw.get("request_contract")
        if _is_contract(request_contract):
            ref = self._register_contract(request_contract, mode="input")
            return {"required": True, "content": {"application/json": {"schema": {"$ref": ref}}}}

        # 1.5. If any route parameter is a Contract subclass, use it as the request body contract directly
        for pm in getattr(route.route_metadata, "parameters", []) or []:
            if pm.source != "dep" and _is_contract(pm.type):
                ref = self._register_contract(pm.type, mode="input")
                return {"required": True, "content": {"application/json": {"schema": {"$ref": ref}}}}

        # 2. ParameterMetadata source='body'
        body_props: dict[str, Any] = {}
        body_required: list[str] = []
        for pm in getattr(route.route_metadata, "parameters", []) or []:
            if pm.source == "body":
                body_props[pm.name] = python_type_to_schema(pm.type)
                if pm.required:
                    body_required.append(pm.name)
        if body_props:
            schema: dict[str, Any] = {"type": "object", "properties": body_props}
            if body_required:
                schema["required"] = body_required
            return {"required": True, "content": {"application/json": {"schema": schema}}}

        # 3. Annotated[X, Body(...)]
        if handler:
            try:
                sig = inspect.signature(handler)
                for pname, param in sig.parameters.items():
                    if pname in ("self", "cls", "ctx", "request"):
                        continue
                    hint = param.annotation
                    if get_origin(hint) is not None and "Annotated" in str(get_origin(hint)):
                        args = get_args(hint)
                        for ann in args[1:]:
                            ann_name = _node_name(ann).lower()
                            if "body" in ann_name:
                                return {
                                    "required": True,
                                    "content": {"application/json": {"schema": python_type_to_schema(args[0])}},
                                }
            except (ValueError, TypeError):
                pass

        # 4. Handler source analysis
        if handler:
            try:
                source = inspect.getsource(handler)
            except (OSError, TypeError):
                source = ""
            if "ctx.json()" in source:
                return {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}}
            if "ctx.form()" in source:
                return {
                    "required": True,
                    "content": {"application/x-www-form-urlencoded": {"schema": {"type": "object"}}},
                }

        # 5. Docstring Body: section
        if doc.body_description:
            return {
                "required": True,
                "content": {"application/json": {"schema": {"type": "object", "description": doc.body_description}}},
            }

        return None

    # ── Responses ──────────────────────────────────────────────────────

    def _build_responses(self, route: CompiledRoute, handler: Any, doc: ParsedDocstring) -> dict[str, dict[str, Any]]:
        """Build response definitions with fault-aware error responses."""
        responses: dict[str, dict[str, Any]] = {}
        route_meta = route.route_metadata
        raw = getattr(route_meta, "_raw_metadata", {}) or {}
        status = str(getattr(route_meta, "status_code", 200) or 200)

        success: dict[str, Any] = {
            "description": _STATUS_DESCRIPTIONS.get(int(status), "Successful response"),
        }

        response_contract = raw.get("response_contract")
        response_model = getattr(route_meta, "response_model", None)

        if _is_contract(response_contract):
            ref = self._register_contract(response_contract, mode="output")
            success["content"] = {"application/json": {"schema": {"$ref": ref}}}
        elif response_model is not None:
            if _is_contract(response_model):
                ref = self._register_contract(response_model, mode="output")
                success["content"] = {"application/json": {"schema": {"$ref": ref}}}
            elif _is_model(response_model):
                ref = self._register_model(response_model)
                success["content"] = {"application/json": {"schema": {"$ref": ref}}}
            else:
                success["content"] = {"application/json": {"schema": python_type_to_schema(response_model)}}
        else:
            # SSE detection from source
            source = ""
            if handler and self.config.infer_responses:
                try:
                    source = inspect.getsource(handler)
                except (OSError, TypeError):
                    source = ""
            if "SSEResponse" in source:
                success["content"] = {"text/event-stream": {"schema": {"type": "string"}}}
            elif "Response.html(" in source:
                success["content"] = {"text/html": {"schema": {"type": "string"}}}
            elif "Response.text(" in source:
                success["content"] = {"text/plain": {"schema": {"type": "string"}}}
            else:
                success["content"] = {"application/json": {"schema": {"type": "object"}}}

        responses[status] = success

        # Docstring Raises: → typed error responses
        for raise_info in doc.raises:
            err_status = raise_info.get("status") or "500"
            responses.setdefault(
                err_status,
                {
                    "description": raise_info.get("description") or raise_info["exception"],
                    "content": {"application/json": {"schema": _ERROR_REF}},
                },
            )

        # Auto 422 for body methods
        if route.http_method in _BODY_METHODS:
            responses.setdefault(
                "422",
                {
                    "description": _STATUS_DESCRIPTIONS[422],
                    "content": {"application/json": {"schema": _VALIDATION_REF}},
                },
            )

        return responses

    # ── Security ───────────────────────────────────────────────────────

    def _pipeline_nodes(self, route: CompiledRoute) -> list[Any]:
        pipeline = list(getattr(route.route_metadata, "pipeline", []) or [])
        if route.controller_metadata:
            pipeline = list(getattr(route.controller_metadata, "pipeline", []) or []) + pipeline
        return pipeline

    def _build_operation_security(self, route: CompiledRoute) -> list[dict[str, list[str]]] | None:
        """Detect security requirements from class + method pipeline guards, decorators, and clearance."""
        security: list[dict[str, list[str]]] = []

        # 1. Pipeline nodes
        for node in self._pipeline_nodes(route):
            name = _node_name(node).lower()
            if "oauth" in name:
                scopes = list(getattr(node, "scopes", []) or [])
                security.append({"oauth2": scopes})
            elif "apikey" in name:
                security.append({"apiKeyAuth": []})
            elif "session" in name:
                security.append({"cookieAuth": []})
            elif "basic" in name:
                security.append({"basicAuth": []})
            elif "authguard" in name or name in ("auth", "authenticated"):
                security.append({"bearerAuth": []})
            elif "scope" in name or "role" in name:
                scopes = list(getattr(node, "scopes", None) or getattr(node, "roles", None) or [])
                if security:
                    for key in security[-1]:
                        security[-1][key] = scopes
                else:
                    security.append({"bearerAuth": scopes})

        # 2. Handler decorators
        handler = getattr(route.controller_class, route.route_metadata.handler_name, None)
        if handler is not None:
            if getattr(handler, "__authenticated__", False):
                if not any("bearerAuth" in s for s in security):
                    security.append({"bearerAuth": []})

            guards = getattr(handler, "__guards__", [])
            for guard in guards:
                if isinstance(guard, type):
                    name = guard.__name__.lower()
                else:
                    name = type(guard).__name__.lower()

                if "oauth" in name:
                    scopes = list(getattr(guard, "scopes", []) or [])
                    security.append({"oauth2": scopes})
                elif "apikey" in name:
                    security.append({"apiKeyAuth": []})
                elif "session" in name:
                    security.append({"cookieAuth": []})
                elif "basic" in name:
                    security.append({"basicAuth": []})
                elif "authguard" in name or "authenticated" in name or name == "auth":
                    if not any("bearerAuth" in s for s in security):
                        security.append({"bearerAuth": []})
                elif "scope" in name or "role" in name:
                    scopes = list(getattr(guard, "scopes", None) or getattr(guard, "roles", None) or [])
                    added = False
                    if security:
                        for s in security:
                            if "bearerAuth" in s:
                                s["bearerAuth"] = list(set(s["bearerAuth"]) | set(scopes))
                                added = True
                            elif "oauth2" in s:
                                s["oauth2"] = list(set(s["oauth2"]) | set(scopes))
                                added = True
                    if not added:
                        security.append({"bearerAuth": scopes})

            # 3. Clearance system
            try:
                from aquilia.auth.clearance import build_merged_clearance, AccessLevel
                clearance = build_merged_clearance(route.controller_class, handler)
                if clearance is not None and clearance.effective_level > AccessLevel.PUBLIC:
                    if not security:
                        security.append({"bearerAuth": []})
            except Exception:
                pass

        return security or None

    def _detect_all_security_schemes(self, routes: list[CompiledRoute]) -> None:
        """Scan all routes' pipelines, handlers, and clearance to populate ``securitySchemes``."""
        for route in routes:
            nodes = self._pipeline_nodes(route)
            handler = getattr(route.controller_class, route.route_metadata.handler_name, None)
            
            # Check decorator __authenticated__
            if handler is not None and getattr(handler, "__authenticated__", False):
                self._security_schemes.setdefault(
                    "bearerAuth",
                    {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT",
                        "description": "JWT Bearer token authentication",
                    },
                )
                
            # Check handler __guards__
            guards = getattr(handler, "__guards__", []) if handler is not None else []
            for guard in guards:
                if isinstance(guard, type):
                    name = guard.__name__.lower()
                else:
                    name = type(guard).__name__.lower()
                
                if "oauth" in name:
                    self._security_schemes.setdefault(
                        "oauth2",
                        {
                            "type": "oauth2",
                            "flows": {
                                "authorizationCode": {
                                    "authorizationUrl": "/auth/authorize",
                                    "tokenUrl": "/auth/token",
                                    "scopes": {},
                                }
                            },
                        },
                    )
                elif "apikey" in name:
                    self._security_schemes.setdefault(
                        "apiKeyAuth",
                        {
                            "type": "apiKey",
                            "in": "header",
                            "name": "X-API-Key",
                            "description": "API key authentication",
                        },
                    )
                elif "session" in name:
                    self._security_schemes.setdefault(
                        "cookieAuth",
                        {
                            "type": "apiKey",
                            "in": "cookie",
                            "name": "session",
                            "description": "Session cookie authentication",
                        },
                    )
                elif "basic" in name:
                    self._security_schemes.setdefault("basicAuth", {"type": "http", "scheme": "basic"})
                elif "authguard" in name or "scope" in name or "role" in name or name in ("auth", "authenticated"):
                    self._security_schemes.setdefault(
                        "bearerAuth",
                        {
                            "type": "http",
                            "scheme": "bearer",
                            "bearerFormat": "JWT",
                            "description": "JWT Bearer token authentication",
                        },
                    )
                    
            # Check clearance
            try:
                from aquilia.auth.clearance import build_merged_clearance, AccessLevel
                clearance = build_merged_clearance(route.controller_class, handler) if handler else None
                if clearance is not None and clearance.effective_level > AccessLevel.PUBLIC:
                    self._security_schemes.setdefault(
                        "bearerAuth",
                        {
                            "type": "http",
                            "scheme": "bearer",
                            "bearerFormat": "JWT",
                            "description": "JWT Bearer token authentication",
                        },
                    )
            except Exception:
                pass

            for node in nodes:
                name = _node_name(node).lower()
                if "oauth" in name:
                    self._security_schemes.setdefault(
                        "oauth2",
                        {
                            "type": "oauth2",
                            "flows": {
                                "authorizationCode": {
                                    "authorizationUrl": "/auth/authorize",
                                    "tokenUrl": "/auth/token",
                                    "scopes": {},
                                }
                            },
                        },
                    )
                elif "apikey" in name:
                    self._security_schemes.setdefault(
                        "apiKeyAuth",
                        {
                            "type": "apiKey",
                            "in": "header",
                            "name": "X-API-Key",
                            "description": "API key authentication",
                        },
                    )
                elif "session" in name:
                    self._security_schemes.setdefault(
                        "cookieAuth",
                        {
                            "type": "apiKey",
                            "in": "cookie",
                            "name": "session",
                            "description": "Session cookie authentication",
                        },
                    )
                elif "basic" in name:
                    self._security_schemes.setdefault("basicAuth", {"type": "http", "scheme": "basic"})
                elif "authguard" in name or "scope" in name or "role" in name or name in ("auth", "authenticated"):
                    self._security_schemes.setdefault(
                        "bearerAuth",
                        {
                            "type": "http",
                            "scheme": "bearer",
                            "bearerFormat": "JWT",
                            "description": "JWT Bearer token authentication",
                        },
                    )

    # ── Extensions ─────────────────────────────────────────────────────

    def _build_extensions(self, route: CompiledRoute) -> dict[str, Any]:
        """``x-specula-*`` vendor extensions for a route."""
        ext: dict[str, Any] = {}
        cfg = self.config

        module = getattr(route, "app_name", None)
        if module:
            ext["x-specula-module"] = module

        handler = getattr(route.controller_class, route.route_metadata.handler_name, None)

        if cfg.include_effect_annotations and handler is not None:
            effects = getattr(handler, "__flow_effects__", None)
            if effects:
                ext["x-specula-effects"] = list(effects)

        if cfg.include_pipeline_annotations:
            nodes = self._pipeline_nodes(route)
            if nodes:
                ext["x-specula-pipeline"] = [_node_name(n) for n in nodes]

        raw = getattr(route.route_metadata, "_raw_metadata", {}) or {}
        throttle = raw.get("throttle")
        if throttle is not None:
            ext["x-specula-throttle"] = throttle if isinstance(throttle, dict) else {"policy": _node_name(throttle)}

        version = getattr(route.route_metadata, "version", None)
        version_meta = getattr(route, "version_metadata", None) or {}
        if version_meta.get("versions"):
            ext["x-specula-version"] = list(version_meta["versions"])
        elif version is not None:
            ext["x-specula-version"] = str(version)

        if handler is not None:
            sec_ext = self._build_security_extension(route, handler)
            if sec_ext:
                ext["x-specula-security"] = sec_ext

        return ext

    def _build_security_extension(self, route: CompiledRoute, handler: Any) -> dict[str, Any] | None:
        if handler is None:
            return None

        security_info: dict[str, Any] = {}

        # 1. Check if authenticated
        authenticated = getattr(handler, "__authenticated__", False)
        guards = getattr(handler, "__guards__", [])
        
        has_auth_guard = False
        for g in guards:
            g_class = g if isinstance(g, type) else type(g)
            if g_class.__name__ in ("AuthGuard", "RoleGuard", "ScopeGuard", "PolicyGuard", "ClearanceGuard"):
                has_auth_guard = True
                break
                
        for node in self._pipeline_nodes(route):
            node_class = node if isinstance(node, type) else type(node)
            if "auth" in node_class.__name__.lower() or "guard" in node_class.__name__.lower():
                has_auth_guard = True
                break

        if authenticated or has_auth_guard:
            security_info["authenticated"] = True

        # 2. Extract guards details
        guard_details = []
        for g in guards:
            if isinstance(g, type):
                guard_details.append({
                    "name": g.__name__,
                    "type": "class"
                })
            else:
                details = {
                    "name": type(g).__name__,
                    "type": "instance"
                }
                if hasattr(g, "optional"):
                    details["optional"] = getattr(g, "optional")
                if hasattr(g, "roles"):
                    details["roles"] = list(getattr(g, "roles") or [])
                if hasattr(g, "scopes"):
                    details["scopes"] = list(getattr(g, "scopes") or [])
                if hasattr(g, "require_all"):
                    details["require_all"] = getattr(g, "require_all")
                if hasattr(g, "key"):
                    details["key"] = getattr(g, "key")
                if hasattr(g, "resource") and getattr(g, "resource") is not None:
                    details["resource"] = str(getattr(g, "resource"))
                guard_details.append(details)

        if guard_details:
            security_info["guards"] = guard_details

        # 3. Extract Clearance details
        try:
            from aquilia.auth.clearance import build_merged_clearance, AccessLevel
            clearance = build_merged_clearance(route.controller_class, handler)
            if clearance is not None:
                conditions_names = []
                for cond in clearance.conditions:
                    if hasattr(cond, "__name__"):
                        conditions_names.append(cond.__name__)
                    elif hasattr(type(cond), "__name__"):
                        conditions_names.append(type(cond).__name__)
                    else:
                        conditions_names.append(str(cond))

                security_info["clearance"] = {
                    "level": clearance.level.name if clearance.level is not None else "AUTHENTICATED",
                    "level_value": clearance.level.value if clearance.level is not None else 10,
                    "entitlements": list(clearance.entitlements),
                    "conditions": conditions_names,
                    "compartment": clearance.compartment,
                }
        except Exception:
            pass

        return security_info if security_info else None

    # ── Tags ───────────────────────────────────────────────────────────

    def _resolve_tags(self, route: CompiledRoute) -> list[str]:
        """Tags: route → controller → module → controller class name."""
        tags = list(getattr(route.route_metadata, "tags", []) or [])
        if not tags and route.controller_metadata:
            tags = list(getattr(route.controller_metadata, "tags", []) or [])
        if not tags and self.config.group_by_module and getattr(route, "app_name", None):
            tags = [route.app_name]
        if not tags:
            tags = [route.controller_class.__name__.replace("Controller", "")]
        return tags

    def _register_tags(self, route: CompiledRoute, tags: list[str]) -> None:
        for tag in tags:
            if tag in self._tag_names:
                continue
            self._tag_names.add(tag)
            info: dict[str, Any] = {"name": tag}
            if tag == route.controller_class.__name__.replace("Controller", ""):
                doc = inspect.getdoc(route.controller_class)
                if doc:
                    info["description"] = doc.split("\n")[0]
            self._tags.append(info)

    # ── Schema registration ────────────────────────────────────────────

    def _register_contract(self, contract_cls: type, *, mode: str) -> str:
        """Register a Contract schema; return $ref string."""
        from .contract import contract_to_schema

        name = contract_cls.__name__ if mode == "output" else f"{contract_cls.__name__}Input"
        if name not in self._schemas:
            try:
                schema = contract_to_schema(contract_cls, mode=mode)
                self._extract_and_flatten_defs(schema, mode)
                self._schemas[name] = schema
            except Exception as exc:  # noqa: BLE001 — degrade to plain object
                logger.warning("Specula: contract schema for %s failed: %s", name, exc)
                self._schemas[name] = {"type": "object"}
        return f"#/components/schemas/{name}"

    def _extract_and_flatten_defs(self, schema: dict[str, Any], parent_mode: str) -> None:
        """Recursively extract $defs from a schema, register them in components, and rewrite $refs."""
        if not isinstance(schema, dict):
            return

        defs = schema.pop("$defs", {}) or {}
        for def_name, def_schema in defs.items():
            target_name = f"{def_name}Input" if parent_mode == "input" else def_name
            if target_name not in self._schemas:
                # Recursively process the nested schema before registering it
                self._extract_and_flatten_defs(def_schema, parent_mode)
                self._schemas[target_name] = def_schema

        self._rewrite_refs_in_place(schema, parent_mode)

    def _rewrite_refs_in_place(self, schema: Any, parent_mode: str) -> None:
        """Recursively rewrite "#/$defs/XYZ" refs to "#/components/schemas/XYZ" (or XYZInput)."""
        if isinstance(schema, dict):
            ref = schema.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                def_name = ref.split("/").pop()
                target_name = f"{def_name}Input" if parent_mode == "input" else def_name
                schema["$ref"] = f"#/components/schemas/{target_name}"
            for val in schema.values():
                self._rewrite_refs_in_place(val, parent_mode)
        elif isinstance(schema, list):
            for val in schema:
                self._rewrite_refs_in_place(val, parent_mode)

    def _register_model(self, model_cls: type) -> str:
        """Register an ORM Model schema; return $ref string."""
        from .model import model_to_schema

        name = model_cls.__name__
        if name not in self._schemas:
            try:
                self._schemas[name] = model_to_schema(model_cls)
            except Exception as exc:  # noqa: BLE001 — degrade to plain object
                logger.warning("Specula: model schema for %s failed: %s", name, exc)
                self._schemas[name] = {"type": "object"}
        return f"#/components/schemas/{name}"

    def _register_schema(self, name: str, schema: dict[str, Any]) -> str:
        """Register a raw schema; return $ref string."""
        self._schemas[name] = schema
        return f"#/components/schemas/{name}"

    def _register_response_schema(self, route: CompiledRoute) -> None:
        """Ensure response_model / response_contract schemas land in components."""
        raw = getattr(route.route_metadata, "_raw_metadata", {}) or {}
        model = getattr(route.route_metadata, "response_model", None)
        contract = raw.get("response_contract")

        if _is_contract(contract):
            self._register_contract(contract, mode="output")
        if model is None:
            return
        if _is_contract(model):
            self._register_contract(model, mode="output")
        elif _is_model(model):
            self._register_model(model)
        elif isinstance(model, type) and hasattr(model, "__annotations__") and model.__name__ not in self._schemas:
            self._schemas[model.__name__] = self._dataclass_schema(model)

    @staticmethod
    def _dataclass_schema(cls: type) -> dict[str, Any]:
        """Schema for a plain dataclass / annotated class."""
        properties: dict[str, Any] = {}
        required: list[str] = []
        try:
            from typing import get_type_hints

            hints = get_type_hints(cls, include_extras=True)
        except Exception:  # noqa: BLE001
            hints = getattr(cls, "__annotations__", {})

        for fname, ftype in hints.items():
            if fname.startswith("_"):
                continue
            properties[fname] = python_type_to_schema(ftype)
            if getattr(cls, fname, inspect.Parameter.empty) is inspect.Parameter.empty:
                required.append(fname)

        schema: dict[str, Any] = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        doc = inspect.getdoc(cls)
        if doc:
            schema["description"] = doc.split("\n")[0]
        return schema

    # ── WebSocket routes ───────────────────────────────────────────────

    def _process_websocket_route(self, route: CompiledRoute, path: str) -> None:
        """Document a WS route as a GET op with ``x-specula-websocket: true``."""
        route_meta = route.route_metadata
        ctrl_name = route.controller_class.__name__.replace("Controller", "")
        operation: dict[str, Any] = {
            "operationId": f"{ctrl_name}_{route_meta.handler_name}",
            "summary": route_meta.summary or f"WebSocket: {path}",
            "description": "WebSocket upgrade endpoint. Connect with the WebSocket protocol.",
            "responses": {
                "101": {"description": "Switching Protocols — WebSocket upgrade"},
            },
            "x-specula-websocket": True,
        }
        tags = self._resolve_tags(route)
        if tags:
            operation["tags"] = tags
            self._register_tags(route, tags)
        self._path_items.setdefault(path, {})["get"] = operation

    # ── Spec assembly ──────────────────────────────────────────────────

    def _assemble_spec(self) -> dict[str, Any]:
        """Assemble the final OpenAPI 3.1.0 spec dict."""
        spec: dict[str, Any] = {
            "openapi": "3.1.0",
            "info": self._build_info(),
            "paths": self._path_items,
        }

        servers = self.config.servers or [{"url": "/", "description": "Current server"}]
        spec["servers"] = servers

        if self._tags:
            spec["tags"] = sorted(self._tags, key=lambda t: t["name"])

        components: dict[str, Any] = {}
        if self._schemas:
            components["schemas"] = dict(self._schemas)
        if self._security_schemes:
            components["securitySchemes"] = self._security_schemes
        if components:
            spec["components"] = components

        if self.config.external_docs_url:
            spec["externalDocs"] = {"url": self.config.external_docs_url}
            if self.config.external_docs_description:
                spec["externalDocs"]["description"] = self.config.external_docs_description

        if self.config.webhooks:
            spec["webhooks"] = self.config.webhooks

        if self.config.tag_groups:
            spec["x-tagGroups"] = self.config.tag_groups

        spec["x-specula-version"] = "2.0.0"
        spec["x-specula-framework"] = "aquilia"
        return spec

    def _build_info(self) -> dict[str, Any]:
        """Assemble the OpenAPI info object."""
        cfg = self.config
        info: dict[str, Any] = {"title": cfg.title, "version": cfg.version}
        if cfg.description:
            info["description"] = cfg.description
        if cfg.terms_of_service:
            info["termsOfService"] = cfg.terms_of_service

        contact = {
            k: v for k, v in {"name": cfg.contact_name, "email": cfg.contact_email, "url": cfg.contact_url}.items() if v
        }
        if contact:
            info["contact"] = contact

        license_info = {
            k: v
            for k, v in {"name": cfg.license_name, "url": cfg.license_url, "identifier": cfg.license_identifier}.items()
            if v
        }
        if license_info:
            info["license"] = license_info

        return info
