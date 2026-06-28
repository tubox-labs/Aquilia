"""
Controller-layer request body validation via Aquilia Blueprints.

Usage::

    from aquilia import Controller, POST, RequestCtx, Response
    from aquilia.controller.validation import validate_body
    from myapp.users.blueprints import CreateUserBlueprint

    class UsersController(Controller):
        prefix = "/users"

        @POST("/")
        @validate_body(CreateUserBlueprint)
        async def create_user(self, ctx: RequestCtx, body: dict):
            user = await self.user_service.create(**body)
            return Response.json({"id": user.id}, status=201)
"""

from __future__ import annotations

import functools
import json
import logging
from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity
from aquilia.response import Response

logger = logging.getLogger("aquilia.controller.validation")

VALIDATION_DOMAIN = FaultDomain.custom("validation", "Request body validation faults")


class ValidationFault(Fault):
    domain = VALIDATION_DOMAIN
    severity = Severity.WARN


class RequestBodyValidationFault(ValidationFault):
    code = "validation.body_invalid"
    message = "Request body failed Blueprint validation"


class RequestBodyParseFault(ValidationFault):
    code = "validation.body_parse_error"
    message = "Request body could not be parsed"


def validate_body(blueprint_class: type, *, projection: str = "__all__") -> Any:
    """
    Decorator: parse + validate the request body through a Blueprint.

    On success:  injects ``body: dict`` as the first extra keyword argument.
    On failure:  returns HTTP 422 Unprocessable Entity with structured errors.

    Args:
        blueprint_class: The Blueprint class to validate against.
        projection:      Blueprint projection to use for allowed fields.
    """

    def decorator(handler: Any) -> Any:
        @functools.wraps(handler)
        async def wrapper(self: Any, ctx: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                content_type = ctx.request.headers.get("content-type", "") or ctx.request.headers.get(
                    "Content-Type", ""
                )
                if "application/json" in content_type:
                    raw_body = await ctx.body()
                    data = json.loads(raw_body) if raw_body else {}
                elif "multipart/form-data" in content_type:
                    data = await ctx.multipart()
                elif "application/x-www-form-urlencoded" in content_type:
                    data = await ctx.form()
                else:
                    raw_body = await ctx.body()
                    if raw_body:
                        try:
                            data = json.loads(raw_body)
                        except Exception:
                            # Try parsing as form URL-encoded
                            form = await ctx.form()
                            data = dict(form)
                    else:
                        data = {}
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                fault = RequestBodyParseFault(context={"error": str(exc)})
                return Response.json(
                    {"error": fault.message, "code": fault.code},
                    status=400,
                )

            try:
                bp = blueprint_class(data=data, projection=projection)
                if not bp.is_sealed():
                    errors = bp.seal_errors() if hasattr(bp, "seal_errors") else {}
                    fault = RequestBodyValidationFault(context={"errors": errors})
                    return Response.json(
                        {"error": fault.message, "code": fault.code, "detail": errors},
                        status=422,
                    )
            except Exception as exc:
                logger.error("Blueprint validation error: %s", exc)
                fault = RequestBodyValidationFault(context={"error": str(exc)})
                return Response.json(
                    {"error": fault.message, "code": fault.code},
                    status=422,
                )

            data = bp.validated_data if hasattr(bp, "validated_data") else data  # type: ignore[assignment]
            return await handler(self, ctx, *args, body=data, **kwargs)

        return wrapper

    return decorator
