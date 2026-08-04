"""
Controller-layer request body validation via Aquilia Contracts.

Usage::

    from aquilia import Controller, POST, RequestCtx, Response
    from aquilia.controller.validation import validate_body
    from myapp.users.contracts import CreateUserContract

    class UsersController(Controller):
        prefix = "/users"

        @POST("/")
        @validate_body(CreateUserContract)
        async def create_user(self, ctx: RequestCtx, body: dict):
            user = await self.user_service.create(**body)
            return Response.json({"id": user.id}, status=201)

Ownership
---------
This decorator is the *sole* binder of the parameter it injects. It advertises
that by setting ``__aquilia_owned_params__`` on the wrapper, which
``ControllerEngine._bind_parameters`` reads and honours by skipping the
parameter. Previously both layers bound ``body``, so every decorated handler
raised ``TypeError: got multiple values for keyword argument 'body'`` and
returned 500 -- see ``tests/test_validate_body_binding.py``.

Cost
----
Capability probing (``is_sealed_async`` vs ``is_sealed``, presence of
``errors``/``validated_data``) is resolved once at decoration time, not per
request. The body is parsed once, by ``Request.json()``, whose cache every other
layer shares; this module never calls a JSON codec directly.
"""

from __future__ import annotations

import functools
import logging
from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity
from aquilia.json import JSONDecodeError
from aquilia.json import loads as _json_loads
from aquilia.request import InvalidJSON, PayloadTooLarge
from aquilia.response import Response

logger = logging.getLogger("aquilia.controller.validation")

VALIDATION_DOMAIN = FaultDomain.custom("validation", "Request body validation faults")

__all__ = [
    "RequestBodyParseFault",
    "RequestBodyValidationFault",
    "ValidationFault",
    "validate_body",
]


class ValidationFault(Fault):
    domain = VALIDATION_DOMAIN
    severity = Severity.WARN


class RequestBodyValidationFault(ValidationFault):
    code = "validation.body_invalid"
    message = "Request body failed Contract validation"


class RequestBodyParseFault(ValidationFault):
    code = "validation.body_parse_error"
    message = "Request body could not be parsed"


def _parse_failure() -> Response:
    """Build the 400 for an unparseable body.

    Constructed without a traceback: a malformed body is a client error, and
    synthesising a traceback for it cost ~40x a successful request (CPython's
    fine-grained error locations recompile source to draw carets). That made
    malformed input a cheap denial-of-service lever.
    """
    return Response.json(
        {"error": RequestBodyParseFault.message, "code": RequestBodyParseFault.code},
        status=400,
    )


def _invalid(errors: Any) -> Response:
    """Build the 422 for a body that parsed but failed validation."""
    return Response.json(
        {
            "error": RequestBodyValidationFault.message,
            "code": RequestBodyValidationFault.code,
            "detail": errors,
        },
        status=422,
    )


async def _read_body(ctx: Any) -> Any:
    """Read the request body as a mapping, dispatching on content type.

    Everything goes through the ``ctx`` accessors, which delegate to
    ``Request`` -- so the JSON parse is the cached one every other layer shares.
    This module must never invoke a codec itself; doing so is how it previously
    ended up running stdlib ``json`` while the rest of the framework ran
    something else, parsing every body twice.

    Args:
        ctx: The request context.

    Returns:
        The decoded body, or ``{}`` when there is no body.

    Raises:
        InvalidJSON: Body was declared JSON but is malformed.
        PayloadTooLarge: Body exceeded the configured limit.
    """
    content_type = ""
    request = getattr(ctx, "request", None)
    if request is not None:
        headers = getattr(request, "headers", None)
        if headers is not None:
            content_type = headers.get("content-type", "") or headers.get("Content-Type", "") or ""

    if "multipart/form-data" in content_type:
        return await ctx.multipart()
    if "application/x-www-form-urlencoded" in content_type:
        return dict(await ctx.form())

    # Default to JSON, including when the content type is absent or unknown --
    # that matches the previous behaviour.
    #
    # Prefer the request's own json(): it returns the *cached* parse, so a body
    # some earlier layer already read is not decoded a second time. Contexts that
    # only expose raw bytes (test doubles, custom adapters) fall through to
    # decoding what ctx.body() hands back.
    if request is not None and callable(getattr(request, "json", None)):
        return await ctx.json()

    raw = await ctx.body()
    if not raw:
        return {}
    if isinstance(raw, (bytes, bytearray, memoryview, str)):
        return _json_loads(raw)
    # Some contexts hand back an already-decoded body.
    return raw


def validate_body(
    contract_class: type,
    *,
    projection: str = "__all__",
    param: str = "body",
) -> Any:
    """
    Parse and validate the request body through a Contract.

    On success the validated data is injected as the ``param`` keyword argument.
    On failure the handler is never called and a structured error response is
    returned: 400 when the body could not be parsed, 422 when it parsed but
    failed validation.

    Args:
        contract_class: The Contract class to validate against.
        projection: Contract projection selecting the allowed fields.
        param: Name of the handler parameter to inject. This decorator becomes
            the sole owner of that parameter; the controller engine will not
            also bind it.

    Returns:
        The handler decorator.
    """
    # ── Resolved once, at decoration time ───────────────────────────────────
    # These were `hasattr` probes on the request path. The contract class cannot
    # change between requests, so the answers cannot either.
    _has_async_seal = hasattr(contract_class, "is_sealed_async")
    _has_errors = hasattr(contract_class, "errors")
    _has_seal_errors = hasattr(contract_class, "seal_errors")
    _has_validated_data = hasattr(contract_class, "validated_data")

    def decorator(handler: Any) -> Any:
        @functools.wraps(handler)
        async def wrapper(self: Any, ctx: Any, *args: Any, **kwargs: Any) -> Any:
            # Single parse, via the request's own cache. Content-type dispatch
            # lives in Request/RequestCtx -- duplicating it here is what led to
            # this module running a second, different JSON codec.
            # PayloadTooLarge is re-raised, not folded into the 400: it has its
            # own 413 semantics and its own fault handler. Listed first in case
            # it shares a base with the parse errors below.
            try:
                data = await _read_body(ctx)
            except PayloadTooLarge:
                raise
            except (InvalidJSON, JSONDecodeError, UnicodeDecodeError, ValueError):
                return _parse_failure()

            if data is None:
                data = {}

            contract = contract_class(data=data, projection=projection)
            if _has_async_seal:
                sealed = await contract.is_sealed_async()
            else:
                sealed = contract.is_sealed()

            if not sealed:
                if _has_errors:
                    errors = contract.errors
                elif _has_seal_errors:
                    errors = contract.seal_errors()
                else:
                    errors = {}
                return _invalid(errors)

            validated = contract.validated_data if _has_validated_data else data
            kwargs[param] = validated
            return await handler(self, ctx, *args, **kwargs)

        # Declare ownership so the engine does not bind `param` as well.
        owned = getattr(handler, "__aquilia_owned_params__", frozenset())
        wrapper.__aquilia_owned_params__ = owned | {param}
        wrapper.__aquilia_request_contract__ = contract_class
        return wrapper

    return decorator
