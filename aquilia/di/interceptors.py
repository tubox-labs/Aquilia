"""
Provider-level interceptors — DI-integrated AOP for Aquilia.

Nest has Interceptors/Guards, Spring has ``@Around`` advice. Aquilia's
controller layer already ships an :class:`aquilia.controller.base.Interceptor`
(before/after around handlers). This module brings the same idea *down into the
container*: wrap the **instantiation** of any provider so cross-cutting concerns
(timing, logging, tracing, caching, proxying) run around object creation and
around the created instance's methods — without touching the service class.

Two composable pieces:

* :class:`ProviderInterceptor` — a small protocol with ``around_instantiate``.
* :class:`InterceptingProvider` — wraps another provider and runs a chain of
  interceptors around its ``instantiate``.

Reuse note: :class:`ProviderInterceptor` deliberately mirrors the controller
:class:`~aquilia.controller.base.Interceptor` before/after shape, so the mental
model is identical at both layers.

Example — log every instantiation::

    from aquilia.di.interceptors import ProviderInterceptor, intercept

    class LogInterceptor(ProviderInterceptor):
        async def around_instantiate(self, ctx, nxt):
            print("creating", ctx.provider.meta.name)
            instance = await nxt()
            print("created", ctx.provider.meta.name)
            return instance

    provider = intercept(ClassProvider(UserService), LogInterceptor())
    container.register(provider)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from ..faults.domains import DIFault
from .core import ProviderMeta

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from .core import Provider, ResolveCtx


class InterceptContext:
    """Context passed to a :class:`ProviderInterceptor`.

    Attributes:
        provider: The provider being instantiated.
        resolve_ctx: The active :class:`~aquilia.di.core.ResolveCtx`.
        meta: The provider's :class:`~aquilia.di.core.ProviderMeta`.
    """

    __slots__ = ("provider", "resolve_ctx", "meta")

    def __init__(self, provider: Provider, resolve_ctx: ResolveCtx) -> None:
        self.provider = provider
        self.resolve_ctx = resolve_ctx
        self.meta = provider.meta


@runtime_checkable
class ProviderInterceptor(Protocol):
    """Around-advice for provider instantiation.

    Implement :meth:`around_instantiate`; call ``nxt()`` to proceed to the next
    interceptor (or the real instantiation) and return the (possibly wrapped)
    instance. Skip the ``nxt()`` call to short-circuit with your own object.

    Example::

        class TimingInterceptor(ProviderInterceptor):
            async def around_instantiate(self, ctx, nxt):
                import time
                t0 = time.monotonic()
                obj = await nxt()
                dur = time.monotonic() - t0
                logger.info("built %s in %.4fs", ctx.meta.name, dur)
                return obj
    """

    async def around_instantiate(
        self,
        ctx: InterceptContext,
        nxt: Callable[[], Awaitable[Any]],
    ) -> Any:
        """Run around the wrapped provider's instantiation."""
        ...


class InterceptingProvider:
    """A provider that runs a chain of :class:`ProviderInterceptor` around another.

    Transparent to the container: exposes the same :class:`ProviderMeta` as the
    wrapped provider, so tokens, scope, and tags are unchanged. Interceptors run
    in registration order (first-registered is outermost).

    Args:
        inner: The provider whose instantiation is intercepted.
        interceptors: Ordered interceptors (outermost first).

    Example::

        wrapped = InterceptingProvider(
            ClassProvider(PaymentService, scope="app"),
            [TimingInterceptor(), TracingInterceptor()],
        )
        container.register(wrapped)
    """

    __slots__ = ("_inner", "_interceptors", "_meta")

    def __init__(self, inner: Provider, interceptors: list[ProviderInterceptor]) -> None:
        if not interceptors:
            raise DIFault(
                code="DI_NO_INTERCEPTORS",
                message="InterceptingProvider requires at least one interceptor.",
                metadata={"provider": inner.meta.name},
            )
        self._inner = inner
        self._interceptors = list(interceptors)
        # Mirror the inner provider's metadata verbatim (token/scope preserved).
        m = inner.meta
        self._meta = ProviderMeta(
            name=m.name,
            token=m.token,
            scope=m.scope,
            tags=m.tags,
            module=m.module,
            qualname=m.qualname,
            line=m.line,
            version=m.version,
            allow_lazy=m.allow_lazy,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    @property
    def inner(self) -> Provider:
        """The wrapped provider."""
        return self._inner

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Instantiate the inner provider through the interceptor chain."""
        ictx = InterceptContext(self._inner, ctx)

        # Build the call chain from the inside out so the first interceptor
        # in the list is the outermost frame.
        async def _base() -> Any:
            return await self._inner.instantiate(ctx)

        nxt: Callable[[], Awaitable[Any]] = _base
        for interceptor in reversed(self._interceptors):
            nxt = _bind(interceptor, ictx, nxt)
        return await nxt()

    async def shutdown(self) -> None:
        """Delegate shutdown to the inner provider."""
        await self._inner.shutdown()


def _bind(
    interceptor: ProviderInterceptor,
    ctx: InterceptContext,
    nxt: Callable[[], Awaitable[Any]],
) -> Callable[[], Awaitable[Any]]:
    """Bind one interceptor around ``nxt`` (avoids late-binding closure bug)."""

    async def _run() -> Any:
        return await interceptor.around_instantiate(ctx, nxt)

    return _run


def intercept(provider: Provider, *interceptors: ProviderInterceptor) -> InterceptingProvider:
    """Wrap *provider* with one or more interceptors.

    Convenience constructor for :class:`InterceptingProvider`.

    Args:
        provider: The provider to wrap.
        *interceptors: One or more interceptors (outermost first).

    Returns:
        An :class:`InterceptingProvider`.

    Example::

        container.register(intercept(ClassProvider(UserService), LogInterceptor()))
    """
    return InterceptingProvider(provider, list(interceptors))
