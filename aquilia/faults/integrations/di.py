"""
AquilaFaults - DI Integration.

Integrates fault handling with Dependency Injection system:
1. Replace ProviderNotFoundError with ProviderNotFoundFault
2. Add scope violation faults
3. Integrate with DI resolution lifecycle

This module patches the DI Container to use AquilaFaults.
"""

from aquilia.di.core import Container
from aquilia.di.errors import ProviderNotFoundError as OldProviderNotFoundError
from aquilia.faults import (
    FaultContext,
    FaultDomain,
    FaultHandler,
    FaultResult,
    Resolved,
    Severity,
)
from aquilia.faults.domains import (
    DIFault,
)


class CircularDependencyFault(DIFault):
    """Circular dependency detected."""

    def __init__(self, cycle: list[str]):
        cycle_str = " → ".join(cycle)
        super().__init__(
            code="CIRCULAR_DEPENDENCY",
            message=f"Circular dependency detected: {cycle_str}",
            severity=Severity.ERROR,
            metadata={"cycle": cycle, "cycle_length": len(cycle)},
        )


class ProviderRegistrationFault(DIFault):
    """Provider registration failed."""

    def __init__(self, token: str, reason: str):
        super().__init__(
            code="PROVIDER_REGISTRATION_FAILED",
            message=f"Failed to register provider for '{token}': {reason}",
            metadata={"token": token, "reason": reason},
        )


class AsyncResolutionFault(DIFault):
    """Async resolution in sync context."""

    def __init__(self, token: str):
        super().__init__(
            code="ASYNC_RESOLUTION_IN_SYNC_CONTEXT",
            message=f"Cannot resolve async provider '{token}' in sync context; use await resolve_async()",
            severity=Severity.ERROR,
            metadata={"token": token},
        )


def patch_di_container():
    """
    Patch DI Container to emit structured faults.

    Enriches or converts bare exceptions:
    - ProviderNotFoundError → enriched in place (already a ``DIFault``)
    - RuntimeError (async) → AsyncResolutionFault
    - ValueError (registration) → ProviderRegistrationFault

    Returns:
        ``None``.

    Note:
        The patch is idempotent.  It is applied whenever a server is
        constructed, and re-wrapping already-wrapped methods on every call
        would stack wrappers without bound.

    Usage::

        patch_di_container()
    """

    if getattr(Container.resolve, "__aquilia_fault_patched__", False):
        return

    # Store original methods
    original_resolve = Container.resolve
    original_resolve_async = Container.resolve_async
    original_register = Container.register

    def _enrich_not_found(container, error, token, tag):
        """
        Attach resolution context to a provider-not-found error, in place.

        Args:
            container: The ``Container`` that failed to resolve.
            error: The raised ``ProviderNotFoundError``.
            token: The token that was requested.
            tag: Optional resolution tag.

        Returns:
            The same error instance, with ``metadata`` filled in.

        Note:
            ``ProviderNotFoundError`` already subclasses ``DIFault``, so it is
            a structured fault.  Re-raising a separate ``ProviderNotFoundFault``
            would change the exception *type* and silently break every
            ``except ProviderNotFoundError`` handler in application code, so
            the original error is enriched and re-raised instead.
        """
        unwrapped, _, _ = (
            container._unwrap_token(token) if hasattr(container, "_unwrap_token") else (token, None, False)
        )
        tok_name = getattr(error, "token", None) or (unwrapped if isinstance(unwrapped, str) else str(unwrapped))
        metadata = getattr(error, "metadata", None)
        if isinstance(metadata, dict):
            metadata.setdefault("provider", tok_name)
            metadata.setdefault("tag", tag)
            metadata.setdefault("candidates", list(getattr(error, "candidates", None) or []))
        return error

    def patched_resolve(self, token, *, tag=None, optional=False):
        """Patched resolve with fault handling."""
        try:
            return original_resolve(self, token, tag=tag, optional=optional)
        except OldProviderNotFoundError as e:
            raise _enrich_not_found(self, e, token, tag) from None
        except RuntimeError as e:
            msg = str(e)
            if "resolve() called from async context" in msg:
                raise AsyncResolutionFault(token=str(token)) from e
            raise

    async def patched_resolve_async(self, token, *, tag=None, optional=False, ctx=None):
        """Patched resolve_async with fault handling."""
        try:
            return await original_resolve_async(self, token, tag=tag, optional=optional, ctx=ctx)
        except OldProviderNotFoundError as e:
            raise _enrich_not_found(self, e, token, tag) from None

    def patched_register(self, provider, tag=None):
        """Patched register with fault handling."""
        try:
            return original_register(self, provider, tag=tag)
        except ValueError as e:
            # Extract token from error message
            msg = str(e)
            token = "unknown"
            if "already registered" in msg:
                # Try to extract token
                import re

                match = re.search(r"'([^']+)' already registered", msg)
                if match:
                    token = match.group(1)

            raise ProviderRegistrationFault(token=token, reason=msg) from e

    # Apply patches
    patched_resolve.__aquilia_fault_patched__ = True
    Container.resolve = patched_resolve
    Container.resolve_async = patched_resolve_async
    Container.register = patched_register


def create_di_fault_handler():
    """
    Create fault handler for DI operations.

    Returns a handler that converts DI faults to structured responses.
    """

    class DIFaultHandler(FaultHandler):
        """Handle DI-specific faults."""

        def can_handle(self, ctx: FaultContext) -> bool:
            return ctx.fault.domain == FaultDomain.DI

        async def handle(self, ctx: FaultContext) -> FaultResult:
            """Log DI fault and resolve with diagnostic info."""
            fault = ctx.fault

            # Build helpful response
            response = {
                "error": "dependency_injection_fault",
                "code": fault.code,
                "message": fault.message,
                "metadata": fault.metadata,
                "trace_id": ctx.trace_id,
            }

            # Add suggestions for common issues
            if fault.code == "PROVIDER_NOT_FOUND":
                response["suggestions"] = [
                    "Register a provider for this token",
                    "Check if the provider is in the correct scope",
                    "Verify the token name matches exactly",
                ]
            elif fault.code == "CIRCULAR_DEPENDENCY":
                response["suggestions"] = [
                    "Break the cycle by using lazy injection",
                    "Use a factory or service locator pattern",
                    "Reconsider the dependency structure",
                ]
            elif fault.code == "SCOPE_VIOLATION":
                response["suggestions"] = [
                    "Use a compatible scope (e.g., request → transient)",
                    "Convert singleton to request-scoped",
                    "Use a provider pattern for scope bridging",
                ]

            return Resolved(response)

    return DIFaultHandler()


# Auto-patch on import (optional - can be called explicitly)
# patch_di_container()
