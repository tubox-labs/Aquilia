"""Structured faults for the middleware subsystem.

This is the first module in the package permitted to import
:mod:`aquilia.faults` — everything under ``core/`` and ``utils/`` must stay
free of it so ``aquilia.faults.engine`` can import ``Middleware`` without a
cycle. See ``core/base.py`` for why.

Each fault also inherits the builtin exception the old code raised
(``TypeError`` for registration, ``RuntimeError``/``TypeError`` for contract
violations). Faults already subclass ``Exception``, so the extra base is free,
and it means ``except TypeError`` in code written before the fault system keeps
working. The builtin bases are scheduled for removal in 2.0.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.domains import ConfigFault, ConfigInvalidFault, FlowFault


class MiddlewareRegistrationFault(ConfigFault, TypeError):
    """A middleware was rejected at registration time.

    Raised for a bad base class, a wrong signature, a sync hook, or an ``add()``
    on a frozen stack — anything that should fail at boot rather than on the
    first request.

    Inherits ``TypeError`` for backward compatibility with call sites written
    before the fault system existed.
    """

    def __init__(self, reason: str, *, name: str | None = None, **kwargs: Any):
        super().__init__(
            code="MIDDLEWARE_INVALID",
            message=reason,
            metadata={"middleware": name, **kwargs.get("metadata", {})},
        )

    # ── Constructors, so the message text lives in one place ─────────────

    @classmethod
    def not_a_middleware(cls, type_name: str) -> MiddlewareRegistrationFault:
        return cls(
            f"Middleware of type '{type_name}' must inherit from the 'Middleware' base class.",
            name=type_name,
        )

    @classmethod
    def not_callable(cls, type_name: str) -> MiddlewareRegistrationFault:
        return cls(f"Middleware of type '{type_name}' must be callable.", name=type_name)

    @classmethod
    def bad_signature(cls, name: str, detail: str) -> MiddlewareRegistrationFault:
        return cls(
            f"Middleware '{name}' has an invalid signature: {detail}. "
            f"It must accept exactly three parameters: (request, ctx, next_handler).",
            name=name,
        )

    @classmethod
    def not_async(cls, name: str) -> MiddlewareRegistrationFault:
        return cls(f"Middleware '{name}' must be a coroutine function (async def).", name=name)

    @classmethod
    def frozen(cls, name: str) -> MiddlewareRegistrationFault:
        return cls(
            f"Cannot register middleware '{name}': the stack is frozen. "
            f"The chain is compiled and cached once at startup, so middleware added "
            f"afterwards would never run. Register it during application setup instead.",
            name=name,
        )


class MiddlewarePriorityCollisionFault(ConfigInvalidFault):
    """Two middleware share a scope and priority under ``strict_priorities``.

    Their relative order would fall back to registration order, which is not
    part of the public API.

    Subclasses ``ConfigInvalidFault`` (code ``CONFIG_INVALID``) so existing
    ``except ConfigInvalidFault`` handlers and the ``strict_priorities``
    contract keep working unchanged.
    """

    def __init__(self, reason: str, *, key: str = "middleware.priority", **kwargs: Any):
        super().__init__(key, reason, **kwargs)


class MiddlewareContractFault(FlowFault, RuntimeError):
    """A middleware returned something other than a ``Response``.

    Inherits ``RuntimeError`` for backward compatibility. The wrong-type variant
    additionally reports as ``TypeError``, matching what the old chain raised.
    """

    def __init__(self, reason: str, *, name: str | None = None, **kwargs: Any):
        super().__init__(
            code="MIDDLEWARE_CONTRACT_VIOLATION",
            message=reason,
            metadata={"middleware": name, **kwargs.get("metadata", {})},
        )

    @classmethod
    def returned_none(cls, name: str) -> MiddlewareContractFault:
        return cls(
            f"Middleware '{name}' returned None instead of a Response object. "
            f"Make sure the middleware is not missing a return statement or forgot "
            f"to await next_handler.",
            name=name,
        )

    @classmethod
    def returned_wrong_type(cls, name: str, type_name: str) -> MiddlewareContractFault:
        return _MiddlewareReturnTypeFault(
            f"Middleware '{name}' returned invalid type '{type_name}' instead of a Response object.",
            name=name,
        )


class _MiddlewareReturnTypeFault(MiddlewareContractFault, TypeError):
    """Wrong-type return. Split out so it reports as ``TypeError`` while the
    missing-return case stays a ``RuntimeError``, exactly as before."""


__all__ = [
    "MiddlewareRegistrationFault",
    "MiddlewarePriorityCollisionFault",
    "MiddlewareContractFault",
]
