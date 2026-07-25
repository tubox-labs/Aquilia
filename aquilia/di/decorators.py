"""
Decorators and injection helpers for ergonomic DI usage.
"""

import functools
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypeVar, get_type_hints

from .scopes import ServiceScopeLiteral

if TYPE_CHECKING:
    from collections.abc import Callable as _Callable

T = TypeVar("T")


@dataclass
class Inject:
    """
    Injection metadata marker for parameter-level dependency injection.

    Args:
        token: Explicit provider token (type or string key). Inferred from
            the base type hint if ``None``.
        tag: Optional container tag for disambiguating between multiple providers
            registered for the same interface or token.
        optional: If ``True``, resolves to ``None`` if no provider is found in the
            container, rather than raising a ``ProviderNotFoundError``.

    Returns:
        An ``Inject`` metadata marker instance for use inside ``Annotated[...]``.

    Note:
        When used as ``Annotated[typing.Any, Inject("modules.auth.services:CrossAppService")]``,
        the DI container unwraps the metadata marker and resolves the target string
        or class token directly from the container registry.

    Usage::

        from typing import Annotated, Any
        from aquilia.di import Inject, inject

        # Simple type-inferred injection
        class UserService:
            def __init__(self, repo: UserRepo):
                self.repo = repo

        # Tagged injection for disambiguation
        class OrderService:
            def __init__(
                self,
                primary_db: Annotated[Database, Inject(tag="primary")],
                replica_db: Annotated[Database, Inject(tag="readonly")],
            ):
                self.primary_db = primary_db
                self.replica_db = replica_db

        # String token cross-module injection
        class AuthController:
            def __init__(
                self,
                cross_app: Annotated[Any, Inject("modules.auth.services:CrossAppService")],
            ):
                self.cross_app = cross_app

        # Optional injection fallback
        class CacheManager:
            def __init__(
                self,
                redis: Annotated[RedisClient, Inject(optional=True)],
            ):
                self.redis = redis
    """

    token: type | str | None = None
    tag: str | None = None
    optional: bool = False

    # Internal marker for provider introspection
    _inject_token: type | str | None = None
    _inject_tag: str | None = None
    _inject_optional: bool = False

    def __post_init__(self):
        self._inject_token = self.token
        self._inject_tag = self.tag
        self._inject_optional = self.optional


def inject(
    token: type | str | None = None,
    *,
    tag: str | None = None,
    optional: bool = False,
) -> Inject:
    """
    Factory function creating injection metadata markers for type annotations.

    Args:
        token: Optional explicit provider token (type or string key). Inferred
            from base type hint if ``None``.
        tag: Optional container tag for disambiguating between multiple implementations.
        optional: If ``True``, resolves to ``None`` if the provider is not found
            in the container, preventing resolution errors.

    Returns:
        An :class:`Inject` metadata object configured with the specified parameters.

    Note:
        This is a lower-case helper equivalent to instantiating :class:`Inject` directly.
        It integrates with ``Annotated[T, inject(...)]`` across controllers, services,
        and request DAG dependency resolution.

    Usage::

        from typing import Annotated
        from aquilia.di import inject

        def handler(
            db: Annotated[Database, inject(tag="readonly")],
            cache: Annotated[Cache, inject(optional=True)],
            auth: Annotated[Any, inject("modules.auth.services:CrossAppService")],
        ):
            ...
    """
    return Inject(token=token, tag=tag, optional=optional)


def service(
    *,
    scope: ServiceScopeLiteral = "app",
    tag: str | None = None,
    name: str | None = None,
    when: "_Callable[[ConditionContext], bool] | None" = None,
) -> Callable[[type[T]], type[T]]:
    """
    Decorator to mark a class as a DI service.

    Args:
        scope: Service scope (singleton, app, request, transient, pooled, ephemeral)
        tag: Optional tag for disambiguation
        name: Optional explicit service name
        when: Optional registration predicate. Receives a
            :class:`ConditionContext` (environment + config) and returns
            ``True`` to register the service, ``False`` to skip it. Enables
            environment/feature-gated providers (Spring ``@Profile`` /
            ``@ConditionalOnProperty`` equivalent). Honoured when
            ``DISettings.enable_conditional_providers`` is on.

    Returns:
        Decorator function

    Example::

        @service(scope="request", tag="primary")
        class UserService:
            def __init__(self, repo: UserRepo):
                self.repo = repo

    Conditional example — only in production::

        @service(when=lambda c: c.env == "prod")
        class RealPaymentGateway: ...

        @service(when=lambda c: c.env != "prod")
        class FakePaymentGateway: ...
    """

    def decorator(cls: type[T]) -> type[T]:
        # Attach metadata to class
        cls.__di_scope__ = scope  # type: ignore
        cls.__di_tag__ = tag  # type: ignore
        cls.__di_name__ = name or cls.__name__  # type: ignore
        if when is not None:
            cls.__di_condition__ = when  # type: ignore
        return cls

    return decorator


def factory(
    *,
    scope: ServiceScopeLiteral = "app",
    tag: str | None = None,
    name: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to mark a function as a DI factory.

    Args:
        scope: Service scope
        tag: Optional tag for disambiguation
        name: Optional explicit factory name

    Returns:
        Decorator function

    Example:
        @factory(scope="singleton", name="db_pool")
        async def create_db_pool(config: Config) -> DatabasePool:
            return await DatabasePool.connect(config.db_url)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        # Attach metadata to function
        func.__di_scope__ = scope  # type: ignore
        func.__di_tag__ = tag  # type: ignore
        func.__di_name__ = name or func.__name__  # type: ignore
        func.__di_factory__ = True  # type: ignore
        return func

    return decorator


def provides(
    token: type | str,
    *,
    scope: ServiceScopeLiteral = "app",
    tag: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator to explicitly declare what a factory provides.

    Useful when return type annotation is generic or abstract.

    Args:
        token: Type or string key that this factory provides
        scope: Service scope
        tag: Optional tag

    Returns:
        Decorator function

    Example:
        @provides(UserRepository, scope="app", tag="sql")
        def create_sql_repo(db: Database) -> UserRepository:
            return SqlUserRepository(db)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func.__di_provides__ = token  # type: ignore
        func.__di_scope__ = scope  # type: ignore
        func.__di_tag__ = tag  # type: ignore
        func.__di_factory__ = True  # type: ignore
        return func

    return decorator


def auto_inject(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to auto-inject dependencies into a function.

    Looks up dependencies from a thread-local container.

    WARNING: This is convenience sugar with some overhead.
    Prefer explicit dependency passing in hot paths.

    Example:
        @auto_inject
        async def my_handler(request: Request, db: Database):
            # db is automatically resolved from request container
            ...
    """
    from .compat import get_request_container

    sig = getattr(func, "__signature__", None)
    try:
        hints = get_type_hints(func, include_extras=True) if sig is None else None
    except Exception:
        hints = getattr(func, "__annotations__", {})

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Get request container from context
        container = get_request_container()
        if container is None:
            from ..faults.domains import DIResolutionFault

            raise DIResolutionFault(
                provider="auto_inject",
                reason="No request container in context; cannot auto-inject",
            )

        # SEC-DI-12: Warn if auto-injecting from a non-request container
        if hasattr(container, "_scope") and container._scope not in ("request", "ephemeral"):
            import logging as _log

            _log.getLogger("aquilia.di").warning(
                "@auto_inject resolving from %s-scoped container; expected request/ephemeral scope.",
                container._scope,
            )

        # Resolve missing dependencies
        if sig:
            params = sig.parameters
        else:
            import inspect

            params = inspect.signature(func).parameters

        for param_name, param in params.items():
            if param_name in kwargs or param_name == "self":
                continue

            # Get type hint
            type_hint = hints.get(param_name) if hints else param.annotation
            if type_hint is None or type_hint == param.empty:
                continue

            # Resolve from container
            try:
                resolved = await container.resolve_async(type_hint)
                kwargs[param_name] = resolved
            except Exception:
                # Optional or has default - skip
                if param.default != param.empty:
                    continue
                raise

        return await func(*args, **kwargs)

    return wrapper


# Convenience alias
injectable = service


# ══════════════════════════════════════════════════════════════════════════
#  Conditional / environment-gated providers
# ══════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True, slots=True)
class ConditionContext:
    """Context handed to a conditional-registration predicate.

    Attributes:
        env: The active environment label (``AQUILIA_ENV`` or config ``env``).
        config: The raw config mapping/loader, for property-based conditions.

    Example::

        @conditional(lambda c: c.env == "prod" and c.get("cache.backend") == "redis")
        class RedisCacheWarmup: ...
    """

    env: str = "prod"
    config: Any = None

    def get(self, path: str, default: Any = None) -> Any:
        """Dot-path lookup into the config (``"cache.backend"``).

        Works with a :class:`~aquilia.config.ConfigLoader` (via its ``get``)
        or a plain nested dict.
        """
        cfg = self.config
        if cfg is None:
            return default
        if hasattr(cfg, "get") and not isinstance(cfg, dict):
            try:
                return cfg.get(path, default)
            except TypeError:
                pass
        current: Any = cfg
        for part in path.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def is_env(self, *names: str) -> bool:
        """Return whether the active env matches any of *names* (case-insensitive)."""
        low = self.env.lower()
        return any(low == n.lower() for n in names)


def conditional(
    predicate: "_Callable[[ConditionContext], bool]",
) -> Callable[[type[T]], type[T]]:
    """Class decorator: register the service only when *predicate* is true.

    A standalone form of ``@service(when=...)`` for classes already decorated
    (or discovered by convention). Honoured when
    ``DISettings.enable_conditional_providers`` is on.

    Args:
        predicate: Callable taking a :class:`ConditionContext`, returning
            ``True`` to register.

    Example::

        @conditional(lambda c: c.is_env("prod", "staging"))
        class MetricsExporter: ...
    """

    def decorator(cls: type[T]) -> type[T]:
        cls.__di_condition__ = predicate  # type: ignore[attr-defined]
        return cls

    return decorator


def should_register(target: Any, ctx: ConditionContext) -> bool:
    """Evaluate a target's ``@conditional`` / ``when=`` predicate.

    Returns ``True`` when the target has no condition, or its predicate passes.
    Predicate errors are treated as ``False`` (skip) and never crash the boot.

    Args:
        target: A class or factory possibly carrying ``__di_condition__``.
        ctx: The :class:`ConditionContext` to evaluate against.

    Returns:
        Whether the target should be registered.

    Example::

        if should_register(UserService, ConditionContext(env="prod", config=loader)):
            container.register(ClassProvider(UserService))
    """
    predicate = getattr(target, "__di_condition__", None)
    if predicate is None:
        return True
    try:
        return bool(predicate(ctx))
    except Exception:
        import logging as _log

        _log.getLogger("aquilia.di").warning(
            "Condition predicate for %r raised; skipping registration.",
            getattr(target, "__name__", target),
        )
        return False
