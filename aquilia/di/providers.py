"""
Provider implementations for different instantiation strategies.
"""

import asyncio
import inspect
import types
from collections.abc import Callable, Coroutine
from contextlib import asynccontextmanager, suppress
from typing import Any, TypeVar

from .core import Provider, ProviderMeta, ResolveCtx
from .errors import DIError

T = TypeVar("T")


def _normalize_optional_token(annotation: Any) -> tuple[Any, bool]:
    """Normalize Optional/union annotations for DI token lookup.

    Returns:
        (normalized_token, is_optional_annotation)
    """
    from typing import Union, get_args, get_origin

    origin = get_origin(annotation)
    if origin in (Union, types.UnionType):
        args = get_args(annotation)
        if not args:
            return annotation, False

        non_none_args = [arg for arg in args if arg is not type(None)]
        has_none = len(non_none_args) != len(args)

        # Optional[T] -> resolve by T and mark optional.
        if has_none and len(non_none_args) == 1:
            return non_none_args[0], True

        # Complex unions (A | B | None) remain unchanged to avoid ambiguity.
        return annotation, has_none

    return annotation, False


class ClassProvider:
    """
    Provider that instantiates a class by resolving constructor dependencies.

    Supports async __init__ via async_init() convention.
    """

    __slots__ = ("_meta", "_cls", "_dependencies", "_has_async_init")

    def __init__(
        self,
        cls: type[T],
        scope: str = "app",
        tags: tuple[str, ...] = (),
        allow_lazy: bool = False,
    ):
        self._cls = cls
        self._dependencies = self._extract_dependencies(cls)
        self._has_async_init = hasattr(cls, "async_init")

        # Build metadata
        module = cls.__module__
        qualname = cls.__qualname__
        token = f"{module}.{qualname}"

        # Try to get source file and line
        try:
            inspect.getsourcefile(cls)
            _, line = inspect.getsourcelines(cls)
        except (TypeError, OSError):
            line = None

        self._meta = ProviderMeta(
            name=cls.__name__,
            token=token,
            scope=scope,
            tags=tags,
            module=module,
            qualname=qualname,
            line=line,
            allow_lazy=allow_lazy,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Instantiate class by resolving dependencies."""
        # Resolve dependencies
        resolved_deps = {}
        for dep_name, dep_info in self._dependencies.items():
            dep_token = dep_info["token"]
            dep_tag = dep_info.get("tag")

            resolved = await ctx.container.resolve_async(
                dep_token,
                tag=dep_tag,
                optional=dep_info.get("optional", False),
            )
            resolved_deps[dep_name] = resolved

        # Instantiate
        instance = self._cls(**resolved_deps)

        # Call async_init if present
        if self._has_async_init:
            await instance.async_init()

        return instance

    async def shutdown(self) -> None:
        """No-op for class provider (instances handle their own shutdown)."""
        pass

    def _extract_dependencies(self, cls: type) -> dict[str, dict[str, Any]]:
        """
        Extract dependencies from __init__ signature.

        Returns:
            Dict mapping parameter names to dependency info
        """
        deps = {}

        # Check if using default object.__init__
        if cls.__init__ is object.__init__:
            return deps

        try:
            sig = inspect.signature(cls.__init__)
        except ValueError:
            # Handle classes like builtins that might not support signature inspection
            return deps

        try:
            # SEC-DI-02: Start with eval_str=False to avoid arbitrary evaluation.
            # If postponed annotations are strings, attempt a controlled
            # get_type_hints() resolution using the function's namespaces.
            type_hints = inspect.get_annotations(cls.__init__, eval_str=False)

            if any(isinstance(v, str) for v in type_hints.values()):
                from typing import get_type_hints

                type_hints = get_type_hints(cls.__init__, include_extras=True)
        except Exception:
            # Fallback for older python or hint resolution failure.
            try:
                from typing import get_type_hints

                type_hints = get_type_hints(cls.__init__, include_extras=True)
            except Exception:
                type_hints = {}

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue

            # Skip varargs and kwargs
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Extract type hint
            # Prefer resolved hint, fallback to raw annotation
            annotation = type_hints.get(param_name, param.annotation)

            if annotation == inspect.Parameter.empty:
                # If default value exists, it's optional and we skip dependency injection
                if param.default != inspect.Parameter.empty:
                    continue

                raise DIError(f"Missing type annotation for parameter '{param_name}' in {cls.__qualname__}.__init__")

            # Check for Inject metadata
            dep_info = self._parse_annotation(annotation)
            dep_info["optional"] = dep_info.get("optional", False) or param.default != inspect.Parameter.empty

            deps[param_name] = dep_info

        return deps

    def _parse_annotation(self, annotation: Any) -> dict[str, Any]:
        """Parse type annotation for Inject metadata."""
        from typing import get_args, get_origin

        # Check for Annotated[Type, Inject(...)]
        origin = get_origin(annotation)
        if origin is not None:
            from typing import Annotated

            if origin is Annotated:
                args = get_args(annotation)
                base_type = args[0]
                metadata = args[1:] if len(args) > 1 else ()

                # Look for Inject marker
                normalized_base, optional_from_type = _normalize_optional_token(base_type)
                result = {"token": normalized_base, "optional": optional_from_type}
                for meta in metadata:
                    if hasattr(meta, "_inject_token") and meta._inject_token is not None:
                        result["token"] = meta._inject_token
                    if hasattr(meta, "_inject_tag"):
                        result["tag"] = meta._inject_tag
                    if hasattr(meta, "_inject_optional"):
                        result["optional"] = meta._inject_optional
                return result

        # Plain type annotation
        normalized, optional_from_type = _normalize_optional_token(annotation)
        return {"token": normalized, "optional": optional_from_type}


class FactoryProvider:
    """
    Provider that calls a factory function to produce instances.

    Supports both sync and async factories.
    """

    __slots__ = ("_meta", "_factory", "_is_async", "_dependencies")

    def __init__(
        self,
        factory: Callable,
        scope: str = "app",
        tags: tuple[str, ...] = (),
        name: str | None = None,
    ):
        self._factory = factory
        self._is_async = inspect.iscoroutinefunction(factory)
        self._dependencies = self._extract_dependencies(factory)

        # Build metadata
        module = factory.__module__
        qualname = factory.__qualname__

        # Check for explicit name in metadata if name arg is None
        if name is None and hasattr(factory, "__di_name__") and factory.__di_name__ != factory.__name__:
            name = factory.__di_name__

        token = name or f"{module}.{qualname}"

        try:
            inspect.getsourcefile(factory)
            _, line = inspect.getsourcelines(factory)
        except (TypeError, OSError):
            line = None

        self._meta = ProviderMeta(
            name=name or factory.__name__,
            token=token,
            scope=scope,
            tags=tags,
            module=module,
            qualname=qualname,
            line=line,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Call factory with resolved dependencies."""
        # Resolve dependencies
        resolved_deps = {}
        for dep_name, dep_info in self._dependencies.items():
            resolved = await ctx.container.resolve_async(
                dep_info["token"],
                tag=dep_info.get("tag"),
                optional=dep_info.get("optional", False),
            )
            resolved_deps[dep_name] = resolved

        # Call factory
        if self._is_async:
            return await self._factory(**resolved_deps)
        else:
            return self._factory(**resolved_deps)

    async def shutdown(self) -> None:
        """No-op for factory provider."""
        pass

    def _extract_dependencies(self, factory: Callable) -> dict[str, dict[str, Any]]:
        """Extract dependencies from factory signature.

        Now properly handles Annotated[T, Inject(...)] annotations,
        matching ClassProvider's behavior.
        """
        deps = {}
        sig = inspect.signature(factory)

        # Try to get resolved type hints (handles Annotated properly)
        try:
            from typing import get_type_hints

            type_hints = get_type_hints(factory, include_extras=True)
        except Exception:
            type_hints = {}

        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            annotation = type_hints.get(param_name, param.annotation)
            if annotation == inspect.Parameter.empty:
                # Skip unannotated params with defaults
                if param.default != inspect.Parameter.empty:
                    continue
                continue

            dep_info = self._parse_annotation(annotation)
            dep_info["optional"] = dep_info.get("optional", False) or param.default != inspect.Parameter.empty
            deps[param_name] = dep_info

        return deps

    @staticmethod
    def _parse_annotation(annotation: Any) -> dict[str, Any]:
        """Parse type annotation for Inject/Dep metadata.

        Mirrors ClassProvider._parse_annotation for consistency.
        """
        from typing import get_args, get_origin

        origin = get_origin(annotation)
        if origin is not None:
            try:
                from typing import Annotated

                if origin is Annotated:
                    args = get_args(annotation)
                    base_type = args[0]
                    normalized_base, optional_from_type = _normalize_optional_token(base_type)
                    result = {"token": normalized_base, "optional": optional_from_type}
                    for meta in args[1:]:
                        if hasattr(meta, "_inject_token") and meta._inject_token is not None:
                            result["token"] = meta._inject_token
                        if hasattr(meta, "_inject_tag"):
                            result["tag"] = meta._inject_tag
                        if hasattr(meta, "_inject_optional"):
                            result["optional"] = meta._inject_optional
                    return result
            except ImportError:
                pass

        normalized, optional_from_type = _normalize_optional_token(annotation)
        return {"token": normalized, "optional": optional_from_type}


class ValueProvider:
    """Provider that returns a pre-bound constant value."""

    __slots__ = ("_meta", "_value")

    def __init__(
        self,
        value: Any,
        token: type | str,
        name: str | None = None,
        scope: str = "singleton",
        tags: tuple[str, ...] = (),
    ):
        token_str = token if isinstance(token, str) else f"{token.__module__}.{token.__qualname__}"
        self._value = value
        self._meta = ProviderMeta(
            name=name or "value",
            token=token_str,
            scope=scope,
            tags=tags,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Return pre-bound value."""
        return self._value

    async def shutdown(self) -> None:
        """No-op for value provider."""
        pass


class PoolProvider:
    """
    Provider that manages a pool of instances.

    Uses asyncio.Queue for FIFO/LIFO pooling.
    """

    __slots__ = (
        "_meta",
        "_factory",
        "_pool",
        "_max_size",
        "_strategy",
        "_created",
        "_acquire_timeout",
    )

    def __init__(
        self,
        factory: Callable[[], Coroutine[Any, Any, T]],
        max_size: int,
        token: type | str,
        name: str | None = None,
        strategy: str = "FIFO",  # FIFO or LIFO
        tags: tuple[str, ...] = (),
        acquire_timeout: float = 30.0,  # SEC-DI-05: default 30s timeout
    ):
        # SEC-DI-05: Validate pool size
        if max_size < 1:
            from ..faults.domains import DIResolutionFault

            raise DIResolutionFault(
                provider=str(token),
                reason=f"Pool max_size must be >= 1, got {max_size}",
            )
        self._factory = factory
        self._max_size = max_size
        self._strategy = strategy
        self._pool: asyncio.Queue | None = None
        self._created = 0
        self._acquire_timeout = acquire_timeout

        token_str = token if isinstance(token, str) else f"{token.__module__}.{token.__qualname__}"

        self._meta = ProviderMeta(
            name=name or "pool",
            token=token_str,
            scope="pooled",
            tags=tags,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Acquire instance from pool (creates pool on first call)."""
        if self._pool is None:
            if self._strategy == "LIFO":
                self._pool = asyncio.LifoQueue(maxsize=self._max_size)
            else:
                self._pool = asyncio.Queue(maxsize=self._max_size)

        # Try to get from pool (non-blocking)
        try:
            instance = self._pool.get_nowait()
            return instance
        except asyncio.QueueEmpty:
            pass

        # Pool empty - create new instance if under limit
        if self._created < self._max_size:
            instance = await self._factory()
            self._created += 1
            return instance

        # Wait for available instance (SEC-DI-05: bounded timeout)
        try:
            return await asyncio.wait_for(self._pool.get(), timeout=self._acquire_timeout)
        except asyncio.TimeoutError:
            from ..faults.domains import DIResolutionFault

            raise DIResolutionFault(
                provider=self._meta.token,
                reason=(
                    f"Pool '{self._meta.name}' exhausted: timed out after "
                    f"{self._acquire_timeout}s waiting for an available instance "
                    f"(max_size={self._max_size})"
                ),
            )

    async def release(self, instance: Any) -> None:
        """Release instance back to pool."""
        if self._pool is not None:
            try:
                self._pool.put_nowait(instance)
            except asyncio.QueueFull:
                # Pool full - destroy instance
                if hasattr(instance, "close"):
                    await instance.close()

    @asynccontextmanager
    async def acquire(self, ctx: ResolveCtx = None):
        """Acquire an instance from the pool with auto-release.

        Usage::

            async with pool_provider.acquire(ctx) as conn:
                await conn.execute(...)
            # conn is automatically released back to pool
        """
        instance = await self.instantiate(ctx or ResolveCtx(container=None))
        try:
            yield instance
        finally:
            await self.release(instance)

    async def shutdown(self) -> None:
        """Shutdown pool and clean up instances."""
        if self._pool is None:
            return

        while not self._pool.empty():
            try:
                instance = self._pool.get_nowait()
                if hasattr(instance, "close"):
                    await instance.close()
            except asyncio.QueueEmpty:
                break


class AliasProvider:
    """Provider that aliases one token to another."""

    __slots__ = ("_meta", "_target_token", "_target_tag")

    def __init__(
        self,
        token: type | str,
        target_token: type | str,
        target_tag: str | None = None,
        name: str | None = None,
    ):
        self._target_token = target_token
        self._target_tag = target_tag

        token_str = token if isinstance(token, str) else f"{token.__module__}.{token.__qualname__}"

        self._meta = ProviderMeta(
            name=name or "alias",
            token=token_str,
            scope="singleton",  # Aliases don't create instances
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Resolve target token."""
        return await ctx.container.resolve_async(
            self._target_token,
            tag=self._target_tag,
        )

    async def shutdown(self) -> None:
        """No-op for alias provider."""
        pass


class LazyProxyProvider:
    """
    Provider that creates a lazy proxy for cycle resolution.

    Only use when explicitly allowed in manifest.
    """

    __slots__ = ("_meta", "_target_token", "_target_tag")

    def __init__(
        self,
        token: type | str,
        target_token: type | str,
        target_tag: str | None = None,
        name: str | None = None,
    ):
        self._target_token = target_token
        self._target_tag = target_tag

        token_str = token if isinstance(token, str) else f"{token.__module__}.{token.__qualname__}"

        self._meta = ProviderMeta(
            name=name or "lazy_proxy",
            token=token_str,
            scope="singleton",
            allow_lazy=True,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Create lazy proxy."""
        proxy = _LazyProxy(
            ctx.container,
            self._target_token,
            self._target_tag,
        )
        return proxy

    async def shutdown(self) -> None:
        """No-op for lazy proxy."""
        pass


class _LazyProxy:
    """Lazy proxy that defers resolution until first attribute access."""

    __slots__ = ("_container", "_token", "_tag", "_instance")

    def __init__(self, container, token, tag):
        object.__setattr__(self, "_container", container)
        object.__setattr__(self, "_token", token)
        object.__setattr__(self, "_tag", tag)
        object.__setattr__(self, "_instance", None)

    def _resolve(self):
        """Resolve actual instance on first access.

        SEC-DI-06: Refuse to create throwaway event loops — callers must
        either resolve eagerly during startup or use the async API.
        """
        if object.__getattribute__(self, "_instance") is None:
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                pass
            else:
                from ..faults.domains import DIResolutionFault

                raise DIResolutionFault(
                    provider=str(object.__getattribute__(self, "_token")),
                    reason=(
                        "Cannot lazily resolve synchronously inside a running async "
                        "event loop. Use 'await container.resolve_async(...)' or "
                        "resolve eagerly during startup."
                    ),
                )
            # SEC-DI-06: Use a short-lived loop but with a guard
            _loop = asyncio.new_event_loop()
            try:
                instance = _loop.run_until_complete(
                    object.__getattribute__(self, "_container").resolve_async(
                        object.__getattribute__(self, "_token"),
                        tag=object.__getattribute__(self, "_tag"),
                    )
                )
            finally:
                _loop.close()
            object.__setattr__(self, "_instance", instance)
        return object.__getattribute__(self, "_instance")

    def __getattr__(self, name):
        instance = self._resolve()
        return getattr(instance, name)

    def __call__(self, *args, **kwargs):
        instance = self._resolve()
        return instance(*args, **kwargs)


class ScopedProvider:
    """
    Wrapper provider that enforces scope semantics.

    Used for request/ephemeral scopes.
    """

    __slots__ = ("_meta", "_inner_provider", "_scope")

    def __init__(self, inner: Provider, scope: str):
        self._inner_provider = inner
        self._scope = scope

        # Copy metadata but override scope
        inner_meta = inner.meta
        self._meta = ProviderMeta(
            name=inner_meta.name,
            token=inner_meta.token,
            scope=scope,
            tags=inner_meta.tags,
            module=inner_meta.module,
            qualname=inner_meta.qualname,
            line=inner_meta.line,
            version=inner_meta.version,
            allow_lazy=inner_meta.allow_lazy,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """Delegate to inner provider."""
        return await self._inner_provider.instantiate(ctx)

    async def shutdown(self) -> None:
        """Delegate to inner provider."""
        await self._inner_provider.shutdown()


class BlueprintProvider:
    """
    DI Provider that creates Blueprint instances with request context.

    When resolved, the provider:
    1. Parses the request body (JSON or form data)
    2. Creates the Blueprint with ``data=body`` and a context dict
       containing ``request``, ``container``, and ``identity``
    3. Returns the **Blueprint instance** (not yet sealed)

    The handler can then call ``blueprint.is_sealed()`` and ``blueprint.imprint()``.

    Usage::

        from aquilia.di import Container
        from aquilia.di.providers import BlueprintProvider

        container.register(
            BlueprintProvider(UserBlueprint, scope="request")
        )

        # In handler:
        async def create_user(self, ctx, blueprint: UserBlueprint):
            blueprint.is_sealed(raise_fault=True)
            user = await blueprint.imprint()
            return Response.json(UserBlueprint(instance=user).data, status=201)
    """

    __slots__ = ("_meta", "_blueprint_cls", "_auto_seal")

    def __init__(
        self,
        blueprint_cls: type,
        *,
        scope: str = "request",
        auto_seal: bool = False,
        tags: tuple[str, ...] = (),
    ):
        self._blueprint_cls = blueprint_cls
        self._auto_seal = auto_seal

        module = blueprint_cls.__module__
        qualname = blueprint_cls.__qualname__
        token = f"{module}.{qualname}"

        try:
            inspect.getsourcefile(blueprint_cls)
            _, line = inspect.getsourcelines(blueprint_cls)
        except (TypeError, OSError):
            line = None

        self._meta = ProviderMeta(
            name=blueprint_cls.__name__,
            token=token,
            scope=scope,
            tags=tags,
            module=module,
            qualname=qualname,
            line=line,
        )

    @property
    def meta(self) -> ProviderMeta:
        return self._meta

    async def instantiate(self, ctx: ResolveCtx) -> Any:
        """
        Create Blueprint instance with request data from DI context.

        The provider looks for a ``Request`` instance in the container
        to parse the body.  If no request is available (e.g. testing),
        the Blueprint is created without data.
        """
        container = ctx.container

        # Try to resolve request from container
        request = None

        with suppress(Exception):
            request = await container.resolve_async("aquilia.request.Request", optional=True)

        if request is not None:
            # Delegate to the hardened integration layer which handles:
            # - Body size limits
            # - Content-Type detection
            # - Form unflatten depth/key limits
            # - DI parameter extraction (Query, Header)
            from aquilia.blueprints.integration import bind_blueprint_to_request

            # Get identity for context
            identity = None
            state = getattr(request, "state", None)
            if state:
                identity = state.get("identity") if isinstance(state, dict) else getattr(state, "identity", None)

            extra_context = {"container": container}
            if identity is not None:
                extra_context["identity"] = identity

            bp_instance = await bind_blueprint_to_request(
                self._blueprint_cls,
                request,
                context=extra_context,
            )
        else:
            # No request available (e.g. testing) -- create empty Blueprint
            bp_instance = self._blueprint_cls(
                data={},
                context={"container": container},
            )

        if self._auto_seal:
            bp_instance.is_sealed(raise_fault=True)

        return bp_instance

    async def shutdown(self) -> None:
        """No-op for blueprint provider."""
        pass
